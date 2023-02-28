# E4E Data Management
Welcome to the E4E Data Management Tool Suite.

This suite should be used to manage data in the field, duplicate data across multiple drives for redundancy, compiling and staging all data after a deployment to the E4E NAS, and final archiving and management of deployment data on the NAS.

There are four tools provided by this suite:
- `E4EDuplicator`
- `E4EDataWrangler`
- `E4ECommitter`
- `E4EArchiver`

Each of these also has a corresponding command line version:
- `E4EDuplicatorCli`
- `E4EDataWranglerCli`
- `E4ECommitterCli`
- `E4EArchiverCli`

## Development
1. Open `e4e-data-management.code-workspace` in VS Code
2. Create a terminal
3. Run `python -m venv .venv`
4. Select the new virtual environment for the workspace
5. Create a new Python terminal
6. Run `python -m pip install -e .[dev]`

`e4edm init_dataset --date date --project project --location location [--path path]`
`e4edm init_mission --timestamp timestamp --device device --country country --region region --site site --mission mission [--notes notes]`
`e4edm config parameter value`
`e4edm status`
`e4edm activate dataset [day mission]`
`e4edm add files`
`e4edm commit`
`e4edm duplicate paths`
`e4edm validate`
`e4edm push destination`
`e4edm zip`
`e4edm unzip`
`e4edm list`
`e4edm prune`

# Developer Notes
The final dataset folder should have the following internal structure:
```
[YYYY].[MM].[PROJ].[GEN_LOCATION]/
    ED-00/
        [Data as defined by the project]
        metadata.json
    ED-01/
        [Data as defined by the project]
        metadata.json
    ...
    .e4edm.pkl
    readme.md/.docx
    manifest.json
```

`.e4edm.pkl` is a E4E Data Management Tool file - this is not part of the dataset, but should not be removed.  This is to retain state for the E4E Data Management tool.

`manifest.json` shall contain the following information