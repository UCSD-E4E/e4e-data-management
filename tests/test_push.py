'''Tests pushing files
'''
import datetime as dt
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Tuple

import pytest

from e4e_data_management.core import DataManager
from e4e_data_management.metadata import Metadata


def test_push(single_mission_data: Tuple[Tuple[DataManager, Path], Tuple[Path, int, int]],
              test_readme: Path):
    """Tests pushing data

    Args:
        test_app (Tuple[DataManager, Path]): Test app
        test_data (Tuple[Path, int, int]): Test data
        test_readme (Path): Test Readme
    """
    test_app, _ = single_mission_data
    app, _ = test_app

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
def test_valid_readme_names(single_mission: Tuple[DataManager, Path], readme_name: str):
    """Tests valid readme names

    Args:
        test_app (Tuple[DataManager, Path]): Test app
        readme_name (str): Readme name
    """
    app, _ = single_mission

    with TemporaryDirectory() as data_dir:
        readme_path = Path(data_dir).joinpath(readme_name)
        with open(readme_path, 'w', encoding='ascii') as handle:
            handle.write('readme\n')
        app.add([readme_path])
        app.commit()

        with TemporaryDirectory() as push_dir:
            push_path = Path(push_dir)
            app.push(push_path)
