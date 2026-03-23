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
