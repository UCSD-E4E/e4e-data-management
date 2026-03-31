use std::fs;
use std::io;
use std::path::{Path, PathBuf};
use std::sync::atomic::{AtomicU64, Ordering};

use rayon::prelude::*;

use crate::db::{DatasetDb, DatasetMeta, MissionRecord, StagedFileRecord};
use crate::errors::{E4EError, Result};
use crate::manifest;
use crate::metadata::{self, MetadataRecord};

// ─────────────────────────────────────────────────────────────
// State types
// ─────────────────────────────────────────────────────────────

#[derive(Clone, Debug)]
pub struct MissionState {
    pub record: MissionRecord,
    pub staged_files: Vec<StagedFileRecord>,
    pub committed_files: Vec<String>,
}

#[derive(Clone, Debug)]
pub struct DatasetState {
    pub root: PathBuf,
    pub day_0: String,
    pub pushed: bool,
    pub version: i32,
    pub last_country: Option<String>,
    pub last_region: Option<String>,
    pub last_site: Option<String>,
    pub missions: Vec<MissionState>,
    pub staged_files: Vec<PathBuf>,
    pub committed_files: Vec<String>,
}

const VERSION: i32 = 2;
const MANIFEST_NAME: &str = "manifest.json";
const DB_NAME: &str = ".e4edm.db";

// ─────────────────────────────────────────────────────────────
// Load / Save helpers
// ─────────────────────────────────────────────────────────────

/// Load all dataset state from `.e4edm.db`.  Falls back to scanning filesystem
/// for `metadata.json` files if the DB doesn't exist yet.
pub fn load_dataset_state(root: &Path) -> Result<DatasetState> {
    let db_path = root.join(DB_NAME);
    if db_path.exists() {
        let db = DatasetDb::open(root)?;
        load_from_db(&db, root)
    } else {
        load_from_filesystem(root)
    }
}

fn load_from_db(db: &DatasetDb, root: &Path) -> Result<DatasetState> {
    let meta = db.get_dataset_meta()?;
    let mission_records = db.get_missions()?;
    let mut missions = Vec::new();
    for rec in mission_records {
        let staged = db.get_mission_staged_files(&rec.name)?;
        let committed = db.get_mission_committed_files(&rec.name)?;
        missions.push(MissionState {
            record: rec,
            staged_files: staged,
            committed_files: committed,
        });
    }
    let staged_paths: Vec<PathBuf> = db
        .get_dataset_staged_files()?
        .into_iter()
        .map(PathBuf::from)
        .collect();
    let committed = db.get_dataset_committed_files()?;
    Ok(DatasetState {
        root: root.to_path_buf(),
        day_0: meta.day_0,
        pushed: meta.pushed,
        version: meta.version,
        last_country: meta.last_country,
        last_region: meta.last_region,
        last_site: meta.last_site,
        missions,
        staged_files: staged_paths,
        committed_files: committed,
    })
}

fn load_from_filesystem(root: &Path) -> Result<DatasetState> {
    // Try to find metadata.json files and reconstruct day_0 from them
    let mut metadata_files: Vec<PathBuf> = Vec::new();
    visit_dirs(root, &mut |p| {
        if p.file_name().map(|n| n == "metadata.json").unwrap_or(false) {
            metadata_files.push(p.to_path_buf());
        }
    })?;

    if metadata_files.is_empty() {
        return Err(E4EError::Runtime(
            "No config file and no data!".to_string(),
        ));
    }

    // Use first metadata file to determine day_0
    let first_meta_file = &metadata_files[0];
    let meta = metadata::read_metadata(first_meta_file.parent().unwrap())?;
    let mission_date = parse_date_from_iso(&meta.timestamp)?;

    // Check if the first path component starts with 'ED'
    let rel = first_meta_file.strip_prefix(root).unwrap();
    let day_0 = if rel
        .components()
        .next()
        .and_then(|c| c.as_os_str().to_str())
        .map(|s| s.starts_with("ED"))
        .unwrap_or(false)
    {
        let day_str = rel
            .components()
            .next()
            .unwrap()
            .as_os_str()
            .to_str()
            .unwrap();
        let mission_day: i64 = day_str[3..].parse().unwrap_or(0);
        subtract_days(&mission_date, mission_day)
    } else {
        mission_date
    };

    Ok(DatasetState {
        root: root.to_path_buf(),
        day_0,
        pushed: false,
        version: VERSION,
        last_country: None,
        last_region: None,
        last_site: None,
        missions: Vec::new(),
        staged_files: Vec::new(),
        committed_files: Vec::new(),
    })
}

fn visit_dirs(dir: &Path, cb: &mut dyn FnMut(&Path)) -> io::Result<()> {
    if dir.is_dir() {
        for entry in fs::read_dir(dir)? {
            let entry = entry?;
            let path = entry.path();
            if path.is_dir() {
                visit_dirs(&path, cb)?;
            } else {
                cb(&path);
            }
        }
    }
    Ok(())
}

/// Save dataset state back to `.e4edm.db`.
pub fn save_dataset_state(state: &DatasetState) -> Result<()> {
    let db = DatasetDb::open(&state.root)?;
    let meta = DatasetMeta {
        day_0: state.day_0.clone(),
        pushed: state.pushed,
        version: state.version,
        last_country: state.last_country.clone(),
        last_region: state.last_region.clone(),
        last_site: state.last_site.clone(),
    };
    // Ensure a row exists
    db.init_dataset(&state.day_0, state.version)?;
    db.update_dataset_meta(&meta)?;

    for mission in &state.missions {
        db.insert_mission(&mission.record)?;
        db.set_mission_staged_files(&mission.record.name, &mission.staged_files)?;
        db.add_mission_committed_files(
            &mission.record.name,
            &mission.committed_files,
        )?;
    }

    let staged_strs: Vec<String> = state
        .staged_files
        .iter()
        .map(|p| p.to_string_lossy().into_owned())
        .collect();
    db.set_dataset_staged_files(&staged_strs)?;
    db.add_dataset_committed_files(&state.committed_files)?;

    Ok(())
}

// ─────────────────────────────────────────────────────────────
// Public operations
// ─────────────────────────────────────────────────────────────

/// Create a new empty dataset on disk, init the DB, write an empty manifest.
pub fn create_dataset(root: &Path, day_0: &str) -> Result<DatasetState> {
    fs::create_dir_all(root)?;
    let db = DatasetDb::open(root)?;
    db.init_dataset(day_0, VERSION)?;

    // Write empty manifest
    let manifest_path = root.join(MANIFEST_NAME);
    manifest::write_manifest(&manifest_path, &manifest::ManifestData::new())?;

    let state = DatasetState {
        root: root.to_path_buf(),
        day_0: day_0.to_string(),
        pushed: false,
        version: VERSION,
        last_country: None,
        last_region: None,
        last_site: None,
        missions: Vec::new(),
        staged_files: Vec::new(),
        committed_files: Vec::new(),
    };
    Ok(state)
}

