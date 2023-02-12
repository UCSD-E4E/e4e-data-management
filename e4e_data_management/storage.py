'''Storage Commit Tool main logic
'''
import argparse
import os
import re
from pathlib import Path

from e4e_data_management.validator import Dataset


class StorageTool:
    """Storage Tool application logic
    """
    def __init__(self,
            source: Path):
        self.root = source
        self.dataset = Dataset(source)

    def validate(self):
        """Validates the structure of the expedition dataset
        """
        dir_contents = os.listdir(self.root.as_posix())

        # Find the README file
        candidates = [f for f in dir_contents\
            if re.search(r"readme\.(md|docx|pdf)", f, re.I)]
        assert len(candidates) == 1
        n_files = 1

        # Check if a manifest already exists
        if self.root.joinpath('manifest.json').exists():
            n_files += 1

        # Check that there are day directories
        day_dirs = [self.root.joinpath(f) for f in dir_contents\
            if re.search(r"ED-\d*", f)]
        assert len(day_dirs) == len(dir_contents) - n_files
        assert all(f.is_dir() for f in day_dirs)

        # Check that there are only directories in each day directory
        for day_dir in day_dirs:
            dirs = day_dir.glob('*')
            assert all(dir.is_dir() for dir in dirs)
            # Check that each of these contains a metadata and manifest file
            for run in dirs:
                assert run.joinpath('manifest.json').exists()
                assert run.joinpath('metadata.json').exists()

    def prep(self):
        """Prepares the dataset by updating the manifest
        """
        self.dataset.generate_manifest()

    def commit(self):
        """Commits this dataset to the data staging area
        """

def gui():
    """GUI Entry Point
    """

def cli():
    """CLI Entry Point
    """
    parser = argparse.ArgumentParser(
        description="Expedition Data Commit Tool"
    )
    parser.add_argument('source', type=Path)

    args = parser.parse_args()

    source = args.source
    if not source.is_dir():
        raise RuntimeError('Source is not a directory')

    app = StorageTool(
        source=source
    )
    app.validate()
    app.prep()
    app.commit()

if __name__ == '__main__':
    cli()
