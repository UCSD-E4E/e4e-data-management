use std::fs;
use std::path::PathBuf;

use pyo3::create_exception;
use pyo3::prelude::*;
use pyo3::types::PyDict;

mod db;
mod dataset;
mod errors;
mod manifest;
mod metadata;
mod manager;
mod utils;

use db::{DatasetInfo, StagedFileRecord};
use dataset::{DatasetState, MissionState};
use errors::E4EError;
use manager::DataManagerState;
use metadata::MetadataRecord;

// ─────────────────────────────────────────────────────────────
// Python exceptions
// ─────────────────────────────────────────────────────────────

create_exception!(_core, Incomplete, pyo3::exceptions::PyException);
create_exception!(_core, MissionFilesInStaging, Incomplete);
create_exception!(_core, ReadmeFilesInStaging, Incomplete);
create_exception!(_core, ReadmeNotFound, Incomplete);
create_exception!(_core, CorruptedDataset, pyo3::exceptions::PyException);

impl From<E4EError> for PyErr {
    fn from(err: E4EError) -> PyErr {
        match err {
            E4EError::MissionFilesInStaging => {
                MissionFilesInStaging::new_err(err.to_string())
            }
            E4EError::ReadmeFilesInStaging => {
                ReadmeFilesInStaging::new_err(err.to_string())
            }
            E4EError::ReadmeNotFound(ref msg) => ReadmeNotFound::new_err(msg.clone()),
            E4EError::CorruptedDataset => CorruptedDataset::new_err(err.to_string()),
            other => pyo3::exceptions::PyRuntimeError::new_err(other.to_string()),
        }
    }
}

// ─────────────────────────────────────────────────────────────
// PyStagedFile
// ─────────────────────────────────────────────────────────────

#[pyclass(frozen)]
struct PyStagedFile {
    #[pyo3(get)]
    origin_path: String,
    #[pyo3(get)]
    target_path: String,
    #[pyo3(get)]
    hash: String,
}

impl From<&StagedFileRecord> for PyStagedFile {
    fn from(r: &StagedFileRecord) -> Self {
        PyStagedFile {
            origin_path: r.origin_path.clone(),
            target_path: r.target_path.clone(),
            hash: r.hash.clone(),
        }
    }
}

// ─────────────────────────────────────────────────────────────
// PyMission
// ─────────────────────────────────────────────────────────────

#[pyclass]
struct PyMission {
    inner: MissionState,
}

#[pymethods]
impl PyMission {
    #[getter]
    fn name(&self) -> &str {
        &self.inner.record.name
    }

    #[getter]
    fn path(&self) -> &str {
        &self.inner.record.path
    }

    #[getter]
    fn staged_files(&self) -> Vec<PyStagedFile> {
        self.inner
            .staged_files
            .iter()
            .map(PyStagedFile::from)
            .collect()
    }

    #[getter]
    fn committed_files(&self) -> Vec<String> {
        self.inner.committed_files.clone()
    }

    // Expose metadata fields for Python wrappers
    #[getter]
    fn country(&self) -> &str {
        &self.inner.record.metadata.country
    }

    #[getter]
    fn region(&self) -> &str {
        &self.inner.record.metadata.region
    }

    #[getter]
    fn site(&self) -> &str {
        &self.inner.record.metadata.site
    }

    #[getter]
    fn device(&self) -> &str {
        &self.inner.record.metadata.device
    }

    #[getter]
    fn timestamp(&self) -> &str {
        &self.inner.record.metadata.timestamp
    }
}

// ─────────────────────────────────────────────────────────────
// PyDataset
// ─────────────────────────────────────────────────────────────

#[pyclass]
struct PyDataset {
    inner: DatasetState,
}

#[pymethods]
impl PyDataset {
    #[classmethod]
    fn load(_cls: &Bound<'_, pyo3::types::PyType>, root: &str) -> PyResult<Self> {
        let path = PathBuf::from(root);
        let state = dataset::load_dataset_state(&path)?;
        Ok(PyDataset { inner: state })
    }