/// Add a new mission: create directory, write metadata.json + manifest.json,
/// update dataset manifest, persist to DB.
pub fn add_mission(state: &mut DatasetState, meta: &MetadataRecord) -> Result<MissionRecord> {
    let mission_date = parse_date_from_iso(&meta.timestamp)?;
    let expedition_day = days_between(&state.day_0, &mission_date)?;
    let day_path = state.root.join(format!("ED-{:02}", expedition_day));
    let mission_path = day_path.join(&meta.mission_name);

    fs::create_dir_all(&mission_path)?;
    metadata::write_metadata(&mission_path, meta)?;

    // Create an empty manifest for the mission containing only metadata.json
    let mission_manifest_path = mission_path.join(MANIFEST_NAME);
    let mission_meta_files = vec![mission_path.join("metadata.json")];
    let mission_manifest_data =
        manifest::compute_hashes(&mission_path, &mission_meta_files)?;
    manifest::write_manifest(&mission_manifest_path, &mission_manifest_data)?;

    // Mission name is "ED-{day:02} {mission_name}"
    let mission_name = format!("ED-{:02} {}", expedition_day, meta.mission_name);

    let record = MissionRecord {
        name: mission_name.clone(),
        path: mission_path.to_string_lossy().into_owned(),
        metadata: meta.clone(),
    };

    // Update dataset manifest to include new mission files (metadata.json, manifest.json)
    let new_files = vec![
        mission_path.join("metadata.json"),
        mission_manifest_path,
    ];
    let dataset_manifest_path = state.root.join(MANIFEST_NAME);
    manifest::update_manifest(&dataset_manifest_path, &state.root, &new_files)?;

    // Update last_country, last_region, last_site
    state.last_country = Some(meta.country.clone());
    state.last_region = Some(meta.region.clone());
    state.last_site = Some(meta.site.clone());

    let mission_state = MissionState {
        record: record.clone(),
        staged_files: Vec::new(),
        committed_files: Vec::new(),
    };
    state.missions.push(mission_state);

    // Persist
    let db = DatasetDb::open(&state.root)?;
    db.insert_mission(&record)?;
    let dataset_meta = DatasetMeta {
        day_0: state.day_0.clone(),
        pushed: state.pushed,
        version: state.version,
        last_country: state.last_country.clone(),
        last_region: state.last_region.clone(),
        last_site: state.last_site.clone(),
    };
    db.update_dataset_meta(&dataset_meta)?;

    Ok(record)
}

/// Remove a mission from the dataset: strip its files from the dataset manifest,
/// delete its directory from disk, and remove it from the DB.
pub fn remove_mission(state: &mut DatasetState, mission_name: &str) -> Result<()> {
    let idx = state
        .missions
        .iter()
        .position(|m| m.record.name == mission_name)
        .ok_or_else(|| E4EError::Runtime(format!("Mission not found: {}", mission_name)))?;

    // Derive mission_path from state.root and the mission name to avoid stale
    // absolute paths stored in the DB (e.g. from a previous TemporaryDirectory).
    // Mission name format: "ED-{day} {mission_sub_name}" where mission_sub_name
    // may contain slashes for nested paths like "reef-laser-03/right/box".
    let mission_path = {
        let parts: Vec<&str> = mission_name.splitn(2, ' ').collect();
        if parts.len() == 2 {
            state.root.join(parts[0]).join(parts[1])
        } else {
            PathBuf::from(&state.missions[idx].record.path)
        }
    };

    // Build the posix-style relative prefix used as manifest keys (e.g. "ED-00/M1")
    let rel_prefix = mission_path
        .strip_prefix(&state.root)
        .map_err(|e| E4EError::Runtime(e.to_string()))?;
    let rel_prefix_posix = rel_prefix
        .components()
        .map(|c| c.as_os_str().to_string_lossy().into_owned())
        .collect::<Vec<_>>()
        .join("/");

    // Remove all matching entries from the dataset manifest
    let manifest_path = state.root.join(MANIFEST_NAME);
    let mut manifest_data = manifest::read_manifest(&manifest_path)?;
    manifest_data.retain(|k, _| !k.starts_with(&format!("{}/", rel_prefix_posix)));
    manifest::write_manifest(&manifest_path, &manifest_data)?;

    // Delete the mission directory
    if mission_path.exists() {
        fs::remove_dir_all(&mission_path)?;
    }

    // Remove the day directory (ED-XX) if it is now empty
    if let Some(day_dir) = mission_path.parent() {
        if day_dir != state.root {
            if let Ok(mut entries) = fs::read_dir(day_dir) {
                if entries.next().is_none() {
                    let _ = fs::remove_dir(day_dir);
                }
            }
        }
    }

    // Remove from DB
    let db = DatasetDb::open(&state.root)?;
    db.delete_mission(mission_name)?;

    // Remove from in-memory state
    state.missions.remove(idx);

    Ok(())
}

/// Stage files for a mission (pre-compute hashes).
pub fn stage_mission_files(
    state: &mut DatasetState,
    mission_name: &str,
    paths: &[PathBuf],
    destination: Option<&Path>,
) -> Result<Vec<StagedFileRecord>> {
    let mission_idx = state
        .missions
        .iter()
        .position(|m| m.record.name == mission_name)
        .ok_or_else(|| E4EError::Runtime(format!("Mission not found: {}", mission_name)))?;

    let mission_path = PathBuf::from(&state.missions[mission_idx].record.path);
    let dst = match destination {
        Some(d) => mission_path.join(d),
        None => mission_path.clone(),
    };

    let mut new_staged: Vec<StagedFileRecord> = Vec::new();

    for path in paths {
        let origin = path.canonicalize().unwrap_or_else(|_| path.to_path_buf());
        if origin.is_file() {
            let hash = manifest::compute_file_hash(&origin)?;
            let target = dst.join(origin.file_name().unwrap());
            new_staged.push(StagedFileRecord {
                origin_path: origin.to_string_lossy().into_owned(),
                target_path: target.to_string_lossy().into_owned(),
                hash,
            });
        } else if origin.is_dir() {
            for entry in walkdir::WalkDir::new(&origin)
                .into_iter()
                .filter_map(|e| e.ok())
                .filter(|e| e.file_type().is_file())
            {
                let file = entry.path();
                let rel = file.strip_prefix(&origin).unwrap();
                let target = dst.join(rel);
                let hash = manifest::compute_file_hash(file)?;
                new_staged.push(StagedFileRecord {
                    origin_path: file.to_string_lossy().into_owned(),
                    target_path: target.to_string_lossy().into_owned(),
                    hash,
                });
            }
        } else {
            return Err(E4EError::Runtime(format!(
                "Not a normal file: {}",
                path.display()
            )));
        }
    }

    // Merge new staged files with existing ones (dedup on target_path)
    let existing = &mut state.missions[mission_idx].staged_files;
    for sf in &new_staged {
        if !existing.iter().any(|e| e.target_path == sf.target_path) {
            existing.push(sf.clone());
        }
    }

    let db = DatasetDb::open(&state.root)?;
    db.set_mission_staged_files(mission_name, &state.missions[mission_idx].staged_files)?;

    Ok(new_staged)
}

