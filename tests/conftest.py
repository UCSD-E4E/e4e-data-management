'''Common Test Fixtures
'''
from collections import namedtuple
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from e4e_data_management.core import DataManager

TestFixture = namedtuple('Test Fixture', ['app', 'root'])

@pytest.fixture(name='test_app')
def create_test_app() -> TestFixture:
    """Creates a test app

    Yields:
        TestFisture: App and root directory
    """
    with TemporaryDirectory() as temp_dir:
        root_dir = Path(temp_dir)
        app = DataManager(
            app_config_dir=root_dir
        )
        yield TestFixture(app, root_dir)
