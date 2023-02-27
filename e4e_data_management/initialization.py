import argparse
import datetime as dt
from pathlib import Path
from typing import List

from e4e_data_management.core import DataManager

def init_dataset(args: List[str]) -> None:
    """initialize_dataset command line interface

    Args:
        args (List[str]): Command Line Arguments
    """
    app = DataManager()
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
    app.initialize_dataset(
        date=date,
        project=project,
        location=location,
        directory=directory
    )

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
    parser.add_argument('--region', '-r',
                        help='Mission region',
                        required=False,
                        default=None)
    parser.add_argument('--site', '-s',
                        help='Mission site',
                        required=True)
    parser.add_argument('--name', '-n',
                        help='Mission name',
                        required=True)
    parser.add_argument('--message', '-m',
                        help='Mission notes')
    args = parser.parse_args(args=args)
