use std::collections::HashMap;
use std::fs;
use std::io::{Read, Write};
use std::path::{Path, PathBuf};
use std::sync::atomic::{AtomicU64, Ordering};

use rayon::prelude::*;
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};

use crate::errors::{E4EError, Result};
use crate::utils::convert_to_4space_indent;

const TMP_SUFFIX: &str = ".e4edm_tmp";

#[derive(Serialize, Deserialize, Clone, Debug)]
pub struct ManifestEntry {
    pub sha256sum: String,
    pub size: u64,
}

pub type ManifestData = HashMap<String, ManifestEntry>;

/// Copy `src` to a temp file beside `dst`, verify the hash, then rename into place.
/// If the hash does not match or the write fails, the temp file is removed.
pub fn copy_and_verify(src: &Path, dst: &Path, expected_hash: &str) -> Result<()> {
    let tmp_name = format!(
        "{}{}",
        dst.file_name().unwrap_or_default().to_string_lossy(),
        TMP_SUFFIX
    );
    let tmp = dst.with_file_name(tmp_name);

    let result = (|| -> Result<()> {
        let mut src_file = fs::File::open(src).map_err(|e| {
            E4EError::Runtime(format!("Cannot open '{}': {}", src.display(), e))
        })?;
        let mut tmp_file = fs::File::create(&tmp).map_err(|e| {
            E4EError::Runtime(format!("Cannot create '{}': {}", tmp.display(), e))
        })?;
        let mut hasher = Sha256::new();
        let mut buf = [0u8; 65536];
        loop {
            let n = src_file.read(&mut buf).map_err(|e| {
                E4EError::Runtime(format!("Cannot read '{}': {}", src.display(), e))
            })?;
            if n == 0 {
                break;
            }
            hasher.update(&buf[..n]);
            tmp_file.write_all(&buf[..n]).map_err(|e| {
                E4EError::Runtime(format!("Cannot write '{}': {}", tmp.display(), e))
            })?;
        }
        let computed = hex::encode(hasher.finalize());
        if computed != expected_hash {
            return Err(E4EError::Runtime(format!(
                "Hash mismatch copying '{}': expected {}, got {}",
                src.display(),
                expected_hash,
                computed
            )));
        }
        fs::rename(&tmp, dst).map_err(|e| {
            E4EError::Runtime(format!(
                "Cannot rename '{}' to '{}': {}",
                tmp.display(),
                dst.display(),
                e
            ))
        })?;
        Ok(())
    })();

    if result.is_err() {
        let _ = fs::remove_file(&tmp);
    }
    result
}

/// Remove any leftover `.e4edm_tmp` files under `dir` from a previous interrupted push.
pub fn cleanup_temp_files(dir: &Path) -> Result<()> {
    if !dir.exists() {
        return Ok(());
    }
    for entry in walkdir::WalkDir::new(dir) {
        let entry = entry.map_err(|e| E4EError::Runtime(e.to_string()))?;
        let path = entry.path();
        if path.is_file()
            && path
                .file_name()
                .map(|n| n.to_string_lossy().ends_with(TMP_SUFFIX))
                .unwrap_or(false)
        {
            fs::remove_file(path)?;
        }
    }
    Ok(())
}

/// Returns true if `path` is a temp file created by `copy_and_verify`.
pub fn is_temp_file(path: &Path) -> bool {
    path.file_name()
        .map(|n| n.to_string_lossy().ends_with(TMP_SUFFIX))
        .unwrap_or(false)
}

/// Read a file in 4096-byte chunks, compute SHA256, return hex string.
pub fn compute_file_hash(path: &Path) -> Result<String> {
    let mut file = fs::File::open(path)?;
    let mut hasher = Sha256::new();
    let mut buf = [0u8; 65536];
    loop {
        let n = file.read(&mut buf)?;
        if n == 0 {
            break;
        }
        hasher.update(&buf[..n]);
    }
    Ok(hex::encode(hasher.finalize()))
}

