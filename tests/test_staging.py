'''Data staging tests
'''
import datetime as dt
import os
from pathlib import Path
from typing import Tuple
from unittest.mock import Mock

from e4e_data_management.core import DataManager
from e4e_data_management.metadata import Metadata


def test_stage_commit_files(test_app: Tuple[Mock, DataManager, Path],
                            test_data: Tuple[Path, int, int]):
    """Test staging data
    """
    _, app, root = test_app
    data_dir, n_files, _ = test_data
    app.initialize_dataset(
        date=dt.date(2023, 3, 2),
        project='TestStaging',
        location='San Diego',
        directory=root
    )
    app.initialize_mission(
        metadata=Metadata(
            timestamp=dt.datetime.fromisoformat('2023-03-02T00:11-08:00'),
            device='Device 1',
            country='USA',
            region='California',
            site='Site 1',
            mission='TSF001'
        )
    )

    app.add(list(data_dir.rglob('*.bin')))

    assert len(app.active_mission.staged_files) == n_files
    assert len(app.active_mission.committed_files) == 0

    app.commit()

    assert len(app.active_mission.staged_files) == 0
    assert len(app.active_mission.committed_files) == n_files

    expected_files = [
        Path('.e4edm.pkl'),
        Path('manifest.json'),
        Path('ED-00'),
        Path('ED-00', 'TSF001'),
        Path('ED-00', 'TSF001', 'metadata.json'),
        Path('ED-00', 'TSF001', 'manifest.json'),
    ]
    expected_files.extend(
        [Path('ED-00', 'TSF001', f'{file_idx:04d}.bin') for file_idx in range(n_files)]
    )
    dataset_dir = root.joinpath('2023.03.02.TestStaging.San Diego')
    current_files = sorted(file.relative_to(dataset_dir) for file in dataset_dir.rglob('*'))
    assert current_files == sorted(expected_files)

    assert app.validate()

def test_stage_commit_readme(test_app: Tuple[Mock, DataManager, Path],
                            test_readme: Path):
    """Test staging data
    """
    _, app, root = test_app
    app.initialize_dataset(
        date=dt.date(2023, 3, 2),
        project='TestStaging',
        location='San Diego',
        directory=root
    )
    app.initialize_mission(
        metadata=Metadata(
            timestamp=dt.datetime.fromisoformat('2023-03-02T00:11-08:00'),
            device='Device 1',
            country='USA',
            region='California',
            site='Site 1',
            mission='TSF001'
        )
    )

    app.add([test_readme], readme=True)

    assert len(app.active_mission.staged_files) == 0
    assert len(app.active_mission.committed_files) == 0
    assert len(app.active_dataset.staged_files) == 1
    assert len(app.active_dataset.committed_files) == 0

    app.commit(readme=True)

    assert len(app.active_mission.staged_files) == 0
    assert len(app.active_mission.committed_files) == 0
    assert len(app.active_dataset.staged_files) == 0
    assert len(app.active_dataset.committed_files) == 1

    expected_files = [
        Path('.e4edm.pkl'),
        Path('manifest.json'),
        Path('readme.md'),
        Path('ED-00'),
        Path('ED-00', 'TSF001'),
        Path('ED-00', 'TSF001', 'metadata.json'),
        Path('ED-00', 'TSF001', 'manifest.json'),
    ]
    dataset_dir = root.joinpath('2023.03.02.TestStaging.San Diego')
    current_files = sorted(file.relative_to(dataset_dir) for file in dataset_dir.rglob('*'))
    assert current_files == sorted(expected_files)

    assert app.validate()

def test_relative_path(test_app: Tuple[Mock, DataManager, Path], test_data: Tuple[Path, int, int]):
    """Tests that adding a relative path retains the origin of the relative path and doesn't throw
    an exception

    Args:
        test_app (Tuple[Mock, DataManager, Path]): Test application
        test_data (Tuple[Path, int, int]): Test data
    """
    _, app, root_dir = test_app
    data_dir, _, _ = test_data

    app.initialize_dataset(
        date=dt.date.fromisoformat('2023-03-25'),
        project='Test Relative Path',
        location='San Diego',
        directory=root_dir
    )
    app.initialize_mission(
        metadata=Metadata(
        timestamp=dt.datetime.fromisoformat('2023-03-25T15:10-07:00'),
        device='DUT',
        country='USA',
        region='Southern California',
        site='e4edm',
        mission='test_relative_path'
        )
    )

    original_working_dir = Path.cwd()

    os.chdir(data_dir)

    app.add([Path('0000.bin')])

    os.chdir(original_working_dir)

    app.commit()

    assert root_dir.joinpath('2023.03.25.Test Relative Path.San Diego',
                             'ED-00',
                             'test_relative_path',
                             '0000.bin').exists()
