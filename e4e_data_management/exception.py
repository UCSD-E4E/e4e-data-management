'''E4E Data Management Exceptions
'''
from e4e_data_management._core import (
    MissionFilesInStaging,
    ReadmeFilesInStaging,
    ReadmeNotFound,
    CorruptedDataset,
)


class Incomplete(Exception):
    """Dataset not complete"""