/// Commit staged mission files: copy, verify, update manifests.
pub fn commit_mission_files(
    state: &mut DatasetState,
    mission_name: &str,
) -> Result<Vec<PathBuf>> {
    let mission_idx = state
        .missions
        .iter()
        .position(|m| m.record.name == mission_name)
        .ok_or_else(|| E4EError::Runtime(format!("Mission not found: {}", mission_name)))?;

    let mission_path = PathBuf::from(state.missions[mission_idx].record.path.clone());
    let staged = state.missions[mission_idx].staged_files.clone();

    let mut committed: Vec<PathBuf> = Vec::new();
    let mut committed_with_hashes: Vec<(PathBuf, String)> = Vec::new();
    for sf in &staged {
        let src = PathBuf::from(&sf.origin_path);
        let dst = PathBuf::from(&sf.target_path);
        if let Some(parent) = dst.parent() {
            fs::create_dir_all(parent)?;
        }
        fs::copy(&src, &dst)?;
        // Verify the copy is intact by recomputing the hash of the destination.
        let actual_hash = manifest::compute_file_hash(&dst)?;
        if actual_hash != sf.hash {
            return Err(E4EError::Runtime(format!(
                "Hash mismatch after copy: {}",
                src.display()
            )));
        }
        committed.push(dst.clone());
        committed_with_hashes.push((dst, sf.hash.clone()));
    }

    // Update mission manifest using pre-computed hashes (no re-read of file contents)
    let mission_manifest_path = mission_path.join(MANIFEST_NAME);
    manifest::update_manifest_with_known_hashes(
        &mission_manifest_path,
        &mission_path,
        &committed_with_hashes,
    )?;

    // Update dataset manifest: data files reuse staged hashes; mission manifest was just
    // rewritten so its hash must be freshly computed (it's small, one hash is fine).
    let mission_manifest_hash = manifest::compute_file_hash(&mission_manifest_path)?;
    let mut dataset_update = committed_with_hashes;
    dataset_update.push((mission_manifest_path, mission_manifest_hash));
    manifest::update_manifest_with_known_hashes(
        &state.root.join(MANIFEST_NAME),
        &state.root,
        &dataset_update,
    )?;

    // Update state
    let relative_committed: Vec<String> = committed
        .iter()
        .map(|p| {
            p.strip_prefix(&mission_path)
                .map(|r| r.to_string_lossy().into_owned())
                .unwrap_or_else(|_| p.to_string_lossy().into_owned())
        })
        .collect();
    state.missions[mission_idx]
        .committed_files
        .extend(relative_committed.clone());
    state.missions[mission_idx].staged_files.clear();

    // Persist
    let db = DatasetDb::open(&state.root)?;
    db.clear_mission_staged_files(mission_name)?;
    db.add_mission_committed_files(mission_name, &relative_committed)?;

    Ok(committed)
}

/// Stage files at the dataset level (readme files).
pub fn stage_dataset_files(state: &mut DatasetState, paths: &[PathBuf]) -> Result<()> {
    for p in paths {
        if !state.staged_files.contains(p) {
            state.staged_files.push(p.clone());
        }
    }
    let strs: Vec<String> = state
        .staged_files
        .iter()
        .map(|p| p.to_string_lossy().into_owned())
        .collect();
    let db = DatasetDb::open(&state.root)?;
    db.set_dataset_staged_files(&strs)?;
    Ok(())
}

/// Commit dataset-level staged files (readme).
pub fn commit_dataset_files(state: &mut DatasetState) -> Result<Vec<PathBuf>> {
    let staged = state.staged_files.clone();
    let mut committed: Vec<PathBuf> = Vec::new();

    for path in &staged {
        let src = path.canonicalize().unwrap_or_else(|_| path.clone());
        if src.is_file() {
            // Goes into dataset root
            let dst = state.root.join(src.file_name().unwrap());
            if let Some(parent) = dst.parent() {
                fs::create_dir_all(parent)?;
            }
            fs::copy(&src, &dst)?;
            // Verify using size (readme files)
            let src_size = fs::metadata(&src)?.len();
            let dst_size = fs::metadata(&dst)?.len();
            if src_size != dst_size {
                return Err(E4EError::Runtime(format!(
                    "Copy size mismatch: {}",
                    src.display()
                )));
            }
            committed.push(dst);
        } else if src.is_dir() {
            for entry in walkdir::WalkDir::new(&src)
                .into_iter()
                .filter_map(|e| e.ok())
                .filter(|e| e.file_type().is_file())
            {
                let file = entry.path().to_path_buf();
                let rel = file.strip_prefix(&src).unwrap();
                let dst = state.root.join(rel);
                if let Some(parent) = dst.parent() {
                    fs::create_dir_all(parent)?;
                }
                fs::copy(&file, &dst)?;
                // Verify copy integrity using size
                let src_size = fs::metadata(&file)?.len();
                let dst_size = fs::metadata(&dst)?.len();
                if src_size != dst_size {
                    return Err(E4EError::Runtime(format!(
                        "Copy size mismatch: {}",
                        file.display()
                    )));
                }
                committed.push(dst);
            }
        }
    }

    // Update dataset manifest
    let dataset_manifest_path = state.root.join(MANIFEST_NAME);
    manifest::update_manifest(&dataset_manifest_path, &state.root, &committed)?;

    // Update state
    let committed_strs: Vec<String> = committed
        .iter()
        .map(|p| p.to_string_lossy().into_owned())
        .collect();
    state.committed_files.extend(committed_strs.clone());
    state.staged_files.clear();

    let db = DatasetDb::open(&state.root)?;
    db.clear_dataset_staged_files()?;
    db.add_dataset_committed_files(&committed_strs)?;

    Ok(committed)
}

/// Validate the dataset against its manifest (hash check).
pub fn validate_dataset(root: &Path) -> Result<bool> {
    Ok(validate_dataset_failures(root)?.is_empty())
}

/// Return a list of validation failure messages for the dataset, calling
/// `progress(current, total)` after each file is hashed.
pub fn validate_dataset_failures_with_progress<F>(root: &Path, progress: F) -> Result<Vec<String>>
where
    F: Fn(u64, u64) + Send + Sync,
{
    let manifest_path = root.join(MANIFEST_NAME);
    let manifest_data = manifest::read_manifest(&manifest_path)?;
    let files = get_dataset_files(root);
    manifest::collect_validation_failures_with_progress(&manifest_data, root, &files, "hash", progress)
}

/// Return a list of validation failure messages for the dataset.
/// An empty list means the dataset is valid.
pub fn validate_dataset_failures(root: &Path) -> Result<Vec<String>> {
    validate_dataset_failures_with_progress(root, |_, _| {})
}

/// Check that dataset is complete and ready to push.
pub fn check_complete(state: &DatasetState) -> Result<()> {
    // 1. Any mission has staged files?
    if state.missions.iter().any(|m| !m.staged_files.is_empty()) {
        return Err(E4EError::MissionFilesInStaging);
    }

    // 2. Dataset has staged files?
    if !state.staged_files.is_empty() {
        return Err(E4EError::ReadmeFilesInStaging);
    }

    // 3. No readme.*?
    use std::ffi::OsStr;
    let readme_entries: Vec<_> = fs::read_dir(&state.root)?
        .filter_map(|e| e.ok())
        .filter(|e| {
            e.file_name()
                .to_string_lossy()
                .to_lowercase()
                .starts_with("readme")
        })
        .collect();

    if readme_entries.is_empty() {
        return Err(E4EError::ReadmeNotFound("Readme not found".to_string()));
    }

    let acceptable_exts: &[&OsStr] = &[OsStr::new("md"), OsStr::new("docx")];
    let has_acceptable = readme_entries.iter().any(|e| {
        Path::new(&e.file_name())
            .extension()
            .map(|ext| acceptable_exts.contains(&ext.to_ascii_lowercase().as_os_str()))
            .unwrap_or(false)
    });
    if !has_acceptable {
        return Err(E4EError::ReadmeNotFound(
            "Acceptable extension not found".to_string(),
        ));
    }

    // 4. Validate integrity
    if !validate_dataset(&state.root)? {
        return Err(E4EError::CorruptedDataset);
    }

    Ok(())
}

