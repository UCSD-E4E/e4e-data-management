'''Tests pushing files
'''
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Tuple
from unittest.mock import Mock

import pytest

from e4e_data_management.core import DataManager


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
    'Readme.docx',
    'readme.pdf'
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
