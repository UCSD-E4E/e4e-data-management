'''Tests pushing files
'''
import datetime as dt
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Tuple

import pytest

from e4e_data_management.core import DataManager
from e4e_data_management.metadata import Metadata


def test_push(test_app: Tuple[DataManager, Path],
              test_data: Tuple[Path, int, int],
              test_readme: Path):
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
    app.add([test_readme])
    app.commit()
    with TemporaryDirectory() as push_dir:
        push_path = Path(push_dir)
        app.push(push_path)

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
def test_valid_readme_names(test_app: Tuple[DataManager, Path], readme_name: str):
    """Tests valid readme names

    Args:
        test_app (Tuple[DataManager, Path]): Test app
        readme_name (str): Readme name
    """
    app, root_dir = test_app
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
    with TemporaryDirectory() as data_dir:
        readme_path = Path(data_dir).joinpath(readme_name)
        with open(readme_path, 'w', encoding='ascii') as handle:
            handle.write('readme\n')
        app.add([readme_path])
        app.commit()

        with TemporaryDirectory() as push_dir:
            push_path = Path(push_dir)
            app.push(push_path)
