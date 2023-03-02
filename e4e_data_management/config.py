'''Configuration class
'''
from __future__ import annotations

import pickle
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Optional

import appdirs


@dataclass
class AppConfiguration:
    """Configuration singleton

    Returns:
        Configuration: Application configuration
    """
    config_path: Path
    current_dataset_name: Optional[str] = None
    current_dataset: Optional[Path] = None
    current_mission: Optional[Path] = None
    datasets: Dict[str, Path] = field(default_factory=dict)

    __app_config_instance = None
    @classmethod
    def get_instance(cls, config_dir: Optional[Path] = None) -> AppConfiguration:
        """Retrieves the singleton Configuration instance

        Returns:
            Configuration: Configuration singleton
        """
        # global __app_config_instance # pylint: disable=invalid-name,global-statement
        try:
            if cls.__app_config_instance is None:
                cls.__app_config_instance = cls.__load(config_dir=config_dir)
            if cls.__app_config_instance.config_path != config_dir:
                cls.__app_config_instance = cls.__load(config_dir=config_dir)
        except Exception: # pylint: disable=broad-except
            cls.__app_config_instance = cls.__load()
        return cls.__app_config_instance

    @classmethod
    def __load(cls, *, config_dir: Optional[Path] = None) -> AppConfiguration:
        if config_dir is None:
            config_dir = Path(appdirs.user_config_dir(
                appname='E4EDataManagement',
                appauthor='Engineers for Exploration'
            ))

        config_file = config_dir.joinpath('config.pkl')
        if not config_file.exists():
            return AppConfiguration(config_path=config_dir)
        with open(config_file, 'rb') as handle:
            return pickle.load(handle)

    def save(self) -> None:
        """Saves the configuration to disk
        """
        config_file = self.config_path.joinpath('config.pkl')
        if not config_file.exists():
            config_file.parent.mkdir(parents=True, exist_ok=True)
        with open(config_file, 'wb') as handle:
            pickle.dump(self, handle)

    def add_dataset(self, name: str, path: Path, *, no_check: bool = False) -> None:
        """Convenience function to add a dataset

        Args:
            name (str): Dataset Name
            path (Path): Path to dataset
            no_check (bool, optional): Bypasses the existence check. Defaults to False.

        Raises:
            RuntimeError: If that named dataset already exists
        """
        if not no_check and name in self.datasets:
            raise RuntimeError('Dataset with that name already exists!')
        self.current_dataset_name = name
        self.current_dataset = path
        self.datasets[name] = path

        self.save()
