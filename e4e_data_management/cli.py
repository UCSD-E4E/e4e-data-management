'''E4E Data Management Core
'''
import argparse
import datetime as dt
import logging
import logging.handlers
import sys
import time
from dataclasses import dataclass
from glob import glob
from pathlib import Path
from typing import Callable, List, Optional, TypeVar

from rich.progress import (BarColumn, MofNCompleteColumn, Progress,
                           SpinnerColumn, TextColumn, TimeRemainingColumn)
from wakepy import keep

from e4e_data_management import __version__
from e4e_data_management.core import DataManager
from e4e_data_management.metadata import Metadata
from e4e_data_management.data import Dataset
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


class DataManagerCLI:
    """Data Manager Command Line Interface
    """
    def __init__(self):
        self.__configure_logging()
        self._log = logging.getLogger('e4edm.cli')
        self._log.debug('Invoking version %s from %s', __version__, __file__)
        try:
            self.app = DataManager.load()
            commands = [
                'init',
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
                'prune',
                'ls',
                'reset',
                'rm',
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

            self.__configure_init_parser(parsers['init'])
            self.__configure_status_parser(parsers['status'])
            self.__configure_list_parser(parsers['list'])
            self.__configure_add_parser(parsers['add'])
            self.__configure_commit_parser(parsers['commit'])
            self.__configure_duplicate_parser(parsers['duplicate'])
            self.__configure_push_parser(parsers['push'])
            self.__configure_prune_parser(parsers['prune'])
            self.__configure_config_parser(parsers['config'])
            self.__configure_activate_parser(parsers['activate'])
            self.__configure_ls_parser(parsers['ls'])
            self.__configure_validate_parser(parsers['validate'])
            self.__configure_reset_parser(parsers['reset'])
            self.__configure_rm_parser(parsers['rm'])
            # self.__configure_zip_parser(parsers['zip'])
            # self.__configure_unzip_parser(parsers['unzip'])

            self.parser.add_argument('--version', action='version', version=f'e4edm {__version__}')
            self.parser.set_defaults(func=self.parser.print_help)
        except Exception as exc:
            self._log.exception('Exception during application load/configuration')
            raise exc

    def __configure_validate_parser(self, parser: argparse.ArgumentParser):
        parser.add_argument('root_dir', nargs='?', default=None, type=Path)
        parser.set_defaults(func=self.__external_validate)

    def __external_validate(self, root_dir: Optional[Path]):
        with Progress(
            SpinnerColumn(),
            TextColumn('[bold blue]{task.description}'),
            BarColumn(),
            MofNCompleteColumn(),
            TimeRemainingColumn(),
            speed_estimate_period=600,
        ) as progress:
            task = progress.add_task('Validating\u2026', total=None)
            # Parallel callbacks arrive in bursts with identical timestamps, which
            # prevents Rich from computing a rate.  Render at most 10 times per
            # second so samples are spaced in time.
            last_t = [time.monotonic()]
            interval = 0.1

            def on_validate_progress(current: int, total: int) -> None:
                now = time.monotonic()
                if now - last_t[0] >= interval or current == total:
                    last_t[0] = now
                    progress.update(task, completed=current, total=total)

            if root_dir is None:
                failures = self.app.validate_failures_with_progress(on_validate_progress)
            else:
                dataset = Dataset.load(path=root_dir)
                failures = dataset.validate_failures_with_progress(on_validate_progress)

        if failures:
            print('Dataset validation failed:')
            for reason in failures:
                print(f'  {reason}')
        else:
            print('Dataset valid')

    def __configure_logging(self) -> None:
        log_dir = Path(DataManager.dirs.user_log_dir).resolve()
        log_dir.mkdir(parents=True, exist_ok=True)
        log_dest = log_dir.joinpath('e4edm.log')

        root_logger = logging.getLogger()
        root_logger.setLevel(logging.DEBUG)

        log_file_handler = logging.handlers.RotatingFileHandler(log_dest,
                                                                maxBytes=5*1024*1024,
                                                                backupCount=5)
        log_file_handler.setLevel(logging.DEBUG)

        root_formatter = logging.Formatter(('%(asctime)s.%(msecs)03d - %(name)s - %(levelname)s - '
                                           '%(message)s'),
                                           datefmt="%Y-%m-%d %H:%M:%S")
        log_file_handler.setFormatter(root_formatter)
        root_logger.addHandler(log_file_handler)

        logging.Formatter.converter = time.gmtime

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
        for dataset_name, dataset in self.app.datasets.items():
            if dataset.pushed:
                pushed_str = '*'
            else:
                pushed_str = ' '
            print(f'{dataset_name} {pushed_str}')

    def list_missions_cmd(self, dataset: str) -> None:
        """Lists the missions in the specified dataset"""
        datasets = self.app.datasets
        if dataset not in datasets:
            raise RuntimeError(f'Dataset not found: {dataset}')
        for mission_name in datasets[dataset].missions:
            print(mission_name)

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
        if not start:
            start = dt.datetime.min
        if not end:
            end = dt.datetime.max
        if start.tzinfo is None:
            start = start.replace(tzinfo=local_tz)
        if end.tzinfo is None:
            end = end.replace(tzinfo=local_tz)
        if end < start:
            raise RuntimeError('end before start')
        resolved_paths = [path
                        for path in resolved_paths
                        if start <= dt.datetime.fromtimestamp(path.stat().st_mtime, local_tz) \
                              <= end]
        self.app.add(paths=resolved_paths, readme=readme, destination=destination)

    def status_cmd(self):
        """Handles status cmd

        Args:
            app (DataManager): DataManager app
        """
        status_message = self.app.status()
        for line in status_message.splitlines():
            print(line)

    def ls_dir(self, path: Path):
        """Lists the files in the given directory with information relevant to e4edm

        Args:
            path (Path): Path to ls
        """
        local_tz = dt.datetime.now().astimezone().tzinfo
        print(path.as_posix())
        dirs = sorted([node for node in path.glob('*') if node.is_dir()])
        files = sorted([node for node in path.glob('*') if node.is_file()])
        dir_times = [dt.datetime.fromtimestamp(node.stat().st_mtime, local_tz) for node in dirs]
        file_times = [dt.datetime.fromtimestamp(node.stat().st_mtime, local_tz) for node in files]
        for idx, dir_path in enumerate(dirs):
            print(f'{dir_times[idx].isoformat()} {dir_path.name}')
        for idx, file in enumerate(files):
            print(f'{file_times[idx].isoformat()} {file.name}')

    def prune_cmd(self):
        """Prunes old datasets
        """
        pruned_datasets = self.app.prune()
        print('Removed: ')
        for dataset in pruned_datasets:
            print(dataset)

    def main(self):
        """Main function
        """
        try:
            self._log.info("Invoked with %s", ' '.join(sys.argv))
            args = self.parser.parse_args()
            arg_dict = vars(args)

            arg_fn = args.func
            arg_dict.pop('func')

            with keep.running():
                arg_fn(**arg_dict)
        except KeyboardInterrupt:
            sys.exit(130)
        except Exception as exc:
            self._log.exception('Exception during main execution')
            raise exc

    def __configure_ls_parser(self, parser: argparse.ArgumentParser):
        parser.add_argument('path', type=Path, default=Path('.'))
        parser.set_defaults(func=self.ls_dir)

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
        parser.set_defaults(func=self.prune_cmd)

    def push_cmd(self, path: Path) -> None:
        """Push the active dataset to `path` with a rich progress bar."""
        with Progress(
            SpinnerColumn(),
            TextColumn('[bold blue]{task.description}'),
            BarColumn(),
            MofNCompleteColumn(),
            TimeRemainingColumn(),
            speed_estimate_period=600,
        ) as progress:
            push_task = progress.add_task('Pushing\u2026', total=None)
            val_task = progress.add_task('Validating\u2026', total=None, visible=False)
            # Parallel callbacks arrive in bursts with identical timestamps, which
            # prevents Rich from computing a rate.  Count every callback but only
            # render at most 10 times per second so samples are spaced in time.
            counts = [0, 0]   # [push_done, val_done]
            last_t = [time.monotonic()]
            interval = 0.1

            def on_push_progress(current: int, total: int) -> None:
                file_count = total // 2
                now = time.monotonic()
                if current <= file_count:
                    counts[0] += 1
                    if now - last_t[0] >= interval or counts[0] == file_count:
                        last_t[0] = now
                        progress.update(push_task, total=file_count, completed=counts[0])
                else:
                    if not progress.tasks[int(val_task)].visible:
                        progress.update(push_task, visible=False)
                        progress.update(val_task, total=file_count, visible=True)
                        last_t[0] = now
                    counts[1] += 1
                    if now - last_t[0] >= interval or counts[1] == file_count:
                        last_t[0] = now
                        progress.update(val_task, completed=counts[1])

            if not path.exists():
                raise FileNotFoundError(f'Path not found: {path.resolve()}')
            try:
                self.app.push_with_progress(path, on_push_progress)
            except RuntimeError as exc:
                raise RuntimeError(f'Push to {path.resolve()} failed: {exc}') from exc

    def __configure_push_parser(self, parser: argparse.ArgumentParser):
        parser.add_argument('path', type=Path)
        parser.set_defaults(func=self.push_cmd)

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
        subparsers = parser.add_subparsers()
        subparsers.add_parser('dataset').set_defaults(func=self.list_datasets_cmd)
        mission_parser = subparsers.add_parser('mission')
        mission_parser.add_argument('dataset', type=str, help='Dataset name')
        mission_parser.set_defaults(func=self.list_missions_cmd)
        parser.set_defaults(func=parser.print_help)

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

    def __configure_init_parser(self, parser: argparse.ArgumentParser):
        subparsers = parser.add_subparsers()
        self.__configure_init_dataset_parser(subparsers.add_parser('dataset'))
        self.__configure_init_mission_parser(subparsers.add_parser('mission'))
        parser.set_defaults(func=parser.print_help)

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

    def __configure_reset_parser(self, parser: argparse.ArgumentParser):
        parser.set_defaults(func=self.app.reset)

    def rm_mission_cmd(self, mission: str, dataset: Optional[str]) -> None:
        """Remove a mission, defaulting to the active dataset when --dataset is omitted"""
        if dataset is None:
            active = self.app.active_dataset
            if active is None:
                raise RuntimeError('No dataset active and no --dataset specified')
            dataset = active.name
        self.app.remove_mission(dataset=dataset, mission=mission)

    def __configure_rm_parser(self, parser: argparse.ArgumentParser):
        subparsers = parser.add_subparsers()
        mission_parser = subparsers.add_parser('mission')
        mission_parser.add_argument('mission', type=str, help='Mission name')
        mission_parser.add_argument('--dataset', type=str, default=None,
                                    help='Dataset name (defaults to the active dataset)')
        mission_parser.set_defaults(func=self.rm_mission_cmd)
        parser.set_defaults(func=parser.print_help)

def main():
    """Main bootstrap
    """
    DataManagerCLI().main()

if __name__ == '__main__':
    main()
