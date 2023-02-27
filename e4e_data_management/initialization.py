import argparse
import datetime as dt
from pathlib import Path
from typing import List

from e4e_data_management.config import AppConfiguration
from e4e_data_management.validator import Dataset


def init_dataset(args: List[str]) -> None:
    """initialize_dataset command line interface

    Args:
        args (List[str]): Command Line Arguments
    """
    parser = argparse.ArgumentParser(
        prog='e4edm init_dataset'
    )
    parser.add_argument('--date', '-d',
                        help='Date of expedition (YY.MM)',
                        required=True,
                        type=dt.date.fromisoformat)
    parser.add_argument('--project', '-P',
                        help='Project',
                        required=True)
    parser.add_argument('--location', '-l',
                        help='Expedition location (common name)',
                        required=True)
    parser.add_argument('--path', '-p',
                        default=Path('.'),
                        type=Path,
                        help='Dataset location, defaults to current directory')

    args = parser.parse_args(args=args)
    date: dt.date = args.date
    project: str = args.project
    location: str = args.location
    directory: Path = args.path
    initialize_dataset(date, project, location, directory)

def initialize_dataset(date: dt.date, project: str, location: str, directory: Path):
    """Initializes a new dataset

    Args:
        date (dt.date): Date of expedition
        project (str): Expedition's project
        location (str): Expedition common name
        directory (Path): Path to create dataset in
    """
    dataset_path = directory.joinpath(
        f'{date.year}.{date.month}.{project}.{location}')
    dataset_path.mkdir(parents=True, exist_ok=True)

    config = AppConfiguration.get_instance()
    config.current_dataset = dataset_path
    config.save()

    dataset = Dataset(dataset_path)
    dataset.generate_manifest()

def init_mission(args: List[str]) -> None:
    """`init_mission` command line interface

    Args:
        args (List[str]): Arguments
    """
    parser = argparse.ArgumentParser(
        prog='e4edm init_mission'
    )
    parser.add_argument('--timestamp', '-t',
                        help='Mission timestamp',
                        required=True,
                        type=dt.datetime.fromisoformat)
    parser.add_argument('--device', '-d',
                        help='Mission device identifier',
                        required=True,
                        type=str)
    parser.add_argument('--country', '-c',
                        help='Mission country',
                        required=False,
                        default=None)