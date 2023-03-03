'''Tests creating a dataset
'''
import datetime as dt
from pathlib import Path
from typing import Tuple
from unittest.mock import Mock

import pytest

from e4e_data_management.core import DataManager


def test_init_dataset(test_app: Tuple[Mock, DataManager, Path]):
    """Tests creating the dataset
    """
    _, app, root_dir = test_app
    date = dt.date(2023, 2, 28)
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

    assert app.active_dataset.root == dataset_dir
    assert app.active_dataset.name == '2023.02.TEST.San Diego'
    assert app.active_mission is None

def test_init_existing(test_app: Tuple[Mock, DataManager, Path]):
    """Tests that running init on an existing dataset will do nothing
    """
    _, app, root_dir = test_app
    date = dt.date(2023, 2, 28)
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

    assert app.active_dataset.name == '2023.02.TEST.San Diego'
    assert app.active_mission is None
