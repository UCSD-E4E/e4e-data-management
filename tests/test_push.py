'''Tests pushing files
'''
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Tuple
from unittest.mock import Mock

import pytest

from e4e_data_management.core import DataManager
from e4e_data_management.data import Dataset


def test_push(single_mission_data: Tuple[Tuple[Mock, DataManager, Path], Tuple[Path, int, int]],
              test_readme: Path):
    """Tests pushing data

    Args:
        test_app (Tuple[DataManager, Path]): Test app
        test_data (Tuple[Path, int, int]): Test data
        test_readme (Path): Test Readme
    """
    test_app, _ = single_mission_data
    _, app, _ = test_app

    app.add([test_readme], readme=True)
    app.commit(readme=True)
    with TemporaryDirectory() as push_dir:
        push_path = Path(push_dir)
        app.push(push_path)

        assert push_path.joinpath(app.active_dataset.name).is_dir()

@pytest.mark.parametrize('readme_name', [
    'readme.md',
    'readme.MD',
    'Readme.md',
    'README.md',
    'README.MD',
    'readme.docx',
    'readme.DOCX',
    'Readme.docx'
])
def test_valid_readme_names(single_mission: Tuple[Mock, DataManager, Path], readme_name: str):
    """Tests valid readme names

    Args:
        test_app (Tuple[DataManager, Path]): Test app
        readme_name (str): Readme name
    """
    _, app, _ = single_mission

    with TemporaryDirectory() as data_dir:
        readme_path = Path(data_dir).joinpath(readme_name)
        with open(readme_path, 'w', encoding='ascii') as handle:
            handle.write('readme\n')
        app.add([readme_path], readme=True)
        app.commit(readme=True)

        with TemporaryDirectory() as push_dir:
            push_path = Path(push_dir)
            app.push(push_path)


def test_push_recovers_from_partial_push(
        single_mission_data: Tuple[Tuple[Mock, DataManager, Path], Tuple[Path, int, int]],
        test_readme: Path):
    """A second push to the same destination succeeds when the existing copy is a
    compatible subset (simulates recovery from an interrupted push)"""
    test_app, _ = single_mission_data
    _, app, _ = test_app

    app.add([test_readme], readme=True)
    app.commit(readme=True)

    with TemporaryDirectory() as push_dir:
        push_path = Path(push_dir)
        app.push(push_path)

        dest = push_path / app.active_dataset.name

        # Remove one file from the destination manifest to simulate a partial push
        manifest_path = dest / 'manifest.json'
        with open(manifest_path, encoding='ascii') as f:
            manifest = json.load(f)
        first_key = next(iter(manifest))
        del manifest[first_key]
        with open(manifest_path, 'w', encoding='ascii') as f:
            json.dump(manifest, f)

        # Push should succeed: remaining destination files are a subset of source
        app.push(push_path)


def test_push_fails_when_destination_has_conflicting_file(
        single_mission_data: Tuple[Tuple[Mock, DataManager, Path], Tuple[Path, int, int]],
        test_readme: Path):
    """Push raises an error when a file at the destination has a different hash,
    indicating it belongs to a different dataset"""
    test_app, _ = single_mission_data
    _, app, _ = test_app

    app.add([test_readme], readme=True)
    app.commit(readme=True)

    with TemporaryDirectory() as push_dir:
        push_path = Path(push_dir)
        app.push(push_path)

        dest = push_path / app.active_dataset.name

        # Corrupt a manifest entry at the destination so the hash differs
        manifest_path = dest / 'manifest.json'
        with open(manifest_path, encoding='ascii') as f:
            manifest = json.load(f)
        first_key = next(iter(manifest))
        manifest[first_key]['sha256sum'] = 'deadbeef' * 8
        with open(manifest_path, 'w', encoding='ascii') as f:
            json.dump(manifest, f)

        with pytest.raises(RuntimeError):
            app.push(push_path)


def test_pushed_dataset_passes_validate(
        single_mission_data: Tuple[Tuple[Mock, DataManager, Path], Tuple[Path, int, int]],
        test_readme: Path):
    """The pushed dataset passes validate after a successful push"""
    test_app, _ = single_mission_data
    _, app, _ = test_app

    app.add([test_readme], readme=True)
    app.commit(readme=True)

    with TemporaryDirectory() as push_dir:
        push_path = Path(push_dir)
        app.push(push_path)

        pushed_root = push_path / app.active_dataset.name
        ds = Dataset.load(path=pushed_root)
        assert ds.validate_failures() == []


def test_push_fails_when_destination_has_extra_file(
        single_mission_data: Tuple[Tuple[Mock, DataManager, Path], Tuple[Path, int, int]],
        test_readme: Path):
    """Push fails if the destination contains a file that is not in the source manifest,
    leaving no valid-looking but corrupt pushed dataset"""
    test_app, _ = single_mission_data
    _, app, _ = test_app

    app.add([test_readme], readme=True)
    app.commit(readme=True)

    with TemporaryDirectory() as push_dir:
        push_path = Path(push_dir)
        app.push(push_path)

        dest = push_path / app.active_dataset.name
        # Plant an extra file not tracked in the manifest
        extra = dest / 'extra_file.bin'
        extra.write_bytes(b'not in manifest')

        with pytest.raises(RuntimeError):
            app.push(push_path)
