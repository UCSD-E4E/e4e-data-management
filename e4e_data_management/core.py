'''Core application logic
'''
import datetime as dt
import json
import logging
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Set

import appdirs

from e4e_data_management._core import (
    PyDataManager as _DataManager,
    PyDataset as _Dataset,
    PyMission as _Mission,
)
from e4e_data_management.data import Manifest as _Manifest


class _MissionView:
    """Thin wrapper around PyMission for Python attribute access"""

    def __init__(self, inner: _Mission):
        self._inner = inner

    @property
    def name(self) -> str:
        return self._inner.name

    @property
    def path(self) -> Path:
        return Path(self._inner.path)

    @property
    def staged_files(self) -> list:
        return self._inner.staged_files

    @property
    def committed_files(self) -> List[str]:
        return self._inner.committed_files

    @property
    def country(self) -> str:
        return self._inner.country

    @property
    def region(self) -> str:
        return self._inner.region

    @property
    def site(self) -> str:
        return self._inner.site

    @property
    def device(self) -> str:
        return self._inner.device

    @property
    def timestamp(self) -> str:
        return self._inner.timestamp


class _DatasetView:
    """Thin wrapper around PyDataset for Python attribute access"""

    def __init__(self, inner: _Dataset):
        self._inner = inner

    @property
    def pushed(self) -> bool:
        return self._inner.pushed

    @property
    def last_country(self) -> Optional[str]:
        return self._inner.last_country

    @property
    def last_region(self) -> Optional[str]:
        return self._inner.last_region

    @property
    def last_site(self) -> Optional[str]:
        return self._inner.last_site

    @property
    def root(self) -> Path:
        return Path(self._inner.root)

    @property
    def name(self) -> str:
        return self._inner.name

    @property
    def staged_files(self) -> List[Path]:
        return [Path(p) for p in self._inner.staged_files]

    @property
    def committed_files(self) -> List[str]:
        return self._inner.committed_files

    @property
    def missions(self) -> Dict[str, _MissionView]:
        return {m.name: _MissionView(m) for m in self._inner.missions}

    @property
    def sites(self) -> Set[str]:
        return {m.site for m in self._inner.missions}

    @property
    def countries(self) -> Set[str]:
        return {m.country for m in self._inner.missions}

    @property
    def regions(self) -> Set[str]:
        return {m.region for m in self._inner.missions}

    @property
    def devices(self) -> Set[str]:
        return {m.device for m in self._inner.missions}

    @property
    def manifest(self) -> _Manifest:
        root = Path(self._inner.root)
        return _Manifest(root / 'manifest.json', root)

    def validate(self) -> bool:
        return self._inner.validate()

    def validate_failures(self) -> List[str]:
        return self._inner.validate_failures()


class DataManager:  # pylint: disable=too-many-public-methods
    dirs = appdirs.AppDirs(
        appname='E4EDataManagement',
        appauthor='Engineers for Exploration'
    )
    config_dir = None

    def __init__(self, *, app_config_dir=None):
        if app_config_dir is None:
            app_config_dir = Path(self.dirs.user_config_dir)
        default_dataset_dir = str(Path(self.dirs.user_data_dir))
        self._inner = _DataManager(str(app_config_dir), default_dataset_dir)
        self._log = logging.getLogger('e4edm.core')

    @classmethod
    def load(cls, *, config_dir=None) -> 'DataManager':
        if config_dir is None:
            config_dir = cls.config_dir or Path(cls.dirs.user_config_dir)
        obj = cls.__new__(cls)
        obj._inner = _DataManager.load(str(config_dir))
        obj._log = logging.getLogger('e4edm.core')
        return obj

    def save(self) -> None:
        self._inner.save()

    @property
    def active_dataset(self) -> Optional[_DatasetView]:
        ds = self._inner.active_dataset
        if ds is None:
            return None
        return _DatasetView(ds)

    @property
    def active_mission(self) -> Optional[_MissionView]:
        m = self._inner.active_mission
        if m is None:
            return None
        return _MissionView(m)

    @property
    def datasets(self) -> Dict[str, _DatasetView]:
        return {name: _DatasetView(ds) for name, ds in self._inner.datasets.items()}

    @property
    def dataset_dir(self) -> Path:
        return Path(self._inner.dataset_dir)

    @dataset_dir.setter
    def dataset_dir(self, value) -> None:
        self._inner.dataset_dir = str(Path(value))

    @property
    def version(self) -> int:
        return self._inner.version

    def initialize_dataset(self, date: dt.date, project: str, location: str,
                           directory: Path) -> None:
        dataset_name = f'{date.strftime("%Y.%m.%d")}.{project}.{location}'
        dataset_path = Path(directory) / dataset_name
        self._log.info('Initializing dataset at %s', dataset_path.as_posix())
        self._inner.initialize_dataset(
            date.isoformat(), project, location, str(directory)
        )

    def initialize_mission(self, metadata) -> None:
        self._inner.initialize_mission(
            timestamp=metadata.timestamp.isoformat(),
            device=metadata.device,
            country=metadata.country,
            region=metadata.region,
            site=metadata.site,
            mission=metadata.mission,
            notes=metadata.notes,
            properties=json.dumps(metadata.properties)
        )

    def status(self) -> str:
        return self._inner.status()

    def activate(self, dataset: str, day=None, mission=None,
                 root_dir=None) -> None:
        self._inner.activate(
            dataset,
            day,
            mission,
            str(root_dir) if root_dir is not None else None
        )

    def add(self, paths: Iterable[Path], readme: bool = False,
            destination=None) -> None:
        self._inner.add(
            [str(p) for p in paths],
            readme,
            str(destination) if destination is not None else None
        )

    def commit(self, readme: bool = False) -> None:
        self._inner.commit(readme)

    def duplicate(self, paths: List[Path]) -> None:
        self._inner.duplicate([str(p) for p in paths])

    def validate(self) -> bool:
        return self._inner.validate()

    def validate_failures(self) -> List[str]:
        return self._inner.validate_failures()

    def push(self, path: Path) -> None:
        self._inner.push(str(path))

    def remove_mission(self, dataset: str, mission: str) -> None:
        self._inner.remove_mission(dataset, mission)

    def zip(self, output_path: Path) -> None:
        self._inner.zip_dataset(str(output_path))

    def prune(self) -> Set[str]:
        return set(self._inner.prune())

    def reset(self) -> None:
        self._inner.reset()

    def list_datasets(self) -> List[str]:
        return self._inner.list_datasets()
