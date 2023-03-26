'''Tests for the status output
'''
import re
from pathlib import Path
from typing import Tuple
from unittest.mock import Mock

from e4e_data_management.core import DataManager


def test_readme_staging(single_mission: Tuple[Mock, DataManager, Path], test_readme: Path):
    """Tests that a staged README file is displayed in the status output

    Args:
        single_mission (Tuple[Mock, DataManager, Path]): Single mission test app
        test_readme (Path): Test Readme file
    """
    _, app, _ = single_mission

    app.add([test_readme], readme=True)

    status_output = app.status()

    regex = r"readme\.md|readme\.docx"

    matches = re.findall(regex, status_output, re.MULTILINE | re.IGNORECASE)

    assert len(matches) != 0
