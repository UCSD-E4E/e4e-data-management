'''E4E Data Management Core
'''
import argparse
import datetime as dt
from dataclasses import dataclass
from glob import glob
from pathlib import Path
from typing import Callable, List, Optional, TypeVar

from e4e_data_management import __version__
from e4e_data_management.core import DataManager
from e4e_data_management.metadata import Metadata

T = TypeVar('T')
@dataclass
class Parameter:
    """Command Line Parameters
    """
    name: str
    getter: Callable[[None], T]
    setter: Callable[[T], None]
    parser: Callable[[str], T]
    formatter: Callable[[T], str]
    validator: Callable[[T], bool]


class DataMangerCLI:
    """Data Manager Command Line Interface
    """
    def __init__(self):
        self.app = DataManager.load()
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
        self.parameters = [
            Parameter(
            name='dataset_dir',
            getter=lambda: getattr(self.app, 'dataset_dir'),
            setter=lambda x: setattr(self.app, 'dataset_dir', x),
            parser=Path,
            formatter=Path.as_posix,
            validator=Path.is_dir
            ),
            Parameter(
            name='version',
            getter=lambda: getattr(self.app, 'version'),
            setter=None,
            parser=int,
            formatter=str,
            validator=None
            )
        ]
        self.parser = argparse.ArgumentParser()
        subparsers = self.parser.add_subparsers()
        parsers = {cmd:subparsers.add_parser(cmd) for cmd in commands}

        self.__configure_init_dataset_parser(parsers['init_dataset'])
        self.__configure_init_mission_parser(parsers['init_mission'])
        self.__configure_status_parser(parsers['status'])
        self.__configure_list_parser(parsers['list'])
        self.__configure_add_parser(parsers['add'])
        self.__configure_commit_parser(parsers['commit'])
        self.__configure_duplicate_parser(parsers['duplicate'])
        self.__configure_push_parser(parsers['push'])
        self.__configure_prune_parser(parsers['prune'])
        self.__configure_config_parser(parsers['config'])
        self.__configure_activate_parser(parsers['activate'])
        # self.__configure_validate_parser(parsers['validate'])
        # self.__configure_zip_parser(parsers['zip'])
        # self.__configure_unzip_parser(parsers['unzip'])

        self.parser.add_argument('--version', action='version', version=f'e4edm {__version__}')
        self.parser.set_defaults(func=self.parser.print_help)


    def configure_parameters(self, parameter: str, value: Optional[str]) -> None:
        """Configures or prints the specified parameter

        Args:
            parameter (str): Parameter name
            value (Optional[str]): Parameter value, or none to print the current value
        """
        parameter_map = {param.name:param for param in self.parameters}
        if parameter not in parameter_map:
            raise RuntimeError('Unrecognized parameter')
        param = parameter_map[parameter]
        if value is None:
            print(param.formatter(param.getter()))
        else:
            param_value = param.parser(value)
            if not param.validator(param_value):
                raise RuntimeError(f'Failed to set value {param_value} due to {param.validator} '
                                   'error')
            param.setter(param_value)
            self.app.save()

    def init_dataset_fromisoformat(self, token: str) -> dt.date:
        """Provides a `today` bypass for fromisoformat

        Args:
            token (str): User input token

        Returns:
            dt.date: Date object
        """
        if token.lower() == 'today':
            return dt.date.today()
        return dt.date.fromisoformat(token)

    def init_mission_cmd(self, **kwargs) -> None:
        """`init_mission` command line interface

        Args:
            args (List[str]): Arguments
        """
        metadata = Metadata(
            **kwargs
        )
        self.app.initialize_mission(
            metadata=metadata
        )

    def list_datasets_cmd(self) -> None:
        """Lists the known datasets

        Args:
            args (List[str]): Arguments
        """
        datasets = self.app.list_datasets()
        if len(datasets) == 0:
            print('No datasets found')
        else:
            for dataset in datasets:
                print(dataset)

    def add_files_cmd(self,
                    paths: List[str],
                    readme: bool,
                    start: Optional[dt.datetime] = None,
                    end: Optional[dt.datetime] = None,
                    destination: Optional[Path] = None):
        """Add files parsing

        Any timestamps passed if timezone-naive will be assumed to be using the local timezone

        Args:
            paths (List[str]): Paths to add
            readme (bool): Readme flag
            start (Optional[dt.datetime], optional): Earliest timestamp to stage. Defaults to None.
            end (Optional[dt.datetime], optional): Latest timestamp to stage. Defaults to None.
            destination (Optional[Path], optional): Destination directory within the dataset.
            Defaults to None.
        """
        # pylint: disable=too-many-arguments
        # `add_files_cmd` reflects the complexity/flexibility of the `e4edm add` command
        local_tz = dt.datetime.now().astimezone().tzinfo
        resolved_paths: List[Path] = []
        for path in paths:
            resolved_paths.extend(Path(file) for file in glob(path))
        if start:
            if start.tzinfo is None:
                start = start.replace(tzinfo=local_tz)
            resolved_paths = [path
                            for path in resolved_paths
                            if dt.datetime.fromtimestamp(path.stat().st_mtime, local_tz) >= start]
        if end:
            if end.tzinfo is None:
                end = end.replace(tzinfo=local_tz)
            resolved_paths = [path
                            for path in resolved_paths
                            if dt.datetime.fromtimestamp(path.stat().st_mtime, local_tz) <= end]
        self.app.add(paths=resolved_paths, readme=readme, destination=destination)

    def status_cmd(self):
        """Handles status cmd

        Args:
            app (DataManager): DataManager app
        """
        print(self.app.status())

    def main(self):
        """Main function
        """
        args = self.parser.parse_args()
        arg_dict = vars(args)

        arg_fn = args.func
        arg_dict.pop('func')

        arg_fn(**arg_dict)

    def __configure_config_parser(self, parser: argparse.ArgumentParser):
        parser.add_argument('parameter',
                            type=str,
                            help='Parameter name',
                            choices=[param.name for param in self.parameters])
        parser.add_argument('value',
                            type=str,
                            help='Parameter value',
                            default=None,
                            nargs='?')
        parser.set_defaults(func=self.configure_parameters)

    def __configure_activate_parser(self, parser: argparse.ArgumentParser):
        parser.add_argument('dataset',
                            type=str,
                            help='Dataset name')
        parser.add_argument('--day',
                            type=int,
                            help='Mission day',
                            default=None,
                            required=False)
        parser.add_argument('--mission',
                            type=str,
                            help='Mission name',
                            default=None,
                            required=False)
        parser.add_argument('--root_dir',
                            type=Path,
                            help='Dataset location',
                            required=False,
                            default=None)
        parser.set_defaults(func=self.app.activate)

    def __configure_prune_parser(self, parser: argparse.ArgumentParser):
        parser.set_defaults(func=self.app.prune)

    def __configure_push_parser(self, parser: argparse.ArgumentParser):
        parser.add_argument('path', type=Path)
        parser.set_defaults(func=self.app.push)

    def __configure_duplicate_parser(self, parser: argparse.ArgumentParser):
        parser.add_argument('paths', nargs='+', type=Path)
        parser.set_defaults(func=self.app.duplicate)

    def __configure_commit_parser(self, parser: argparse.ArgumentParser):
        parser.add_argument('--readme', action='store_true')
        parser.set_defaults(func=self.app.commit)

    def __configure_add_parser(self, parser: argparse.ArgumentParser):
        parser.add_argument('paths', nargs='+', type=str)
        parser.add_argument('--readme', action='store_true')
        parser.add_argument('--start', default=None, type=dt.datetime.fromisoformat)
        parser.add_argument('--end', default=None, type=dt.datetime.fromisoformat)
        parser.add_argument('--destination', default=None, type=Path)
        parser.set_defaults(func=self.add_files_cmd)

    def __configure_list_parser(self, parser: argparse.ArgumentParser):
        parser.set_defaults(func=self.list_datasets_cmd)

    def __configure_status_parser(self, parser: argparse.ArgumentParser):
        parser.set_defaults(func=self.status_cmd)

    def __configure_init_mission_parser(self, parser: argparse.ArgumentParser):
        parser.add_argument('--timestamp', '-t',
                                            help=('ISO 8601 Mission timestamp, '
                                                  'YYYY-MM-DDThh:mm:ss\u00B1hh:mm'),
                                            required=True,
                                            type=dt.datetime.fromisoformat)
        parser.add_argument('--device', '-d',
                            help='Mission device identifier',
                            required=True,
                            type=str)
        if self.app.active_dataset and self.app.active_dataset.last_country:
            parser.add_argument('--country', '-c',
                                help='Mission country',
                                required=False,
                                default=self.app.active_dataset.last_country)
        else:
            parser.add_argument('--country', '-c',
                                help='Mission country',
                                required=True)
        if self.app.active_dataset and self.app.active_dataset.last_region:
            parser.add_argument('--region', '-r',
                                help='Mission region',
                                required=False,
                                default=self.app.active_dataset.last_region)
        else:
            parser.add_argument('--region', '-r',
                                help='Mission region',
                                required=True)
        if self.app.active_dataset and self.app.active_dataset.last_site:
            parser.add_argument('--site', '-s',
                                help='Mission site',
                                required=False,
                                default=self.app.active_dataset.last_site)
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
        parser.set_defaults(func=self.init_mission_cmd)

    def __configure_init_dataset_parser(self, parser: argparse.ArgumentParser):
        parser.add_argument(
            '--date', '-d',
            help='ISO 8601 Date of expedition (YYYY-MM-DD) or "today"',
            required=True,
            type=self.init_dataset_fromisoformat)
        parser.add_argument('--project', '-p',
                            help='Project',
                            required=True)
        parser.add_argument('--location', '-l',
                            help='Expedition location (common name)',
                            required=True)
        data_dir = Path(self.app.dataset_dir)
        parser.add_argument('--path',
                            default=data_dir,
                            type=Path,
                            help=f'Dataset location, defaults to {data_dir.as_posix()}',
                            dest='directory')
        parser.set_defaults(func=self.app.initialize_dataset)

def main():
    """Main bootstrap
    """
    DataMangerCLI().main()

if __name__ == '__main__':
    main()
