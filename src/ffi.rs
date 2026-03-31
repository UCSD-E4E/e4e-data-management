// ffi.rs – C ABI layer for E4E Data Management
//
// All exported symbols are `#[no_mangle] pub extern "C"`.
// Callers must free any `*mut c_char` returned via an `out` pointer by calling
// `e4e_string_free`.  The pointer returned by `e4e_last_error` is owned by
// thread-local storage and must NOT be freed.
//
// Return value convention: 0 = success, -1 = error (see e4e_last_error).

use std::cell::RefCell;
use std::ffi::{CStr, CString};
use std::os::raw::c_char;
use std::path::PathBuf;

use serde::Serialize;

use crate::dataset::{self, DatasetState};
use crate::db::{DatasetDb, DatasetInfo, DatasetMeta};
use crate::errors::E4EError;
use crate::manager::{self, DataManagerState};
use crate::metadata::MetadataRecord;
use crate::manifest;

// ─────────────────────────────────────────────────────────────────────────────
// Thread-local last-error storage
// ─────────────────────────────────────────────────────────────────────────────

thread_local! {
    static LAST_ERROR: RefCell<CString> = RefCell::new(CString::new("").unwrap());
}

fn set_last_error(msg: &str) {
    let cs = CString::new(msg).unwrap_or_else(|_| CString::new("(non-UTF-8 error)").unwrap());
    LAST_ERROR.with(|cell| *cell.borrow_mut() = cs);
}

// ─────────────────────────────────────────────────────────────────────────────
// JSON DTO types
// ─────────────────────────────────────────────────────────────────────────────

#[derive(Serialize)]
struct MissionInfoJson {
    name: String,
    path: String,
    country: String,
    region: String,
    site: String,
    device: String,
    timestamp: String,
    staged_files: usize,
    committed_files: usize,
}

#[derive(Serialize)]
struct DatasetInfoJson {
    name: String,
    root: String,
    pushed: bool,
    last_country: Option<String>,
    last_region: Option<String>,
    last_site: Option<String>,
    missions: Vec<MissionInfoJson>,
    active_mission: Option<String>,
}

// ─────────────────────────────────────────────────────────────────────────────
// Opaque handle
// ─────────────────────────────────────────────────────────────────────────────

pub struct FfiDataManager {
    inner: DataManagerState,
    active_dataset: Option<DatasetState>,
    active_mission_name: Option<String>,
}

