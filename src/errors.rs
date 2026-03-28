use thiserror::Error;

#[derive(Error, Debug)]
pub enum E4EError {
    #[error("Mission files still in staging area")]
    MissionFilesInStaging,

    #[error("Readme files still in staging area")]
    ReadmeFilesInStaging,

    #[error("{0}")]
    ReadmeNotFound(String),

    #[error("Corrupted dataset")]
    CorruptedDataset,

    #[error("IO error: {0}")]
    Io(#[from] std::io::Error),

    #[error("SQLite error: {0}")]
    Sqlite(#[from] rusqlite::Error),

    #[error("JSON error: {0}")]
    Json(#[from] serde_json::Error),

    #[error("Runtime error: {0}")]
    Runtime(String),
}

pub type Result<T> = std::result::Result<T, E4EError>;
