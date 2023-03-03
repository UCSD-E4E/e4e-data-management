'''Tests the CLI
'''
import datetime as dt
from pathlib import Path
from shlex import split
from typing import Tuple
from unittest.mock import Mock, patch

from e4e_data_management.cli import main
from e4e_data_management.core import DataManager
from e4e_data_management.metadata import Metadata


def test_init_dataset():
    """Tests initialize dataset
    """
    args = split('e4edm init_dataset --date 2023-03-02 --project "TEST" --location "San Diego"')
    e4edm_mock = Mock(spec=DataManager)
    with patch('sys.argv', args),\
         patch('e4e_data_management.cli.DataManager', e4edm_mock):
        main()
        initialize_dataset_mock: Mock = e4edm_mock.load.return_value.initialize_dataset
        initialize_dataset_mock.assert_called_once_with(
            date=dt.date(2023, 3, 2),
            project='TEST',
            location='San Diego',
            directory=Path('.')
        )

def test_init_mission(test_mock_app: Tuple[Mock, DataManager, Path]):
    """Tests init_mission
    """
    mock, app, root_dir = test_mock_app

    app.initialize_dataset(
        date=dt.date(2023,3,2),
        project='TEST',
        location='San Diego',
        directory=root_dir
    )

    args = split('e4edm init_mission --timestamp 2023-03-02T15:06-08:00 --device Device1 '
                '--country USA --region California --site SD --name RUN001')
    with patch('sys.argv', args),\
            patch('e4e_data_management.cli.DataManager', mock):
        main()
        mock.initialize_mission.assert_called_once_with(
            metadata=Metadata(
                timestamp=dt.datetime(2023, 3, 2, 15, 6,
                                        tzinfo=dt.timezone(dt.timedelta(hours=-8))),
                country='USA',
                device='Device1',
                region='California',
                site='SD',
                mission='RUN001',
                notes=None
            )
        )
