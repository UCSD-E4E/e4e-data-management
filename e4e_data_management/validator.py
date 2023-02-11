'''Validation logic
'''
import json
from hashlib import sha256
from pathlib import Path
from typing import Dict, Union, Generator


class Dataset:
    """Dataset
    """
    def __init__(self, root: Path):
        self.__root = root

    def generate_manifest(self):
        """Generates the checksummed manifest
        """
        root = self.__root
        data = self.__compute_hashes(root)
        with open(self.__root.joinpath('manifest.json'), 'w', encoding='ascii') as handle:
            json.dump(data, handle, indent=4)

    def __compute_hashes(self, root: Path):
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
            if file == self.__root.joinpath('manifest.json'):
                continue
            if not file.is_file():
                continue
            yield file