impl FfiDataManager {
    /// Load or refresh the active dataset state from disk.
    fn ensure_active_dataset(&mut self) -> crate::errors::Result<&mut DatasetState> {
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
        if let (Some(ds), Some(name)) =
            (&self.active_dataset, &self.inner.active_dataset_name.clone())
        {
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

    /// Build a DatasetInfoJson for a given dataset info + loaded state (optional).
    fn dataset_info_to_json(&self, info: &DatasetInfo, active_mission: Option<&str>) -> DatasetInfoJson {
        // Try to load fresh state; fall back to info fields if unavailable.
        let state_result = dataset::load_dataset_state(&PathBuf::from(&info.root_path));
        let missions = match &state_result {
            Ok(state) => state
                .missions
                .iter()
                .map(|m| MissionInfoJson {
                    name: m.record.name.clone(),
                    path: m.record.path.clone(),
                    country: m.record.metadata.country.clone(),
                    region: m.record.metadata.region.clone(),
                    site: m.record.metadata.site.clone(),
                    device: m.record.metadata.device.clone(),
                    timestamp: m.record.metadata.timestamp.clone(),
                    staged_files: m.staged_files.len(),
                    committed_files: m.committed_files.len(),
                })
                .collect(),
            Err(_) => Vec::new(),
        };

        DatasetInfoJson {
            name: info.name.clone(),
            root: info.root_path.clone(),
            pushed: info.pushed,
            last_country: info.last_country.clone(),
            last_region: info.last_region.clone(),
            last_site: info.last_site.clone(),
            missions,
            active_mission: active_mission.map(String::from),
        }
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// Helper: write an owned String into a caller-supplied `*mut *mut c_char`
// ─────────────────────────────────────────────────────────────────────────────

/// Allocates a CString, writes its raw pointer to `*out`, and returns 0.
/// On CString allocation failure, sets last error and returns -1.
///
/// # Safety
/// `out` must be a valid, non-null pointer to a `*mut c_char`.
unsafe fn write_string_out(s: String, out: *mut *mut c_char) -> i32 {
    match CString::new(s) {
        Ok(cs) => {
            *out = cs.into_raw();
            0
        }
        Err(_) => {
            set_last_error("Failed to allocate CString for output");
            -1
        }
    }
}

/// Helper to safely read a `*const c_char` into a `&str`, setting last error on failure.
unsafe fn cstr_to_str<'a>(ptr: *const c_char, name: &str) -> Result<&'a str, ()> {
    if ptr.is_null() {
        set_last_error(&format!("Null pointer for argument '{}'", name));
        return Err(());
    }
    CStr::from_ptr(ptr).to_str().map_err(|_| {
        set_last_error(&format!("Invalid UTF-8 in argument '{}'", name));
    })
}

/// Helper to read an optional (nullable) `*const c_char`.
unsafe fn cstr_to_opt_str<'a>(ptr: *const c_char) -> Option<&'a str> {
    if ptr.is_null() {
        return None;
    }
    CStr::from_ptr(ptr).to_str().ok()
}

// ─────────────────────────────────────────────────────────────────────────────
// Exported C functions
// ─────────────────────────────────────────────────────────────────────────────

/// Returns a pointer to the last error string stored in thread-local storage.
/// The returned pointer is valid until the next FFI call on this thread.
/// The caller must NOT free this pointer.
#[no_mangle]
pub extern "C" fn e4e_last_error() -> *const c_char {
    LAST_ERROR.with(|cell| cell.borrow().as_ptr())
}

/// Frees a `*mut c_char` that was allocated by an FFI function via an `out` pointer.
///
/// # Safety
/// `s` must have been returned by an `e4e_*` function via an out-pointer, or must be null.
#[no_mangle]
pub unsafe extern "C" fn e4e_string_free(s: *mut c_char) {
    if !s.is_null() {
        drop(CString::from_raw(s));
    }
}

/// Returns the default configuration directory as a heap-allocated string.
/// The caller must free the string with `e4e_string_free`.
/// Returns 0 on success, -1 if the platform provides no suitable directory.
///
/// # Safety
/// `out` must be a valid non-null pointer to a `*mut c_char`.
#[no_mangle]
pub unsafe extern "C" fn e4e_default_config_dir(out: *mut *mut c_char) -> i32 {
    match manager::default_config_dir() {
        Some(path) => write_string_out(path.to_string_lossy().into_owned(), out),
        None => {
            set_last_error("Could not determine default config directory for this platform");
            -1
        }
    }
}

/// Load (or create) the data manager from `config_dir`.
/// Returns a heap-allocated `FfiDataManager` handle, or NULL on error.
/// The caller is responsible for eventually calling `e4e_dm_free`.
///
/// # Safety
/// `config_dir` must be a valid, non-null, null-terminated UTF-8 C string.
#[no_mangle]
pub unsafe extern "C" fn e4e_dm_load(config_dir: *const c_char) -> *mut FfiDataManager {
    let dir = match cstr_to_str(config_dir, "config_dir") {
        Ok(s) => s,
        Err(_) => return std::ptr::null_mut(),
    };

    match DataManagerState::load(&PathBuf::from(dir)) {
        Ok(state) => {
            let active_mission_name = state.active_mission_name.clone().filter(|s| !s.is_empty());
            let dm = Box::new(FfiDataManager {
                inner: state,
                active_dataset: None,
                active_mission_name,
            });
            Box::into_raw(dm)
        }
        Err(e) => {
            set_last_error(&e.to_string());
            std::ptr::null_mut()
        }
    }
}

/// Free a `FfiDataManager` handle previously returned by `e4e_dm_load`.
///
/// # Safety
/// `dm` must have been returned by `e4e_dm_load` and not yet freed.
#[no_mangle]
pub unsafe extern "C" fn e4e_dm_free(dm: *mut FfiDataManager) {
    if !dm.is_null() {
        drop(Box::from_raw(dm));
    }
}

/// Get a human-readable status string.
/// On success, writes a heap-allocated string to `*out` (free with `e4e_string_free`) and returns 0.
/// On error, returns -1 and sets last error.
///
/// # Safety
/// `dm` and `out` must be valid non-null pointers.
#[no_mangle]
pub unsafe extern "C" fn e4e_status(dm: *mut FfiDataManager, out: *mut *mut c_char) -> i32 {
    let dm = &mut *dm;

    let active_ds_name = dm.inner.active_dataset_name.clone().unwrap_or_default();
    if active_ds_name.is_empty() {
        return write_string_out("No dataset active".to_string(), out);
    }

    let ds = match dm.ensure_active_dataset() {
        Ok(ds) => ds.clone(),
        Err(_) => return write_string_out("No dataset active".to_string(), out),
    };

    let ds_path = ds.root.to_string_lossy().into_owned();
    let mut output = format!("Dataset {} at {} activated", active_ds_name, ds_path);

    let active_mission_name = dm.active_mission_name.clone().unwrap_or_default();
    if active_mission_name.is_empty() {
        output.push_str("\nNo mission active");
        return write_string_out(output, out);
    }

    let mission_opt = ds
        .missions
        .iter()
        .find(|m| m.record.name == active_mission_name)
        .cloned();

    match mission_opt {
        None => {
            output.push_str("\nNo mission active");
        }
        Some(mission) => {
            output.push_str(&format!(
                "\nMission {} at {} activated",
                active_mission_name, mission.record.path
            ));
            if !mission.staged_files.is_empty() {
                output.push_str(&format!("\n{} staged files", mission.staged_files.len()));
            }
            if !ds.staged_files.is_empty() {
                output.push_str(&format!("\n{} staged dataset files", ds.staged_files.len()));
            }
        }
    }

    write_string_out(output, out)
}

/// List all known datasets as a JSON array of DatasetInfoJson objects.
/// On success, writes a heap-allocated JSON string to `*out` and returns 0.
/// On error, returns -1.
///
/// # Safety
/// `dm` and `out` must be valid non-null pointers.
#[no_mangle]
pub unsafe extern "C" fn e4e_list_datasets(dm: *mut FfiDataManager, out: *mut *mut c_char) -> i32 {
    let dm = &mut *dm;

    let active_name = dm.inner.active_dataset_name.clone().unwrap_or_default();
    let active_mission = dm.active_mission_name.clone();

    let json_list: Vec<DatasetInfoJson> = dm
        .inner
        .dataset_infos
        .iter()
        .map(|info| {
            let am = if info.name == active_name {
                active_mission.as_deref()
            } else {
                None
            };
            dm.dataset_info_to_json(info, am)
        })
        .collect();

    match serde_json::to_string(&json_list) {
        Ok(s) => write_string_out(s, out),
        Err(e) => {
            set_last_error(&e.to_string());
            -1
        }
    }
}

/// Get the currently active dataset as a JSON DatasetInfoJson, or the string "null" if none.
/// On success, writes a heap-allocated JSON string to `*out` and returns 0.
/// On error, returns -1.
///
/// # Safety
/// `dm` and `out` must be valid non-null pointers.
#[no_mangle]
pub unsafe extern "C" fn e4e_active_dataset(dm: *mut FfiDataManager, out: *mut *mut c_char) -> i32 {
    let dm = &mut *dm;

    let active_name = match dm.inner.active_dataset_name.clone().filter(|s| !s.is_empty()) {
        Some(n) => n,
        None => return write_string_out("null".to_string(), out),
    };

    let info = match dm.inner.find_dataset(&active_name).cloned() {
        Some(i) => i,
        None => return write_string_out("null".to_string(), out),
    };

    let active_mission = dm.active_mission_name.clone();
    let json_obj = dm.dataset_info_to_json(&info, active_mission.as_deref());

    match serde_json::to_string(&json_obj) {
        Ok(s) => write_string_out(s, out),
        Err(e) => {
            set_last_error(&e.to_string());
            -1
        }
    }
}

/// Initialize (create) a new dataset.
///
/// # Safety
/// All pointer parameters must be valid non-null null-terminated UTF-8 C strings.
#[no_mangle]
pub unsafe extern "C" fn e4e_initialize_dataset(
    dm: *mut FfiDataManager,
    date: *const c_char,
    project: *const c_char,
    location: *const c_char,
    directory: *const c_char,
) -> i32 {
    let dm = &mut *dm;

    let date_str = match cstr_to_str(date, "date") { Ok(s) => s, Err(_) => return -1 };
    let project_str = match cstr_to_str(project, "project") { Ok(s) => s, Err(_) => return -1 };
    let location_str = match cstr_to_str(location, "location") { Ok(s) => s, Err(_) => return -1 };
    let directory_str = match cstr_to_str(directory, "directory") { Ok(s) => s, Err(_) => return -1 };

    let date_parts: Vec<&str> = date_str.split('-').collect();
    if date_parts.len() < 3 {
        set_last_error("Invalid date string: expected YYYY-MM-DD");
        return -1;
    }
    let y: u32 = date_parts[0].parse().unwrap_or(0);
    let m: u32 = date_parts[1].parse().unwrap_or(0);
    let d: u32 = date_parts[2].parse().unwrap_or(0);
    let dataset_name = format!("{:04}.{:02}.{:02}.{}.{}", y, m, d, project_str, location_str);

    if dm.inner.find_dataset(&dataset_name).is_some() {
        set_last_error("Dataset with that name already exists");
        return -1;
    }

    let dataset_path = PathBuf::from(directory_str).join(&dataset_name);
    let day_0 = date_str.to_string();

    let state = match dataset::create_dataset(&dataset_path, &day_0) {
        Ok(s) => s,
        Err(e) => { set_last_error(&e.to_string()); return -1; }
    };

    if let Err(e) = dataset::save_dataset_state(&state) {
        set_last_error(&e.to_string());
        return -1;
    }

    let info = DatasetInfo {
        name: dataset_name.clone(),
        root_path: dataset_path.to_string_lossy().into_owned(),
        pushed: false,
        last_country: None,
        last_region: None,
        last_site: None,
        day_0: Some(day_0),
    };

    if let Err(e) = dm.inner.upsert_dataset_info(info) {
        set_last_error(&e.to_string());
        return -1;
    }

    dm.inner.active_dataset_name = Some(dataset_name);
    dm.inner.active_mission_name = None;
    dm.active_mission_name = None;
    dm.active_dataset = Some(state);

    if let Err(e) = dm.inner.save() {
        set_last_error(&e.to_string());
        return -1;
    }

    0
}

/// Initialize (create) a new mission inside the currently active dataset.
///
/// # Safety
/// All pointer parameters must be valid non-null null-terminated UTF-8 C strings.
#[no_mangle]
pub unsafe extern "C" fn e4e_initialize_mission(
    dm: *mut FfiDataManager,
    timestamp: *const c_char,
    device: *const c_char,
    country: *const c_char,
    region: *const c_char,
    site: *const c_char,
    mission_name: *const c_char,
    notes: *const c_char,
) -> i32 {
    let dm = &mut *dm;

    let timestamp_str = match cstr_to_str(timestamp, "timestamp") { Ok(s) => s, Err(_) => return -1 };
    let device_str = match cstr_to_str(device, "device") { Ok(s) => s, Err(_) => return -1 };
    let country_str = match cstr_to_str(country, "country") { Ok(s) => s, Err(_) => return -1 };
    let region_str = match cstr_to_str(region, "region") { Ok(s) => s, Err(_) => return -1 };
    let site_str = match cstr_to_str(site, "site") { Ok(s) => s, Err(_) => return -1 };
    let mission_name_str = match cstr_to_str(mission_name, "mission_name") { Ok(s) => s, Err(_) => return -1 };
    let notes_str = match cstr_to_str(notes, "notes") { Ok(s) => s, Err(_) => return -1 };

    let meta = MetadataRecord {
        timestamp: timestamp_str.to_string(),
        device: device_str.to_string(),
        country: country_str.to_string(),
        region: region_str.to_string(),
        site: site_str.to_string(),
        mission_name: mission_name_str.to_string(),
        properties: String::new(),
        notes: notes_str.to_string(),
    };

    let active_name = dm.inner.active_dataset_name.clone().unwrap_or_default();

    let (new_mission_name, updated_info) = {
        let ds = match dm.ensure_active_dataset() {
            Ok(ds) => ds,
            Err(e) => { set_last_error(&e.to_string()); return -1; }
        };
        let record = match dataset::add_mission(ds, &meta) {
            Ok(r) => r,
            Err(e) => { set_last_error(&e.to_string()); return -1; }
        };
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

    if let Err(e) = dm.inner.upsert_dataset_info(updated_info) {
        set_last_error(&e.to_string());
        return -1;
    }

    dm.active_mission_name = Some(new_mission_name.clone());
    dm.inner.active_mission_name = Some(new_mission_name);

    if let Err(e) = dm.inner.save() {
        set_last_error(&e.to_string());
        return -1;
    }

    0
}

/// Activate a dataset (and optionally a mission within it).
/// Pass NULL for `mission` to activate only the dataset.
///
/// # Safety
/// `dm` and `dataset` must be valid non-null pointers. `mission` may be null.
#[no_mangle]
pub unsafe extern "C" fn e4e_activate(
    dm: *mut FfiDataManager,
    dataset: *const c_char,
    mission: *const c_char,
) -> i32 {
    let dm = &mut *dm;

    let dataset_str = match cstr_to_str(dataset, "dataset") { Ok(s) => s, Err(_) => return -1 };
    let mission_opt = cstr_to_opt_str(mission);

    let info = match dm.inner.find_dataset(dataset_str).cloned() {
        Some(i) => i,
        None => {
            set_last_error(&format!("Dataset not found: {}", dataset_str));
            return -1;
        }
    };

    let ds_state = match dataset::load_dataset_state(&PathBuf::from(&info.root_path)) {
        Ok(s) => s,
        Err(e) => { set_last_error(&e.to_string()); return -1; }
    };

    dm.active_dataset = Some(ds_state.clone());
    dm.inner.active_dataset_name = Some(dataset_str.to_string());

    if let Some(mission_name) = mission_opt.filter(|s| !s.is_empty()) {
        // Verify the mission exists
        if !ds_state.missions.iter().any(|m| m.record.name == mission_name) {
            set_last_error(&format!("Mission not found: {}", mission_name));
            return -1;
        }
        dm.active_mission_name = Some(mission_name.to_string());
        dm.inner.active_mission_name = Some(mission_name.to_string());
    } else {
        dm.active_mission_name = None;
        dm.inner.active_mission_name = None;
    }

    if let Err(e) = dm.inner.save() {
        set_last_error(&e.to_string());
        return -1;
    }

    0
}

/// Stage files into the active dataset or mission.
/// `paths_json` is a JSON array of path strings.
/// `readme` non-zero means stage at dataset level (README).
/// `destination` may be NULL (no sub-directory).
///
/// # Safety
/// `dm` and `paths_json` must be valid non-null pointers. `destination` may be null.
#[no_mangle]
pub unsafe extern "C" fn e4e_add_files(
    dm: *mut FfiDataManager,
    paths_json: *const c_char,
    readme: i32,
    destination: *const c_char,
) -> i32 {
    let dm = &mut *dm;

    let paths_str = match cstr_to_str(paths_json, "paths_json") { Ok(s) => s, Err(_) => return -1 };
    let paths: Vec<String> = match serde_json::from_str(paths_str) {
        Ok(v) => v,
        Err(e) => { set_last_error(&format!("Invalid paths JSON: {}", e)); return -1; }
    };
    let path_bufs: Vec<PathBuf> = paths.iter().map(PathBuf::from).collect();
    let dest_opt = cstr_to_opt_str(destination).map(PathBuf::from);

    if readme != 0 {
        let ds = match dm.ensure_active_dataset() {
            Ok(ds) => ds,
            Err(e) => { set_last_error(&e.to_string()); return -1; }
        };
        if let Err(e) = dataset::stage_dataset_files(ds, &path_bufs) {
            set_last_error(&e.to_string());
            return -1;
        }
        dm.sync_active_dataset_info();
        if let Err(e) = dm.inner.save() {
            set_last_error(&e.to_string());
            return -1;
        }
        return 0;
    }

    let mission_name = match dm.active_mission_name.clone().filter(|s| !s.is_empty()) {
        Some(n) => n,
        None => {
            set_last_error("No active mission");
            return -1;
        }
    };

    let ds = match dm.ensure_active_dataset() {
        Ok(ds) => ds,
        Err(e) => { set_last_error(&e.to_string()); return -1; }
    };

    if let Err(e) = dataset::stage_mission_files(ds, &mission_name, &path_bufs, dest_opt.as_deref()) {
        set_last_error(&e.to_string());
        return -1;
    }

    dm.sync_active_dataset_info();
    if let Err(e) = dm.inner.save() {
        set_last_error(&e.to_string());
        return -1;
    }

    0
}

/// Commit staged files in the active mission (or dataset when `readme` is non-zero).
///
/// # Safety
/// `dm` must be a valid non-null pointer.
#[no_mangle]
pub unsafe extern "C" fn e4e_commit(dm: *mut FfiDataManager, readme: i32) -> i32 {
    let dm = &mut *dm;

    if readme != 0 {
        let ds = match dm.ensure_active_dataset() {
            Ok(ds) => ds,
            Err(e) => { set_last_error(&e.to_string()); return -1; }
        };
        if let Err(e) = dataset::commit_dataset_files(ds) {
            set_last_error(&e.to_string());
            return -1;
        }
        dm.sync_active_dataset_info();
        if let Err(e) = dm.inner.save() {
            set_last_error(&e.to_string());
            return -1;
        }
        return 0;
    }

    let mission_name = match dm.active_mission_name.clone().filter(|s| !s.is_empty()) {
        Some(n) => n,
        None => {
            set_last_error("No active mission");
            return -1;
        }
    };

    let ds = match dm.ensure_active_dataset() {
        Ok(ds) => ds,
        Err(e) => { set_last_error(&e.to_string()); return -1; }
    };

    if let Err(e) = dataset::commit_mission_files(ds, &mission_name) {
        set_last_error(&e.to_string());
        return -1;
    }

    dm.sync_active_dataset_info();
    if let Err(e) = dm.inner.save() {
        set_last_error(&e.to_string());
        return -1;
    }

    0
}

// ─────────────────────────────────────────────────────────────────────────────
// Progress callback type
// ─────────────────────────────────────────────────────────────────────────────

/// Optional C progress callback: called with `(current, total)` files processed.
pub type ProgressFn = unsafe extern "C" fn(current: u64, total: u64);

// ─────────────────────────────────────────────────────────────────────────────
// Shared push / validate implementation
// ─────────────────────────────────────────────────────────────────────────────

unsafe fn push_impl<F: Fn(u64, u64) + Send + Sync>(
    dm: &mut FfiDataManager,
    dest_str: &str,
    progress: F,
) -> i32 {
    let dest_root = PathBuf::from(dest_str);

    let ds = match dm.ensure_active_dataset() {
        Ok(ds) => ds,
        Err(e) => { set_last_error(&e.to_string()); return -1; }
    };

    if let Err(e) = dataset::check_complete(ds) {
        set_last_error(&e.to_string());
        return -1;
    }

    let ds_root = ds.root.clone();
    let ds_name = ds_root
        .file_name()
        .map(|n| n.to_string_lossy().into_owned())
        .unwrap_or_default();
    let destination = dest_root.join(&ds_name);

    if destination.exists() {
        let manifest_path = ds_root.join("manifest.json");
        match manifest::read_manifest(&manifest_path) {
            Ok(src_manifest) => {
                if let Err(e) = dataset::check_destination_is_subset(&src_manifest, &destination) {
                    set_last_error(&e.to_string());
                    return -1;
                }
            }
            Err(e) => { set_last_error(&e.to_string()); return -1; }
        }
    }

    if let Err(e) = std::fs::create_dir_all(&destination) {
        set_last_error(&e.to_string());
        return -1;
    }

    if let Err(e) = dataset::duplicate_dataset_with_progress(ds, &[destination], progress) {
        set_last_error(&e.to_string());
        return -1;
    }

    // Mark pushed
    let ds = match dm.ensure_active_dataset() {
        Ok(ds) => ds,
        Err(e) => { set_last_error(&e.to_string()); return -1; }
    };

    ds.pushed = true;
    let db_result = DatasetDb::open(&ds.root.clone());
    match db_result {
        Ok(db) => {
            let meta = DatasetMeta {
                day_0: ds.day_0.clone(),
                pushed: true,
                version: ds.version,
                last_country: ds.last_country.clone(),
                last_region: ds.last_region.clone(),
                last_site: ds.last_site.clone(),
            };
            if let Err(e) = db.update_dataset_meta(&meta) {
                set_last_error(&e.to_string());
                return -1;
            }
        }
        Err(e) => { set_last_error(&e.to_string()); return -1; }
    }

    dm.sync_active_dataset_info();
    if let Err(e) = dm.inner.save() {
        set_last_error(&e.to_string());
        return -1;
    }

    0
}

unsafe fn validate_impl<F: Fn(u64, u64) + Send + Sync>(
    dm: &mut FfiDataManager,
    out: *mut *mut c_char,
    progress: F,
) -> i32 {
    let ds = match dm.ensure_active_dataset() {
        Ok(ds) => ds,
        Err(e) => { set_last_error(&e.to_string()); return -1; }
    };
    let root = ds.root.clone();

    let failures = match dataset::validate_dataset_failures_with_progress(&root, progress) {
        Ok(f) => f,
        Err(e) => { set_last_error(&e.to_string()); return -1; }
    };

    match serde_json::to_string(&failures) {
        Ok(s) => write_string_out(s, out),
        Err(e) => { set_last_error(&e.to_string()); -1 }
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// Push / validate exported functions
// ─────────────────────────────────────────────────────────────────────────────

/// Push (duplicate) the active dataset to the given path.
///
/// # Safety
/// `dm` and `path` must be valid non-null pointers to null-terminated UTF-8 C strings.
#[no_mangle]
pub unsafe extern "C" fn e4e_push(dm: *mut FfiDataManager, path: *const c_char) -> i32 {
    let dm = &mut *dm;
    let dest_str = match cstr_to_str(path, "path") { Ok(s) => s, Err(_) => return -1 };
    push_impl(dm, dest_str, |_, _| {})
}

/// Push with a progress callback `cb(current, total)`.  Pass NULL for no progress reporting.
///
/// # Safety
/// `dm` and `path` must be valid non-null pointers.  `cb` may be null.
#[no_mangle]
pub unsafe extern "C" fn e4e_push_with_progress(
    dm: *mut FfiDataManager,
    path: *const c_char,
    cb: Option<ProgressFn>,
) -> i32 {
    let dm = &mut *dm;
    let dest_str = match cstr_to_str(path, "path") { Ok(s) => s, Err(_) => return -1 };
    push_impl(dm, dest_str, move |current, total| {
        if let Some(f) = cb {
            f(current, total);
        }
    })
}

/// Validate the active dataset and return a JSON array of failure strings.
/// On success, writes a heap-allocated JSON string to `*out` and returns 0.
///
/// # Safety
/// `dm` and `out` must be valid non-null pointers.
#[no_mangle]
pub unsafe extern "C" fn e4e_validate(dm: *mut FfiDataManager, out: *mut *mut c_char) -> i32 {
    let dm = &mut *dm;
    validate_impl(dm, out, |_, _| {})
}

/// Validate with a progress callback `cb(current, total)`.  Pass NULL for no progress reporting.
///
/// # Safety
/// `dm` and `out` must be valid non-null pointers.  `cb` may be null.
#[no_mangle]
pub unsafe extern "C" fn e4e_validate_with_progress(
    dm: *mut FfiDataManager,
    out: *mut *mut c_char,
    cb: Option<ProgressFn>,
) -> i32 {
    let dm = &mut *dm;
    validate_impl(dm, out, move |current, total| {
        if let Some(f) = cb {
            f(current, total);
        }
    })
}

/// Remove a mission from a named dataset.
///
/// # Safety
/// `dm`, `dataset`, and `mission` must be valid non-null pointers.
#[no_mangle]
pub unsafe extern "C" fn e4e_remove_mission(
    dm: *mut FfiDataManager,
    dataset: *const c_char,
    mission: *const c_char,
) -> i32 {
    let dm = &mut *dm;

    let dataset_str = match cstr_to_str(dataset, "dataset") { Ok(s) => s, Err(_) => return -1 };
    let mission_str = match cstr_to_str(mission, "mission") { Ok(s) => s, Err(_) => return -1 };

    let info = match dm.inner.find_dataset(dataset_str).cloned() {
        Some(i) => i,
        None => {
            set_last_error(&format!("Dataset not found: {}", dataset_str));
            return -1;
        }
    };

    let mut ds_state = match dataset::load_dataset_state(&PathBuf::from(&info.root_path)) {
        Ok(s) => s,
        Err(e) => { set_last_error(&e.to_string()); return -1; }
    };

    if let Err(e) = dataset::remove_mission(&mut ds_state, mission_str) {
        set_last_error(&e.to_string());
        return -1;
    }

    if dm.inner.active_dataset_name.as_deref() == Some(dataset_str) {
        if dm.active_mission_name.as_deref() == Some(mission_str) {
            dm.active_mission_name = None;
            dm.inner.active_mission_name = None;
        }
        dm.active_dataset = Some(ds_state);
    }

    if let Err(e) = dm.inner.save() {
        set_last_error(&e.to_string());
        return -1;
    }

    0
}

/// Prune pushed or missing datasets. Returns a JSON array of removed dataset names.
/// On success, writes to `*out` and returns 0.
///
/// # Safety
/// `dm` and `out` must be valid non-null pointers.
#[no_mangle]
pub unsafe extern "C" fn e4e_prune(dm: *mut FfiDataManager, out: *mut *mut c_char) -> i32 {
    let dm = &mut *dm;

    let mut to_remove: Vec<String> = Vec::new();

    for info in &dm.inner.dataset_infos {
        let root = PathBuf::from(&info.root_path);
        if !root.exists() || info.pushed {
            to_remove.push(info.name.clone());
        }
    }

    if let Some(ref active_name) = dm.inner.active_dataset_name.clone() {
        if to_remove.contains(active_name) {
            dm.inner.active_dataset_name = None;
            dm.active_dataset = None;
            dm.active_mission_name = None;
            dm.inner.active_mission_name = None;
        }
    }

    for name in &to_remove {
        if let Some(info) = dm.inner.find_dataset(name).cloned() {
            let root = PathBuf::from(&info.root_path);
            if root.exists() {
                if let Err(e) = std::fs::remove_dir_all(&root) {
                    set_last_error(&e.to_string());
                    return -1;
                }
            }
        }
        if let Err(e) = dm.inner.remove_dataset_info(name) {
            set_last_error(&e.to_string());
            return -1;
        }
    }

    if let Err(e) = dm.inner.save() {
        set_last_error(&e.to_string());
        return -1;
    }

    match serde_json::to_string(&to_remove) {
        Ok(s) => write_string_out(s, out),
        Err(e) => { set_last_error(&e.to_string()); -1 }
    }
}
