'''Tests the CLI
'''
import datetime as dt
from pathlib import Path
from shlex import split
from tempfile import TemporaryDirectory
from time import sleep
from typing import Tuple
from unittest.mock import Mock, patch

import appdirs
import pytest

from e4e_data_management.cli import main
from e4e_data_management.core import DataManager
from e4e_data_management.metadata import Metadata


def test_init_dataset(test_bare_app: Tuple[Mock, DataManager, Path]):
    """Tests initialize dataset
    """
    mock, _, _ = test_bare_app
    args = split('e4edm init_dataset --date 2023-03-02 --project "TEST" --location "San Diego"')
    with patch('sys.argv', args):
        main()
        mock.initialize_dataset.assert_called_once_with(
            date=dt.date(2023, 3, 2),
            project='TEST',
            location='San Diego',
            directory=Path(appdirs.user_data_dir(
            appname='E4EDataManagement',
            appauthor='Engineers for Exploration'
            ))
        )

def test_init_dataset_today(test_app: Tuple[Mock, DataManager, Path]):
    """Tests init_dataset with the `today` parameter

    Args:
        test_app (Tuple[Mock, DataManager, Path]): Test application
    """
    mock, _, _ = test_app
    args = split('e4edm init_dataset --date today --project TEST --location Location')
    with patch('sys.argv', args):
        main()
        mock.initialize_dataset.assert_called_once_with(
            date=dt.date.today(),
            project='TEST',
            location='Location',
            directory=Path(appdirs.user_data_dir(
            appname='E4EDataManagement',
            appauthor='Engineers for Exploration'
            ))
        )

def test_init_mission(test_app: Tuple[Mock, DataManager, Path]):
    """Tests that `e4edm init_mission` properly calls DataManager.initialize_mission

    Args:
        test_app (Tuple[Mock, DataManager, Path]): Test application
    """
    mock, app, root_dir = test_app

    app.initialize_dataset(
        date=dt.date(2023,3,2),
        project='TEST',
        location='San Diego',
        directory=root_dir
    )

    args = split('e4edm init_mission --timestamp 2023-03-02T15:06-08:00 --device Device1 '
                '--country USA --region California --site SD --name RUN001')
    with patch('sys.argv', args):
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
                notes=''
            )
        )

def test_add_files(single_mission: Tuple[Mock, DataManager, Path],
                   test_data: Tuple[Path, int, int]):
    """Tests adding files

    Args:
        test_app (Tuple[Mock, DataManager, Path]): Mock App
        test_data (Tuple[Path, int, int]): Test Data
    """
    mock, _, _ = single_mission
    data_dir, _, _ = test_data

    bin_files = list(data_dir.rglob('*.bin'))[:2]
    args = split(f'e4edm add {bin_files[0].as_posix()} {bin_files[1].as_posix()}')
    with patch('sys.argv', args):
        main()
        mock.add.assert_called_once_with(paths=bin_files, readme=False, destination=None)

def test_add_files_start(single_mission: Tuple[Mock, DataManager, Path],
                   test_data: Tuple[Path, int, int]):
    """Tests adding files

    Args:
        test_app (Tuple[Mock, DataManager, Path]): Mock App
        test_data (Tuple[Path, int, int]): Test Data
    """
    mock, _, _ = single_mission
    data_dir, _, _ = test_data


    sleep(1)

    start_time = dt.datetime.now()

    args = split(f'e4edm add {data_dir.as_posix()}/*.bin '
                 f'--start {start_time.isoformat()}')
    with patch('sys.argv', args):
        main()
        mock.add.assert_called_once_with(paths=[], readme=False, destination=None)

def test_add_files_timezone(single_mission: Tuple[Mock, DataManager, Path],
                            test_data: Tuple[Path, int, int]):
    """Tests whether timezone-aware timestamps can be fed into `e4edm add`

    Args:
        single_mission (Tuple[Mock, DataManager, Path]): Single mission app
        test_data (Tuple[Path, int, int]): Test data
    """
    mock, _, _ = single_mission
    data_dir, _, _ = test_data
    local_tz = dt.datetime.now().astimezone().tzinfo
    sleep(1)
    start_time = dt.datetime.now(tz=local_tz)

    args = split(f'e4edm add --start {start_time.isoformat()} {data_dir.as_posix()}/*')
    with patch('sys.argv', args):
        main()
        mock.add.assert_called_once_with(paths=[], readme=False, destination=None)