/// For each file, compute relative posix path, hash, and size.
pub fn compute_hashes(root: &Path, files: &[PathBuf]) -> Result<ManifestData> {
    let mut data = ManifestData::new();
    for file in files {
        let rel_path = file
            .strip_prefix(root)
            .map_err(|e| crate::errors::E4EError::Runtime(e.to_string()))?;
        // Convert to posix-style path (forward slashes)
        let rel_posix = rel_path
            .components()
            .map(|c| c.as_os_str().to_string_lossy().into_owned())
            .collect::<Vec<_>>()
            .join("/");
        let cksum = compute_file_hash(file)?;
        let size = fs::metadata(file)?.len();
        data.insert(rel_posix, ManifestEntry { sha256sum: cksum, size });
    }
    Ok(data)
}

/// Read JSON manifest file.
pub fn read_manifest(path: &Path) -> Result<ManifestData> {
    if !path.exists() {
        return Ok(ManifestData::new());
    }
    let content = fs::read_to_string(path)?;
    let data: ManifestData = serde_json::from_str(&content)?;
    Ok(data)
}

/// Write JSON manifest with 4-space indent.
pub fn write_manifest(path: &Path, data: &ManifestData) -> Result<()> {
    let content = serde_json::to_string_pretty(data)?;
    // serde_json::to_string_pretty uses 2-space indent; we need 4-space to match Python
    // Re-serialize with manual 4-space indent
    let content4 = convert_to_4space_indent(&content);
    fs::write(path, content4)?;
    Ok(())
}

/// Read existing manifest, add new entries, write back.
pub fn update_manifest(path: &Path, root: &Path, files: &[PathBuf]) -> Result<()> {
    let mut data = read_manifest(path)?;
    let new_entries = compute_hashes(root, files)?;
    data.extend(new_entries);
    write_manifest(path, &data)?;
    Ok(())
}

/// Update manifest using pre-computed hashes, only stat()ing files for size.
/// Avoids re-reading file contents when the hash is already known.
pub fn update_manifest_with_known_hashes(
    path: &Path,
    root: &Path,
    files: &[(PathBuf, String)], // (abs_path, sha256_hex)
) -> Result<()> {
    let mut data = read_manifest(path)?;
    for (file, hash) in files {
        let rel_path = file
            .strip_prefix(root)
            .map_err(|e| crate::errors::E4EError::Runtime(e.to_string()))?;
        let rel_posix = rel_path
            .components()
            .map(|c| c.as_os_str().to_string_lossy().into_owned())
            .collect::<Vec<_>>()
            .join("/");
        let size = fs::metadata(file)?.len();
        data.insert(rel_posix, ManifestEntry { sha256sum: hash.clone(), size });
    }
    write_manifest(path, &data)?;
    Ok(())
}

/// Collect validation failures for manifest entries, calling `progress(current, total)`
/// after each file is processed.
///
/// Returns a list of human-readable failure messages.  An empty list means
/// the dataset is valid.  Also checks for manifest entries whose files are
/// missing from disk.
///
/// For "hash": verify sha256sum matches; for "size": verify file size matches.
/// Hash checks are performed in parallel across all files.
pub fn collect_validation_failures_with_progress<F>(
    data: &ManifestData,
    root: &Path,
    files: &[PathBuf],
    method: &str,
    progress: F,
) -> Result<Vec<String>>
where
    F: Fn(u64, u64) + Send + Sync,
{
    if method != "hash" && method != "size" {
        return Err(crate::errors::E4EError::Runtime(format!(
            "Unknown validation method: {}",
            method
        )));
    }

    let total = files.len() as u64;
    let counter = AtomicU64::new(0);

    // Process each on-disk file in parallel.  Each thread returns:
    //   Ok((rel_posix, Option<failure_message>))
    // or Err(...) on an I/O or strip_prefix error.
    let results: Result<Vec<(String, Option<String>)>> = files
        .par_iter()
        .map(|file| {
            let rel_path = file
                .strip_prefix(root)
                .map_err(|e| crate::errors::E4EError::Runtime(e.to_string()))?;
            let rel_posix = rel_path
                .components()
                .map(|c| c.as_os_str().to_string_lossy().into_owned())
                .collect::<Vec<_>>()
                .join("/");

            let failure = match data.get(&rel_posix) {
                None => Some(format!("unlisted file: {}", rel_posix)),
                Some(entry) => match method {
                    "hash" => {
                        let computed = compute_file_hash(file)?;
                        if computed != entry.sha256sum {
                            Some(format!(
                                "hash mismatch: {} (expected {}, got {})",
                                rel_posix, entry.sha256sum, computed
                            ))
                        } else {
                            None
                        }
                    }
                    "size" => {
                        let size = fs::metadata(file)?.len();
                        if size != entry.size {
                            Some(format!(
                                "size mismatch: {} (expected {} bytes, got {} bytes)",
                                rel_posix, entry.size, size
                            ))
                        } else {
                            None
                        }
                    }
                    _ => unreachable!(),
                },
            };

            let current = counter.fetch_add(1, Ordering::Relaxed) + 1;
            progress(current, total);

            Ok((rel_posix, failure))
        })
        .collect();

    let pairs = results?;

    let on_disk: std::collections::HashSet<&str> =
        pairs.iter().map(|(rel, _)| rel.as_str()).collect();

    let mut failures: Vec<String> = pairs.iter().filter_map(|(_, f)| f.clone()).collect();

    // Check for manifest entries whose files are absent from disk.
    for key in data.keys() {
        if !on_disk.contains(key.as_str()) {
            failures.push(format!("missing file: {}", key));
        }
    }

    Ok(failures)
}

