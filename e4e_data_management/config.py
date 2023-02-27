'''Configuration class
'''
from __future__ import annotations

import pickle
import datetime as dt
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Optional, List

import appdirs

@dataclass
class ExpeditionConfiguration:
    """Expedition configuration parameters

    Returns:
        ExpeditionConfiguration: Configuraton parameters
    """
    root_path: Path
    day_0: dt.date
    last_country: str = ''
    last_region: str = ''
    last_site: str = ''
    countries: List[str] = field(default_factory=list)
    regions: List[str] = field(default_factory=list)
    sites: List[str] = field(default_factory=list)

    @classmethod
    def load(cls, path: Path) -> ExpeditionConfiguration:
        """Loads the configuration from disk

        Args:
            path (Path): Path to expedition root

        Returns:
            ExpeditionConfiguration: Configuration
        """
        config_dir = path

        config_file = config_dir.joinpath('.e4edm.pkl')
        if not config_file.exists():
            config_file.parent.mkdir(parents=True, exist_ok=True)
        with open(config_file, 'rb') as handle:
            return pickle.load(handle)

    def save(self, path: Path) -> None:
        """Saves the configuration to disk
        """
        config_dir = path

        config_file = config_dir.joinpath('.e4edm.pkl')
        if not config_file.exists():
            config_file.parent.mkdir(parents=True, exist_ok=True)
        with open(config_file, 'wb') as handle:
            pickle.dump(self, handle)

@dataclass
class AppConfiguration:
    """Configuration singleton

    Returns:
        Configuration: Application configuration
    """
    current_dataset_name: Optional[str] = None
    current_dataset: Optional[Path] = None
    current_mission: Optional[Path] = None
    datasets: Dict[str, Path] = field(default_factory=dict)

    __app_config_instance = None
    @classmethod
    def get_instance(cls) -> AppConfiguration:
        """Retrieves the singleton Configuration instance

        Returns:
            Configuration: Configuration singleton
        """
        # global __app_config_instance # pylint: disable=invalid-name,global-statement
        if cls.__app_config_instance is None:
            cls.__app_config_instance = cls.__load()
        return cls.__app_config_instance

    @classmethod
    def __load(cls) -> AppConfiguration:
        config_dir = Path(appdirs.user_config_dir(
            appname='E4EDataManagement',
            appauthor='Engineers for Exploration'
        ))

        config_file = config_dir.joinpath('config.pkl')
        if not config_file.exists():
            return AppConfiguration()
        with open(config_file, 'rb') as handle:
            return pickle.load(handle)

    def save(self) -> None:
        """Saves the configuration to disk
        """
        config_dir = Path(appdirs.user_config_dir(
            appname='E4EDataManagement',
            appauthor='Engineers for Exploration'
        ))

        config_file = config_dir.joinpath('config.pkl')
        if not config_file.exists():
            config_file.parent.mkdir(parents=True, exist_ok=True)
        with open(config_file, 'wb') as handle:
            pickle.dump(self, handle)
