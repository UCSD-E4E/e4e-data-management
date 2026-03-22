use std::path::{Path, PathBuf};

use crate::db::{DatasetInfo, ManagerDb};
use crate::errors::Result;

/// Current manager schema version.
const VERSION: i32 = 2;

#[derive(Clone, Debug)]
pub struct DataManagerState {
    pub config_dir: PathBuf,
    pub active_dataset_name: Option<String>,
    pub active_mission_name: Option<String>,
    pub dataset_dir: PathBuf,
    pub version: i32,
    pub dataset_infos: Vec<DatasetInfo>,
}

impl DataManagerState {
    /// Creates a fresh manager state and persists it to `config.db`.
    pub fn new(config_dir: &Path, default_dataset_dir: &Path) -> Result<Self> {
        let state = DataManagerState {
            config_dir: config_dir.to_path_buf(),
            active_dataset_name: None,
            active_mission_name: None,
            dataset_dir: default_dataset_dir.to_path_buf(),
            version: VERSION,
            dataset_infos: Vec::new(),
        };
        state.save()?;
        Ok(state)
    }

    /// Loads from `config.db`, or creates fresh if the file doesn't exist.
    pub fn load(config_dir: &Path) -> Result<Self> {
        let db_path = config_dir.join("config.db");
        if !db_path.exists() {
            // Use a sensible default — the caller can override dataset_dir after load
            let default_dataset_dir = config_dir.join("data");
            return Self::new(config_dir, &default_dataset_dir);
        }
        let db = ManagerDb::open(config_dir)?;
        let dataset_infos = db.get_all_datasets()?;
        let active_dataset_name = db.get_config("active_dataset")?;
        let active_mission_name = db.get_config("active_mission")?;
        let dataset_dir = db
            .get_config("dataset_dir")?
            .map(PathBuf::from)
            .unwrap_or_else(|| config_dir.join("data"));

        Ok(DataManagerState {
            config_dir: config_dir.to_path_buf(),
            active_dataset_name,
            active_mission_name,
            dataset_dir,
            version: VERSION,
            dataset_infos,
        })
    }

    /// Saves the current state to `config.db`.
    pub fn save(&self) -> Result<()> {
        let db = ManagerDb::open(&self.config_dir)?;
        // Persist config values
        if let Some(ref name) = self.active_dataset_name {
            db.set_config("active_dataset", name)?;
        } else {
            // Remove the key if no active dataset
            db.set_config("active_dataset", "")?;
        }
        if let Some(ref name) = self.active_mission_name {
            db.set_config("active_mission", name)?;
        } else {
            db.set_config("active_mission", "")?;
        }
        db.set_config(
            "dataset_dir",
            &self.dataset_dir.to_string_lossy(),
        )?;
        // Persist all dataset infos
        for info in &self.dataset_infos {
            db.upsert_dataset(info)?;
        }
        Ok(())
    }

    /// Look up a DatasetInfo by name.
    pub fn find_dataset(&self, name: &str) -> Option<&DatasetInfo> {
        self.dataset_infos.iter().find(|d| d.name == name)
    }

    /// Update a DatasetInfo in the list (or insert if not present).
    pub fn upsert_dataset_info(&mut self, info: DatasetInfo) -> Result<()> {
        if let Some(existing) = self.dataset_infos.iter_mut().find(|d| d.name == info.name) {
            *existing = info.clone();
        } else {
            self.dataset_infos.push(info.clone());
        }
        // Persist
        let db = ManagerDb::open(&self.config_dir)?;
        db.upsert_dataset(&info)?;
        Ok(())
    }

    /// Remove a dataset from the known list.
    pub fn remove_dataset_info(&mut self, name: &str) -> Result<()> {
        self.dataset_infos.retain(|d| d.name != name);
        let db = ManagerDb::open(&self.config_dir)?;
        db.remove_dataset(name)?;
        Ok(())
    }


}


#[cfg(test)]
mod tests {
    use super::*;
    use tempfile::tempdir;

    // ── DataManagerState::new ─────────────────────────────────────

    #[test]
    fn new_creates_config_db_in_config_dir() {
        let tmp = tempdir().unwrap();
        DataManagerState::new(tmp.path(), &tmp.path().join("data")).unwrap();
        assert!(tmp.path().join("config.db").exists());
    }

    #[test]
    fn new_state_has_correct_defaults() {
        let tmp = tempdir().unwrap();
        let data_dir = tmp.path().join("mydata");
        let state = DataManagerState::new(tmp.path(), &data_dir).unwrap();
        assert_eq!(state.version, 2);
        assert!(state.active_dataset_name.is_none());
        assert!(state.active_mission_name.is_none());
        assert!(state.dataset_infos.is_empty());
        assert_eq!(state.dataset_dir, data_dir);
    }