/// Verify that the dataset at `dest` (if it exists) is a subset of the source dataset.
///
/// Every file recorded in the destination's `manifest.json` must also appear in
/// `source_manifest` with an identical SHA-256 hash.  Returns `Ok(())` when it is
/// safe to push (destination absent, empty, or a compatible partial copy).  Returns
/// an error describing the first conflict found.
pub fn check_destination_is_subset(
    source_manifest: &manifest::ManifestData,
    dest: &Path,
) -> Result<()> {
    if !dest.exists() {
        return Ok(());
    }
    let dest_manifest = manifest::read_manifest(&dest.join(MANIFEST_NAME))?;
    for (rel_path, dest_entry) in &dest_manifest {
        match source_manifest.get(rel_path) {
            Some(src_entry) if src_entry.sha256sum == dest_entry.sha256sum => {}
            Some(_) => {
                return Err(E4EError::Runtime(format!(
                    "File '{}' at destination has a different hash from the source dataset",
                    rel_path
                )));
            }
            None => {
                return Err(E4EError::Runtime(format!(
                    "File '{}' exists at destination but is not in the source dataset",
                    rel_path
                )));
            }
        }
    }
    Ok(())
}

/// Return all data files in a dataset root (excluding manifest.json and .e4edm.db).
pub fn get_dataset_files(root: &Path) -> Vec<PathBuf> {
    let excluded = [root.join(MANIFEST_NAME), root.join(DB_NAME)];
    let mut files = Vec::new();
    let walker = walkdir::WalkDir::new(root).into_iter();
    for entry in walker.filter_map(|e| e.ok()) {
        let path = entry.path().to_path_buf();
        if !path.is_file() {
            continue;
        }
        if excluded.contains(&path) {
            continue;
        }
        files.push(path);
    }
    files
}

/// Duplicate the dataset to each destination, calling `progress(current, total)` as
/// files are copied and then verified.  Progress runs 1..N during the copy phase and
/// N+1..2N during the destination validation phase.
pub fn duplicate_dataset_with_progress<F>(
    state: &DatasetState,
    destinations: &[PathBuf],
    progress: F,
) -> Result<()>
where
    F: Fn(u64, u64) + Send + Sync,
{
    let manifest_path = state.root.join(MANIFEST_NAME);
    let manifest_data = manifest::read_manifest(&manifest_path)?;
    let file_count = manifest_data.len() as u64;
    let total = file_count * 2;

    let entries: Vec<(&String, &manifest::ManifestEntry)> = manifest_data.iter().collect();

    for dest in destinations {
        fs::create_dir_all(dest)?;

        // Clear any leftover temp files from a previous interrupted push.
        manifest::cleanup_temp_files(dest)?;

        // Phase 1: copy files in parallel, verifying hash during the write.
        // Each file is hashed as it is streamed to the destination, so no
        // separate re-read of the destination is needed for copied files.
        let counter = AtomicU64::new(0);
        let first_error: std::sync::Mutex<Option<E4EError>> = std::sync::Mutex::new(None);

        entries.par_iter().for_each(|(rel_path, entry)| {
            // Stop early if a previous iteration already failed.
            if first_error.lock().unwrap().is_some() {
                return;
            }

            let src = state.root.join(rel_path);
            let dst = dest.join(rel_path.as_str());

            let result = (|| -> Result<()> {
                if let Some(parent) = dst.parent() {
                    fs::create_dir_all(parent).map_err(|e| {
                        if e.kind() == std::io::ErrorKind::AlreadyExists {
                            E4EError::Runtime(format!(
                                "Cannot create directory '{}': path exists as a file",
                                parent.display()
                            ))
                        } else {
                            E4EError::Io(e)
                        }
                    })?;
                }

                // Skip if the destination file already has the correct hash.
                let already_correct = dst.exists()
                    && manifest::compute_file_hash(&dst)
                        .map(|h| h == entry.sha256sum)
                        .unwrap_or(false);

                if !already_correct {
                    if dst.is_dir() {
                        return Err(E4EError::Runtime(format!(
                            "Cannot copy '{}': destination path '{}' exists as a directory",
                            rel_path,
                            dst.display()
                        )));
                    }
                    // Copy and verify the hash inline — no second read needed.
                    manifest::copy_and_verify(&src, &dst, &entry.sha256sum)?;
                }
                Ok(())
            })();

            if let Err(e) = result {
                let mut guard = first_error.lock().unwrap();
                if guard.is_none() {
                    *guard = Some(e);
                }
            }

            let i = counter.fetch_add(1, Ordering::Relaxed);
            progress(i + 1, total);
        });

        if let Some(e) = first_error.into_inner().unwrap() {
            return Err(e);
        }

        // Phase 2: check for unlisted files at the destination.
        // Hashes were already verified inline during copy, so only a directory
        // walk is needed here — no re-hashing.
        let all_dest_files = get_dataset_files(dest);
        let unlisted: Vec<String> = all_dest_files
            .iter()
            .filter_map(|file| {
                let rel = file.strip_prefix(dest.as_path()).ok()?;
                let rel_posix = rel
                    .components()
                    .map(|c| c.as_os_str().to_string_lossy().into_owned())
                    .collect::<Vec<_>>()
                    .join("/");
                if !manifest_data.contains_key(&rel_posix)
                    && !manifest::is_temp_file(file)
                {
                    Some(format!("unlisted file: {}", rel_posix))
                } else {
                    None
                }
            })
            .collect();

        for i in 0..all_dest_files.len() as u64 {
            progress(file_count + i + 1, total);
        }

        if !unlisted.is_empty() {
            return Err(E4EError::Runtime(format!(
                "Unlisted files at destination {}:\n  {}",
                dest.display(),
                unlisted.join("\n  ")
            )));
        }

        manifest::write_manifest(&dest.join(MANIFEST_NAME), &manifest_data)?;
    }
    Ok(())
}

/// Duplicate the dataset to each destination.
#[cfg_attr(not(feature = "python"), allow(dead_code))]
pub fn duplicate_dataset(state: &DatasetState, destinations: &[PathBuf]) -> Result<()> {
    duplicate_dataset_with_progress(state, destinations, |_, _| {})
}

/// Create a zip archive of the dataset.
#[cfg_attr(not(feature = "python"), allow(dead_code))]
pub fn create_zip(state: &DatasetState, zip_path: &Path) -> Result<()> {
    let manifest_path = state.root.join(MANIFEST_NAME);
    let manifest_data = manifest::read_manifest(&manifest_path)?;

    use std::io::Write;
    let file = fs::File::create(zip_path)?;
    let mut zip = zip::ZipWriter::new(file);
    let options = zip::write::SimpleFileOptions::default()
        .compression_method(zip::CompressionMethod::Deflated);

    let dataset_name = state
        .root
        .file_name()
        .unwrap_or_default()
        .to_string_lossy()
        .into_owned();

    for rel_path in manifest_data.keys() {
        let src = state.root.join(rel_path);
        let arc_path = format!("{}/{}", dataset_name, rel_path);
        zip.start_file(&arc_path, options)
            .map_err(|e| crate::errors::E4EError::Runtime(e.to_string()))?;
        let data = fs::read(&src)?;
        zip.write_all(&data)?;
    }
    zip.finish().map_err(|e| crate::errors::E4EError::Runtime(e.to_string()))?;
    Ok(())
}

