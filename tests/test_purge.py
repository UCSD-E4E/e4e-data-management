'''Test purging files
'''
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Tuple
from unittest.mock import Mock

from e4e_data_management.core import DataManager


def test_purge(single_mission_data: Tuple[Tuple[Mock, DataManager, Path], Tuple[Path, int, int]],
               test_readme: Path):
    """Tests purging data

    Args:
        single_mission_data (Tuple[Tuple[Mock, DataManager, Path], Tuple[Path, int, int]]): Test Data
        test_readme (Path): Test Readme
    """
    app_fixture, _ = single_mission_data
    _, app, root_dir = app_fixture

    app.add([test_readme], readme=True)
    app.commit(readme=True)

    with TemporaryDirectory() as push_dir:
        app.push(Path(push_dir))
    assert len(list(root_dir.glob('2023.03.02.Test.San Diego'))) == 1
    app.prune()
    assert len(list(root_dir.glob('2023.03.02.Test.San Diego'))) == 0
