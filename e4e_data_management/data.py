'''Data classes
'''
from __future__ import annotations

import datetime as dt
import json
import logging
import pickle
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from shutil import copy2
from typing import (Callable, Dict, Generator, Iterable, List, Optional, Set,
                    Union)

from e4e_data_management.metadata import Metadata


@dataclass
class StagedFile:
    """Staged File data type

    """
    origin_path: Path
    target_path: Path
    hash: str

    def __hash__(self) -> int:
        return hash((self.origin_path, self.target_path, self.hash))

class Manifest:
    """Manifest of files
    """
    def __init__(self, path: Path, root: Optional[Path] = None):
        self.path = path
        if root is None:
            root = path.parent
        self.__root = root.resolve()

    def validate(self,
                 manifest: Dict[str, Dict[str, Union[str, int]]],
                 files: Iterable[Path],
                 *,
                 method: str = 'hash',
                 root: Optional[Path] = None) -> bool:
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
        if root is None:
            root = self.__root
        for file in files:
            file_key = file.relative_to(root).as_posix()
            if file_key not in manifest:
                return False
            if method == 'hash':
                computed_hash = self.compute_file_hash(file)
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
        with open(self.path, 'r', encoding='ascii') as handle:
            return json.load(handle)

    def generate(self, files: Iterable[Path]):
        """Generates the manifest with only the specified files

        Args:
            files (Iterable[Path]): Files to make manifest to
        """
        data = self.compute_hashes(
            root=self.__root,
            files=files
        )
        self.write(data)

    def write(self,
              data: Dict[str, Dict[str, Union[str, int]]],
              *,
              path: Optional[Path] = None) -> None:
        """Writes the manifest to disk

        Args:
            data (Dict[str, Dict[str, Union[str, int]]]): Manifest data
            path (Optional[Path], optional): Manifest file path. Defaults to None.
        """
        if path is None:
            path = self.path
        with open(path, 'w', encoding='ascii') as handle:
            json.dump(data, handle, indent=4)

    def update(self, files: Iterable[Path]):
        """Updates the manifest with the specified files

        Args:
            files (Iterable[Path]): Iterable of new files
        """
        data = self.get_dict()
        files_to_checksum = (file
                             for file in files)
        new_checksums = self.compute_hashes(
            root=self.__root,
            files=files_to_checksum
        )
        data.update(new_checksums)
        self.write(data)

    def compute_hashes(self,
                         root: Path,
                         files: Iterable[Path],
                         hash_fn: Optional[Callable[[Path], str]] = None
                         ) -> Dict[str, Dict[str, Union[str, int]]]:
        """Computes the hashes

        Args:
            root (Path): Root directory
            files (Iterable[Path]): Files to analyze
            hash_fn (Optional[Callable[[Path], str]], optional): Hash Function. Defaults to None.

        Returns:
            Dict[str, Dict[str, Union[str, int]]]: Hash results
        """
        if not hash_fn:
            hash_fn = self.compute_file_hash
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
    def compute_file_hash(cls, file: Path) -> str:
        """Computes a file hash

        Args:
            file (Path): Path to file

        Returns:
            str: Hash digest
        """
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
        self.__log = logging.getLogger(f'e4edm.mission {mission_metadata.mission}')
        self.path = path.resolve()
        self.metadata = mission_metadata
        self.committed_files: List[Path] = []
        self.staged_files: Set[StagedFile] = set()
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

    def stage(self, paths: Iterable[Path], destination: Optional[Path] = None):
        """Add paths to the staging area.

        This function will iterate and recursively seek all normal files in the specification.  This
        is stored as a mapping from the original path to the destination path, as well as the
        expected hash for the final file.

        Args:
            paths (Iterable[Path]): Collection of paths to stage
            destination (Optional[Path], optional): Destination directory in mission to place 
            assets. Defaults to None.

        Raises:
            RuntimeWarning: Unsupported file type
        """
        if not destination:
            destination = Path('.')
        dst = self.path.joinpath(destination)
        for path in paths:
            origin_path = path.resolve()
            if origin_path.is_file():
                file_hash = Manifest.compute_file_hash(origin_path.resolve())
                target_path = dst.joinpath(path.name).resolve()
                self.staged_files.add(
                    StagedFile(
                    origin_path=origin_path,
                    target_path=target_path,
                    hash=file_hash
                    )
                )
                self.__log.info('Staging %s (%s) to %s', origin_path.as_posix(), file_hash,
                                target_path.as_posix())
            elif origin_path.is_dir():
                for file in origin_path.rglob('*'):
                    if file.is_dir():
                        continue
                    origin_file = file.resolve()
                    target_path = dst.joinpath(origin_file.relative_to(origin_path)).resolve()
                    file_hash = Manifest.compute_file_hash(origin_file)
                    self.staged_files.add(
                        StagedFile(
                        origin_path=origin_file,
                        target_path=target_path,
                        hash=file_hash
                        )
                    )
                    self.__log.info('Staging %s (%s) to %s', origin_file.as_posix(), file_hash,
                                target_path.as_posix())
            else:
                raise RuntimeWarning('Not a normal file')

    @property
    def name(self) -> str:
        """Returns a canonical name for this mission

        Returns:
            str: Name
        """
        return f'{self.path.parent.name} {self.path.name}'

    def commit(self) -> List[Path]:
        """Commits staged files to the mission

        Raises:
            RuntimeError: Copy fail
        """
        committed_files: List[Path] = []
        for staged_file in self.staged_files:
            staged_file.target_path.parent.mkdir(parents=True, exist_ok=True)
            copy2(src=staged_file.origin_path, dst=staged_file.target_path)
            if Manifest.compute_file_hash(staged_file.target_path) != staged_file.hash:
                raise RuntimeError(f'Failed to copy {staged_file.origin_path.as_posix()}')
            committed_files.append(staged_file.target_path)
            self.__log.info('Copied %s to %s',
                            staged_file.origin_path.as_posix(),
                            staged_file.target_path.as_posix())
        self.manifest.update(committed_files)
        self.committed_files.extend([file.relative_to(self.path) for file in committed_files])
        self.staged_files = set()
        return committed_files