/// Collect validation failures without progress reporting.
#[cfg_attr(not(feature = "python"), allow(dead_code))]
#[cfg_attr(not(test), allow(dead_code))]
pub fn collect_validation_failures(
    data: &ManifestData,
    root: &Path,
    files: &[PathBuf],
    method: &str,
) -> Result<Vec<String>> {
    collect_validation_failures_with_progress(data, root, files, method, |_, _| {})
}


#[cfg(test)]
mod tests {
    use super::*;
    use std::fs;
    use tempfile::tempdir;

    fn write_file(path: &Path, content: &[u8]) {
        fs::write(path, content).unwrap();
    }

    // ── compute_file_hash ────────────────────────────────────────

    #[test]
    fn hash_of_empty_file_is_known_sha256() {
        let dir = tempdir().unwrap();
        let file = dir.path().join("empty.bin");
        write_file(&file, b"");
        let hash = compute_file_hash(&file).unwrap();
        assert_eq!(
            hash,
            "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
        );
    }

    #[test]
    fn hash_is_64_hex_chars_and_deterministic() {
        let dir = tempdir().unwrap();
        let file = dir.path().join("data.bin");
        write_file(&file, b"hello world");
        let h1 = compute_file_hash(&file).unwrap();
        let h2 = compute_file_hash(&file).unwrap();
        assert_eq!(h1.len(), 64);
        assert_eq!(h1, h2);
    }

    #[test]
    fn different_contents_produce_different_hashes() {
        let dir = tempdir().unwrap();
        let f1 = dir.path().join("a.bin");
        let f2 = dir.path().join("b.bin");
        write_file(&f1, b"aaa");
        write_file(&f2, b"bbb");
        assert_ne!(
            compute_file_hash(&f1).unwrap(),
            compute_file_hash(&f2).unwrap()
        );
    }

    // ── compute_hashes ───────────────────────────────────────────

    #[test]
    fn compute_hashes_single_file_correct_key_and_size() {
        let dir = tempdir().unwrap();
        let file = dir.path().join("test.bin");
        write_file(&file, b"content");
        let result = compute_hashes(dir.path(), &[file.clone()]).unwrap();
        let entry = result.get("test.bin").expect("key missing");
        assert_eq!(entry.size, 7);
        assert_eq!(entry.sha256sum, compute_file_hash(&file).unwrap());
    }

    #[test]
    fn compute_hashes_subdirectory_uses_posix_path() {
        let dir = tempdir().unwrap();
        let sub = dir.path().join("sub");
        fs::create_dir(&sub).unwrap();
        let file = sub.join("data.bin");
        write_file(&file, b"x");
        let result = compute_hashes(dir.path(), &[file]).unwrap();
        assert!(result.contains_key("sub/data.bin"), "expected posix-style key");
    }

    #[test]
    fn compute_hashes_multiple_files() {
        let dir = tempdir().unwrap();
        let f1 = dir.path().join("a.bin");
        let f2 = dir.path().join("b.bin");
        write_file(&f1, b"aaa");
        write_file(&f2, b"bbb");
        let result = compute_hashes(dir.path(), &[f1, f2]).unwrap();
        assert_eq!(result.len(), 2);
        assert!(result.contains_key("a.bin"));
        assert!(result.contains_key("b.bin"));
    }

