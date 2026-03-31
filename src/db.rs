use std::path::Path;

use rusqlite::{Connection, OptionalExtension, params};

use crate::errors::Result;
use crate::metadata::MetadataRecord;

// ─────────────────────────────────────────────────────────────
// Shared record types
// ─────────────────────────────────────────────────────────────

#[derive(Clone, Debug)]
pub struct MissionRecord {
    pub name: String,
    pub path: String,
    pub metadata: MetadataRecord,
}

#[derive(Clone, Debug)]
pub struct StagedFileRecord {
    pub origin_path: String,
    pub target_path: String,
    pub hash: String,
}

#[derive(Clone, Debug)]
pub struct DatasetMeta {
    pub day_0: String,
    pub pushed: bool,
    pub version: i32,
    pub last_country: Option<String>,
    pub last_region: Option<String>,
    pub last_site: Option<String>,
}

// ─────────────────────────────────────────────────────────────
// DatasetDb  –  .e4edm.db in the dataset root
// ─────────────────────────────────────────────────────────────

pub struct DatasetDb {
    conn: Connection,
}

impl DatasetDb {
    /// Opens `.e4edm.db` in `root`, creating tables if they don't exist.
    pub fn open(root: &Path) -> Result<Self> {
        let db_path = root.join(".e4edm.db");
        let conn = Connection::open(&db_path)?;
        let db = DatasetDb { conn };
        db.create_tables()?;
        Ok(db)
    }