// ─────────────────────────────────────────────────────────────
// Date helpers
// ─────────────────────────────────────────────────────────────

/// Parse the date part from an ISO 8601 datetime string.
/// Returns a "YYYY-MM-DD" string (date portion only).
pub fn parse_date_from_iso(iso: &str) -> Result<String> {
    // ISO strings may be "2023-03-02T19:38:00-08:00" or just "2023-03-02"
    let date_part = iso.split('T').next().unwrap_or(iso);
    Ok(date_part.to_string())
}

/// Compute number of days between two "YYYY-MM-DD" date strings.
/// Returns (b - a).days  (positive if b is after a).
pub fn days_between(a: &str, b: &str) -> Result<i64> {
    let a_days = date_to_days(a)?;
    let b_days = date_to_days(b)?;
    Ok(b_days - a_days)
}

fn subtract_days(date_str: &str, n: i64) -> String {
    let days = date_to_days(date_str).unwrap_or(0);
    days_to_date(days - n)
}

/// Convert "YYYY-MM-DD" to a Julian-day integer (simple calculation).
fn date_to_days(date: &str) -> Result<i64> {
    let parts: Vec<&str> = date.split('-').collect();
    if parts.len() < 3 {
        return Err(E4EError::Runtime(format!(
            "Invalid date string: {}",
            date
        )));
    }
    let y: i64 = parts[0].parse().map_err(|e: std::num::ParseIntError| {
        E4EError::Runtime(e.to_string())
    })?;
    let m: i64 = parts[1].parse().map_err(|e: std::num::ParseIntError| {
        E4EError::Runtime(e.to_string())
    })?;
    let d: i64 = parts[2].parse().map_err(|e: std::num::ParseIntError| {
        E4EError::Runtime(e.to_string())
    })?;
    // Simplified Julian Day Number
    let a = (14 - m) / 12;
    let y2 = y + 4800 - a;
    let m2 = m + 12 * a - 3;
    let jdn = d + (153 * m2 + 2) / 5 + 365 * y2 + y2 / 4 - y2 / 100 + y2 / 400 - 32045;
    Ok(jdn)
}

fn days_to_date(jdn: i64) -> String {
    // Convert Julian Day Number back to calendar date
    let l = jdn + 68569;
    let n = (4 * l) / 146097;
    let l = l - (146097 * n + 3) / 4;
    let i = (4000 * (l + 1)) / 1461001;
    let l = l - (1461 * i) / 4 + 31;
    let j = (80 * l) / 2447;
    let d = l - (2447 * j) / 80;
    let l = j / 11;
    let m = j + 2 - 12 * l;
    let y = 100 * (n - 49) + i + l;
    format!("{:04}-{:02}-{:02}", y, m, d)
}

#[cfg(test)]
mod tests {
    use super::*;
    use tempfile::tempdir;

    fn meta(timestamp: &str, mission: &str) -> MetadataRecord {
        MetadataRecord {
            timestamp: timestamp.to_string(),
            device: "Device1".to_string(),
            country: "USA".to_string(),
            region: "California".to_string(),
            site: "SD".to_string(),
            mission_name: mission.to_string(),
            properties: "{}".to_string(),
            notes: String::new(),
        }
    }

    // ── Date helpers ─────────────────────────────────────────────

    #[test]
    fn parse_date_strips_time_component() {
        assert_eq!(parse_date_from_iso("2023-03-02T19:38:00-08:00").unwrap(), "2023-03-02");
    }

    #[test]
    fn parse_date_passes_through_date_only_string() {
        assert_eq!(parse_date_from_iso("2023-03-02").unwrap(), "2023-03-02");
    }

    #[test]
    fn days_between_same_day_is_zero() {
        assert_eq!(days_between("2023-03-02", "2023-03-02").unwrap(), 0);
    }

    #[test]
    fn days_between_consecutive_days_is_one() {
        assert_eq!(days_between("2023-03-02", "2023-03-03").unwrap(), 1);
    }

    #[test]
    fn days_between_multi_day_span() {
        assert_eq!(days_between("2023-03-02", "2023-03-05").unwrap(), 3);
    }

    #[test]
    fn days_between_cross_month_boundary() {
        assert_eq!(days_between("2023-01-31", "2023-02-01").unwrap(), 1);
    }

    #[test]
    fn days_between_cross_year_boundary() {
        assert_eq!(days_between("2022-12-31", "2023-01-01").unwrap(), 1);
    }

    #[test]
    fn days_between_is_negative_when_b_before_a() {
        assert_eq!(days_between("2023-03-05", "2023-03-02").unwrap(), -3);
    }

    // ── create_dataset ────────────────────────────────────────────

    #[test]
    fn create_dataset_produces_directory_manifest_and_db() {
        let tmp = tempdir().unwrap();
        let root = tmp.path().join("2023.03.02.Test.SD");
        let state = create_dataset(&root, "2023-03-02").unwrap();
        assert!(root.exists());
        assert!(root.join("manifest.json").exists());
        assert!(root.join(".e4edm.db").exists());
        assert_eq!(state.day_0, "2023-03-02");
        assert!(!state.pushed);
        assert!(state.missions.is_empty());
    }

    // ── add_mission ───────────────────────────────────────────────

    #[test]
    fn add_mission_on_day_zero_uses_ed_00() {
        let tmp = tempdir().unwrap();
        let root = tmp.path().join("ds");
        let mut state = create_dataset(&root, "2023-03-02").unwrap();
        let record = add_mission(&mut state, &meta("2023-03-02T10:00:00+00:00", "M1")).unwrap();
        assert_eq!(record.name, "ED-00 M1");
        assert!(root.join("ED-00").join("M1").join("metadata.json").exists());
        assert!(root.join("ED-00").join("M1").join("manifest.json").exists());
    }

    #[test]
    fn add_mission_on_next_day_uses_ed_01() {
        let tmp = tempdir().unwrap();
        let root = tmp.path().join("ds");
        let mut state = create_dataset(&root, "2023-03-02").unwrap();
        let record = add_mission(&mut state, &meta("2023-03-03T08:00:00+00:00", "M2")).unwrap();
        assert_eq!(record.name, "ED-01 M2");
        assert!(root.join("ED-01").join("M2").exists());
    }

    #[test]
    fn add_mission_updates_last_country_region_site() {
        let tmp = tempdir().unwrap();
        let root = tmp.path().join("ds");
        let mut state = create_dataset(&root, "2023-03-02").unwrap();
        add_mission(&mut state, &meta("2023-03-02T10:00:00+00:00", "M1")).unwrap();
        assert_eq!(state.last_country, Some("USA".to_string()));
        assert_eq!(state.last_region, Some("California".to_string()));
        assert_eq!(state.last_site, Some("SD".to_string()));
    }