def test_add_files_end(single_mission: Tuple[Mock, DataManager, Path],
                   test_data: Tuple[Path, int, int]):
    """Tests adding files

    Args:
        test_app (Tuple[Mock, DataManager, Path]): Mock App
        test_data (Tuple[Path, int, int]): Test Data
    """
    mock, _, _ = single_mission
    data_dir, _, _ = test_data


    bin_files = list(data_dir.glob('*.bin'))
    sleep(1)

    start_time = dt.datetime.now()

    args = split(f'e4edm add {data_dir.as_posix()}/*.bin '
                 f'--end {start_time.isoformat()}')
    with patch('sys.argv', args):
        main()
        mock.add.assert_called_once_with(paths=bin_files, readme=False, destination=None)

def test_add_glob(single_mission: Tuple[Mock, DataManager, Path],
                   test_data: Tuple[Path, int, int]):
    """Tests adding files

    Args:
        test_app (Tuple[Mock, DataManager, Path]): Mock App
        test_data (Tuple[Path, int, int]): Test Data
    """
    mock, _, _ = single_mission
    data_dir, _, _ = test_data

    args = split(f'e4edm add {data_dir.as_posix()}/*.bin')
    with patch('sys.argv', args):
        main()
        mock.add.assert_called_once_with(paths=list(data_dir.glob('*.bin')),
                                         readme=False,
                                         destination=None)

def test_add_multifile(single_mission: Tuple[Mock, DataManager, Path]):
    """Tests adding multiple files at the same time

    Args:
        single_mission (Tuple[Mock, DataManager, Path]): Single mission
    """
    mock, _, root_dir = single_mission

    file1 = root_dir.joinpath('test1.txt')
    file1.touch()

    file2 = root_dir.joinpath('test2.txt')
    file2.touch()

    args = split(f'e4edm add {file1.as_posix()} {file2.as_posix()}')
    with patch('sys.argv', args):
        main()
        mock.add.assert_called_once_with(paths=[file1, file2], readme=False, destination=None)

def test_commit_files(single_mission: Tuple[Mock, DataManager, Path],
                      test_data: Tuple[Path, int, int]):
    """Tests committing files

    Args:
        test_app (Tuple[Mock, DataManager, Path]): Mock App
        test_data (Tuple[Path, int, int]): Test Data
    """
    mock, app, _ = single_mission
    data_dir, _, _ = test_data

    bin_files = list(data_dir.rglob('*.bin'))[:2]
    app.add(
        paths=bin_files
    )
    args = split('e4edm commit')
    with patch('sys.argv', args):
        main()
        mock.commit.assert_called_once()

def test_push_files(
        single_mission_data: Tuple[Tuple[Mock, DataManager, Path], Tuple[Path, int, int]]):
    """Tests pushing files

    Args:
        test_app (Tuple[Mock, DataManager, Path]): Mock App
        test_data (Tuple[Path, int, int]): Test Data
    """
    test_app, _ = single_mission_data
    mock, _, _ = test_app

    with TemporaryDirectory() as push_dir:
        push_path = Path(push_dir)
        args = split(f'e4edm push {push_path.as_posix()}')
        with patch('sys.argv', args):
            main()
            mock.push.assert_called_once_with(path=push_path)

def test_add_readme(single_mission: Tuple[Mock, DataManager, Path], test_readme: Path):
    """Tests pushing readmes

    Args:
        single_mission (Tuple[Mock, DataManager, Path]): Test app
    """
    mock, _, _ = single_mission

    args = split(f'e4edm add --readme {test_readme.as_posix()}')
    with patch('sys.argv', args):
        main()
        mock.add.assert_called_once_with(paths=[test_readme], readme=True, destination=None)

