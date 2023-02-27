'''Data classes
'''
import datetime as dt
import json
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from typing import Dict, Generator, Union


@dataclass
class Site:
    country: str
    region: str
    site: str

class Mission:
    def __init__(self, path: Path) -> None:
        pass

class Dataset:
    """Dataset
    """

    __MANIFEST_NAME = 'manifest.json'

    def __init__(self, root: Path):
        self.__root = root

    def validate(self,
            manifest: Dict[str, Dict[str, Union[str, int]]],
            *,
            method: str = 'hash') -> bool:
        """Validates the dataset against the provided manifest

        Args:
            manifest (Dict[str, Dict[str, Union[str, int]]]): Manifest
            method (str, optional): Validation method, either 'hash' or 'size'. Defaults to 'hash'.

        Raises:
            RuntimeError: Invalid method

        Returns:
            bool: True if valid, otherwise False
        """
        for file in self.get_files():
            file_key = file.relative_to(self.__root).as_posix()
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
                raise RuntimeError('Unknown method')
        return True

    def get_manifest(self) -> Dict[str, Dict[str, Union[str, int]]]:
        """Gets the manifest data

        Returns:
            Dict[str, Dict[str, Union[str, int]]]: Dictionary of paths and hashes/sizes
        """
        if not self.__root.joinpath(self.__MANIFEST_NAME).is_file():
            return self.__compute_hashes(self.__root)
        with open(self.__root.joinpath(self.__MANIFEST_NAME), 'r', encoding='ascii') as handle:
            return json.load(handle)

    def generate_manifest(self):
        """Generates the checksummed manifest
        """
        root = self.__root
        data = self.__compute_hashes(root)
        with open(self.__root.joinpath(self.__MANIFEST_NAME), 'w', encoding='ascii') as handle:
            json.dump(data, handle, indent=4)

    def __compute_hashes(self, root: Path) -> Dict[str, Dict[str, Union[str, int]]]:
        data: Dict[str, Dict[str, Union[str, int]]] = {}
        for file in self.get_files():
            rel_path = file.relative_to(root).as_posix()
            cksum = self.__hash(file)
            file_size = file.lstat().st_size
            data[rel_path] = {
                'sha256sum': cksum,
                'size': file_size
            }

        return data

    def __hash(self, file: Path):
        cksum = sha256()
        with open(file, 'rb') as handle:
            for byte_block in iter(lambda: handle.read(4096), b''):
                cksum.update(byte_block)
        return cksum.hexdigest()

    def get_files(self) -> Generator[Path, None, None]:
        """Yields all of the files in this dataset

        Yields:
            Generator[Path, None, None]: Files
        """
        for file in self.__root.rglob('*'):
            if file == self.__root.joinpath(self.__MANIFEST_NAME):
                continue
            if not file.is_file():
                continue
            yield file

    def add_mission(self) -> None:
        pass