'''Test validators
'''
import sys
import json
import subprocess
from pathlib import Path

from e4e_data_management.data import Dataset


def test_create_manifests():
    """Tests the structure and validity of manifest files
    """
    expedition_root = Path('example_dataset')
    runs = [
        expedition_root.joinpath('ED-1', 'RUN001'),
        expedition_root.joinpath('ED-1', 'RUN002'),
        expedition_root.joinpath('ED-1', 'RUN003'),
        expedition_root.joinpath('ED-2', 'RUN004'),
        expedition_root.joinpath('ED-2', 'RUN005'),
    ]

    datasets = [
        Dataset(root=run) for run in runs
    ]

    for dataset in datasets:
        dataset.generate_manifest()

    for run in runs:
        validate_folder(run)

    expedition_dataset = Dataset(root=expedition_root)
    expedition_dataset.generate_manifest()
    validate_folder(expedition_root)

def validate_folder(run: Path):
    """Validates the folder contents

    Args:
        run (Path): Folder to validate
    """
    manifest_file = run.joinpath('manifest.json')
    with open(manifest_file, 'r', encoding='ascii') as handle:
        manifest = json.load(handle)
    for file in run.rglob('*'):
        if file == manifest_file:
            continue
        if file.is_dir():
            continue
        manifest_key = file.relative_to(run).as_posix()
        assert manifest_key in manifest

        if sys.platform == 'linux':
            output = subprocess.check_output(['sha256sum', file.as_posix()])
            cksum = output.decode().splitlines()[0].split()[0]
        elif sys.platform == 'win32':
            # Note: certUtil actually throws an error on empty string!  So we need to bypass...
            if file.lstat().st_size != 0:
                output = subprocess.check_output(
                    ['certUtil', '-hashfile', file.absolute().as_posix(), 'SHA256'])
                cksum = output.decode().splitlines()[1].strip()
            else:
                cksum = 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855'
        else:
            raise NotImplementedError

        assert cksum == manifest[manifest_key]['sha256sum']

def test_self_validate(single_validated_expedition: Path):
    """Tests self consistency

    Args:
        single_validated_expedition (Path): Validated Expedition
    """
    dataset = Dataset(single_validated_expedition)
    manifest = dataset.get_manifest()
    assert dataset.validate(manifest=manifest)
    