    // ── read_manifest / write_manifest ───────────────────────────

    #[test]
    fn write_read_manifest_roundtrip() {
        let dir = tempdir().unwrap();
        let path = dir.path().join("manifest.json");
        let mut data = ManifestData::new();
        data.insert(
            "file.bin".to_string(),
            ManifestEntry { sha256sum: "abc123".to_string(), size: 42 },
        );
        write_manifest(&path, &data).unwrap();
        let back = read_manifest(&path).unwrap();
        assert_eq!(back["file.bin"].sha256sum, "abc123");
        assert_eq!(back["file.bin"].size, 42);
    }

    #[test]
    fn read_manifest_returns_empty_when_file_absent() {
        let dir = tempdir().unwrap();
        let data = read_manifest(&dir.path().join("manifest.json")).unwrap();
        assert!(data.is_empty());
    }

    #[test]
    fn write_manifest_uses_4_space_indent() {
        let dir = tempdir().unwrap();
        let path = dir.path().join("manifest.json");
        let mut data = ManifestData::new();
        data.insert(
            "f.bin".to_string(),
            ManifestEntry { sha256sum: "abc".to_string(), size: 1 },
        );
        write_manifest(&path, &data).unwrap();
        for line in fs::read_to_string(&path).unwrap().lines() {
            let leading = line.len() - line.trim_start_matches(' ').len();
            assert_eq!(leading % 4, 0, "non-4-multiple indent on line: {line:?}");
        }
    }

    // ── update_manifest ─────────────────────────────────────────

    #[test]
    fn update_manifest_preserves_existing_and_adds_new() {
        let dir = tempdir().unwrap();
        let path = dir.path().join("manifest.json");
        let mut initial = ManifestData::new();
        initial.insert(
            "old.bin".to_string(),
            ManifestEntry { sha256sum: "old".to_string(), size: 1 },
        );
        write_manifest(&path, &initial).unwrap();

        let new_file = dir.path().join("new.bin");
        write_file(&new_file, b"new");
        update_manifest(&path, dir.path(), &[new_file]).unwrap();

        let result = read_manifest(&path).unwrap();
        assert!(result.contains_key("old.bin"), "old entry should be preserved");
        assert!(result.contains_key("new.bin"), "new entry should be added");
    }

    // ── is_temp_file ─────────────────────────────────────────────

    #[test]
    fn is_temp_file_returns_true_for_tmp_suffix() {
        let path = std::path::Path::new("/some/dir/file.bin.e4edm_tmp");
        assert!(is_temp_file(path));
    }

    #[test]
    fn is_temp_file_returns_false_for_normal_file() {
        assert!(!is_temp_file(std::path::Path::new("/some/dir/file.bin")));
    }

    #[test]
    fn is_temp_file_returns_false_for_root() {
        assert!(!is_temp_file(std::path::Path::new("/")));
    }

    // ── cleanup_temp_files ────────────────────────────────────────

    #[test]
    fn cleanup_temp_files_removes_tmp_files() {
        let dir = tempdir().unwrap();
        let tmp_file = dir.path().join("data.bin.e4edm_tmp");
        let keep_file = dir.path().join("data.bin");
        write_file(&tmp_file, b"junk");
        write_file(&keep_file, b"keep");
        cleanup_temp_files(dir.path()).unwrap();
        assert!(!tmp_file.exists(), "temp file should be removed");
        assert!(keep_file.exists(), "normal file should be kept");
    }

    #[test]
    fn cleanup_temp_files_on_nonexistent_dir_is_ok() {
        let dir = tempdir().unwrap();
        let missing = dir.path().join("does_not_exist");
        cleanup_temp_files(&missing).unwrap();
    }

    #[test]
    fn cleanup_temp_files_removes_nested_tmp_files() {
        let dir = tempdir().unwrap();
        let sub = dir.path().join("sub");
        fs::create_dir(&sub).unwrap();
        let tmp_file = sub.join("nested.bin.e4edm_tmp");
        write_file(&tmp_file, b"junk");
        cleanup_temp_files(dir.path()).unwrap();
        assert!(!tmp_file.exists());
    }

    // ── copy_and_verify ───────────────────────────────────────────