    #[test]
    fn add_mission_appended_to_dataset_manifest() {
        let tmp = tempdir().unwrap();
        let root = tmp.path().join("ds");
        let mut state = create_dataset(&root, "2023-03-02").unwrap();
        add_mission(&mut state, &meta("2023-03-02T10:00:00+00:00", "M1")).unwrap();
        let manifest = manifest::read_manifest(&root.join("manifest.json")).unwrap();
        assert!(manifest.keys().any(|k| k.contains("metadata.json")));
    }

    // ── stage / commit mission files ──────────────────────────────

    #[test]
    fn stage_and_commit_copies_file_to_mission_directory() {
        let tmp = tempdir().unwrap();
        let root = tmp.path().join("ds");
        let mut state = create_dataset(&root, "2023-03-02").unwrap();
        add_mission(&mut state, &meta("2023-03-02T10:00:00+00:00", "M1")).unwrap();

        let src = tmp.path().join("data.bin");
        fs::write(&src, b"file content").unwrap();

        stage_mission_files(&mut state, "ED-00 M1", &[src], None).unwrap();
        assert_eq!(state.missions[0].staged_files.len(), 1);
        assert_eq!(state.missions[0].committed_files.len(), 0);

        commit_mission_files(&mut state, "ED-00 M1").unwrap();
        assert_eq!(state.missions[0].staged_files.len(), 0);
        assert_eq!(state.missions[0].committed_files.len(), 1);

        let dest = root.join("ED-00").join("M1").join("data.bin");
        assert!(dest.exists());
        assert_eq!(fs::read(&dest).unwrap(), b"file content");
    }

    #[test]
    fn stage_with_destination_places_file_in_subdirectory() {
        let tmp = tempdir().unwrap();
        let root = tmp.path().join("ds");
        let mut state = create_dataset(&root, "2023-03-02").unwrap();
        add_mission(&mut state, &meta("2023-03-02T10:00:00+00:00", "M1")).unwrap();

        let src = tmp.path().join("data.bin");
        fs::write(&src, b"data").unwrap();
        stage_mission_files(&mut state, "ED-00 M1", &[src], Some(Path::new("subdir"))).unwrap();
        commit_mission_files(&mut state, "ED-00 M1").unwrap();

        assert!(root.join("ED-00").join("M1").join("subdir").join("data.bin").exists());
    }

    #[test]
    fn commit_verifies_hash_and_updates_manifests() {
        let tmp = tempdir().unwrap();
        let root = tmp.path().join("ds");
        let mut state = create_dataset(&root, "2023-03-02").unwrap();
        add_mission(&mut state, &meta("2023-03-02T10:00:00+00:00", "M1")).unwrap();

        let src = tmp.path().join("data.bin");
        fs::write(&src, b"verifiable").unwrap();
        stage_mission_files(&mut state, "ED-00 M1", &[src], None).unwrap();
        commit_mission_files(&mut state, "ED-00 M1").unwrap();

        // Mission manifest should contain the committed file
        let mission_manifest =
            manifest::read_manifest(&root.join("ED-00").join("M1").join("manifest.json")).unwrap();
        assert!(mission_manifest.contains_key("data.bin"));

        // Dataset manifest should also be updated
        let ds_manifest = manifest::read_manifest(&root.join("manifest.json")).unwrap();
        assert!(ds_manifest.keys().any(|k| k.ends_with("data.bin")));
    }

    // ── stage / commit dataset files (readme) ────────────────────

    #[test]
    fn stage_and_commit_dataset_files_copies_readme_to_root() {
        let tmp = tempdir().unwrap();
        let root = tmp.path().join("ds");
        let mut state = create_dataset(&root, "2023-03-02").unwrap();

        let readme = tmp.path().join("readme.md");
        fs::write(&readme, b"# Readme").unwrap();

        stage_dataset_files(&mut state, &[readme]).unwrap();
        assert_eq!(state.staged_files.len(), 1);
        commit_dataset_files(&mut state).unwrap();
        assert_eq!(state.staged_files.len(), 0);
        assert!(root.join("readme.md").exists());
    }

    // ── validate_dataset ─────────────────────────────────────────

    #[test]
    fn validate_dataset_passes_for_intact_files() {
        let tmp = tempdir().unwrap();
        let root = tmp.path().join("ds");
        let mut state = create_dataset(&root, "2023-03-02").unwrap();
        add_mission(&mut state, &meta("2023-03-02T10:00:00+00:00", "M1")).unwrap();

        let src = tmp.path().join("data.bin");
        fs::write(&src, b"good").unwrap();
        stage_mission_files(&mut state, "ED-00 M1", &[src], None).unwrap();
        commit_mission_files(&mut state, "ED-00 M1").unwrap();

        assert!(validate_dataset(&root).unwrap());
    }

    #[test]
    fn validate_dataset_fails_after_file_corruption() {
        let tmp = tempdir().unwrap();
        let root = tmp.path().join("ds");
        let mut state = create_dataset(&root, "2023-03-02").unwrap();
        add_mission(&mut state, &meta("2023-03-02T10:00:00+00:00", "M1")).unwrap();

        let src = tmp.path().join("data.bin");
        fs::write(&src, b"original").unwrap();
        stage_mission_files(&mut state, "ED-00 M1", &[src], None).unwrap();
        commit_mission_files(&mut state, "ED-00 M1").unwrap();

        // Tamper with the committed file
        fs::write(root.join("ED-00").join("M1").join("data.bin"), b"tampered").unwrap();

        assert!(!validate_dataset(&root).unwrap());
    }

    // ── check_complete ────────────────────────────────────────────

    #[test]
    fn check_complete_errors_when_mission_files_staged() {
        let tmp = tempdir().unwrap();
        let root = tmp.path().join("ds");
        let mut state = create_dataset(&root, "2023-03-02").unwrap();
        add_mission(&mut state, &meta("2023-03-02T10:00:00+00:00", "M1")).unwrap();

        let src = tmp.path().join("data.bin");
        fs::write(&src, b"x").unwrap();
        stage_mission_files(&mut state, "ED-00 M1", &[src], None).unwrap();

        assert!(matches!(
            check_complete(&state).unwrap_err(),
            E4EError::MissionFilesInStaging
        ));
    }

    #[test]
    fn check_complete_errors_when_dataset_files_staged() {
        let tmp = tempdir().unwrap();
        let root = tmp.path().join("ds");
        let mut state = create_dataset(&root, "2023-03-02").unwrap();

        let readme = tmp.path().join("readme.md");
        fs::write(&readme, b"readme").unwrap();
        stage_dataset_files(&mut state, &[readme]).unwrap();

        assert!(matches!(
            check_complete(&state).unwrap_err(),
            E4EError::ReadmeFilesInStaging
        ));
    }

    #[test]
    fn check_complete_errors_when_no_readme_present() {
        let tmp = tempdir().unwrap();
        let root = tmp.path().join("ds");
        let state = create_dataset(&root, "2023-03-02").unwrap();
        assert!(matches!(
            check_complete(&state).unwrap_err(),
            E4EError::ReadmeNotFound(_)
        ));
    }

