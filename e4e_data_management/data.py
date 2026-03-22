'''Data classes - thin Python wrappers around Rust _core types
'''
from __future__ import annotations

import json
from hashlib import sha256
from pathlib import Path
from typing import Dict, Iterable, Optional, Union

from e4e_data_management._core import PyDataset as _Dataset


class Manifest:
    """Manifest helper - reads/writes manifest.json files.

    Kept for backward compatibility with tests that import Manifest directly.
    """

    def __init__(self, path: Path, root: Optional[Path] = None):
        self.path = path
        self._root = (root or path.parent).resolve()

    def generate(self, files: Iterable[Path]):
        """Generate manifest from files."""
        data = self._compute_hashes(self._root, files)
        self._write(data)

    def get_dict(self) -> Dict[str, Dict[str, Union[str, int]]]:
        with open(self.path, 'r', encoding='ascii') as handle:
            return json.load(handle)

    def _write(self, data: Dict, path: Optional[Path] = None):
        target = path or self.path
        with open(target, 'w', encoding='ascii') as handle:
            json.dump(data, handle, indent=4)

    def update(self, files: Iterable[Path]):
        data = self.get_dict()
        new_data = self._compute_hashes(self._root, files)
        data.update(new_data)
        self._write(data)

    def validate(self,
                 manifest: Dict,
                 files: Iterable[Path],
                 *,
                 method: str = 'hash',
                 root: Optional[Path] = None) -> bool:
        effective_root = root or self._root
        for file in files:
            if not file.is_file():
                continue
            file_key = file.relative_to(effective_root).as_posix()
            if file_key not in manifest:
                return False
            if method == 'hash':
                if self._compute_file_hash(file) != manifest[file_key]['sha256sum']:
                    return False
            elif method == 'size':
                if file.lstat().st_size != manifest[file_key]['size']:
                    return False
            else:
                raise NotImplementedError(f'Unknown validation method: {method}')
        return True

    @staticmethod
    def _compute_file_hash(file: Path) -> str:
        cksum = sha256()
        with open(file, 'rb') as handle:
            for block in iter(lambda: handle.read(4096), b''):
                cksum.update(block)
        return cksum.hexdigest()

    def _compute_hashes(self, root: Path,
                        files: Iterable[Path]) -> Dict[str, Dict]:
        data = {}
        for file in files:
            if not Path(file).is_file():
                continue
            rel = Path(file).relative_to(root).as_posix()
            data[rel] = {
                'sha256sum': self._compute_file_hash(Path(file)),
                'size': Path(file).lstat().st_size,
            }
        return data


class Dataset:
    """Thin Python wrapper around the Rust Dataset implementation"""

    def __init__(self, inner: _Dataset):
        self._inner = inner
        self._manifest = Manifest(Path(self._inner.root) / 'manifest.json',
                                  Path(self._inner.root))

    @classmethod
    def load(cls, path: Path) -> 'Dataset':
        return cls(_Dataset.load(str(path)))

    def validate(self) -> bool:
        return self._inner.validate()

    @property
    def manifest(self) -> Manifest:
        return self._manifest

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