    // ── DataManagerState::save / load ─────────────────────────────

    #[test]
    fn save_and_load_round_trips_active_dataset_name() {
        let tmp = tempdir().unwrap();
        let data_dir = tmp.path().join("data");
        let mut state = DataManagerState::new(tmp.path(), &data_dir).unwrap();
        state.active_dataset_name = Some("2023.03.02.Test.SD".to_string());
        state.save().unwrap();

        let loaded = DataManagerState::load(tmp.path()).unwrap();
        assert_eq!(loaded.active_dataset_name, Some("2023.03.02.Test.SD".to_string()));
    }

    #[test]
    fn save_and_load_round_trips_dataset_dir() {
        let tmp = tempdir().unwrap();
        let custom_dir = tmp.path().join("custom_data");
        let mut state = DataManagerState::new(tmp.path(), &tmp.path().join("data")).unwrap();
        state.dataset_dir = custom_dir.clone();
        state.save().unwrap();

        let loaded = DataManagerState::load(tmp.path()).unwrap();
        assert_eq!(loaded.dataset_dir, custom_dir);
    }

    #[test]
    fn load_without_existing_db_returns_fresh_state() {
        let tmp = tempdir().unwrap();
        // No config.db exists — should fall back to a fresh state without panicking
        let state = DataManagerState::load(tmp.path()).unwrap();
        assert!(state.active_dataset_name.is_none());
        assert!(state.dataset_infos.is_empty());
    }

    // ── upsert / remove dataset info ─────────────────────────────

    #[test]
    fn upsert_dataset_info_adds_to_list_and_persists() {
        let tmp = tempdir().unwrap();
        let mut state = DataManagerState::new(tmp.path(), &tmp.path().join("data")).unwrap();
        let info = crate::db::DatasetInfo {
            name: "2023.03.02.Test.SD".to_string(),
            root_path: "/tmp/ds".to_string(),
            pushed: false,
            last_country: Some("USA".to_string()),
            last_region: None,
            last_site: None,
            day_0: Some("2023-03-02".to_string()),
        };
        state.upsert_dataset_info(info).unwrap();
        assert_eq!(state.dataset_infos.len(), 1);
        assert_eq!(state.dataset_infos[0].name, "2023.03.02.Test.SD");

        // Verify persistence
        let loaded = DataManagerState::load(tmp.path()).unwrap();
        assert_eq!(loaded.dataset_infos.len(), 1);
    }

    #[test]
    fn upsert_dataset_info_updates_existing_entry() {
        let tmp = tempdir().unwrap();
        let mut state = DataManagerState::new(tmp.path(), &tmp.path().join("data")).unwrap();
        let info = crate::db::DatasetInfo {
            name: "ds1".to_string(),
            root_path: "/tmp/ds1".to_string(),
            pushed: false,
            last_country: None,
            last_region: None,
            last_site: None,
            day_0: None,
        };
        state.upsert_dataset_info(info).unwrap();

        let updated = crate::db::DatasetInfo {
            name: "ds1".to_string(),
            root_path: "/tmp/ds1".to_string(),
            pushed: true, // changed
            last_country: Some("USA".to_string()),
            last_region: None,
            last_site: None,
            day_0: None,
        };
        state.upsert_dataset_info(updated).unwrap();
        // Should still be only one entry
        assert_eq!(state.dataset_infos.len(), 1);
        assert!(state.dataset_infos[0].pushed);
    }

    #[test]
    fn remove_dataset_info_deletes_entry() {
        let tmp = tempdir().unwrap();
        let mut state = DataManagerState::new(tmp.path(), &tmp.path().join("data")).unwrap();
        let info = crate::db::DatasetInfo {
            name: "ds1".to_string(),
            root_path: "/tmp/ds1".to_string(),
            pushed: false,
            last_country: None,
            last_region: None,
            last_site: None,
            day_0: None,
        };
        state.upsert_dataset_info(info).unwrap();
        assert_eq!(state.dataset_infos.len(), 1);
        state.remove_dataset_info("ds1").unwrap();
        assert!(state.dataset_infos.is_empty());

        // Verify removal persists
        let loaded = DataManagerState::load(tmp.path()).unwrap();
        assert!(loaded.dataset_infos.is_empty());
    }

    #[test]
    fn find_dataset_returns_none_for_unknown_name() {
        let tmp = tempdir().unwrap();
        let state = DataManagerState::new(tmp.path(), &tmp.path().join("data")).unwrap();
        assert!(state.find_dataset("nonexistent").is_none());
    }
}
