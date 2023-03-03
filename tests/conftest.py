'''Common Test Fixtures
'''
import random
from collections import namedtuple
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import Mock, patch

import pytest

from e4e_data_management.core import DataManager

AppFixture = namedtuple('AppFixture', ['app', 'root'])
MockAppFixture = namedtuple('MockAppFixture', ['mock', 'app', 'root'])
DataFixture = namedtuple('DataFixture', ['path', 'n_files', 'file_size'])

@pytest.fixture(name='test_app')
def create_test_app() -> AppFixture:
    """Creates a test app

    Yields:
        TestFixture: App and root directory
    """
    with TemporaryDirectory() as temp_dir:
        root_dir = Path(temp_dir)
        app = DataManager(
            app_config_dir=root_dir
        )
        yield AppFixture(app, root_dir)

@pytest.fixture(name='test_mock_app')
def create_mock_test_app() -> MockAppFixture:
    """Creates a mock test app

    Yields:
        TestFixture: Mock, app, and root directory
    """
    with TemporaryDirectory() as temp_dir:
        root_dir = Path(temp_dir)
        DataManager.config_dir = root_dir
        app = DataManager(
            app_config_dir=root_dir
        )

        mock = Mock(app)
        mock.load.return_value = mock
        with patch('e4e_data_management.cli.DataManager', mock):
            yield MockAppFixture(mock, app, root_dir)

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
        data_dir = Path(path)
        for file_idx in range(N_FILES):
            with open(data_dir.joinpath(f'{file_idx:04d}.bin'), 'wb') as handle:
                try:
                    data = random.randbytes(FILE_SIZE)
                except Exception: # pylint: disable=broad-except
                    data = bytes([random.randint(0, 255) for _ in range(FILE_SIZE)])
                handle.write(data)
        yield DataFixture(data_dir, N_FILES, FILE_SIZE)
