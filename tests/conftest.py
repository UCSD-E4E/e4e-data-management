'''Common Test Fixtures
'''
from collections import namedtuple
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest
from unittest.mock import Mock, patch

from e4e_data_management.core import DataManager

AppFixture = namedtuple('AppFixture', ['app', 'root'])
MockAppFixture = namedtuple('MockAppFixture', ['mock', 'app', 'root'])

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
