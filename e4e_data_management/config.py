'''Configuration class
'''
from __future__ import annotations

import pickle
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import appdirs

__app_config_instance: AppConfiguration = None
@dataclass
class AppConfiguration:
    """Configuration singleton

    Returns:
        Configuration: Application configuration
    """
    current_dataset: Optional[Path] = None

    @classmethod
    def get_instance(cls) -> AppConfiguration:
        """Retrieves the singleton Configuration instance

        Returns:
            Configuration: Configuration singleton
        """
        global __app_config_instance # pylint: disable=invalid-name,global-statement
        if __app_config_instance is None:
            __app_config_instance = cls.__load()
        return __app_config_instance

    @classmethod
    def __load(cls) -> AppConfiguration:
        config_dir = Path(appdirs.user_config_dir(
            appname='E4EDataManagement',
            appauthor='Engineers for Exploration'
        ))

        config_file = config_dir.joinpath('config.pkl')
        if not config_file.exists():
            config_file.parent.mkdir(parents=True, exist_ok=True)
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
