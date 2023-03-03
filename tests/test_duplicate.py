'''Testing duplication
'''
import datetime as dt
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Tuple

from e4e_data_management.core import DataManager
from e4e_data_management.metadata import Metadata


def test_push(test_app: Tuple[DataManager, Path],
              test_data: Tuple[Path, int, int]):
    """Tests pushing data

    Args:
        test_app (Tuple[DataManager, Path]): Test app
        test_data (Tuple[Path, int, int]): Test data
        test_readme (Path): Test Readme
    """
    app, root_dir = test_app
    data_dir, _, _ = test_data

    app.initialize_dataset(
        date=dt.date(2023, 3, 2),
        project='Test',
        location='San Diego',
        directory=root_dir
    )
    app.initialize_mission(
        metadata=Metadata(
        timestamp=dt.datetime.fromisoformat('2023-03-02T19:38-08:00'),
        device='Device1',
        country='USA',
        region='California',
        site='SD',
        mission='TPF001'
        )
    )
    app.add(data_dir.rglob('*.bin'))
    app.commit()

    with TemporaryDirectory() as duplication_dir:
        target = Path(duplication_dir)
        app.duplicate([target])

        dataset_dir = root_dir.joinpath('2023.03.Test.San Diego')
        original_files = sorted([file.relative_to(dataset_dir) for file in dataset_dir.rglob('*')
                                 if file.name not in ['.e4edm.pkl']])

        duplicate_files = sorted([file.relative_to(target) for file in target.rglob('*')])

        assert original_files == duplicate_files

        manifest_files = [file
                          for file in target.rglob('*')
                          if file.is_file() and file not in [target.joinpath('manifest.json')]]
        assert app.active_dataset.manifest.validate(
            manifest=app.active_dataset.manifest.get_dict(),
            files=manifest_files,
            root=target
        )
