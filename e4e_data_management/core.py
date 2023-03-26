'''Core application logic
'''
from __future__ import annotations

import datetime as dt
import pickle
import re
from pathlib import Path
from shutil import copy2
from typing import Dict, Iterable, List, Optional
import fnmatch
import appdirs

from e4e_data_management.data import Dataset, Mission
from e4e_data_management.metadata import Metadata


class DataManager:
    """Data Manager Application Core
    """
    __CONFIG_NAME = 'config.pkl'
    __VERSION = 2

    dirs = appdirs.AppDirs(
        appname='E4EDataManagement',
        appauthor='Engineers for Exploration'
    )
    def __init__(self, *, app_config_dir: Optional[Path] = None):
        # self.__log = logging.getLogger('DataManager')
        self.config_path = Path(app_config_dir)
        self.active_dataset: Optional[Dataset] = None
        self.active_mission: Optional[Mission] = None
        self.datasets: Dict[str, Dataset] = {}
        self.version = self.__VERSION
        self.dataset_dir = Path(self.dirs.user_data_dir)
        self.save()

    def upgrade(self):
        """Upgrades self to current version
        """
        if self.version < 2:
            self.dataset_dir = Path(self.dirs.user_data_dir)
        self.version = 2

    @classmethod
    def load(cls, *, config_dir: Optional[Path] = None) -> DataManager:
        """Loads the app from the specified config dir

        Args:
            config_dir (Optional[Path], optional): Configuration directory. Defaults to None.

        Returns:
            DataManager: restored application
        """
        try:
            if config_dir is None:
                config_dir = Path(cls.dirs.user_config_dir)
            config_file = config_dir.joinpath(cls.__CONFIG_NAME)
            if not config_file.exists():
                return DataManager(app_config_dir=config_dir)
            with open(config_file, 'rb') as handle:
                loaded = pickle.load(handle)
                if not isinstance(loaded, DataManager):
                    raise RuntimeError('Not a DataManager')
                if loaded.version != cls.__VERSION:
                    loaded.upgrade()
                return loaded
        except Exception: # pylint: disable=broad-except
            return DataManager(app_config_dir=config_dir)

    def save(self) -> None:
        """Saves the app into the specified config dir
        """
        config_file = self.config_path.joinpath(self.__CONFIG_NAME)
        if not config_file.exists():
            config_file.parent.mkdir(parents=True, exist_ok=True)
        with open(config_file, 'wb') as handle:
            pickle.dump(self, handle)

    def initialize_dataset(self, date: dt.date, project: str, location: str, directory: Path):
        """Initializes a new dataset

        Args:
            date (dt.date): Date of expedition
            project (str): Expedition's project
            location (str): Expedition common name
            directory (Path): Path to create dataset in
        """
        dataset_name = f'{date.year:04d}.{date.month:02d}.{project}.{location}'
        dataset_path = directory.joinpath(dataset_name)

        if dataset_name in self.datasets:
            raise RuntimeError('Dataset with that name already exists!')

        self.active_dataset = Dataset(
            root=dataset_path.absolute(),
            day_0=date
        )
        self.active_dataset.create()
        self.active_dataset.save()
        self.datasets[dataset_name] = self.active_dataset
        self.active_mission = None
        self.save()

    def initialize_mission(self,
                           metadata: Metadata) -> None:
        """Initializes a new mission.  This should create the appropriate folder structure and
        open the staging area

        Args:
            metadata (Metadata): Mission metadata
        """
        if self.active_dataset is None:
            raise RuntimeError('Dataset not active')
        mission = self.active_dataset.add_mission(
            metadata=metadata
        )
        self.active_mission = mission
        self.save()

    def status(self) -> str:
        """Generates a status string

        Returns:
            str: Status
        """
        output = ''
        if self.active_dataset:
            name = self.active_dataset.name
            path = self.active_dataset.root.absolute().as_posix()
            output += f'Dataset {name} at {path} activated'
        else:
            output += 'No dataset active'
            return output

        output += '\n'
        if self.active_mission:
            name = self.active_mission.name
            path = self.active_mission.path.absolute().as_posix()
            output += f'Mission {name} at {path} activated'
        else:
            output += 'No mission active'
            return output

        output += '\n'
        if len(self.active_mission.staged_files) > 0:
            output += f'{len(self.active_mission.staged_files)} staged files:\n\t'
            staged_files = ((f"{file.origin_path.as_posix()} -> "
                            f"{file.target_path.relative_to(self.active_mission.path).as_posix()}")
                                  for file in self.active_mission.staged_files)

            output += '\n\t'.join(staged_files)
        if len(self.active_dataset.staged_files) > 0:
            output += f'{len(self.active_dataset.staged_files)} staged dataset files:\n\t'
            output += '\n\t'.join(file.as_posix() for file in self.active_dataset.staged_files)
        return output

    def activate(self,
                 dataset: str,
                 day: Optional[int] = None,
                 mission: Optional[str] = None,
                 *,
                 root_dir: Optional[Path] = None) -> None:
        """This activates the specified dataset and optionally mission.

        If only dataset is specified, day and mission may not be specified, and either init_mission
        or activate must be called before add may be called.

        Day must be specified with mission and dataset.

        We will look in the application database for the dataset.  If root_dir is specified, we will
        assume that the dataset exists in root_dir

        Args:
            dataset (str): Dataset name
            day (Optional[int], optional): Expedition Day Number. Defaults to None.
            mission (Optional[str], optional): Mission name. Defaults to None.
            root_dir (Optional[Path], optional): Optional root directory. Defaults to None.
        """
        if dataset in self.datasets:
            self.active_dataset = self.datasets[dataset]
        else:
            dataset_path = root_dir.joinpath(dataset)
            if not dataset_path.is_dir():
                raise RuntimeError('Unable to find dataset')
            self.active_dataset = Dataset.load(dataset_path)

        if mission:
            if day is None:
                raise RuntimeError('Expedted day parameter')
            name = f'ED-{day:02d} {mission}'
            self.active_mission = self.active_dataset.missions[name]
        else:
            self.active_mission = None

    def add(self, paths: Iterable[Path],
            readme: bool = False,
            destination: Optional[Path] = None) -> None:
        """This adds a file or directory to the staging area.

        Args:
            paths (Iterable[Path]): List of paths to add
            readme (bool, optional): Readme flag. Defaults to False.
            destination (Optional[Path], optional): Directory in the dataset to add paths to.
            Defaults to None.

        Raises:
            RuntimeError: Dataset not active
            RuntimeError: Mission not active
        """
        if self.active_dataset is None:
            raise RuntimeError('Dataset not active')
        if readme:
            # This is a dataset level readme, no need to seek into the mission
            self.active_dataset.stage(paths)
            self.save()
            return
        if self.active_mission is None:
            raise RuntimeError('Mission not active')
        self.active_mission.stage(paths, destination=destination)
        self.save()

    def commit(self, readme: bool = False) -> None:
        """This should copy files and directories in the staging area to the committed area, and
        compute the hashes and sizes.
        """
        if self.active_dataset is None:
            raise RuntimeError('Dataset not active')
        if readme:
            new_files = self.active_dataset.commit()
        else:
            if self.active_mission is None:
                raise RuntimeError('Mission not active')
            new_files = self.active_mission.commit()
        self.active_dataset.manifest.update(new_files)
        self.active_dataset.manifest.update([self.active_mission.manifest.path])
        self.save()

    def duplicate(self, paths: List[Path]) -> None:
        """This will duplicate the active datasets to the provided paths.  We will assume that only
        the active dataset has changed, and the duplicates have not changed.

        Args:
            paths (List[Path]): List of paths to duplicate to
        """
        manifest = self.active_dataset.manifest.get_dict()
        new_files = [[] * len(paths)]
        for file in manifest:
            src_path = self.active_dataset.root.joinpath(file)
            dests = [dest.joinpath(file) for dest in paths]
            for idx, dest in enumerate(dests):
                dest.parent.mkdir(parents=True, exist_ok=True)
                copy2(src=src_path, dst=dest)
                new_files[idx].append(dest)
        for idx, new_file_list in enumerate(new_files):
            self.active_dataset.manifest.validate(
                manifest=manifest,
                files=new_file_list,
                root=paths[idx])
            self.active_dataset.manifest.write(manifest, path=paths[idx].joinpath('manifest.json'))

    def validate(self) -> bool:
        """This will check that the active dataset is valid and coherent
        """
        if self.active_dataset is None:
            raise RuntimeError('Dataset not active')
        if self.active_mission is None:
            raise RuntimeError('Mission not active')
        return self.active_dataset.validate()

    def push(self, path: Path) -> None:
        """This will check that the dataset is complete, verify the dataset, then copy the dataset
        to the specified location

        Args:
            path (Path): Destination to push completed dataset to
        """
        if any(len(mission.staged_files) != 0
               for mission in self.active_dataset.missions.values()) or \
            len(self.active_dataset.staged_files) != 0:
            raise RuntimeError('Files still in staging')

        # Check that the README is present
        readmes = [file
                   for file in list(self.active_dataset.root.glob('*'))
                   if re.match(fnmatch.translate('readme.*'), file.name, re.IGNORECASE)]

        if len(readmes) == 0:
            raise RuntimeError('Readme not found')
        acceptable_exts = ['.md', '.docx']
        if any(readme.suffix.lower() not in acceptable_exts for readme in readmes):
            raise RuntimeError('Illegal README format')

        # validate self
        self.active_dataset.validate()

        # Duplicate to destination
        self.duplicate([path])

    def zip(self, output_path: Path) -> None:
        """This will zip the active and completed dataset to the specified path

        Args:
            output_path (Path): Output path
        """

    def unzip(self, input_file: Path, output_path: Path) -> None:
        """This will unzip the archived dataset to the specified root

        Args:
            input_file (Path): Archived dataset
            output_path (Path): New root
        """

    def list_datasets(self) -> List[str]:
        """Lists the known datasets

        Returns:
            List[str]: List of dataset names
        """
        return list(self.datasets.keys())

    def prune(self) -> None:
        """Prunes missing datasets
        """
        items_to_remove: List[str] = []
        for name, dataset in self.datasets.items():
            if not dataset.root.exists():
                items_to_remove.append(name)
        for remove in items_to_remove:
            self.datasets.pop(remove)
        self.save()
