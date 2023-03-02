'''Data classes
'''
from __future__ import annotations

import datetime as dt
import json
import pickle
from hashlib import sha256
from pathlib import Path
from typing import (Callable, Dict, Generator, Iterable, List, Optional, Set,
                    Union)

from e4e_data_management.metadata import Metadata


class Manifest:
    """Manifest of files
    """
    def __init__(self, path: Path, root: Optional[Path] = None):
        self.__path = path
        if root is None:
            root = path.parent
        self.__root = root

    def validate(self,
                 manifest: Dict[str, Dict[str, Union[str, int]]],
                 files: Iterable[Path],
                 *,
                 method: str = 'hash') -> bool:
        """Validates the files against the specified manifest

        Args:
            manifest (Dict[str, Dict[str, Union[str, int]]]): Manifest to verify against
            files (Iterable[Path]): Files to verify
            method (str, optional): Verification method. Defaults to 'hash'.

        Raises:
            NotImplementedError: Unsupported verification method

        Returns:
            bool: True if valid, otherwise False
        """
        for file in files:
            file_key = file.relative_to(self.__root)
            if file_key not in manifest:
                return False
            if method == 'hash':
                computed_hash = self.__hash(file)
                if computed_hash != manifest[file_key]['sha256sum']:
                    return False
            elif method == 'size':
                computed_size = file.lstat().st_size
                if computed_size != manifest[file_key]['size']:
                    return False
            else:
                raise NotImplementedError(method)
        return True

    def get_dict(self) -> Dict[str, Dict[str, Union[str, int]]]:
        """Retrieves the dictionary of files and checksums

        Returns:
            Dict[str, Dict[str, Union[str, int]]]: Dictionary of files, checksums and sizes
        """
        with open(self.__path, 'r', encoding='ascii') as handle:
            return json.load(handle)

    def generate(self, files: Iterable[Path]):
        """Generates the manifest with only the specified files

        Args:
            files (Iterable[Path]): Files to make manifest to
        """
        data = self.__compute_hashes(
            root=self.__root,
            files=files
        )
        self.__write(data)

    def __write(self, data: Dict[str, Dict[str, Union[str, int]]]) -> None:
        with open(self.__path, 'w', encoding='ascii') as handle:
            json.dump(data, handle, indent=4)

    def update(self, files: Iterable[Path]):
        """Updates the manifest with the specified files

        Args:
            files (Iterable[Path]): Iterable of new files
        """
        data = self.get_dict()
        files_to_checksum = (file
                             for file in files
                             if file.relative_to(self.__root).as_posix() not in data)
        new_checksums = self.__compute_hashes(
            root=self.__root,
            files=files_to_checksum
        )
        data.update(new_checksums)
        self.__write(data)

    def __compute_hashes(self,
                         root: Path,
                         files: Iterable[Path],
                         hash_fn: Optional[Callable[[Path], str]] = None
                         ) -> Dict[str, Dict[str, Union[str, int]]]:
        if not hash_fn:
            hash_fn = self.__hash
        data: Dict[str, Dict[str, Union[str, int]]] = {}
        for file in files:
            rel_path = file.relative_to(root).as_posix()
            cksum = hash_fn(file)
            file_size = file.lstat().st_size
            data[rel_path] = {
                'sha256sum': cksum,
                'size': file_size
            }

        return data

    @classmethod
    def __hash(cls, file: Path):
        cksum = sha256()
        with open(file, 'rb') as handle:
            for byte_block in iter(lambda: handle.read(4096), b''):
                cksum.update(byte_block)
        return cksum.hexdigest()


class Mission:
    """Mission class
    """
    __MANIFEST_NAME = 'manifest.json'
    def __init__(self, path: Path, mission_metadata: Metadata) -> None:
        self.path = path
        self.metadata = mission_metadata
        self.committed_files: List[Path] = []
        self.staged_files: List[Path] = []
        self.manifest = Manifest(self.path.joinpath(self.__MANIFEST_NAME))

    def create(self) -> None:
        """Creates the initial folder and file structure
        """
        self.path.mkdir(parents=True, exist_ok=False)
        self.metadata.write(self.path)
        self.manifest.generate(self.get_files())

    def get_files(self) -> Generator[Path, None, None]:
        """Yields all of the files in this Mission

        Yields:
            Generator[Path, None, None]: Files
        """
        exclude = [
            self.path.joinpath(self.__MANIFEST_NAME),
        ]
        for file in self.path.rglob('*'):
            if file in exclude:
                continue
            if not file.is_file():
                continue
            yield file

    @classmethod
    def load(cls, path: Path) -> Mission:
        """Loads mission from disk

        Args:
            path (Path): Path to mission folder

        Returns:
            Mission: Mission object
        """
        metadata = Metadata.load(path)
        return Mission(path=path, mission_metadata=metadata)