class Dataset:
    """Dataset
    """
    # pylint: disable=too-many-instance-attributes

    __MANIFEST_NAME = 'manifest.json'
    __CONFIG_NAME = '.e4edm.pkl'
    VERSION = 2

    def __init__(self, root: Path, day_0: dt.date):
        self.__log = logging.getLogger('e4edm.dataset')
        self.root = root.resolve()
        self.day_0: dt.date = day_0
        self.last_country: Optional[str] = None
        self.last_region: Optional[str] = None
        self.last_site: Optional[str] = None
        self.countries: Set[str] = set()
        self.regions: Set[str] = set()
        self.sites: Set[str] = set()
        self.devices: Set[str] = set()
        self.missions: Dict[str, Mission] = {}
        self.manifest = Manifest(self.root.joinpath(self.__MANIFEST_NAME))
        self.committed_files: List[Path] = []
        self.staged_files: List[Path] = []
        self.pushed: bool = False
        self.version = self.VERSION

    def upgrade(self):
        """Upgrades self to latest version
        """
        if self.version < 2:
            self.pushed = False
        self.version = 2

    @classmethod
    def load(cls, path: Path) -> Dataset:
        """Loads the dataset from disk

        Args:
            path (Path): Path to expedition root

        Returns:
            Dataset: Dataset
        """
        try:
            config_file = path.joinpath(cls.__CONFIG_NAME)
            assert config_file.exists()
            with open(config_file, 'rb') as handle:
                loaded = pickle.load(handle)
                if not isinstance(loaded, Dataset):
                    raise RuntimeError('Not a dataset')
                if loaded.version != cls.VERSION:
                    loaded.upgrade()
                return loaded
        except Exception: # pylint: disable=broad-except
            metadata_files = list(path.rglob('metadata.json'))
            if len(metadata_files) == 0:
                raise RuntimeError('No config file and no data!') #pylint: disable=raise-missing-from
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
        self.missions[mission.name] = mission
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

    def validate(self) -> bool:
        """Validates the dataset

        Returns:
            bool: True if valid, otherwise False
        """
        return self.manifest.validate(
            manifest=self.manifest.get_dict(),
            files=self.get_files()
        )

    def stage(self, paths: Iterable[Path]):
        """Add paths to the staging area

        Args:
            paths (Iterable[Path]): Paths to stage
        """
        self.staged_files.extend(paths)
        for path in paths:
            self.__log.info('Staged %s', path.as_posix())

    def commit(self) -> List[Path]:
        """Commits staged files to the mission

        Raises:
            RuntimeError: Copy fail
        """
        # Discover files
        committed_files: List[Path] = []
        for path in self.staged_files:
            added_files: List[Path] = []
            if path.is_file():
                # this goes into the root
                added_files.append(path)
                root = path.parent
            elif path.is_dir():
                # This should get recursively copied in
                for file in path.rglob('*'):
                    if file.is_dir():
                        continue
                    added_files.append(file)
                root = path
            else:
                raise RuntimeError(f'Unknown path type: {path.as_posix()}')
            original_manifest = self.manifest.compute_hashes(
                root=root,
                files=added_files
            )
            new_files: List[Path] = []
            for file in added_files:
                src = file
                dest = self.root.joinpath(file.relative_to(root)).resolve()
                dest.parent.mkdir(parents=True, exist_ok=True)
                copy2(src=src, dst=dest)
                new_files.append(dest)
                self.__log.info('Copied %s to %s', src.as_posix(), dest.as_posix())
            if not self.manifest.validate(manifest=original_manifest, files=new_files):
                raise RuntimeError(f'Failed to copy {path.as_posix()}')
            self.manifest.update(new_files)
            self.committed_files.extend(new_files)
            committed_files.extend(new_files)
        self.staged_files = []
        return committed_files