    #[test]
    fn copy_and_verify_succeeds_with_correct_hash() {
        let dir = tempdir().unwrap();
        let src = dir.path().join("src.bin");
        let dst = dir.path().join("dst.bin");
        let content = b"hello world";
        write_file(&src, content);
        let expected = compute_file_hash(&src).unwrap();
        copy_and_verify(&src, &dst, &expected).unwrap();
        assert!(dst.exists());
        assert_eq!(fs::read(&dst).unwrap(), content);
    }

    #[test]
    fn copy_and_verify_fails_and_cleans_up_on_hash_mismatch() {
        let dir = tempdir().unwrap();
        let src = dir.path().join("src.bin");
        let dst = dir.path().join("dst.bin");
        write_file(&src, b"real content");
        let result = copy_and_verify(&src, &dst, "0000000000000000000000000000000000000000000000000000000000000000");
        assert!(result.is_err());
        assert!(!dst.exists(), "dst should not exist after mismatch");
        // temp file should also be cleaned up
        let tmp = dst.with_file_name("dst.bin.e4edm_tmp");
        assert!(!tmp.exists(), "temp file should be cleaned up");
    }

    // ── collect_validation_failures ──────────────────────────────

    #[test]
    fn validate_by_hash_passes_for_correct_file() {
        let dir = tempdir().unwrap();
        let file = dir.path().join("data.bin");
        write_file(&file, b"hello");
        let data = compute_hashes(dir.path(), &[file.clone()]).unwrap();
        assert!(collect_validation_failures(&data, dir.path(), &[file], "hash").unwrap().is_empty());
    }

    #[test]
    fn validate_by_hash_fails_for_corrupted_file() {
        let dir = tempdir().unwrap();
        let file = dir.path().join("data.bin");
        write_file(&file, b"hello");
        let mut data = compute_hashes(dir.path(), &[file.clone()]).unwrap();
        data.get_mut("data.bin").unwrap().sha256sum = "deadbeef".to_string();
        assert!(!collect_validation_failures(&data, dir.path(), &[file], "hash").unwrap().is_empty());
    }

    #[test]
    fn validate_by_hash_fails_for_missing_manifest_entry() {
        let dir = tempdir().unwrap();
        let file = dir.path().join("data.bin");
        write_file(&file, b"hello");
        // Empty manifest — file not listed
        assert!(!collect_validation_failures(&ManifestData::new(), dir.path(), &[file], "hash").unwrap().is_empty());
    }

    #[test]
    fn validate_by_size_passes_for_correct_size() {
        let dir = tempdir().unwrap();
        let file = dir.path().join("data.bin");
        write_file(&file, b"hello");
        let data = compute_hashes(dir.path(), &[file.clone()]).unwrap();
        assert!(collect_validation_failures(&data, dir.path(), &[file], "size").unwrap().is_empty());
    }

    #[test]
    fn validate_by_size_fails_for_wrong_size() {
        let dir = tempdir().unwrap();
        let file = dir.path().join("data.bin");
        write_file(&file, b"hello"); // 5 bytes
        let mut data = compute_hashes(dir.path(), &[file.clone()]).unwrap();
        data.get_mut("data.bin").unwrap().size = 999;
        assert!(!collect_validation_failures(&data, dir.path(), &[file], "size").unwrap().is_empty());
    }

    #[test]
    fn validate_unknown_method_returns_error() {
        let dir = tempdir().unwrap();
        let file = dir.path().join("data.bin");
        write_file(&file, b"hello");
        let data = compute_hashes(dir.path(), &[file.clone()]).unwrap();
        assert!(collect_validation_failures(&data, dir.path(), &[file], "crc32").is_err());
    }

    // ── convert_to_4space_indent (shared utility, tested here) ──

    #[test]
    fn indent_conversion_doubles_leading_spaces() {
        let input = "{\n  \"key\": \"value\"\n}";
        let output = convert_to_4space_indent(input);
        assert!(output.contains("    \"key\""), "expected 4-space indent");
    }

    #[test]
    fn indent_conversion_zero_indent_unchanged() {
        // No trailing newline in input → no trailing newline in output
        assert_eq!(convert_to_4space_indent("{}"), "{}");
        // Trailing newline is preserved
        assert_eq!(convert_to_4space_indent("{}\n"), "{}\n");
    }
}
