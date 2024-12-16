'''Testing duplication
'''
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Tuple
from unittest.mock import Mock

from e4e_data_management.core import DataManager


def test_duplicate(
        single_mission_data: Tuple[Tuple[Mock, DataManager, Path], Tuple[Path, int, int]]):
    """Tests duplicating data

    Args:
        test_app (Tuple[DataManager, Path]): Test app
        test_data (Tuple[Path, int, int]): Test data
        test_readme (Path): Test Readme
    """
    test_app, _ = single_mission_data
    _, app, root_dir = test_app

    with TemporaryDirectory() as duplication_dir:
        target = Path(duplication_dir)
        app.duplicate([target])

        dataset_dir = root_dir.joinpath('2023.03.02.Test.San Diego')
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