    fn create_tables(&self) -> Result<()> {
        self.conn.execute_batch("
            PRAGMA journal_mode=WAL;

            CREATE TABLE IF NOT EXISTS dataset_meta (
                id              INTEGER PRIMARY KEY CHECK (id = 1),
                day_0           TEXT NOT NULL,
                pushed          INTEGER NOT NULL DEFAULT 0,
                version         INTEGER NOT NULL DEFAULT 2,
                last_country    TEXT,
                last_region     TEXT,
                last_site       TEXT
            );

            CREATE TABLE IF NOT EXISTS missions (
                name            TEXT PRIMARY KEY,
                path            TEXT NOT NULL,
                timestamp       TEXT NOT NULL,
                device          TEXT NOT NULL,
                country         TEXT NOT NULL,
                region          TEXT NOT NULL,
                site            TEXT NOT NULL,
                mission_name    TEXT NOT NULL,
                properties      TEXT NOT NULL DEFAULT '{}',
                notes           TEXT NOT NULL DEFAULT ''
            );

            CREATE TABLE IF NOT EXISTS mission_staged_files (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                mission_name    TEXT NOT NULL,
                origin_path     TEXT NOT NULL,
                target_path     TEXT NOT NULL,
                hash            TEXT NOT NULL,
                UNIQUE(origin_path, target_path)
            );

            CREATE TABLE IF NOT EXISTS mission_committed_files (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                mission_name    TEXT NOT NULL,
                path            TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS dataset_staged_files (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                path            TEXT NOT NULL UNIQUE
            );

            CREATE TABLE IF NOT EXISTS dataset_committed_files (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                path            TEXT NOT NULL UNIQUE
            );
        ")?;
        Ok(())
    }

    // ── dataset_meta ──────────────────────────────────────────

    pub fn init_dataset(&self, day_0: &str, version: i32) -> Result<()> {
        self.conn.execute(
            "INSERT OR IGNORE INTO dataset_meta (id, day_0, pushed, version) VALUES (1, ?1, 0, ?2)",
            params![day_0, version],
        )?;
        Ok(())
    }

    pub fn get_dataset_meta(&self) -> Result<DatasetMeta> {
        let meta = self.conn.query_row(
            "SELECT day_0, pushed, version, last_country, last_region, last_site \
             FROM dataset_meta WHERE id = 1",
            [],
            |row| {
                Ok(DatasetMeta {
                    day_0: row.get(0)?,
                    pushed: row.get::<_, i32>(1)? != 0,
                    version: row.get(2)?,
                    last_country: row.get(3)?,
                    last_region: row.get(4)?,
                    last_site: row.get(5)?,
                })
            },
        )?;
        Ok(meta)
    }

    pub fn update_dataset_meta(&self, meta: &DatasetMeta) -> Result<()> {
        self.conn.execute(
            "UPDATE dataset_meta SET day_0=?1, pushed=?2, version=?3, \
             last_country=?4, last_region=?5, last_site=?6 WHERE id=1",
            params![
                meta.day_0,
                meta.pushed as i32,
                meta.version,
                meta.last_country,
                meta.last_region,
                meta.last_site,
            ],
        )?;
        Ok(())
    }

    // ── missions ──────────────────────────────────────────────

    pub fn insert_mission(&self, mission: &MissionRecord) -> Result<()> {
        self.conn.execute(
            "INSERT OR REPLACE INTO missions \
             (name, path, timestamp, device, country, region, site, mission_name, properties, notes) \
             VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7, ?8, ?9, ?10)",
            params![
                mission.name,
                mission.path,
                mission.metadata.timestamp,
                mission.metadata.device,
                mission.metadata.country,
                mission.metadata.region,
                mission.metadata.site,
                mission.metadata.mission_name,
                mission.metadata.properties,
                mission.metadata.notes,
            ],
        )?;
        Ok(())
    }

    pub fn get_missions(&self) -> Result<Vec<MissionRecord>> {
        let mut stmt = self.conn.prepare(
            "SELECT name, path, timestamp, device, country, region, site, mission_name, properties, notes \
             FROM missions",
        )?;
        let rows = stmt.query_map([], |row| {
            Ok(MissionRecord {
                name: row.get(0)?,
                path: row.get(1)?,
                metadata: MetadataRecord {
                    timestamp: row.get(2)?,
                    device: row.get(3)?,
                    country: row.get(4)?,
                    region: row.get(5)?,
                    site: row.get(6)?,
                    mission_name: row.get(7)?,
                    properties: row.get(8)?,
                    notes: row.get(9)?,
                },
            })
        })?;
        let mut missions = Vec::new();
        for row in rows {
            missions.push(row?);
        }
        Ok(missions)
    }


    // ── mission staged files ───────────────────────────────────

    pub fn set_mission_staged_files(
        &self,
        mission_name: &str,
        files: &[StagedFileRecord],
    ) -> Result<()> {
        let tx = self.conn.unchecked_transaction()?;
        tx.execute(
            "DELETE FROM mission_staged_files WHERE mission_name=?1",
            params![mission_name],
        )?;
        for f in files {
            tx.execute(
                "INSERT OR IGNORE INTO mission_staged_files \
                 (mission_name, origin_path, target_path, hash) VALUES (?1, ?2, ?3, ?4)",
                params![mission_name, f.origin_path, f.target_path, f.hash],
            )?;
        }
        tx.commit()?;
        Ok(())
    }

    pub fn get_mission_staged_files(&self, mission_name: &str) -> Result<Vec<StagedFileRecord>> {
        let mut stmt = self.conn.prepare(
            "SELECT origin_path, target_path, hash FROM mission_staged_files \
             WHERE mission_name=?1",
        )?;
        let rows = stmt.query_map(params![mission_name], |row| {
            Ok(StagedFileRecord {
                origin_path: row.get(0)?,
                target_path: row.get(1)?,
                hash: row.get(2)?,
            })
        })?;
        let mut files = Vec::new();
        for r in rows {
            files.push(r?);
        }
        Ok(files)
    }

    pub fn clear_mission_staged_files(&self, mission_name: &str) -> Result<()> {
        self.conn.execute(
            "DELETE FROM mission_staged_files WHERE mission_name=?1",
            params![mission_name],
        )?;
        Ok(())
    }

    // ── mission committed files ────────────────────────────────

    pub fn add_mission_committed_files(
        &self,
        mission_name: &str,
        files: &[String],
    ) -> Result<()> {
        let tx = self.conn.unchecked_transaction()?;
        for f in files {
            tx.execute(
                "INSERT OR IGNORE INTO mission_committed_files (mission_name, path) VALUES (?1, ?2)",
                params![mission_name, f],
            )?;
        }
        tx.commit()?;
        Ok(())
    }

    pub fn get_mission_committed_files(&self, mission_name: &str) -> Result<Vec<String>> {
        let mut stmt = self.conn.prepare(
            "SELECT path FROM mission_committed_files WHERE mission_name=?1",
        )?;
        let rows = stmt.query_map(params![mission_name], |row| row.get(0))?;
        let mut files = Vec::new();
        for r in rows {
            files.push(r?);
        }
        Ok(files)
    }

    pub fn delete_mission(&self, mission_name: &str) -> Result<()> {
        let tx = self.conn.unchecked_transaction()?;
        tx.execute("DELETE FROM missions WHERE name=?1", params![mission_name])?;
        tx.execute(
            "DELETE FROM mission_staged_files WHERE mission_name=?1",
            params![mission_name],
        )?;
        tx.execute(
            "DELETE FROM mission_committed_files WHERE mission_name=?1",
            params![mission_name],
        )?;
        tx.commit()?;
        Ok(())
    }

    // ── dataset staged files ───────────────────────────────────

    pub fn set_dataset_staged_files(&self, files: &[String]) -> Result<()> {
        let tx = self.conn.unchecked_transaction()?;
        tx.execute("DELETE FROM dataset_staged_files", [])?;
        for f in files {
            tx.execute(
                "INSERT OR IGNORE INTO dataset_staged_files (path) VALUES (?1)",
                params![f],
            )?;
        }
        tx.commit()?;
        Ok(())
    }

    pub fn get_dataset_staged_files(&self) -> Result<Vec<String>> {
        let mut stmt = self.conn.prepare("SELECT path FROM dataset_staged_files")?;
        let rows = stmt.query_map([], |row| row.get(0))?;
        let mut files = Vec::new();
        for r in rows {
            files.push(r?);
        }
        Ok(files)
    }

    pub fn clear_dataset_staged_files(&self) -> Result<()> {
        self.conn.execute("DELETE FROM dataset_staged_files", [])?;
        Ok(())
    }

    // ── dataset committed files ────────────────────────────────

    pub fn add_dataset_committed_files(&self, files: &[String]) -> Result<()> {
        let tx = self.conn.unchecked_transaction()?;
        for f in files {
            tx.execute(
                "INSERT OR IGNORE INTO dataset_committed_files (path) VALUES (?1)",
                params![f],
            )?;
        }
        tx.commit()?;
        Ok(())
    }

    pub fn get_dataset_committed_files(&self) -> Result<Vec<String>> {
        let mut stmt = self.conn.prepare("SELECT path FROM dataset_committed_files")?;
        let rows = stmt.query_map([], |row| row.get(0))?;
        let mut files = Vec::new();
        for r in rows {
            files.push(r?);
        }
        Ok(files)
    }
}

// ─────────────────────────────────────────────────────────────
// ManagerDb  –  config.db in the app config dir
// ─────────────────────────────────────────────────────────────

#[derive(Clone, Debug)]
pub struct DatasetInfo {
    pub name: String,
    pub root_path: String,
    pub pushed: bool,
    pub last_country: Option<String>,
    pub last_region: Option<String>,
    pub last_site: Option<String>,
    pub day_0: Option<String>,
}

pub struct ManagerDb {
    conn: Connection,
}

impl ManagerDb {
    /// Opens `config.db` in `config_dir`, creating tables if they don't exist.
    pub fn open(config_dir: &Path) -> Result<Self> {
        std::fs::create_dir_all(config_dir)?;
        let db_path = config_dir.join("config.db");
        let conn = Connection::open(&db_path)?;
        let db = ManagerDb { conn };
        db.create_tables()?;
        Ok(db)
    }

    fn create_tables(&self) -> Result<()> {
        self.conn.execute_batch("
            PRAGMA journal_mode=WAL;

            CREATE TABLE IF NOT EXISTS config (
                key     TEXT PRIMARY KEY,
                value   TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS datasets (
                name            TEXT PRIMARY KEY,
                root_path       TEXT NOT NULL,
                pushed          INTEGER NOT NULL DEFAULT 0,
                last_country    TEXT,
                last_region     TEXT,
                last_site       TEXT,
                day_0           TEXT
            );
        ")?;
        Ok(())
    }

    // ── config key/value ───────────────────────────────────────

    pub fn get_config(&self, key: &str) -> Result<Option<String>> {
        let val = self
            .conn
            .query_row(
                "SELECT value FROM config WHERE key=?1",
                params![key],
                |row| row.get(0),
            )
            .optional()?;
        Ok(val)
    }

    pub fn set_config(&self, key: &str, value: &str) -> Result<()> {
        self.conn.execute(
            "INSERT OR REPLACE INTO config (key, value) VALUES (?1, ?2)",
            params![key, value],
        )?;
        Ok(())
    }

    // ── datasets ──────────────────────────────────────────────

    pub fn get_all_datasets(&self) -> Result<Vec<DatasetInfo>> {
        let mut stmt = self.conn.prepare(
            "SELECT name, root_path, pushed, last_country, last_region, last_site, day_0 \
             FROM datasets",
        )?;
        let rows = stmt.query_map([], |row| {
            Ok(DatasetInfo {
                name: row.get(0)?,
                root_path: row.get(1)?,
                pushed: row.get::<_, i32>(2)? != 0,
                last_country: row.get(3)?,
                last_region: row.get(4)?,
                last_site: row.get(5)?,
                day_0: row.get(6)?,
            })
        })?;
        let mut infos = Vec::new();
        for r in rows {
            infos.push(r?);
        }
        Ok(infos)
    }

    pub fn upsert_dataset(&self, info: &DatasetInfo) -> Result<()> {
        self.conn.execute(
            "INSERT OR REPLACE INTO datasets \
             (name, root_path, pushed, last_country, last_region, last_site, day_0) \
             VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7)",
            params![
                info.name,
                info.root_path,
                info.pushed as i32,
                info.last_country,
                info.last_region,
                info.last_site,
                info.day_0,
            ],
        )?;
        Ok(())
    }

    pub fn remove_dataset(&self, name: &str) -> Result<()> {
        self.conn
            .execute("DELETE FROM datasets WHERE name=?1", params![name])?;
        Ok(())
    }
}

// ─────────────────────────────────────────────────────────────
// Tests
// ─────────────────────────────────────────────────────────────

#[cfg(test)]
mod tests {
    use super::*;
    use crate::metadata::MetadataRecord;
    use tempfile::tempdir;

    fn open(root: &std::path::Path) -> DatasetDb {
        DatasetDb::open(root).unwrap()
    }

    fn mission(name: &str) -> MissionRecord {
        MissionRecord {
            name: name.to_string(),
            path: format!("/ds/{}", name),
            metadata: MetadataRecord {
                timestamp: "2023-03-02T10:00:00+00:00".to_string(),
                device: "device1".to_string(),
                country: "USA".to_string(),
                region: "California".to_string(),
                site: "SD".to_string(),
                mission_name: name.to_string(),
                properties: "{}".to_string(),
                notes: String::new(),
            },
        }
    }

    // ── dataset_meta ────────────────────────────────────────────

    #[test]
    fn init_and_get_meta_roundtrip() {
        let tmp = tempdir().unwrap();
        let db = open(tmp.path());
        db.init_dataset("2023-03-02", 2).unwrap();
        let meta = db.get_dataset_meta().unwrap();
        assert_eq!(meta.day_0, "2023-03-02");
        assert!(!meta.pushed);
        assert_eq!(meta.version, 2);
        assert!(meta.last_country.is_none());
    }

    #[test]
    fn update_meta_persists_pushed_and_location() {
        let tmp = tempdir().unwrap();
        let db = open(tmp.path());
        db.init_dataset("2023-03-02", 2).unwrap();
        let updated = DatasetMeta {
            day_0: "2023-03-02".to_string(),
            pushed: true,
            version: 2,
            last_country: Some("USA".to_string()),
            last_region: Some("California".to_string()),
            last_site: Some("SD".to_string()),
        };
        db.update_dataset_meta(&updated).unwrap();
        let loaded = db.get_dataset_meta().unwrap();
        assert!(loaded.pushed);
        assert_eq!(loaded.last_country.as_deref(), Some("USA"));
        assert_eq!(loaded.last_region.as_deref(), Some("California"));
        assert_eq!(loaded.last_site.as_deref(), Some("SD"));
    }

    // ── missions ────────────────────────────────────────────────

    #[test]
    fn insert_and_get_missions_roundtrip() {
        let tmp = tempdir().unwrap();
        let db = open(tmp.path());
        db.insert_mission(&mission("ED-00 M1")).unwrap();
        let missions = db.get_missions().unwrap();
        assert_eq!(missions.len(), 1);
        assert_eq!(missions[0].name, "ED-00 M1");
        assert_eq!(missions[0].metadata.country, "USA");
    }

    #[test]
    fn insert_mission_upserts_on_duplicate_name() {
        let tmp = tempdir().unwrap();
        let db = open(tmp.path());
        db.insert_mission(&mission("ED-00 M1")).unwrap();
        // Insert again — should not error (OR REPLACE)
        db.insert_mission(&mission("ED-00 M1")).unwrap();
        assert_eq!(db.get_missions().unwrap().len(), 1);
    }

    #[test]
    fn get_missions_returns_all_records() {
        let tmp = tempdir().unwrap();
        let db = open(tmp.path());
        db.insert_mission(&mission("ED-00 M1")).unwrap();
        db.insert_mission(&mission("ED-00 M2")).unwrap();
        assert_eq!(db.get_missions().unwrap().len(), 2);
    }

    #[test]
    fn delete_mission_removes_record_and_related_file_rows() {
        let tmp = tempdir().unwrap();
        let db = open(tmp.path());
        db.insert_mission(&mission("ED-00 M1")).unwrap();

        db.set_mission_staged_files(
            "ED-00 M1",
            &[StagedFileRecord {
                origin_path: "/src/a.bin".to_string(),
                target_path: "/ds/ED-00/M1/a.bin".to_string(),
                hash: "abc".to_string(),
            }],
        )
        .unwrap();
        db.add_mission_committed_files("ED-00 M1", &["a.bin".to_string()])
            .unwrap();

        db.delete_mission("ED-00 M1").unwrap();

        assert!(db.get_missions().unwrap().is_empty());
        assert!(db.get_mission_staged_files("ED-00 M1").unwrap().is_empty());
        assert!(db.get_mission_committed_files("ED-00 M1").unwrap().is_empty());
    }

    #[test]
    fn delete_mission_does_not_affect_other_missions() {
        let tmp = tempdir().unwrap();
        let db = open(tmp.path());
        db.insert_mission(&mission("ED-00 M1")).unwrap();
        db.insert_mission(&mission("ED-00 M2")).unwrap();
        db.add_mission_committed_files("ED-00 M2", &["data.bin".to_string()])
            .unwrap();

        db.delete_mission("ED-00 M1").unwrap();

        let remaining = db.get_missions().unwrap();
        assert_eq!(remaining.len(), 1);
        assert_eq!(remaining[0].name, "ED-00 M2");
        assert_eq!(
            db.get_mission_committed_files("ED-00 M2").unwrap().len(),
            1
        );
    }

    // ── mission staged files ─────────────────────────────────────

    #[test]
    fn staged_files_set_and_get_roundtrip() {
        let tmp = tempdir().unwrap();
        let db = open(tmp.path());
        let files = vec![
            StagedFileRecord {
                origin_path: "/src/a.bin".to_string(),
                target_path: "/ds/a.bin".to_string(),
                hash: "aaa".to_string(),
            },
            StagedFileRecord {
                origin_path: "/src/b.bin".to_string(),
                target_path: "/ds/b.bin".to_string(),
                hash: "bbb".to_string(),
            },
        ];
        db.set_mission_staged_files("ED-00 M1", &files).unwrap();
        let loaded = db.get_mission_staged_files("ED-00 M1").unwrap();
        assert_eq!(loaded.len(), 2);
        assert!(loaded.iter().any(|f| f.hash == "aaa"));
    }

    #[test]
    fn set_staged_files_replaces_previous_entries() {
        let tmp = tempdir().unwrap();
        let db = open(tmp.path());
        let first = vec![StagedFileRecord {
            origin_path: "/src/a.bin".to_string(),
            target_path: "/ds/a.bin".to_string(),
            hash: "aaa".to_string(),
        }];
        db.set_mission_staged_files("ED-00 M1", &first).unwrap();

        let second = vec![StagedFileRecord {
            origin_path: "/src/b.bin".to_string(),
            target_path: "/ds/b.bin".to_string(),
            hash: "bbb".to_string(),
        }];
        db.set_mission_staged_files("ED-00 M1", &second).unwrap();

        let loaded = db.get_mission_staged_files("ED-00 M1").unwrap();
        assert_eq!(loaded.len(), 1);
        assert_eq!(loaded[0].hash, "bbb");
    }

    #[test]
    fn clear_staged_files_leaves_empty() {
        let tmp = tempdir().unwrap();
        let db = open(tmp.path());
        db.set_mission_staged_files(
            "ED-00 M1",
            &[StagedFileRecord {
                origin_path: "/src/a.bin".to_string(),
                target_path: "/ds/a.bin".to_string(),
                hash: "aaa".to_string(),
            }],
        )
        .unwrap();
        db.clear_mission_staged_files("ED-00 M1").unwrap();
        assert!(db.get_mission_staged_files("ED-00 M1").unwrap().is_empty());
    }

    // ── mission committed files ──────────────────────────────────

    #[test]
    fn committed_files_add_and_get_roundtrip() {
        let tmp = tempdir().unwrap();
        let db = open(tmp.path());
        db.add_mission_committed_files(
            "ED-00 M1",
            &["a.bin".to_string(), "b.bin".to_string()],
        )
        .unwrap();
        let loaded = db.get_mission_committed_files("ED-00 M1").unwrap();
        assert_eq!(loaded.len(), 2);
        assert!(loaded.contains(&"a.bin".to_string()));
    }

    #[test]
    fn committed_files_for_different_missions_are_independent() {
        let tmp = tempdir().unwrap();
        let db = open(tmp.path());
        db.add_mission_committed_files("ED-00 M1", &["a.bin".to_string()])
            .unwrap();
        db.add_mission_committed_files("ED-00 M2", &["a.bin".to_string()])
            .unwrap();
        assert_eq!(
            db.get_mission_committed_files("ED-00 M1").unwrap().len(),
            1
        );
        assert_eq!(
            db.get_mission_committed_files("ED-00 M2").unwrap().len(),
            1
        );
    }

    // ── dataset staged / committed files ────────────────────────

    #[test]
    fn dataset_staged_files_set_and_clear() {
        let tmp = tempdir().unwrap();
        let db = open(tmp.path());
        db.set_dataset_staged_files(&["/ds/readme.md".to_string()])
            .unwrap();
        assert_eq!(db.get_dataset_staged_files().unwrap().len(), 1);
        db.clear_dataset_staged_files().unwrap();
        assert!(db.get_dataset_staged_files().unwrap().is_empty());
    }

    #[test]
    fn dataset_committed_files_add_and_get() {
        let tmp = tempdir().unwrap();
        let db = open(tmp.path());
        db.add_dataset_committed_files(&[
            "/ds/readme.md".to_string(),
            "/ds/readme.docx".to_string(),
        ])
        .unwrap();
        let loaded = db.get_dataset_committed_files().unwrap();
        assert_eq!(loaded.len(), 2);
    }

    #[test]
    fn dataset_committed_files_are_deduplicated() {
        let tmp = tempdir().unwrap();
        let db = open(tmp.path());
        db.add_dataset_committed_files(&["/ds/readme.md".to_string()])
            .unwrap();
        db.add_dataset_committed_files(&["/ds/readme.md".to_string()])
            .unwrap();
        assert_eq!(db.get_dataset_committed_files().unwrap().len(), 1);
    }

    // ── ManagerDb ────────────────────────────────────────────────

    fn open_manager(config_dir: &std::path::Path) -> ManagerDb {
        ManagerDb::open(config_dir).unwrap()
    }

    fn dataset_info(name: &str) -> DatasetInfo {
        DatasetInfo {
            name: name.to_string(),
            root_path: format!("/data/{}", name),
            pushed: false,
            last_country: None,
            last_region: None,
            last_site: None,
            day_0: Some("2024-01-01".to_string()),
        }
    }

    #[test]
    fn manager_config_get_returns_none_when_absent() {
        let tmp = tempdir().unwrap();
        let db = open_manager(tmp.path());
        assert!(db.get_config("missing_key").unwrap().is_none());
    }

    #[test]
    fn manager_config_set_and_get_roundtrip() {
        let tmp = tempdir().unwrap();
        let db = open_manager(tmp.path());
        db.set_config("active_dataset", "2024.01.01.Test.SD").unwrap();
        let val = db.get_config("active_dataset").unwrap();
        assert_eq!(val.as_deref(), Some("2024.01.01.Test.SD"));
    }

    #[test]
    fn manager_config_set_overwrites_existing_value() {
        let tmp = tempdir().unwrap();
        let db = open_manager(tmp.path());
        db.set_config("key", "first").unwrap();
        db.set_config("key", "second").unwrap();
        assert_eq!(db.get_config("key").unwrap().as_deref(), Some("second"));
    }

    #[test]
    fn manager_get_all_datasets_empty_initially() {
        let tmp = tempdir().unwrap();
        let db = open_manager(tmp.path());
        assert!(db.get_all_datasets().unwrap().is_empty());
    }

    #[test]
    fn manager_upsert_and_get_all_datasets_roundtrip() {
        let tmp = tempdir().unwrap();
        let db = open_manager(tmp.path());
        db.upsert_dataset(&dataset_info("2024.01.01.Test.SD")).unwrap();
        let datasets = db.get_all_datasets().unwrap();
        assert_eq!(datasets.len(), 1);
        assert_eq!(datasets[0].name, "2024.01.01.Test.SD");
        assert_eq!(datasets[0].root_path, "/data/2024.01.01.Test.SD");
        assert!(!datasets[0].pushed);
    }

    #[test]
    fn manager_upsert_updates_existing_dataset() {
        let tmp = tempdir().unwrap();
        let db = open_manager(tmp.path());
        db.upsert_dataset(&dataset_info("2024.01.01.Test.SD")).unwrap();
        let updated = DatasetInfo {
            name: "2024.01.01.Test.SD".to_string(),
            root_path: "/data/2024.01.01.Test.SD".to_string(),
            pushed: true,
            last_country: Some("USA".to_string()),
            last_region: Some("California".to_string()),
            last_site: Some("SD".to_string()),
            day_0: Some("2024-01-01".to_string()),
        };
        db.upsert_dataset(&updated).unwrap();
        let datasets = db.get_all_datasets().unwrap();
        assert_eq!(datasets.len(), 1);
        assert!(datasets[0].pushed);
        assert_eq!(datasets[0].last_country.as_deref(), Some("USA"));
    }

    #[test]
    fn manager_remove_dataset_deletes_entry() {
        let tmp = tempdir().unwrap();
        let db = open_manager(tmp.path());
        db.upsert_dataset(&dataset_info("2024.01.01.Test.SD")).unwrap();
        db.upsert_dataset(&dataset_info("2024.02.01.Test.LA")).unwrap();
        db.remove_dataset("2024.01.01.Test.SD").unwrap();
        let datasets = db.get_all_datasets().unwrap();
        assert_eq!(datasets.len(), 1);
        assert_eq!(datasets[0].name, "2024.02.01.Test.LA");
    }

    #[test]
    fn manager_remove_nonexistent_dataset_is_a_noop() {
        let tmp = tempdir().unwrap();
        let db = open_manager(tmp.path());
        db.remove_dataset("does_not_exist").unwrap();
        assert!(db.get_all_datasets().unwrap().is_empty());
    }
}
