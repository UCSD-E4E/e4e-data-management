# E4E Data Management
Welcome to the E4E Data Management Tool Suite.

This suite should be used to manage data in the field, duplicate data across multiple drives for redundancy, compiling and staging all data after a deployment to the E4E NAS, and final archiving and management of deployment data on the NAS.

The following commands are available:
- `e4edm init dataset --date DATE --project PROJECT --location LOCATION [--path DIRECTORY]`
- `e4edm init mission --timestamp TIMESTAMP --device DEVICE --country COUNTRY --region REGION --site SITE --name MISSION [--message NOTES]`
- `e4edm config parameter [value]`
- `e4edm status`
- `e4edm activate DATASET [--day DAY] [--mission MISSION] [--root_dir ROOT_DIR]`
- `e4edm add paths [--readme] [--start START] [--end END] [--destination DESTINATION]`
- `e4edm commit [--readme]`
- `e4edm duplicate paths`
- `e4edm validate [root_dir]`
- `e4edm push path`
- `e4edm list dataset`
- `e4edm list mission DATASET`
- `e4edm prune`
- `e4edm ls path`
- `e4edm rm mission MISSION [--dataset DATASET]`
- `e4edm reset`

## Tutorial
1. Download and install the latest `e4edm` from https://github.com/UCSD-E4E/e4e-data-management/releases
2. To start a dataset, run `e4edm init dataset [-h] --date DATE --project PROJECT --location LOCATION [--path DIRECTORY]`.  `DATE` should be the first day of the dataset in YYYY-MM-DD format.  You can also use `today` to use today's date.  `PROJECT` should be the canonical name of the project.  Ideally, this should not be abbreviated, and should give immediate context to what the dataset is for.  `LOCATION` should be the common name of the minimally encompassing area of the dataset.  Ideally, this should give immediate context to where this dataset was collected.  The default location for datasets is the user's data directory.  This can be configured using `e4edm config`.  You can also override this at dataset creation using the `DIRECTORY` parameter.  This creates a dataset in a folder named `{YYYY}.{MM}.{PROJECT}.{LOCATION}`
3. Once a dataset is created, it is automatically activated and remains active until another dataset is activated or created.  This can be checked using `e4edm status`, and changed using `e4edm activate`.
4. Once the appropriate dataset is activated, you can create a new mission using `e4edm init mission [-h] --timestamp TIMESTAMP --device DEVICE --country COUNTRY --region REGION --site SITE --name MISSION [--message NOTES]`.  `TIMESTAMP` is the ISO 8601 timestamp representing when the mission was captured.  `DEVICE` should be a string describing the device(s) used to capture this data.  `COUNTRY` should be the country of origin.  This creates a mission in a folder at `${DATASET}\${DAY}\{MISSION}`
5. Once a mission is created, it is automatically activated and remains active until another mission or dataset is activated or created.  This can be checked using `e4edm status` and changed using `e4edm activate`.
6. Once the appropriate mission is activated, you can stage files to the mission using `e4edm add [-h] [--start START] [--end END] paths [paths ...]`.  You can stage a single file by name, multiple files by name, multiple files by wildcard, directories by name, and a temporal range of files in a named directory.
    1. Single file by name: `e4edm add C:\Users\e4e\example.txt` will add `${DATASET}\${DAY}\${MISSION}\example.txt`
    2. Multiple files by name: `e4edm add C:\Users\e4e\example1.txt C:\Users\e4e\example2.txt` will add `${DATASET}\${DAY}\${MISSION}\example1.txt` and `${DATASET}\${DAY}\${MISSION}\example2.txt`
    3. Multiple files by wildcard: `e4edm add C:\Users\e4e\example*.txt` will add `${DATASET}\${DAY}\${MISSION}\example1.txt`, `${DATASET}\${DAY}\${MISSION}\example2.txt`, etc.
    4. Single directory by name: `e4edm add C:\Users\e4e\example_data\` will add `${DATASET}\${DAY}\${MISSION}\example_data\file1.ext`, `${DATASET}\${DAY}\${MISSION}\example_data\file2.ext`, etc.
    5. Multiple directories by name: `e4edm add C:\Users\e4e\example_data1\ C:\Users\e4e\example_data2\` will add `${DATASET}\${DAY}\${MISSION}\example_data1\file1.ext`, `${DATASET}\${DAY}\${MISSION}\example_data1\file2.ext`, `${DATASET}\${DAY}\${MISSION}\example_data2\file1.ext`, `${DATASET}\${DAY}\${MISSION}\example_data2\file2.ext`, etc.
    6. Temporal range of files: `e4edm add --start 2023-03-13T15:00 --end 2023-03-13T16:00 C:\Users\e4e\example_data` will add any file in `C:\Users\e4e\example_data` with a last modified time between 13 Mar 2023 at 3:00 PM local and 13 Mar 2023 at 4:00 PM local directly into `${DATASET}\${DAY}\${MISSION}\`
7. Once a file is staged, you can see the staged file using `e4edm status`.
8. Once files are staged, you can commit the staged files using `e4edm commit [-h]`.  This will copy all of the staged files into the dataset directory and verify the copy.
10. Once all mission files are committed, you must add and commit a suitable readme file.  This must be either a MarkDown or docx file.  You can add and commit using `e4edm add --readme path` and `e4edm commit --readme`.
11. Once all files are committed, you can push the dataset to the final directory using `e4edm push [-h] path`.  This will verify all files and completion criteria, the copy the dataset into the final directory.

## Development
1. Install [uv](https://docs.astral.sh/uv/getting-started/installation/) and [Rust](https://rustup.rs/)
2. Open the repository root in VS Code
3. Run `uv sync --dev` to install Python dependencies
4. Run `uv run maturin develop` to compile the Rust extension
5. Select the `.venv` virtual environment for the workspace


# Developer Notes
The final dataset folder should have the following internal structure:
```
[YYYY].[MM].[PROJ].[GEN_LOCATION]/
    ED-00/
        [Mission 1]/
            [Data as defined by the project]
            manifest.json
            metadata.json
        [Mission 2]/
            [Data as defined by the project]
            manifest.json
            metadata.json
        ...
    ED-01/
        [Mission 3]/
            [Data as defined by the project]
            manifest.json
            metadata.json
        [Mission 4]/
            [Data as defined by the project]
            manifest.json
            metadata.json
        ...
    ...
    .e4edm.pkl
    manifest.json
    readme.md/.docx
```

`.e4edm.pkl` is a E4E Data Management Tool file - this is not part of the dataset, but should not be removed.  This is to retain state for the E4E Data Management tool.

`manifest.json` shall contain the following information