'''E4E Data Management Exceptions
'''
from e4e_data_management._core import (
    MissionFilesInStaging,
    ReadmeFilesInStaging,
    ReadmeNotFound,
    CorruptedDataset,
)

__all__ = [
    'MissionFilesInStaging',
    'ReadmeFilesInStaging',
    'ReadmeNotFound',
    'CorruptedDataset',
    'Incomplete',
]


class Incomplete(Exception):
    """Dataset not complete"""
