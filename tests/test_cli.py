'''Tests the CLI
'''
import datetime as dt
from pathlib import Path
from shlex import split
from tempfile import TemporaryDirectory
from time import sleep
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

def test_init_mission(test_app: Tuple[Mock, DataManager, Path]):
    """Tests init_mission
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
        mock.add.assert_called_once_with(paths=bin_files, readme=False)

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
        mock.add.assert_called_once_with(paths=[], readme=False)

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
        mock.add.assert_called_once_with(paths=bin_files, readme=False)
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
        mock.add.assert_called_once_with(paths=list(data_dir.glob('*.bin')), readme=False)

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
        mock.add.assert_called_once_with(paths=[file1, file2], readme=False)

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
        mock.add.assert_called_once_with(paths=[test_readme], readme=True)

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