    #[getter]
    fn pushed(&self) -> bool {
        self.inner.pushed
    }

    #[getter]
    fn last_country(&self) -> Option<&str> {
        self.inner.last_country.as_deref()
    }

    #[getter]
    fn last_region(&self) -> Option<&str> {
        self.inner.last_region.as_deref()
    }

    #[getter]
    fn last_site(&self) -> Option<&str> {
        self.inner.last_site.as_deref()
    }

    #[getter]
    fn root(&self) -> String {
        self.inner.root.to_string_lossy().into_owned()
    }

    #[getter]
    fn name(&self) -> String {
        self.inner
            .root
            .file_name()
            .map(|n| n.to_string_lossy().into_owned())
            .unwrap_or_default()
    }

    #[getter]
    fn staged_files(&self) -> Vec<String> {
        self.inner
            .staged_files
            .iter()
            .map(|p| p.to_string_lossy().into_owned())
            .collect()
    }

    #[getter]
    fn committed_files(&self) -> Vec<String> {
        self.inner.committed_files.clone()
    }

    #[getter]
    fn missions(&self) -> Vec<PyMission> {
        self.inner
            .missions
            .iter()
            .map(|m| PyMission { inner: m.clone() })
            .collect()
    }

    fn validate(&self) -> PyResult<bool> {
        let result = dataset::validate_dataset(&self.inner.root)?;
        Ok(result)
    }

    fn validate_failures(&self) -> PyResult<Vec<String>> {
        Ok(dataset::validate_dataset_failures(&self.inner.root)?)
    }
}

// ─────────────────────────────────────────────────────────────
// PyDataManager
// ─────────────────────────────────────────────────────────────

#[pyclass]
struct PyDataManager {
    inner: DataManagerState,
    /// In-memory active dataset state (loaded on demand)
    active_dataset: Option<DatasetState>,
    /// In-memory active mission state (index into active_dataset.missions)
    active_mission_name: Option<String>,
}

impl PyDataManager {
    /// Load or refresh the active dataset state from disk.
    fn ensure_active_dataset(&mut self) -> errors::Result<&mut DatasetState> {
        if self.active_dataset.is_none() {
            if let Some(name) = &self.inner.active_dataset_name.clone() {
                if !name.is_empty() {
                    if let Some(info) = self.inner.find_dataset(name).cloned() {
                        let state =
                            dataset::load_dataset_state(&PathBuf::from(&info.root_path))?;
                        self.active_dataset = Some(state);
                    }
                }
            }
        }
        self.active_dataset
            .as_mut()
            .ok_or_else(|| E4EError::Runtime("Dataset not active".to_string()))
    }

    /// Sync the active dataset's metadata back into the manager's dataset_infos.
    fn sync_active_dataset_info(&mut self) {
        if let (Some(ds), Some(name)) = (&self.active_dataset, &self.inner.active_dataset_name.clone()) {
            if name.is_empty() {
                return;
            }
            let info = DatasetInfo {
                name: name.clone(),
                root_path: ds.root.to_string_lossy().into_owned(),
                pushed: ds.pushed,
                last_country: ds.last_country.clone(),
                last_region: ds.last_region.clone(),
                last_site: ds.last_site.clone(),
                day_0: Some(ds.day_0.clone()),
            };
            if let Some(existing) = self
                .inner
                .dataset_infos
                .iter_mut()
                .find(|d| d.name == *name)
            {
                *existing = info;
            }
        }
    }
}

#[pymethods]
impl PyDataManager {
    #[new]
    fn new(config_dir: &str, default_dataset_dir: &str) -> PyResult<Self> {
        let state = DataManagerState::new(
            &PathBuf::from(config_dir),
            &PathBuf::from(default_dataset_dir),
        )?;
        Ok(PyDataManager {
            inner: state,
            active_dataset: None,
            active_mission_name: None,
        })
    }

