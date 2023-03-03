'''E4E Data Management Core
'''
import argparse
import datetime as dt
import sys
from pathlib import Path
from typing import Callable, Dict, List

from e4e_data_management.core import DataManager
from e4e_data_management.metadata import Metadata


def init_dataset(args: List[str]) -> None:
    """initialize_dataset command line interface

    Args:
        args (List[str]): Command Line Arguments
    """
    app = DataManager.load()
    parser = argparse.ArgumentParser(
        prog='e4edm init_dataset'
    )
    parser.add_argument('--date', '-d',
                        help='Date of expedition (YY.MM)',
                        required=True,
                        type=dt.date.fromisoformat)
    parser.add_argument('--project', '-p',
                        help='Project',
                        required=True)
    parser.add_argument('--location', '-l',
                        help='Expedition location (common name)',
                        required=True)
    parser.add_argument('--path',
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
    app = DataManager.load()

    if app.active_dataset is None:
        print('No dataset active!')
        return

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
    if app.active_dataset.last_country:
        parser.add_argument('--country', '-c',
                            help='Mission country',
                            required=False,
                            default=app.active_dataset.last_country)
    else:
        parser.add_argument('--country', '-c',
                            help='Mission country',
                            required=True)

    if app.active_dataset.last_region:
        parser.add_argument('--region', '-r',
                            help='Mission region',
                            required=False,
                            default=app.active_dataset.last_region)
    else:
        parser.add_argument('--region', '-r',
                            help='Mission region',
                            required=True)

    if app.active_dataset.last_site:
        parser.add_argument('--site', '-s',
                            help='Mission site',
                            required=False,
                            default=app.active_dataset.last_site)
    else:
        parser.add_argument('--site', '-s',
                            help='Mission site',
                            required=True)

    parser.add_argument('--name', '-n',
                        help='Mission name',
                        required=True)
    parser.add_argument('--message', '-m',
                        help='Mission notes')
    args = parser.parse_args(args=args)

    metadata = Metadata(
        timestamp=args.timestamp,
        device=args.device,
        country=args.country,
        region=args.region,
        site=args.site,
        mission=args.name,
        notes=args.message
    )
    app.initialize_mission(
        metadata=metadata
    )


def print_help():
    """Prints the top level help
    """

def status(args: List[str]) -> None:
    """Prints the current status

    Args:
        args (List[str]): Arguments
    """
    if len(args) != 0:
        print_help()
        return
    print(DataManager.load().status())

def list_datasets(args: List[str]) -> None:
    """Lists the known datasets

    Args:
        args (List[str]): Arguments
    """
    if len(args) != 0:
        print_help()
        return
    datasets = DataManager.load().list_datasets()
    if len(datasets) == 0:
        print('No datasets found')
    else:
        for dataset in datasets:
            print(dataset)

def prune_datasets(args: List[str]):
    """Prunes missing datasets

    Args:
        args (List[str]): Arguments
    """
    if len(args) != 0:
        print_help()
        return
    DataManager.load().prune()

def add_files(args: List[str]):
    """Adds paths to the staging area

    Args:
        args (List[str]): Arguments
    """
    app = DataManager.load()
    parser = argparse.ArgumentParser(
        prog='e4edm add'
    )
    parser.add_argument(
        'paths',
        nargs='+',
        type=Path
    )

    args = parser.parse_args(args=args)
    paths: List[Path] = args.paths
    app.add(paths=paths)

def commit_files(args: List[str]) -> None:
    """Commits files to mission

    Args:
        args (List[str]): args
    """
    app = DataManager.load()
    if len(args) != 0:
        print_help()
        return
    app.commit()

def push(args: List[str]) -> None:
    """Pushes files to a destination

    Args:
        args (List[str]): args
    """
    app = DataManager.load()
    parser = argparse.ArgumentParser('e4edm push')
    parser.add_argument('dest', type=Path)
    args = parser.parse_args(args)
    app.push(path=args.dest)

def duplicate(args: List[str]):
    """Duplication command

    Args:
        args (List[str]): Arguments
    """
    app = DataManager.load()
    parser = argparse.ArgumentParser(
        prog='e4edm duplicate'
    )
    parser.add_argument(
        'paths',
        nargs='+',
        type=Path
    )

    args = parser.parse_args(args=args)
    paths: List[Path] = args.paths
    app.duplicate(paths=paths)

def main():
    """Main function
    """
    command_map: Dict[str, Callable[[List[str]], None]] = {
        'init_dataset': init_dataset,
        'init_mission': init_mission,
        'status': status,
        'list': list_datasets,
        'config': None,
        'activate': None,
        'add': add_files,
        'commit': commit_files,
        'duplicate': duplicate,
        'validate': None,
        'push': push,
        'zip': None,
        'unzip': None,
        'prune': prune_datasets,
    }
    args = sys.argv
    if args[1] not in command_map:
        print_help()
        return
    app_fn = command_map[args[1]]
    app_fn(args[2:])

if __name__ == '__main__':
    main()
