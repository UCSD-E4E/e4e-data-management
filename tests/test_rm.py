'''Integration tests for the rm mission command'''
import datetime as dt
import json
from pathlib import Path
from typing import Tuple
from unittest.mock import Mock

import pytest

from e4e_data_management.core import DataManager
from e4e_data_management.metadata import Metadata


def _make_dataset(app: DataManager, root: Path, name: str = 'TEST') -> str:
    app.initialize_dataset(
        date=dt.date(2023, 3, 2),
        project=name,
        location='San Diego',
        directory=root,
    )
    return app.active_dataset.name


def _make_mission(app: DataManager, name: str) -> str:
    app.initialize_mission(
        metadata=Metadata(
            timestamp=dt.datetime.fromisoformat('2023-03-02T10:00-08:00'),
            device='Device1',
            country='USA',
            region='California',
            site='SD',
            mission=name,
        )
    )
    return app.active_mission.name


def test_rm_mission_removes_directory(test_app: Tuple[Mock, DataManager, Path]):
    """Removing a mission deletes its directory from disk"""
    _, app, root = test_app
    dataset_name = _make_dataset(app, root)
    _make_mission(app, 'M1')

    mission_dir = root / dataset_name / 'ED-00' / 'M1'
    assert mission_dir.exists()

    app.remove_mission(dataset_name, 'ED-00 M1')

    assert not mission_dir.exists()


def test_rm_mission_removes_from_list(test_app: Tuple[Mock, DataManager, Path]):
    """Removed mission no longer appears in list mission output"""
    _, app, root = test_app
    dataset_name = _make_dataset(app, root)
    _make_mission(app, 'M1')

    app.remove_mission(dataset_name, 'ED-00 M1')

    assert 'ED-00 M1' not in app.datasets[dataset_name].missions


def test_rm_mission_updates_manifest(test_app: Tuple[Mock, DataManager, Path],
                                     test_data: Tuple[Path, int, int]):
    """Removed mission's files are stripped from the dataset manifest"""
    _, app, root = test_app
    data_dir, _, _ = test_data
    dataset_name = _make_dataset(app, root)
    _make_mission(app, 'M1')

    bin_files = list(data_dir.glob('*.bin'))[:3]
    app.add(bin_files)
    app.commit()

    manifest_path = root / dataset_name / 'manifest.json'
    with open(manifest_path, encoding='ascii') as f:
        before = json.load(f)
    assert any('ED-00/M1' in k for k in before)

    app.remove_mission(dataset_name, 'ED-00 M1')

    with open(manifest_path, encoding='ascii') as f:
        after = json.load(f)
    assert not any('ED-00/M1' in k for k in after)


def test_rm_last_mission_in_day_removes_day_directory(
        test_app: Tuple[Mock, DataManager, Path]):
    """Removing the only mission in a day also removes the ED-XX directory"""
    _, app, root = test_app
    dataset_name = _make_dataset(app, root)
    _make_mission(app, 'M1')

    day_dir = root / dataset_name / 'ED-00'
    assert day_dir.exists()

    app.remove_mission(dataset_name, 'ED-00 M1')

    assert not day_dir.exists()


def test_rm_mission_preserves_sibling_mission(test_app: Tuple[Mock, DataManager, Path]):
    """Removing one mission on a day leaves its sibling intact"""
    _, app, root = test_app
    dataset_name = _make_dataset(app, root)
    _make_mission(app, 'M1')
    _make_mission(app, 'M2')

    app.remove_mission(dataset_name, 'ED-00 M1')

    day_dir = root / dataset_name / 'ED-00'
    assert day_dir.exists()
    assert (day_dir / 'M2').exists()
    assert 'ED-00 M2' in app.datasets[dataset_name].missions


def test_rm_active_mission_clears_active_state(test_app: Tuple[Mock, DataManager, Path]):
    """Removing the currently active mission clears the active mission pointer"""
    _, app, root = test_app
    dataset_name = _make_dataset(app, root)
    _make_mission(app, 'M1')
    assert app.active_mission is not None

    app.remove_mission(dataset_name, 'ED-00 M1')

    assert app.active_mission is None


def test_rm_mission_not_found_raises(test_app: Tuple[Mock, DataManager, Path]):
    """Attempting to remove a non-existent mission raises RuntimeError"""
    _, app, root = test_app
    dataset_name = _make_dataset(app, root)

    with pytest.raises(RuntimeError):
        app.remove_mission(dataset_name, 'ED-00 nonexistent')


def test_rm_mission_unknown_dataset_raises(test_app: Tuple[Mock, DataManager, Path]):
    """Attempting to remove a mission from an unknown dataset raises RuntimeError"""
    _, app, root = test_app
    _make_dataset(app, root)

    with pytest.raises(RuntimeError):
        app.remove_mission('no_such_dataset', 'ED-00 M1')
