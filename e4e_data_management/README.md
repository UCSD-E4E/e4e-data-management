# e4edm — E4E Data Management CLI

Command-line tool for managing field data collections: staging files into missions, committing and verifying copies, pushing to final destinations, and validating dataset integrity.

**Version:** 0.3.1 | **Python:** ≥ 3.11

---

## Installation

### From a release

Download the latest wheel from the [releases page](https://github.com/UCSD-E4E/e4e-data-management/releases) and install with pip:

```
pip install e4e_data_management-<version>-*.whl
```

### From source

Requires [uv](https://docs.astral.sh/uv/getting-started/installation/) and a [Rust toolchain](https://rustup.rs/).

```
uv sync --dev
uv run maturin develop
```

After that, `e4edm` is available inside the virtual environment:

```
uv run e4edm --help
```

---

## Concepts

| Term | Meaning |
|------|---------|
| **Dataset** | Top-level collection for one deployment. Folder name: `YYYY.MM.DD.PROJECT.LOCATION` |
| **Day** | A sub-folder `ED-NN` grouping missions that happened on the same day relative to the dataset start date |
| **Mission** | A single recording session within a day. Contains data files + `metadata.json` + `manifest.json` |
| **Staging** | Copying a file path into the tool's pending queue (no files moved yet) |
| **Commit** | Actually copying staged files into the dataset directory and verifying SHA-256 hashes |
| **Push** | Duplicating the entire committed dataset to a final destination (NAS, external drive, etc.) |

State is persisted in a SQLite database (`.e4edm.db`) inside each dataset directory, and a manager config database (`config.db`) under the user config directory:

- **Linux/macOS:** `~/.config/Engineers for Exploration/E4EDataManagement/`
- **Windows:** `%APPDATA%\Engineers for Exploration\E4EDataManagement\`

---

## Commands

### Dataset lifecycle

```
e4edm init dataset --date DATE --project PROJECT --location LOCATION [--path DIRECTORY]
```
Create a new dataset. `DATE` is `YYYY-MM-DD` or `today`. The dataset folder is created at `DIRECTORY/YYYY.MM.DD.PROJECT.LOCATION` and immediately activated.

```
e4edm init mission --timestamp TIMESTAMP --device DEVICE \
    --country COUNTRY --region REGION --site SITE --name MISSION [--message NOTES]
```
Create a new mission inside the active dataset. `TIMESTAMP` is ISO 8601 (e.g. `2024-03-15T10:30:00-08:00`). The mission is immediately activated.

```
e4edm activate DATASET [--day DAY] [--mission MISSION] [--root_dir ROOT_DIR]
```
Activate a dataset (and optionally a specific mission within it). Use `--root_dir` if the dataset is not in the configured dataset directory.

```
e4edm status
```
Show the active dataset and mission, along with any staged files.

### Staging and committing files

```
e4edm add PATHS... [--readme] [--start START] [--end END] [--destination SUBDIR]
```
Stage one or more files or directories into the active mission. Glob patterns are expanded.

- `--readme` — stage as a dataset-level readme file (must be `.md` or `.docx`)
- `--start` / `--end` — only include files with a last-modified time in the given ISO 8601 range
- `--destination SUBDIR` — place files in a sub-directory within the mission folder

```
e4edm commit [--readme]
```
Copy all staged files into the dataset, verify SHA-256 hashes, and clear the staging area.
Use `--readme` to commit dataset-level (readme) staged files instead.

```
e4edm reset
```
Clear the staging area for the active mission without committing.

### Validation and pushing

```
e4edm validate [ROOT_DIR]
```
Validate the active dataset (or any dataset at `ROOT_DIR`) by checking all files against `manifest.json`. Prints each failure with a reason:

- `unlisted file: <path>` — file exists on disk but is not in the manifest
- `hash mismatch: <path>` — SHA-256 does not match the recorded value
- `missing file: <path>` — manifest entry has no corresponding file on disk

```
e4edm push PATH
```
Push the active dataset to `PATH/<dataset-name>`. Before copying, verifies that any existing files at the destination are a compatible subset of the source (allows recovery from interrupted pushes). After copying, validates the destination. Skips re-copying files that already match their expected hash.

```
e4edm duplicate PATHS...
```
Duplicate the active dataset to one or more destinations simultaneously.

### Dataset management

```
e4edm list dataset
```
List all known datasets. A `*` suffix indicates the dataset has been pushed.

```
e4edm list mission DATASET
```
List all missions in the named dataset.

```
e4edm rm mission MISSION [--dataset DATASET]
```
Remove a mission from a dataset, deleting its directory from disk. Defaults to the active dataset if `--dataset` is omitted.

```
e4edm prune
```
Remove datasets that have been pushed or whose directories no longer exist from the manager's tracking list, and delete their local directories.

### Utilities

```
e4edm config PARAMETER [value]
```
Read or set a configuration parameter. Available parameters:

| Parameter | Description |
|-----------|-------------|
| `dataset_dir` | Default directory for new datasets |
| `version` | Schema version (read-only) |

```
e4edm ls PATH
```
List the contents of a directory with last-modified timestamps.

---

## Typical workflow

```bash
# 1. Create a dataset for a deployment
e4edm init dataset --date 2024-03-15 --project ReefLaser --location PalmyraAtoll

# 2. Create a mission for the first recording session
e4edm init mission \
    --timestamp 2024-03-15T09:00:00-10:00 \
    --device "reef-laser-01" \
    --country US --region "Pacific" --site "North Beach" \
    --name "morning-survey"

# 3. Stage files
e4edm add /data/raw/2024-03-15/*.bag

# 4. Commit (copies + verifies)
e4edm commit

# 5. Add and commit a readme
e4edm add --readme /data/raw/README.md
e4edm commit --readme

# 6. Validate before push
e4edm validate

# 7. Push to NAS
e4edm push /mnt/nas/deployments
```

---

## Development

```bash
# Install dependencies and build the Rust extension in development mode
uv sync --dev
uv run maturin develop

# Run tests
uv run pytest

# Lint
uv run pylint e4e_data_management
```

The Rust core lives in `../src/`. Changes there require re-running `maturin develop`. Tests are in `../tests/`.
