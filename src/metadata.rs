use std::collections::HashMap;
use std::fs;
use std::path::Path;

use serde::{Deserialize, Serialize};
use serde_json::Value;

use crate::errors::Result;
use crate::utils::convert_to_4space_indent;

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct MetadataRecord {
    /// ISO 8601 string (with timezone, e.g. "2023-03-02T19:38:00-08:00")
    pub timestamp: String,
    pub device: String,
    pub country: String,
    pub region: String,
    pub site: String,
    /// The "mission" field in metadata.json
    pub mission_name: String,
    /// JSON string of arbitrary properties dict
    pub properties: String,
    pub notes: String,
}

/// Internal struct matching the metadata.json on-disk format exactly.
#[derive(Serialize, Deserialize)]
struct MetadataJson {
    timestamp: String,
    device: String,
    notes: String,
    properties: HashMap<String, Value>,
    country: String,
    region: String,
    site: String,
    mission: String,
}

/// Write metadata.json to dir/metadata.json with 4-space indent.
pub fn write_metadata(dir: &Path, meta: &MetadataRecord) -> Result<()> {
    let properties: HashMap<String, Value> = serde_json::from_str(&meta.properties)?;
    let json_obj = MetadataJson {
        timestamp: meta.timestamp.clone(),
        device: meta.device.clone(),
        notes: meta.notes.clone(),
        properties,
        country: meta.country.clone(),
        region: meta.region.clone(),
        site: meta.site.clone(),
        mission: meta.mission_name.clone(),
    };
    let content = serde_json::to_string_pretty(&json_obj)?;
    let content4 = convert_to_4space_indent(&content);
    fs::write(dir.join("metadata.json"), content4)?;
    Ok(())
}

/// Read and validate dir/metadata.json.
pub fn read_metadata(dir: &Path) -> Result<MetadataRecord> {
    let content = fs::read_to_string(dir.join("metadata.json"))?;
    let json_obj: MetadataJson = serde_json::from_str(&content)?;
    let properties = serde_json::to_string(&json_obj.properties)?;
    Ok(MetadataRecord {
        timestamp: json_obj.timestamp,
        device: json_obj.device,
        country: json_obj.country,
        region: json_obj.region,
        site: json_obj.site,
        mission_name: json_obj.mission,
        properties,
        notes: json_obj.notes,
    })
}

#[cfg(test)]
mod tests {
    use super::*;
    use tempfile::tempdir;

    fn sample_record() -> MetadataRecord {
        MetadataRecord {
            timestamp: "2023-03-02T19:38:00-08:00".to_string(),
            device: "Device1".to_string(),
            country: "USA".to_string(),
            region: "California".to_string(),
            site: "SD".to_string(),
            mission_name: "TPF001".to_string(),
            properties: "{}".to_string(),
            notes: "test notes".to_string(),
        }
    }

    #[test]
    fn write_read_roundtrip_preserves_all_fields() {
        let dir = tempdir().unwrap();
        let meta = sample_record();
        write_metadata(dir.path(), &meta).unwrap();
        let loaded = read_metadata(dir.path()).unwrap();
        assert_eq!(loaded.timestamp, meta.timestamp);
        assert_eq!(loaded.device, meta.device);
        assert_eq!(loaded.country, meta.country);
        assert_eq!(loaded.region, meta.region);
        assert_eq!(loaded.site, meta.site);
        assert_eq!(loaded.mission_name, meta.mission_name);
        assert_eq!(loaded.notes, meta.notes);
    }

    #[test]
    fn on_disk_field_is_mission_not_mission_name() {
        let dir = tempdir().unwrap();
        write_metadata(dir.path(), &sample_record()).unwrap();
        let content = std::fs::read_to_string(dir.path().join("metadata.json")).unwrap();
        assert!(content.contains("\"mission\""), "expected 'mission' key on disk");
        assert!(!content.contains("\"mission_name\""), "unexpected 'mission_name' key");
    }

    #[test]
    fn metadata_json_uses_4_space_indent() {
        let dir = tempdir().unwrap();
        write_metadata(dir.path(), &sample_record()).unwrap();
        let content = std::fs::read_to_string(dir.path().join("metadata.json")).unwrap();
        for line in content.lines() {
            let leading = line.len() - line.trim_start_matches(' ').len();
            assert_eq!(leading % 4, 0, "non-4-multiple indent on line: {line:?}");
        }
    }

    #[test]
    fn properties_roundtrip_with_values() {
        let dir = tempdir().unwrap();
        let mut meta = sample_record();
        meta.properties = r#"{"key": "value", "count": 42}"#.to_string();
        write_metadata(dir.path(), &meta).unwrap();
        let loaded = read_metadata(dir.path()).unwrap();
        let props: std::collections::HashMap<String, serde_json::Value> =
            serde_json::from_str(&loaded.properties).unwrap();
        assert_eq!(props["key"], serde_json::Value::String("value".to_string()));
        assert_eq!(props["count"], serde_json::json!(42));
    }

    #[test]
    fn read_metadata_errors_when_file_missing() {
        let dir = tempdir().unwrap();
        assert!(read_metadata(dir.path()).is_err());
    }
}