    #[classmethod]
    fn load(
        _cls: &Bound<'_, pyo3::types::PyType>,
        config_dir: &str,
    ) -> PyResult<Self> {
        let state = DataManagerState::load(&PathBuf::from(config_dir))?;
        let active_mission_name = state
            .active_mission_name
            .clone()
            .filter(|s| !s.is_empty());
        Ok(PyDataManager {
            inner: state,
            active_dataset: None,
            active_mission_name,
        })
    }

    fn save(&self) -> PyResult<()> {
        self.inner.save()?;
        Ok(())
    }

    // ── Getters ───────────────────────────────────────────────

    #[getter]
    fn active_dataset(&mut self) -> PyResult<Option<PyDataset>> {
        match self.ensure_active_dataset() {
            Ok(ds) => Ok(Some(PyDataset { inner: ds.clone() })),
            Err(E4EError::Runtime(_)) => Ok(None),
            Err(e) => Err(e.into()),
        }
    }

    #[getter]
    fn active_mission(&mut self) -> PyResult<Option<PyMission>> {
        let mission_name = match self.active_mission_name.clone() {
            Some(n) if !n.is_empty() => n,
            _ => return Ok(None),
        };
        match self.ensure_active_dataset() {
            Ok(ds) => {
                let mission = ds
                    .missions
                    .iter()
                    .find(|m| m.record.name == mission_name)
                    .map(|m| PyMission { inner: m.clone() });
                Ok(mission)
            }
            Err(E4EError::Runtime(_)) => Ok(None),
            Err(e) => Err(e.into()),
        }
    }