def test_commit_readme(single_mission: Tuple[Mock, DataManager, Path], test_readme: Path):
    """Tests pushing readmes

    Args:
        single_mission (Tuple[Mock, DataManager, Path]): Test app
    """
    mock, app, _ = single_mission
    app.add([test_readme], readme=True)
    args = split('e4edm commit --readme')
    with patch('sys.argv', args):
        main()
        mock.commit.assert_called_once_with(readme=True)

def test_duplicate(
        single_mission_data: Tuple[Tuple[Mock, DataManager, Path], Tuple[Path, int, int]]):
    """Tests duplication

    Args:
        test_mock_app (Tuple[Mock, DataManager, Path]): Mock App
        test_data (Tuple[Path, int, int]): Test Data
    """
    single_mission, _ = single_mission_data
    mock, _, _ = single_mission

    with TemporaryDirectory() as temp_dir1, TemporaryDirectory() as temp_dir2:
        target1 = Path(temp_dir1)
        target2 = Path(temp_dir2)
        args = split(f'e4edm duplicate {target1.as_posix()} {target2.as_posix()}')
        with patch('sys.argv', args):
            main()
            mock.duplicate.assert_called_once_with(paths=[target1, target2])

def test_status(test_app: Tuple[Mock, DataManager, Path]):
    """Tests the status command line interface

    Args:
        test_app (Tuple[Mock, DataManager, Path]): Test app
    """
    mock, _,_ = test_app

    args = split('e4edm status')
    with patch('sys.argv', args):
        main()
        mock.status.assert_called_once_with()

def test_list(single_mission: Tuple[Mock, DataManager, Path]):
    """Tests the list command

    Args:
        single_mission (Tuple[Mock, DataManager, Path]): Single mission
    """
    mock, app, _ = single_mission

    mock.list_datasets.return_value = app.list_datasets()
    args = split('e4edm list')
    with patch('sys.argv', args):
        main()
        mock.list_datasets.assert_called_once_with()

def test_inactive_commands(test_app):
    """Tests that inactive environment doesn't break --help
    """
    # pylint: disable=unused-argument
    args = split('e4edm --help')
    with patch('sys.argv', args), pytest.raises(SystemExit):
        main()

def test_activate(single_mission: Tuple[Mock, DataManager, Path]):
    """Tests the activate command

    Args:
        single_mission (Tuple[Mock, DataManager, Path]): Single mission setup
    """
    mock, app, root_dir = single_mission
    app.initialize_dataset(
        date=dt.date(2023, 3, 3),
        project='test_cli_activate',
        location='Location1',
        directory=root_dir
    )
    app.initialize_mission(
        metadata=Metadata(
        timestamp=dt.datetime.fromisoformat('2023-03-03T22:52-08:00'),
        device='device1',
        country='country',
        region='region',
        site='site',
        mission='mission1'
        )
    )

    args = split('e4edm activate "2023.03.Test.San Diego"')
    with patch('sys.argv', args):
        main()
        mock.activate.assert_called_once_with(
            dataset="2023.03.Test.San Diego",
            day=None,
            mission=None,
            root_dir=None,
        )

    app.activate(
        dataset="2023.03.Test.San Diego",
        day=None,
        mission=None,
        root_dir=None,
    )

    args = split('e4edm activate "2023.03.Test.Location1" --day 0 --mission mission1')
    with patch('sys.argv', args):
        main()
        mock.activate.assert_called_with(
            dataset='2023.03.Test.Location1',
            day=0,
            mission='mission1',
            root_dir=None
        )

def test_set_dataset_dir(test_bare_app: Tuple[Mock, DataManager, Path]):
    """Tests setting the dataset directory

    Args:
        test_app (Tuple[Mock, DataManager, Path]): Test application
    """
    mock, _, _ = test_bare_app

    with TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        args = split(f'e4edm config dataset_dir {temp_path.as_posix()}')
        with patch('sys.argv', args):
            main()
            assert mock.dataset_dir == temp_path