class Dataset:
    """Dataset
    """
    # pylint: disable=too-many-instance-attributes

    __MANIFEST_NAME = 'manifest.json'
    __CONFIG_NAME = '.e4edm.pkl'

    def __init__(self, root: Path, day_0: dt.date):
        self.root = root
        self.day_0: dt.date = day_0
        self.last_country: Optional[str] = None
        self.last_region: Optional[str] = None
        self.last_site: Optional[str] = None
        self.countries: Set[str] = set()
        self.regions: Set[str] = set()
        self.sites: Set[str] = set()
        self.devices: Set[str] = set()
        self.missions: List[Mission] = []
        self.manifest = Manifest(self.root.joinpath(self.__MANIFEST_NAME))

    @classmethod
    def load(cls, path: Path) -> Dataset:
        """Loads the dataset from disk

        Args:
            path (Path): Path to expedition root

        Returns:
            Dataset: Dataset
        """
        config_file = path.joinpath(cls.__CONFIG_NAME)
        if config_file.exists():
            with open(config_file, 'rb') as handle:
                return pickle.load(handle)
        else:
            metadata_files = list(path.rglob('metadata.json'))
            if len(metadata_files) == 0:
                raise RuntimeError('No config file and no data!')
            metadata_file = metadata_files[0].relative_to(path)
            metadata = Metadata.load(metadata_files[0].parent)
            mission_date = metadata.timestamp.date()
            if metadata_file.parts[0].startswith('ED'):
                # This is a dataset that contains multiple days
                mission_day = int(metadata_file.parts[0][3:])
                day_0 = mission_date - dt.timedelta(days=mission_day)
            else:
                day_0 = mission_date
            return Dataset(path, day_0=day_0)

    def save(self, *, path: Optional[Path] = None):
        """Saves the dataset parameters

        Args:
            path (Optional[Path], optional): Path to dataset. Defaults to None.
        """
        if not path:
            path = self.root
        config_file = path.joinpath(self.__CONFIG_NAME)
        if not config_file.exists():
            config_file.parent.mkdir(parents=True, exist_ok=True)
        with open(config_file, 'wb') as handle:
            pickle.dump(self, handle)

    def get_files(self) -> Generator[Path, None, None]:
        """Yields all of the files in this dataset

        Yields:
            Generator[Path, None, None]: Files
        """
        exclude = [
            self.root.joinpath(self.__MANIFEST_NAME),
            self.root.joinpath(self.__CONFIG_NAME)
        ]
        for file in self.root.rglob('*'):
            if file in exclude:
                continue
            if not file.is_file():
                continue
            yield file

    def get_new_files(self) -> Generator[Path, None, None]:
        """Gets all of the new files in this dataset

        Yields:
            Generator[Path, None, None]: New files
        """
        old_files = self.manifest.get_dict().keys()
        return (file for file in self.get_files() if file not in old_files)

    def add_mission(self, metadata: Metadata) -> Mission:
        """Adds a new mission with the specified metadata

        Args:
            metadata (Metadata): Mission metadata
        """
        expedition_day = (metadata.timestamp.date() - self.day_0).days
        day_path = Path(self.root, f'ED-{expedition_day:02d}')
        mission = Mission(
            path=day_path.joinpath(metadata.mission),
            mission_metadata=metadata
        )
        mission.create()
        self.missions.append(mission)
        self.manifest.update(self.get_new_files())

        self.countries.add(metadata.country)
        self.last_country = metadata.country
        self.regions.add(metadata.region)
        self.last_region = metadata.region
        self.sites.add(metadata.site)
        self.last_site = metadata.site
        self.devices.add(metadata.device)
        self.save()

        return mission

    def create(self) -> None:
        """Creates the folder and file structure
        """
        self.root.mkdir(parents=True, exist_ok=False)
        self.manifest.generate(self.get_files())

    @property
    def name(self) -> str:
        """Returns this dataset's name

        Returns:
            str: Dataset name
        """
        return self.root.name