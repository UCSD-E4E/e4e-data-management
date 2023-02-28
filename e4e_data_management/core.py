'''Core application logic
'''
import datetime as dt
import logging
from pathlib import Path
from typing import Dict, Optional, List

from e4e_data_management.config import (AppConfiguration,
                                        ExpeditionConfiguration)
from e4e_data_management.data import Dataset


class DataManager:
    def __init__(self, *, app_config_dir: Optional[Path] = None):
        self.__log = logging.getLogger('DataManager')
        self.appconfig = AppConfiguration.get_instance(config_dir=app_config_dir)
        self.active_dataset: Optional[Dataset] = None
        self.dataset_config: Optional[ExpeditionConfiguration] = None
        if self.appconfig.current_dataset:
            try:
                self.active_dataset = Dataset(self.appconfig.current_dataset)
                self.dataset_config = ExpeditionConfiguration.load(self.appconfig.current_dataset)
            except Exception: # pylint: disable=broad-except
                self.__log.error('Failed to load dataset %s', self.appconfig.current_dataset_name)
                self.active_dataset = None
                self.dataset_config = None
                self.appconfig.current_dataset = None
                self.appconfig.current_dataset_name = None
                self.appconfig.current_mission = None


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
        dataset_path.mkdir(parents=True, exist_ok=True)

        self.appconfig.current_dataset = dataset_path.absolute()
        self.appconfig.current_dataset_name = dataset_name
        self.appconfig.save()

        self.active_dataset = Dataset(dataset_path.absolute())
        self.active_dataset.generate_manifest()

        expedition_config = ExpeditionConfiguration(
            root_path=dataset_path.absolute(),
            day_0=date
        )
        expedition_config.save(dataset_path)

    def initialize_mission(self,
                           timestamp: dt.datetime,
                           device: str,
                           country: str,
                           region: str,
                           site: str,
                           mission: str,
                           notes: str = '',
                           properties: Optional[Dict] = None) -> None:
        """Initializes a new mission.  This should create the appropriate folder structure and
        open the staging area

        Args:
            timestamp (dt.datetime): Mission timestamp
            device (str): Mission device
            country (str): Mission country
            region (str): Mission region
            site (str): Mission site
            mission (str): Mission name
            notes (str, optional): Mission notes. Defaults to ''.
            properties (Optional[Dict], optional): Additional properties. Defaults to None.
        """
        if self.active_dataset is None:
            raise RuntimeError('Dataset not active')
        expedition_day = (timestamp.date() - self.dataset_config.day_0).days
        day_path = Path(self.dataset_config.root_path, f'ED-{expedition_day:02d}')
        mission_path = day_path.joinpath(mission)

    def status(self) -> str:
        """Generates a status string

        Returns:
            str: Status
        """
        output = ''
        if self.appconfig.current_dataset:
            name = self.appconfig.current_dataset_name
            path = self.appconfig.current_dataset.absolute().as_posix()
            output += f'Dataset {name} at {path} activated'
        else:
            output += 'No dataset active'
            return output
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

    def add(self, paths: List[Path]) -> None:
        """This adds a file or directory to the staging area.

        Args:
            paths (List[Path]): List of paths to add
        """

    def commit(self) -> None:
        """This should copy files and directories in the staging area to the committed area, and
        compute the hashes and sizes.
        """

    def duplicate(self, paths: List[Path]) -> None:
        """This will duplicate the active datasets to the provided paths.  We will assume that only
        the active dataset has changed, and the duplicates have not changed.

        Args:
            paths (List[Path]): List of paths to duplicate to
        """

    def validate(self) -> None:
        """This will check that the active dataset is valid and coherent
        """

    def push(self, path: Path) -> None:
        """This will check that the dataset is complete, verify the dataset, then copy the dataset
        to the specified location

        Args:
            path (Path): Destination to push completed dataset to
        """

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
