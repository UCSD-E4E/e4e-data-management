use std::collections::HashMap;
use std::fs;
use std::io::Read;
use std::path::{Path, PathBuf};

use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};

use crate::errors::Result;
use crate::utils::convert_to_4space_indent;

#[derive(Serialize, Deserialize, Clone, Debug)]
pub struct ManifestEntry {
    pub sha256sum: String,
    pub size: u64,
}

pub type ManifestData = HashMap<String, ManifestEntry>;

/// Read a file in 4096-byte chunks, compute SHA256, return hex string.
pub fn compute_file_hash(path: &Path) -> Result<String> {
    let mut file = fs::File::open(path)?;
    let mut hasher = Sha256::new();
    let mut buf = [0u8; 4096];
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

/// Validate manifest entries.
/// For "hash": verify sha256sum matches; for "size": verify file size matches.
pub fn validate_manifest(
    data: &ManifestData,
    root: &Path,
    files: &[PathBuf],
    method: &str,
) -> Result<bool> {
    for file in files {
        let rel_path = file
            .strip_prefix(root)
            .map_err(|e| crate::errors::E4EError::Runtime(e.to_string()))?;
        let rel_posix = rel_path
            .components()
            .map(|c| c.as_os_str().to_string_lossy().into_owned())
            .collect::<Vec<_>>()
            .join("/");
        let entry = match data.get(&rel_posix) {
            Some(e) => e,
            None => return Ok(false),
        };
        match method {
            "hash" => {
                let computed = compute_file_hash(file)?;
                if computed != entry.sha256sum {
                    return Ok(false);
                }
            }
            "size" => {
                let size = fs::metadata(file)?.len();
                if size != entry.size {
                    return Ok(false);
                }
            }
            _ => {
                return Err(crate::errors::E4EError::Runtime(format!(
                    "Unknown validation method: {}",
                    method
                )));
            }
        }
    }
    Ok(true)
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

    // ── validate_manifest ────────────────────────────────────────

    #[test]
    fn validate_by_hash_passes_for_correct_file() {
        let dir = tempdir().unwrap();
        let file = dir.path().join("data.bin");
        write_file(&file, b"hello");
        let data = compute_hashes(dir.path(), &[file.clone()]).unwrap();
        assert!(validate_manifest(&data, dir.path(), &[file], "hash").unwrap());
    }

    #[test]
    fn validate_by_hash_fails_for_corrupted_file() {
        let dir = tempdir().unwrap();
        let file = dir.path().join("data.bin");
        write_file(&file, b"hello");
        let mut data = compute_hashes(dir.path(), &[file.clone()]).unwrap();
        data.get_mut("data.bin").unwrap().sha256sum = "deadbeef".to_string();
        assert!(!validate_manifest(&data, dir.path(), &[file], "hash").unwrap());
    }

    #[test]
    fn validate_by_hash_fails_for_missing_manifest_entry() {
        let dir = tempdir().unwrap();
        let file = dir.path().join("data.bin");
        write_file(&file, b"hello");
        // Empty manifest — file not listed
        assert!(!validate_manifest(&ManifestData::new(), dir.path(), &[file], "hash").unwrap());
    }

    #[test]
    fn validate_by_size_passes_for_correct_size() {
        let dir = tempdir().unwrap();
        let file = dir.path().join("data.bin");
        write_file(&file, b"hello");
        let data = compute_hashes(dir.path(), &[file.clone()]).unwrap();
        assert!(validate_manifest(&data, dir.path(), &[file], "size").unwrap());
    }

    #[test]
    fn validate_by_size_fails_for_wrong_size() {
        let dir = tempdir().unwrap();
        let file = dir.path().join("data.bin");
        write_file(&file, b"hello"); // 5 bytes
        let mut data = compute_hashes(dir.path(), &[file.clone()]).unwrap();
        data.get_mut("data.bin").unwrap().size = 999;
        assert!(!validate_manifest(&data, dir.path(), &[file], "size").unwrap());
    }

    #[test]
    fn validate_unknown_method_returns_error() {
        let dir = tempdir().unwrap();
        let file = dir.path().join("data.bin");
        write_file(&file, b"hello");
        let data = compute_hashes(dir.path(), &[file.clone()]).unwrap();
        assert!(validate_manifest(&data, dir.path(), &[file], "crc32").is_err());
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
