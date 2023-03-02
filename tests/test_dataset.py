'''Tests creating a dataset
'''
import datetime as dt
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from e4e_data_management.core import DataManager


def test_init_dataset():
    """Tests creating the dataset
    """
    with TemporaryDirectory() as temp_folder:
        root_dir = Path(temp_folder)
        app = DataManager(app_config_dir=root_dir)
        date = dt.date.today()
        project = 'TEST'
        location = 'San Diego'
        app.initialize_dataset(
            date=date,
            project=project,
            location=location,
            directory=root_dir
        )

        dataset_dir = root_dir.joinpath(f'{date.year:04d}.{date.month:02d}.{project}.{location}')
        assert dataset_dir.is_dir()
        assert dataset_dir.joinpath('manifest.json').is_file()
        current_files = sorted([file.relative_to(dataset_dir) for file in dataset_dir.rglob('*')])
        expected_files = sorted([
            Path('.e4edm.pkl'),
            Path('manifest.json')
        ])
        assert current_files == expected_files

def test_init_existing():
    """Tests that running init on an existing dataset will do nothing
    """
    with TemporaryDirectory() as temp_folder:
        root_dir = Path(temp_folder)
        app = DataManager(app_config_dir=root_dir)
        date = dt.date.today()
        project = 'TEST'
        location = 'San Diego'
        app.initialize_dataset(
            date=date,
            project=project,
            location=location,
            directory=root_dir
        )

        with pytest.raises(RuntimeError):
            app.initialize_dataset(
                date=date,
                project=project,
                location=location,
                directory=root_dir
            )
