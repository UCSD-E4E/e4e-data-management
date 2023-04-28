'''Common Test Fixtures
'''
import datetime as dt
import random
import sys
from collections import namedtuple
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Tuple
from unittest.mock import Mock, patch

import pytest

from e4e_data_management.core import DataManager
from e4e_data_management.metadata import Metadata

AppFixture = namedtuple('AppFixture', ['app', 'root'])
MockAppFixture = namedtuple('MockAppFixture', ['mock', 'app', 'root'])
DataFixture = namedtuple('DataFixture', ['path', 'n_files', 'file_size'])


@pytest.fixture(name='test_bare_app')
def create_test_bare_app() -> MockAppFixture:
    """Creates a mock test app

    Returns:
        MockAppFixture: Mock app

    """
    with TemporaryDirectory() as temp_dir:
        root_dir = Path(temp_dir).resolve()
        DataManager.config_dir = root_dir
        app = DataManager(
            app_config_dir=root_dir
        )

        default_editor = {
            'win': Path(r'C:\Windows\System32\notepad.exe'),
            'win32': Path(r'C:\Windows\System32\notepad.exe'),
            'linux': Path('/usr/bin/vim')
        }

        if sys.platform in default_editor:
            app.set_editor(default_editor[sys.platform])

        mock = Mock(app)
        mock.load.return_value = mock
        mock.dirs = app.dirs
        mock.dataset_dir = app.dataset_dir
        with patch('e4e_data_management.cli.DataManager', mock):
            yield MockAppFixture(mock, app, root_dir)

@pytest.fixture(name='test_app')
def create_test_app(test_bare_app: Tuple[Mock, DataManager, Path]) -> MockAppFixture:
    """Creates a mock test app

    Yields:
        TestFixture: Mock, app, and root directory
    """
    _, app, root_dir = test_bare_app
    app.dataset_dir = root_dir
    yield test_bare_app

N_FILES = 128
FILE_SIZE = 1024
@pytest.fixture(name='test_data')
def create_test_data() -> DataFixture:
    """Creates test data

    Returns:
        DataFixture: Data Fixture
    """
    random.seed(0)
    with TemporaryDirectory() as path:
        data_dir = Path(path).resolve()
        for file_idx in range(N_FILES):
            with open(data_dir.joinpath(f'{file_idx:04d}.bin'), 'wb') as handle:
                # Python 3.8 doesn't have random.randbytes, so this is the bypass
                try:
                    data = random.randbytes(FILE_SIZE) # pylint: disable=no-member
                except Exception: # pylint: disable=broad-except
                    data = bytes([random.randint(0, 255) for _ in range(FILE_SIZE)])
                handle.write(data)
        yield DataFixture(data_dir, N_FILES, FILE_SIZE)

@pytest.fixture(name='test_readme')
def create_test_readme() -> Path:
    """Creates a test README.md

    Returns:
        Path: README.md
    """
    with TemporaryDirectory() as path:
        readme_path = Path(path).joinpath('readme.md').resolve()
        with open(readme_path, 'w', encoding='ascii') as handle:
            handle.write('readme\n')
        yield readme_path

@pytest.fixture(name='single_mission')
def create_single_mission(test_app: Tuple[Mock, DataManager, Path]
                          ) -> Tuple[Mock, DataManager, Path]:
    """Creates a single mission

    Args:
        test_app (Tuple[DataManager, Path]): Test App

    Returns:
        Tuple[Tuple[DataManager, Path], Tuple[Path, int, int]]: test app, test data
    """
    _, app, root_dir = test_app

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

    return test_app

@pytest.fixture(name='single_mission_data')
def create_single_mission_data(single_mission: Tuple[Mock, DataManager, Path],
                          test_data: Tuple[Path, int, int]
                          ) -> Tuple[Tuple[Mock, DataManager, Path], Tuple[Path, int, int]]:
    """Creates a single mission

    Args:
        test_app (Tuple[DataManager, Path]): Test App
        test_data (Tuple[Path, int, int]): Test Data

    Returns:
        Tuple[Tuple[DataManager, Path], Tuple[Path, int, int]]: test app, test data
    """
    _, app, _ = single_mission
    data_dir, _, _ = test_data

    app.add(data_dir.rglob('*.bin'))
    app.commit()

    return single_mission, test_data
