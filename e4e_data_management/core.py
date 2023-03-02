'''Core application logic
'''
import datetime as dt
import logging
from pathlib import Path
from typing import Optional, List

from e4e_data_management.config import AppConfiguration
from e4e_data_management.data import Dataset, Mission
from e4e_data_management.metadata import Metadata

class DataManager:
    """Data Manager Application Core
    """
    def __init__(self, *, app_config_dir: Optional[Path] = None):
        self.__log = logging.getLogger('DataManager')
        self.appconfig = AppConfiguration.get_instance(config_dir=app_config_dir)
        self.active_dataset: Optional[Dataset] = None
        if self.appconfig.current_dataset:
            try:
                self.active_dataset = Dataset.load(self.appconfig.current_dataset)
            except Exception: # pylint: disable=broad-except
                self.__log.error('Failed to load dataset %s', self.appconfig.current_dataset_name)
                self.active_dataset = None
                self.appconfig.current_dataset = None
                self.appconfig.current_dataset_name = None
                self.appconfig.current_mission = None
                self.appconfig.save()


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

        self.appconfig.add_dataset(
            name=dataset_name,
            path=dataset_path.absolute()
        )

        self.active_dataset = Dataset(
            root=dataset_path.absolute(),
            day_0=date
        )
        self.active_dataset.create()
        self.active_dataset.save()

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
        self.appconfig.current_mission = mission.path
        self.appconfig.save()

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
        if self.active_dataset is None:
            raise RuntimeError('Dataset not active')

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

    def list_datasets(self) -> List[str]:
        """Lists the known datasets

        Returns:
            List[str]: List of dataset names
        """
        return list(self.appconfig.datasets.keys())

    def prune(self) -> None:
        """Prunes missing datasets
        """
        items_to_remove: List[str] = []
        for name, path in self.appconfig.datasets.items():
            if not path.exists():
                items_to_remove.append(name)
        for remove in items_to_remove:
            self.appconfig.datasets.pop(remove)
        self.appconfig.save()
