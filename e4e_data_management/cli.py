'''E4E Data Management Core
'''
import argparse
import datetime as dt
from glob import glob
from pathlib import Path
from typing import List, Optional
from e4e_data_management.core import DataManager
from e4e_data_management.metadata import Metadata


def init_mission_cmd(**kwargs) -> None:
    """`init_mission` command line interface

    Args:
        args (List[str]): Arguments
    """
    app: DataManager = kwargs['app']
    kwargs.pop('app')

    metadata = Metadata(
        **kwargs
    )
    app.initialize_mission(
        metadata=metadata
    )

def list_datasets_cmd(app: DataManager) -> None:
    """Lists the known datasets

    Args:
        args (List[str]): Arguments
    """
    datasets = app.list_datasets()
    if len(datasets) == 0:
        print('No datasets found')
    else:
        for dataset in datasets:
            print(dataset)

def add_files_cmd(app: DataManager,
                  paths: List[str], readme: bool,
                  start: Optional[dt.datetime] = None,
                  end: Optional[dt.datetime] = None):
    """Add files parsing

    Args:
        app (DataManager): App
        paths (List[str]): Paths
    """
    resolved_paths: List[Path] = []
    for path in paths:
        resolved_paths.extend(Path(file) for file in glob(path))
    if start:
        resolved_paths = [path
                          for path in resolved_paths
                          if dt.datetime.fromtimestamp(path.stat().st_mtime) >= start]
    if end:
        resolved_paths = [path
                          for path in resolved_paths
                          if dt.datetime.fromtimestamp(path.stat().st_mtime) <= end]
    app.add(paths=resolved_paths, readme=readme)

def main():
    """Main function
    """
    commands = [
        'init_dataset',
        'init_mission',
        'status',
        'list',
        'config',
        'activate',
        'add',
        'commit',
        'duplicate',
        'validate',
        'push',
        'zip',
        'unzip',
        'prune'
    ]
    app = DataManager.load()
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()
    parsers = {cmd:subparsers.add_parser(cmd) for cmd in commands}

    __configure_init_dataset_parser(app, parsers['init_dataset'])
    __configure_init_mission_parser(app, parsers['init_mission'])
    __configure_status_parser(app, parsers['status'])
    __configure_list_parser(app, parsers['list'])
    __configure_add_parser(app, parsers['add'])
    __configure_commit_parser(app, parsers['commit'])
    __configure_duplicate_parser(app, parsers['duplicate'])
    __configure_push_parser(app, parsers['push'])
    __configure_prune_parser(app, parsers['prune'])
    # __configure_config_parser(app, parsers['config'])
    # __configure_activate_parser(app, parsers['activate'])
    # __configure_validate_parser(app, parsers['validate'])
    # __configure_zip_parser(app, parsers['zip'])
    # __configure_unzip_parser(app, parsers['unzip'])

    args = parser.parse_args()
    arg_fn = args.func
    arg_dict = vars(args)
    arg_dict.pop('func')
    arg_fn(**arg_dict)

def __configure_prune_parser(app: DataManager, parser: argparse.ArgumentParser):
    parser.set_defaults(func=app.prune)

def __configure_push_parser(app: DataManager, parser: argparse.ArgumentParser):
    parser.add_argument('path', type=Path)
    parser.set_defaults(func=app.push)

def __configure_duplicate_parser(app: DataManager, parser: argparse.ArgumentParser):
    parser.add_argument('paths', nargs='+', type=Path)
    parser.set_defaults(func=app.duplicate)

def __configure_commit_parser(app: DataManager, parser: argparse.ArgumentParser):
    parser.add_argument('--readme', action='store_true')
    parser.set_defaults(func=app.commit)

def __configure_add_parser(app: DataManager, parser: argparse.ArgumentParser):
    parser.add_argument('paths', nargs='+', type=str)
    parser.add_argument('--readme', action='store_true')
    parser.add_argument('--start', default=None, type=dt.datetime.fromisoformat)
    parser.add_argument('--end', default=None, type=dt.datetime.fromisoformat)
    parser.set_defaults(func=add_files_cmd, app=app)

def __configure_list_parser(app: DataManager, parser: argparse.ArgumentParser):
    parser.set_defaults(func=list_datasets_cmd, app=app)

def __configure_status_parser(app: DataManager, parser: argparse.ArgumentParser):
    parser.set_defaults(func=app.status)

def __configure_init_mission_parser(app: DataManager, parser: argparse.ArgumentParser):
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
                        required=True,
                        dest='mission')
    parser.add_argument('--message', '-m',
                        help='Mission notes',
                        default='',
                        dest='notes')
    parser.set_defaults(func=init_mission_cmd, app=app)

def __configure_init_dataset_parser(app: DataManager, parser: argparse.ArgumentParser):
    parser.add_argument(
        '--date', '-d',
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
                        help='Dataset location, defaults to current directory',
                        dest='directory')
    parser.set_defaults(func=app.initialize_dataset)

if __name__ == '__main__':
    main()
