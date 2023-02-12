'''Duplication Tool main logic
'''
import argparse
from pathlib import Path
from typing import Iterable, List

from e4e_data_management.validator import Dataset


class Duplicator:
    """Duplication Tool application logic
    """
    def __init__(self,
        source: Path,
        destinations: Iterable[Path],
        *,
        verification_method: str = 'hash'):
        self.source = source
        self.destinations = destinations
        self.__method = verification_method

        self.__validate_args()
        self.dataset = Dataset(self.source)

    def duplicate(self):
        """Does the duplication
        """
        self.dataset.generate_manifest()
        # TODO: Duplicate

    def verify(self):
        """Verifies the output
        """
        reference_manifest = self.dataset.get_manifest()
        for destination in self.destinations:
            Dataset(destination).validate(reference_manifest, method=self.__method)

    def __validate_args(self):
        assert self.source.is_dir()
        assert len(self.destinations) > 0
        assert all(dest.is_dir() for dest in self.destinations)

def gui():
    """GUI Entry Point
    """

def cli():
    """CLI Entry Point
    """
    parser = argparse.ArgumentParser(
        description="Expedition Data Duplication Tool"
    )
    parser.add_argument('source', type=Path)
    parser.add_argument('destination', nargs='+', type=Path)

    args = parser.parse_args()

    source: Path = args.source
    if not source.is_dir():
        raise RuntimeError('Source is not a directory')

    destinations: List[Path] = args.destination

    if not all(dest.is_dir() for dest in destinations):
        raise RuntimeError('Destination is not a directory')


    app = Duplicator(
        source=source,
        destinations=destinations
    )

    app.duplicate()

if __name__ == '__main__':
    cli()
