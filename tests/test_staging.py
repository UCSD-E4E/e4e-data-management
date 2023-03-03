'''Data staging tests
'''
import datetime as dt
from pathlib import Path
from typing import Tuple

from e4e_data_management.core import DataManager
from e4e_data_management.metadata import Metadata


def test_stage_files(test_app: Tuple[DataManager, Path], test_data: Tuple[Path, int, int]):
    """Test staging data
    """
    app, root = test_app
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
    dataset_dir = root.joinpath('2023.03.TestStaging.San Diego')
    current_files = sorted(file.relative_to(dataset_dir) for file in dataset_dir.rglob('*'))
    assert current_files == sorted(expected_files)

    assert app.validate()