    #[getter]
    fn datasets<'py>(&self, py: Python<'py>) -> PyResult<Bound<'py, PyDict>> {
        let dict = PyDict::new_bound(py);
        for info in &self.inner.dataset_infos {
            // Try to load the dataset state
            let ds_result = dataset::load_dataset_state(&PathBuf::from(&info.root_path));
            let state = match ds_result {
                Ok(s) => s,
                Err(_) => {
                    // Dataset might be missing from disk; include a stub
                    DatasetState {
                        root: PathBuf::from(&info.root_path),
                        day_0: info.day_0.clone().unwrap_or_default(),
                        pushed: info.pushed,
                        version: 2,
                        last_country: info.last_country.clone(),
                        last_region: info.last_region.clone(),
                        last_site: info.last_site.clone(),
                        missions: Vec::new(),
                        staged_files: Vec::new(),
                        committed_files: Vec::new(),
                    }
                }
            };
            let py_ds = PyDataset { inner: state };
            dict.set_item(&info.name, pyo3::Py::new(py, py_ds)?)?;
        }
        Ok(dict)
    }

    #[getter]
    fn dataset_dir(&self) -> String {
        self.inner.dataset_dir.to_string_lossy().into_owned()
    }

    #[setter]
    fn set_dataset_dir(&mut self, path: String) -> PyResult<()> {
        self.inner.dataset_dir = PathBuf::from(path);
        self.inner.save()?;
        Ok(())
    }

    #[getter]
    fn version(&self) -> i32 {
        self.inner.version
    }

    // ── Operations ────────────────────────────────────────────

    fn initialize_dataset(
        &mut self,
        date_str: &str,
        project: &str,
        location: &str,
        directory: &str,
    ) -> PyResult<()> {
        // Format: {YYYY}.{MM:02}.{DD:02}.{project}.{location}
        let date_parts: Vec<&str> = date_str.split('-').collect();
        if date_parts.len() < 3 {
            return Err(pyo3::exceptions::PyRuntimeError::new_err(
                "Invalid date string",
            ));
        }
        let y: u32 = date_parts[0].parse().unwrap_or(0);
        let m: u32 = date_parts[1].parse().unwrap_or(0);
        let d: u32 = date_parts[2].parse().unwrap_or(0);
        let dataset_name = format!("{:04}.{:02}.{:02}.{}.{}", y, m, d, project, location);

        // Check duplicate
        if self.inner.find_dataset(&dataset_name).is_some() {
            return Err(pyo3::exceptions::PyRuntimeError::new_err(
                "Dataset with that name already exists!",
            ));
        }

        let dataset_path = PathBuf::from(directory).join(&dataset_name);
        let day_0 = date_str.to_string();

        let state = dataset::create_dataset(&dataset_path, &day_0)?;
        dataset::save_dataset_state(&state)?;

        let info = DatasetInfo {
            name: dataset_name.clone(),
            root_path: dataset_path.to_string_lossy().into_owned(),
            pushed: false,
            last_country: None,
            last_region: None,
            last_site: None,
            day_0: Some(day_0),
        };
        self.inner.upsert_dataset_info(info)?;
        self.inner.active_dataset_name = Some(dataset_name);
        self.inner.active_mission_name = None;
        self.active_mission_name = None;
        self.active_dataset = Some(state);
        self.inner.save()?;
        Ok(())
    }

    #[allow(clippy::too_many_arguments)]
    fn initialize_mission(
        &mut self,
        timestamp: &str,
        device: &str,
        country: &str,
        region: &str,
        site: &str,
        mission: &str,
        notes: &str,
        properties: &str,
    ) -> PyResult<()> {
        let meta = MetadataRecord {
            timestamp: timestamp.to_string(),
            device: device.to_string(),
            country: country.to_string(),
            region: region.to_string(),
            site: site.to_string(),
            mission_name: mission.to_string(),
            properties: properties.to_string(),
            notes: notes.to_string(),
        };

        // Extract active dataset name before mutable borrow
        let active_name = self.inner.active_dataset_name.clone().unwrap_or_default();

        let (mission_name, info) = {
            let ds = self.ensure_active_dataset()?;
            let record = dataset::add_mission(ds, &meta)?;
            let name = record.name.clone();
            let info = DatasetInfo {
                name: active_name,
                root_path: ds.root.to_string_lossy().into_owned(),
                pushed: ds.pushed,
                last_country: ds.last_country.clone(),
                last_region: ds.last_region.clone(),
                last_site: ds.last_site.clone(),
                day_0: Some(ds.day_0.clone()),
            };
            (name, info)
        };

        self.inner.upsert_dataset_info(info)?;

        self.active_mission_name = Some(mission_name.clone());
        self.inner.active_mission_name = Some(mission_name);
        self.inner.save()?;
        Ok(())
    }

    fn status(&mut self) -> PyResult<String> {
        let mut output = String::new();

        let active_ds_name = self.inner.active_dataset_name.clone().unwrap_or_default();
        if active_ds_name.is_empty() {
            return Ok("No dataset active".to_string());
        }

        let ds = match self.ensure_active_dataset() {
            Ok(ds) => ds.clone(),
            Err(_) => return Ok("No dataset active".to_string()),
        };

        let ds_path = ds.root.to_string_lossy().into_owned();
        output.push_str(&format!(
            "Dataset {} at {} activated",
            active_ds_name, ds_path
        ));

        let active_mission_name = self
            .active_mission_name
            .clone()
            .unwrap_or_default();
        if active_mission_name.is_empty() {
            output.push('\n');
            output.push_str("No mission active");
            return Ok(output);
        }

        let mission_opt = ds
            .missions
            .iter()
            .find(|m| m.record.name == active_mission_name)
            .cloned();

        let mission = match mission_opt {
            Some(m) => m,
            None => {
                output.push('\n');
                output.push_str("No mission active");
                return Ok(output);
            }
        };

        let mission_path = &mission.record.path;
        output.push('\n');
        output.push_str(&format!(
            "Mission {} at {} activated",
            active_mission_name, mission_path
        ));

        output.push('\n');
        if !mission.staged_files.is_empty() {
            output.push_str(&format!(
                "{} staged files:\n\t",
                mission.staged_files.len()
            ));
            let mission_root = PathBuf::from(&mission.record.path);
            let mut sorted_staged = mission.staged_files.clone();
            sorted_staged.sort_by(|a, b| {
                let a_name = PathBuf::from(&a.target_path)
                    .file_name()
                    .map(|n| n.to_string_lossy().into_owned())
                    .unwrap_or_default();
                let b_name = PathBuf::from(&b.target_path)
                    .file_name()
                    .map(|n| n.to_string_lossy().into_owned())
                    .unwrap_or_default();
                a_name.cmp(&b_name)
            });
            let lines: Vec<String> = sorted_staged
                .iter()
                .map(|f| {
                    let target = PathBuf::from(&f.target_path);
                    let rel = target
                        .strip_prefix(&mission_root)
                        .map(|r| r.to_string_lossy().into_owned())
                        .unwrap_or_else(|_| f.target_path.clone());
                    // Use forward slashes (posix style)
                    let rel_posix = rel.replace('\\', "/");
                    format!("{} -> {}", f.origin_path, rel_posix)
                })
                .collect();
            output.push_str(&lines.join("\n\t"));
        }

        if !ds.staged_files.is_empty() {
            output.push_str(&format!(
                "{} staged dataset files:\n\t",
                ds.staged_files.len()
            ));
            let paths: Vec<String> = ds
                .staged_files
                .iter()
                .map(|p| p.to_string_lossy().into_owned())
                .collect();
            output.push_str(&paths.join("\n\t"));
        }

        Ok(output)
    }

    #[pyo3(signature = (dataset, day=None, mission=None, root_dir=None))]
    fn activate(
        &mut self,
        dataset: &str,
        day: Option<i64>,
        mission: Option<String>,
        root_dir: Option<String>,
    ) -> PyResult<()> {
        // Find or load the dataset
        let ds_state = if self.inner.find_dataset(dataset).is_some() {
            let info = self.inner.find_dataset(dataset).cloned().unwrap();
            dataset::load_dataset_state(&PathBuf::from(&info.root_path))?
        } else if let Some(ref rdir) = root_dir {
            let dataset_path = PathBuf::from(rdir).join(dataset);
            if !dataset_path.is_dir() {
                return Err(pyo3::exceptions::PyRuntimeError::new_err(
                    "Unable to find dataset",
                ));
            }
            let state = dataset::load_dataset_state(&dataset_path)?;
            // Register it
            let info = DatasetInfo {
                name: dataset.to_string(),
                root_path: dataset_path.to_string_lossy().into_owned(),
                pushed: state.pushed,
                last_country: state.last_country.clone(),
                last_region: state.last_region.clone(),
                last_site: state.last_site.clone(),
                day_0: Some(state.day_0.clone()),
            };
            self.inner.upsert_dataset_info(info)?;
            state
        } else {
            return Err(pyo3::exceptions::PyRuntimeError::new_err(
                "Unable to find dataset",
            ));
        };

        self.active_dataset = Some(ds_state);
        self.inner.active_dataset_name = Some(dataset.to_string());

        // Activate mission if specified
        if let Some(ref mission_name) = mission {
            if !mission_name.is_empty() {
                let day_num = day.ok_or_else(|| {
                    pyo3::exceptions::PyRuntimeError::new_err("Expected day parameter")
                })?;
                let full_name = format!("ED-{:02} {}", day_num, mission_name);
                // Verify the mission exists in the dataset
                let ds = self.active_dataset.as_ref().unwrap();
                if !ds.missions.iter().any(|m| m.record.name == full_name) {
                    return Err(pyo3::exceptions::PyRuntimeError::new_err(format!(
                        "Mission not found: {}",
                        full_name
                    )));
                }
                self.active_mission_name = Some(full_name.clone());
                self.inner.active_mission_name = Some(full_name);
            } else {
                self.active_mission_name = None;
                self.inner.active_mission_name = None;
            }
        } else {
            self.active_mission_name = None;
            self.inner.active_mission_name = None;
        }

        self.inner.save()?;
        Ok(())
    }

    #[pyo3(signature = (paths, readme, destination=None))]
    fn add(
        &mut self,
        paths: Vec<String>,
        readme: bool,
        destination: Option<String>,
    ) -> PyResult<()> {
        let path_bufs: Vec<PathBuf> = paths.iter().map(PathBuf::from).collect();

        if readme {
            // Stage at dataset level
            let ds = self.ensure_active_dataset()?;
            dataset::stage_dataset_files(ds, &path_bufs)?;
            self.sync_active_dataset_info();
            self.inner.save()?;
            return Ok(());
        }

        let mission_name = self
            .active_mission_name
            .clone()
            .filter(|s| !s.is_empty())
            .ok_or_else(|| {
                pyo3::exceptions::PyRuntimeError::new_err("Mission not active")
            })?;

        let dest = destination.as_deref().map(PathBuf::from);
        let ds = self.ensure_active_dataset()?;
        dataset::stage_mission_files(ds, &mission_name, &path_bufs, dest.as_deref())?;
        self.sync_active_dataset_info();
        self.inner.save()?;
        Ok(())
    }

    fn commit(&mut self, readme: bool) -> PyResult<()> {
        if readme {
            let ds = self.ensure_active_dataset()?;
            dataset::commit_dataset_files(ds)?;
            self.sync_active_dataset_info();
            self.inner.save()?;
            return Ok(());
        }

        let mission_name = self
            .active_mission_name
            .clone()
            .filter(|s| !s.is_empty())
            .ok_or_else(|| {
                pyo3::exceptions::PyRuntimeError::new_err("Mission not active")
            })?;

        let ds = self.ensure_active_dataset()?;
        dataset::commit_mission_files(ds, &mission_name)?;
        self.sync_active_dataset_info();
        self.inner.save()?;
        Ok(())
    }

    fn duplicate(&mut self, paths: Vec<String>) -> PyResult<()> {
        let dest_paths: Vec<PathBuf> = paths.iter().map(PathBuf::from).collect();
        let ds = self.ensure_active_dataset()?;
        dataset::duplicate_dataset(ds, &dest_paths)?;
        Ok(())
    }

    fn validate(&mut self) -> PyResult<bool> {
        let ds = self.ensure_active_dataset()?;
        let result = dataset::validate_dataset(&ds.root.clone())?;
        Ok(result)
    }

    fn validate_failures(&mut self) -> PyResult<Vec<String>> {
        let ds = self.ensure_active_dataset()?;
        Ok(dataset::validate_dataset_failures(&ds.root.clone())?)
    }

    fn push(&mut self, path: &str) -> PyResult<()> {
        let dest_root = PathBuf::from(path);
        let ds = self.ensure_active_dataset()?;
        dataset::check_complete(ds)?;

        let ds_root = ds.root.clone();
        let ds_name = ds_root
            .file_name()
            .map(|n| n.to_string_lossy().into_owned())
            .unwrap_or_default();
        let destination = dest_root.join(&ds_name);

        // If the destination already exists, verify it contains only files that are
        // also present in the source dataset with the same content.  This allows push
        // to recover from a previously interrupted push without silently overwriting
        // data that belongs to a different dataset.
        if destination.exists() {
            let src_manifest = manifest::read_manifest(&ds_root.join("manifest.json"))?;
            dataset::check_destination_is_subset(&src_manifest, &destination)?;
        }

        fs::create_dir_all(&destination)?;

        dataset::duplicate_dataset(ds, &[destination])?;

        // Set pushed flag
        let ds = self.ensure_active_dataset()?;
        ds.pushed = true;
        let db = db::DatasetDb::open(&ds.root.clone())?;
        let meta = db::DatasetMeta {
            day_0: ds.day_0.clone(),
            pushed: true,
            version: ds.version,
            last_country: ds.last_country.clone(),
            last_region: ds.last_region.clone(),
            last_site: ds.last_site.clone(),
        };
        db.update_dataset_meta(&meta)?;

        self.sync_active_dataset_info();
        self.inner.save()?;
        Ok(())
    }

    fn remove_mission(&mut self, dataset_name: &str, mission_name: &str) -> PyResult<()> {
        let info = self
            .inner
            .find_dataset(dataset_name)
            .ok_or_else(|| {
                pyo3::exceptions::PyRuntimeError::new_err(format!(
                    "Dataset not found: {}",
                    dataset_name
                ))
            })?
            .clone();

        let mut ds_state =
            dataset::load_dataset_state(&PathBuf::from(&info.root_path))?;
        dataset::remove_mission(&mut ds_state, mission_name)?;

        // If this is the active dataset, refresh cached state and clear active
        // mission if it was the one that was removed.
        if self.inner.active_dataset_name.as_deref() == Some(dataset_name) {
            if self.active_mission_name.as_deref() == Some(mission_name) {
                self.active_mission_name = None;
                self.inner.active_mission_name = None;
            }
            self.active_dataset = Some(ds_state);
        }

        self.inner.save()?;
        Ok(())
    }

    fn zip_dataset(&mut self, output_path: &str) -> PyResult<()> {
        let mut out = PathBuf::from(output_path);
        let ds = self.ensure_active_dataset()?;

        if out.extension().map(|e| e.to_ascii_lowercase()) != Some("zip".into()) {
            let ds_name = ds
                .root
                .file_name()
                .map(|n| n.to_string_lossy().into_owned())
                .unwrap_or_default();
            out = out.join(format!("{}.zip", ds_name));
        }

        if let Some(parent) = out.parent() {
            fs::create_dir_all(parent)?;
        }

        let ds_clone = ds.clone();
        dataset::check_complete(&ds_clone)?;
        dataset::create_zip(&ds_clone, &out)?;
        Ok(())
    }

    fn prune(&mut self) -> PyResult<Vec<String>> {
        let mut to_remove: Vec<String> = Vec::new();

        for info in &self.inner.dataset_infos {
            let root = PathBuf::from(&info.root_path);
            if !root.exists() || info.pushed {
                to_remove.push(info.name.clone());
            }
        }

        // If active dataset is being pruned, clear it
        if let Some(ref active_name) = self.inner.active_dataset_name.clone() {
            if to_remove.contains(active_name) {
                self.inner.active_dataset_name = None;
                self.active_dataset = None;
                self.active_mission_name = None;
                self.inner.active_mission_name = None;
            }
        }

        for name in &to_remove {
            // Delete root if it exists
            if let Some(info) = self.inner.find_dataset(name).cloned() {
                let root = PathBuf::from(&info.root_path);
                if root.exists() {
                    fs::remove_dir_all(&root)?;
                }
            }
            self.inner.remove_dataset_info(name)?;
        }

        self.inner.save()?;
        Ok(to_remove)
    }

    fn reset(&mut self) -> PyResult<()> {
        let mission_name = match self.active_mission_name.clone().filter(|s| !s.is_empty()) {
            Some(n) => n,
            None => return Ok(()),
        };

        let ds = self.ensure_active_dataset()?;
        if let Some(mission) = ds.missions.iter_mut().find(|m| m.record.name == mission_name) {
            mission.staged_files.clear();
        }

        let db = db::DatasetDb::open(&ds.root.clone())?;
        db.clear_mission_staged_files(&mission_name)?;

        self.sync_active_dataset_info();
        self.inner.save()?;
        Ok(())
    }

    fn list_datasets(&self) -> Vec<String> {
        self.inner
            .dataset_infos
            .iter()
            .map(|d| d.name.clone())
            .collect()
    }
}

// ─────────────────────────────────────────────────────────────
// Module definition
// ─────────────────────────────────────────────────────────────

#[pymodule]
fn _core(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add("Incomplete", m.py().get_type_bound::<Incomplete>())?;
    m.add(
        "MissionFilesInStaging",
        m.py().get_type_bound::<MissionFilesInStaging>(),
    )?;
    m.add(
        "ReadmeFilesInStaging",
        m.py().get_type_bound::<ReadmeFilesInStaging>(),
    )?;
    m.add("ReadmeNotFound", m.py().get_type_bound::<ReadmeNotFound>())?;
    m.add("CorruptedDataset", m.py().get_type_bound::<CorruptedDataset>())?;
    m.add_class::<PyStagedFile>()?;
    m.add_class::<PyMission>()?;
    m.add_class::<PyDataset>()?;
    m.add_class::<PyDataManager>()?;
    Ok(())
}
