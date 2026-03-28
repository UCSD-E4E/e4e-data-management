# E4E Data Management

Tool suite for managing field-collected scientific datasets: staging and committing data in the field, duplicating across drives for redundancy, and pushing completed datasets to the E4E NAS.

Available as both a **command-line tool** (`e4edm`) and a **cross-platform desktop GUI**.

---

## Installation

### Command-line tool

Download and install the latest `e4edm` release from the [GitHub releases page](https://github.com/UCSD-E4E/e4e-data-management/releases).

### Desktop GUI

Download the latest `E4EDataManagement` release for your platform (Windows, macOS, Linux) from the [GitHub releases page](https://github.com/UCSD-E4E/e4e-data-management/releases). The GUI reads and writes the same configuration and dataset state as the CLI, so both tools can be used interchangeably.

---

## CLI reference

```
e4edm init dataset  --date DATE --project PROJECT --location LOCATION [--path DIRECTORY]
e4edm init mission  --timestamp TIMESTAMP --device DEVICE --country COUNTRY
                    --region REGION --site SITE --name MISSION [--message NOTES]
e4edm status
e4edm activate DATASET [--day DAY] [--mission MISSION] [--root_dir ROOT_DIR]
e4edm add paths... [--readme] [--start START] [--end END] [--destination DESTINATION]
e4edm commit [--readme]
e4edm duplicate paths...
e4edm validate [root_dir]
e4edm push path
e4edm list dataset
e4edm list mission DATASET
e4edm prune
e4edm ls path
e4edm rm mission MISSION [--dataset DATASET]
e4edm config parameter [value]
e4edm reset
```

---

## Tutorial

### 1 — Create a dataset

```
e4edm init dataset --date 2024-03-15 --project ReefLaser --location Palmyra
```

`--date` accepts an ISO 8601 date (`YYYY-MM-DD`) or the literal `today`.
`--path` overrides the default dataset root directory (configurable via `e4edm config dataset_dir`).

The dataset is created in a folder named `YYYY.MM.DD.PROJECT.LOCATION` and is automatically set as the active dataset.

### 2 — Check status

```
e4edm status
```

Shows the active dataset, active mission, staged files, and committed file counts.

### 3 — Create a mission

```
e4edm init mission --timestamp 2024-03-15T09:00:00-08:00 \
                   --device reef-laser-01 \
                   --country US --region Pacific --site "North Beach" \
                   --name "Morning Survey"
```

The mission is created inside the active dataset and is automatically set as the active mission. If the dataset already has location history, `--country`, `--region`, and `--site` default to the previously used values.

### 4 — Stage files

```
# Single file
e4edm add /path/to/video.mp4

# Multiple files or wildcards
e4edm add /data/raw/*.jpg

# Entire directory
e4edm add /data/raw/

# Time-filtered files
e4edm add --start 2024-03-15T09:00 --end 2024-03-15T10:00 /data/raw/

# Into a subdirectory within the mission
e4edm add --destination video /path/to/video.mp4
```

### 5 — Commit staged files

```
e4edm commit
```

Copies all staged files into the dataset directory and verifies the copy. Run `e4edm status` afterwards to confirm.

### 6 — Add and commit a README

Every dataset requires a README (Markdown or `.docx`) at the dataset level before it can be pushed.

```
e4edm add --readme /path/to/README.md
e4edm commit --readme
```

### 7 — Push to the NAS

```
e4edm push /Volumes/E4E-NAS/deployments
```

Validates all files and completeness criteria, then copies the dataset to the destination. The dataset is marked as pushed and will be removed by `e4edm prune`.

### 8 — Housekeeping

Remove datasets that have been pushed or whose directories no longer exist:

```
e4edm prune
```

Remove a specific mission:

```
e4edm rm mission "Morning Survey"
e4edm rm mission "Morning Survey" --dataset 2024.03.15.ReefLaser.Palmyra
```

---

## Desktop GUI

Launch `E4EDataManagement` to open the GUI. It shares the same configuration directory as the CLI.

**Toolbar buttons:**

| Button | Action |
|---|---|
| **New Dataset** | Opens a form to create a new dataset (date, project, location, directory) |
| **New Mission** | Opens a form to create a mission in the active dataset (enabled when a dataset is active) |
| **Add Files** | Opens a file picker to stage files into the active mission (enabled when a mission is active) |
| **Refresh** | Reloads dataset and mission state from disk |
| **Validate** | Runs validation on the active dataset and displays any failures |
| **Prune** | Removes pushed and missing datasets |
| **Push** | Pushes the active dataset to the specified destination path |

The left panel lists all known datasets. A bold name indicates the active dataset; ✓ means it has been pushed. Clicking a dataset shows its missions and file counts in the detail pane.

---

## Development

**Prerequisites:** [uv](https://docs.astral.sh/uv/getting-started/installation/), [Rust](https://rustup.rs/), [.NET 10 SDK](https://dotnet.microsoft.com/download)

```bash
# Python / CLI
uv sync --dev
uv run maturin develop        # compiles the Rust extension for Python
uv run pytest                 # Python tests
uv run pylint e4e_data_management

# Desktop GUI
dotnet build E4EDataManagement.UI
dotnet test E4EDataManagement.Tests

# Rust (standalone, no Python)
cargo test --lib --no-default-features
cargo clippy --no-default-features
```

The Rust crate is built in two modes:

- **With `python` feature** (default) — compiled by `maturin` as a Python extension module, providing the `_core` C API used by the Python CLI.
- **Without `python` feature** (`--no-default-features`) — compiled as a plain `cdylib` for P/Invoke by the .NET desktop UI, with no Python ABI symbols.

---

## Developer notes

### Dataset directory structure

```
YYYY.MM.DD.PROJECT.LOCATION/
    ED-00/
        Mission 1/
            [data files]
            manifest.json
            metadata.json
        Mission 2/
            [data files]
            manifest.json
            metadata.json
    ED-01/
        Mission 3/
            ...
    ...
    .e4edm.db
    manifest.json
    readme.md  (or readme.docx)
```

`.e4edm.db` is the SQLite database used by the E4E Data Management tool to track staged and committed files, mission records, and dataset state. It is not part of the dataset and should not be removed, but it also should not be submitted or archived.

### `manifest.json`

Each mission and the dataset root contains a `manifest.json` with SHA-256 hashes of all committed files, used to verify data integrity during push.

### `metadata.json`

Each mission contains a `metadata.json` with the mission metadata: timestamp, device, country, region, site, mission name, and notes.

### Configuration

Tool configuration (active dataset, dataset directory, schema version) is stored in a SQLite database (`config.db`) at:

| Platform | Path |
|---|---|
| Linux / macOS | `$XDG_CONFIG_HOME/E4EDataManagement/` (defaults to `~/.config/E4EDataManagement/`) |
| Windows | `%LOCALAPPDATA%\Engineers for Exploration\E4EDataManagement\` |