    #[test]
    fn check_complete_errors_for_unacceptable_readme_extension() {
        let tmp = tempdir().unwrap();
        let root = tmp.path().join("ds");
        let state = create_dataset(&root, "2023-03-02").unwrap();
        fs::write(root.join("readme.txt"), b"readme").unwrap();
        assert!(matches!(
            check_complete(&state).unwrap_err(),
            E4EError::ReadmeNotFound(_)
        ));
    }

    #[test]
    fn check_complete_passes_with_committed_readme() {
        let tmp = tempdir().unwrap();
        let root = tmp.path().join("ds");
        let mut state = create_dataset(&root, "2023-03-02").unwrap();

        let readme = tmp.path().join("readme.md");
        fs::write(&readme, b"# readme").unwrap();
        stage_dataset_files(&mut state, &[readme]).unwrap();
        commit_dataset_files(&mut state).unwrap();

        check_complete(&state).unwrap();
    }

    // ── duplicate_dataset ─────────────────────────────────────────

    #[test]
    fn duplicate_copies_all_manifest_files_to_destination() {
        let tmp = tempdir().unwrap();
        let root = tmp.path().join("ds");
        let mut state = create_dataset(&root, "2023-03-02").unwrap();
        add_mission(&mut state, &meta("2023-03-02T10:00:00+00:00", "M1")).unwrap();

        let src = tmp.path().join("data.bin");
        fs::write(&src, b"payload").unwrap();
        stage_mission_files(&mut state, "ED-00 M1", &[src], None).unwrap();
        commit_mission_files(&mut state, "ED-00 M1").unwrap();

        let dest = tmp.path().join("dest");
        duplicate_dataset(&state, &[dest.clone()]).unwrap();

        assert!(dest.join("manifest.json").exists());
        assert!(dest.join("ED-00").join("M1").join("data.bin").exists());
        // Duplicated file should have the same content
        assert_eq!(
            fs::read(dest.join("ED-00").join("M1").join("data.bin")).unwrap(),
            b"payload"
        );
    }

    // ── create_zip ────────────────────────────────────────────────

    #[test]
    fn create_zip_produces_non_empty_archive_with_correct_paths() {
        let tmp = tempdir().unwrap();
        let root = tmp.path().join("2023.03.02.Test.SD");
        let mut state = create_dataset(&root, "2023-03-02").unwrap();
        let readme = tmp.path().join("readme.md");
        fs::write(&readme, b"readme").unwrap();
        stage_dataset_files(&mut state, &[readme]).unwrap();
        commit_dataset_files(&mut state).unwrap();

        let zip_path = tmp.path().join("archive.zip");
        create_zip(&state, &zip_path).unwrap();
        assert!(zip_path.exists());

        let zip_file = fs::File::open(&zip_path).unwrap();
        let mut archive = zip::ZipArchive::new(zip_file).unwrap();
        let names: Vec<String> =
            (0..archive.len()).map(|i| archive.by_index(i).unwrap().name().to_string()).collect();
        assert!(
            names.iter().any(|n| n.contains("readme.md")),
            "readme.md not found in zip; entries: {names:?}"
        );
        // Paths should be prefixed with the dataset name
        assert!(names.iter().all(|n| n.starts_with("2023.03.02.Test.SD/")));
    }

    // ── load_dataset_state ────────────────────────────────────────

    #[test]
    fn load_dataset_state_restores_missions_and_metadata() {
        let tmp = tempdir().unwrap();
        let root = tmp.path().join("ds");
        let mut state = create_dataset(&root, "2023-03-02").unwrap();
        add_mission(&mut state, &meta("2023-03-02T10:00:00+00:00", "M1")).unwrap();

        let loaded = load_dataset_state(&root).unwrap();
        assert_eq!(loaded.day_0, "2023-03-02");
        assert_eq!(loaded.missions.len(), 1);
        assert_eq!(loaded.missions[0].record.name, "ED-00 M1");
        assert_eq!(loaded.last_country, Some("USA".to_string()));
    }

    #[test]
    fn load_dataset_state_restores_staged_files_after_save() {
        let tmp = tempdir().unwrap();
        let root = tmp.path().join("ds");
        let mut state = create_dataset(&root, "2023-03-02").unwrap();
        add_mission(&mut state, &meta("2023-03-02T10:00:00+00:00", "M1")).unwrap();

        let src = tmp.path().join("data.bin");
        fs::write(&src, b"staged").unwrap();
        stage_mission_files(&mut state, "ED-00 M1", &[src], None).unwrap();

        let loaded = load_dataset_state(&root).unwrap();
        assert_eq!(loaded.missions[0].staged_files.len(), 1);
    }

    // ── remove_mission ───────────────────────────────────────────

    #[test]
    fn remove_mission_deletes_directory_from_disk() {
        let tmp = tempdir().unwrap();
        let root = tmp.path().join("ds");
        let mut state = create_dataset(&root, "2023-03-02").unwrap();
        add_mission(&mut state, &meta("2023-03-02T10:00:00+00:00", "M1")).unwrap();

        let mission_dir = root.join("ED-00").join("M1");
        assert!(mission_dir.exists());

        remove_mission(&mut state, "ED-00 M1").unwrap();

        assert!(!mission_dir.exists());
    }

    #[test]
    fn remove_mission_strips_entries_from_dataset_manifest() {
        let tmp = tempdir().unwrap();
        let root = tmp.path().join("ds");
        let mut state = create_dataset(&root, "2023-03-02").unwrap();
        add_mission(&mut state, &meta("2023-03-02T10:00:00+00:00", "M1")).unwrap();

        remove_mission(&mut state, "ED-00 M1").unwrap();

        let manifest_data = manifest::read_manifest(&root.join("manifest.json")).unwrap();
        assert!(manifest_data.keys().all(|k| !k.starts_with("ED-00/M1/")));
    }

    #[test]
    fn remove_mission_removes_empty_day_directory() {
        let tmp = tempdir().unwrap();
        let root = tmp.path().join("ds");
        let mut state = create_dataset(&root, "2023-03-02").unwrap();
        add_mission(&mut state, &meta("2023-03-02T10:00:00+00:00", "M1")).unwrap();

        remove_mission(&mut state, "ED-00 M1").unwrap();

        assert!(!root.join("ED-00").exists());
    }

    #[test]
    fn remove_mission_preserves_day_dir_when_sibling_remains() {
        let tmp = tempdir().unwrap();
        let root = tmp.path().join("ds");
        let mut state = create_dataset(&root, "2023-03-02").unwrap();
        add_mission(&mut state, &meta("2023-03-02T10:00:00+00:00", "M1")).unwrap();
        add_mission(&mut state, &meta("2023-03-02T11:00:00+00:00", "M2")).unwrap();

        remove_mission(&mut state, "ED-00 M1").unwrap();

        assert!(root.join("ED-00").exists());
        assert!(root.join("ED-00").join("M2").exists());
    }

    #[test]
    fn remove_mission_preserves_sibling_manifest_entries() {
        let tmp = tempdir().unwrap();
        let root = tmp.path().join("ds");
        let mut state = create_dataset(&root, "2023-03-02").unwrap();
        add_mission(&mut state, &meta("2023-03-02T10:00:00+00:00", "M1")).unwrap();
        add_mission(&mut state, &meta("2023-03-02T11:00:00+00:00", "M2")).unwrap();

        remove_mission(&mut state, "ED-00 M1").unwrap();

        let manifest_data = manifest::read_manifest(&root.join("manifest.json")).unwrap();
        assert!(manifest_data.keys().any(|k| k.starts_with("ED-00/M2/")));
        assert!(manifest_data.keys().all(|k| !k.starts_with("ED-00/M1/")));
    }

