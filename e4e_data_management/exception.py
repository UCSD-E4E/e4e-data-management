'''E4E Data Management Exceptions
'''
from abc import ABC


class Incomplete(Exception, ABC):
    """Dataset not complete
    """


class MissionFilesInStaging(Incomplete):
    """Mission files still in staging area
    """


class ReadmeFilesInStaging(Incomplete):
    """Readme files still in staging area
    """


class ReadmeNotFound(Incomplete):
    """Readme files not found
    """


class CorruptedDataset(Exception):
    """Corrupted Dataset
    """