    #[test]
    fn remove_mission_removes_it_from_state() {
        let tmp = tempdir().unwrap();
        let root = tmp.path().join("ds");
        let mut state = create_dataset(&root, "2023-03-02").unwrap();
        add_mission(&mut state, &meta("2023-03-02T10:00:00+00:00", "M1")).unwrap();
        add_mission(&mut state, &meta("2023-03-02T11:00:00+00:00", "M2")).unwrap();

        assert_eq!(state.missions.len(), 2);
        remove_mission(&mut state, "ED-00 M1").unwrap();
        assert_eq!(state.missions.len(), 1);
        assert_eq!(state.missions[0].record.name, "ED-00 M2");
    }

    #[test]
    fn remove_mission_also_removes_committed_files_from_manifest() {
        let tmp = tempdir().unwrap();
        let root = tmp.path().join("ds");
        let mut state = create_dataset(&root, "2023-03-02").unwrap();
        add_mission(&mut state, &meta("2023-03-02T10:00:00+00:00", "M1")).unwrap();

        let src = tmp.path().join("data.bin");
        fs::write(&src, b"payload").unwrap();
        stage_mission_files(&mut state, "ED-00 M1", &[src], None).unwrap();
        commit_mission_files(&mut state, "ED-00 M1").unwrap();

        // Confirm the committed file is in the dataset manifest before removal
        let before = manifest::read_manifest(&root.join("manifest.json")).unwrap();
        assert!(before.keys().any(|k| k.ends_with("data.bin")));

        remove_mission(&mut state, "ED-00 M1").unwrap();

        let after = manifest::read_manifest(&root.join("manifest.json")).unwrap();
        assert!(after.keys().all(|k| !k.ends_with("data.bin")));
    }

    #[test]
    fn remove_mission_errors_for_unknown_mission() {
        let tmp = tempdir().unwrap();
        let root = tmp.path().join("ds");
        let mut state = create_dataset(&root, "2023-03-02").unwrap();

        let err = remove_mission(&mut state, "ED-00 nonexistent").unwrap_err();
        assert!(err.to_string().contains("Mission not found"));
    }

    // ── check_destination_is_subset ──────────────────────────────

    fn make_committed_dataset(tmp: &tempfile::TempDir, name: &str) -> DatasetState {
        let root = tmp.path().join(name);
        let mut state = create_dataset(&root, "2023-03-02").unwrap();
        add_mission(&mut state, &meta("2023-03-02T10:00:00+00:00", "M1")).unwrap();
        let src = tmp.path().join("data.bin");
        fs::write(&src, b"payload").unwrap();
        stage_mission_files(&mut state, "ED-00 M1", &[src], None).unwrap();
        commit_mission_files(&mut state, "ED-00 M1").unwrap();
        state
    }

    #[test]
    fn subset_check_passes_when_destination_does_not_exist() {
        let tmp = tempdir().unwrap();
        let state = make_committed_dataset(&tmp, "ds");
        let src_manifest =
            manifest::read_manifest(&state.root.join("manifest.json")).unwrap();
        let nonexistent = tmp.path().join("nowhere");
        check_destination_is_subset(&src_manifest, &nonexistent).unwrap();
    }

    #[test]
    fn subset_check_passes_when_destination_has_empty_manifest() {
        let tmp = tempdir().unwrap();
        let state = make_committed_dataset(&tmp, "ds");
        let src_manifest =
            manifest::read_manifest(&state.root.join("manifest.json")).unwrap();
        // Destination exists but has no files
        let dest = tmp.path().join("dest");
        fs::create_dir_all(&dest).unwrap();
        check_destination_is_subset(&src_manifest, &dest).unwrap();
    }

    #[test]
    fn subset_check_passes_when_destination_is_partial_copy() {
        let tmp = tempdir().unwrap();
        let state = make_committed_dataset(&tmp, "ds");
        let src_manifest =
            manifest::read_manifest(&state.root.join("manifest.json")).unwrap();

        // Duplicate to dest then delete some files from the dest manifest
        let dest = tmp.path().join("dest");
        duplicate_dataset(&state, &[dest.clone()]).unwrap();

        // Remove one entry from dest manifest to simulate a partial push
        let dest_manifest_path = dest.join("manifest.json");
        let mut dest_manifest = manifest::read_manifest(&dest_manifest_path).unwrap();
        let first_key = dest_manifest.keys().next().unwrap().clone();
        dest_manifest.remove(&first_key);
        manifest::write_manifest(&dest_manifest_path, &dest_manifest).unwrap();

        check_destination_is_subset(&src_manifest, &dest).unwrap();
    }

    #[test]
    fn subset_check_passes_when_destination_is_full_copy() {
        let tmp = tempdir().unwrap();
        let state = make_committed_dataset(&tmp, "ds");
        let src_manifest =
            manifest::read_manifest(&state.root.join("manifest.json")).unwrap();
        let dest = tmp.path().join("dest");
        duplicate_dataset(&state, &[dest.clone()]).unwrap();
        check_destination_is_subset(&src_manifest, &dest).unwrap();
    }

    #[test]
    fn subset_check_fails_when_destination_has_extra_file() {
        let tmp = tempdir().unwrap();
        let state = make_committed_dataset(&tmp, "ds");
        let src_manifest =
            manifest::read_manifest(&state.root.join("manifest.json")).unwrap();

        // Destination has a file not in source
        let dest = tmp.path().join("dest");
        duplicate_dataset(&state, &[dest.clone()]).unwrap();
        let dest_manifest_path = dest.join("manifest.json");
        let mut dest_manifest = manifest::read_manifest(&dest_manifest_path).unwrap();
        dest_manifest.insert(
            "extra/alien.bin".to_string(),
            manifest::ManifestEntry { sha256sum: "abc".to_string(), size: 3 },
        );
        manifest::write_manifest(&dest_manifest_path, &dest_manifest).unwrap();

        let err = check_destination_is_subset(&src_manifest, &dest).unwrap_err();
        assert!(err.to_string().contains("not in the source dataset"));
    }

    #[test]
    fn subset_check_fails_when_destination_file_has_different_hash() {
        let tmp = tempdir().unwrap();
        let state = make_committed_dataset(&tmp, "ds");
        let src_manifest =
            manifest::read_manifest(&state.root.join("manifest.json")).unwrap();

        let dest = tmp.path().join("dest");
        duplicate_dataset(&state, &[dest.clone()]).unwrap();

        // Corrupt one entry in the dest manifest
        let dest_manifest_path = dest.join("manifest.json");
        let mut dest_manifest = manifest::read_manifest(&dest_manifest_path).unwrap();
        let first_key = dest_manifest.keys().next().unwrap().clone();
        dest_manifest.get_mut(&first_key).unwrap().sha256sum = "deadbeef".to_string();
        manifest::write_manifest(&dest_manifest_path, &dest_manifest).unwrap();

        let err = check_destination_is_subset(&src_manifest, &dest).unwrap_err();
        assert!(err.to_string().contains("different hash"));
    }
}
