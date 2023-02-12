'''Manifest Class Tester
'''

import datetime as dt
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from e4e_data_management.metadata import Metadata


def test_manifest_serialization():
    """Testing manifest serialization
    """
    manifest = Metadata(
        timestamp=dt.datetime.now().astimezone(),
        device='test',
        country='USA',
        region='California',
        site='San Diego',
        mission='test_manifest_serialization',
        properties={
            'seed': 123,
            'random_float': 3.14,
            'random_bool': True,
            'random_string': 'asdf',
            'random_null': None
        },
        notes='Random Note'
    )
    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        manifest.write(directory=root)

        new_manifest = Metadata.load(directory=root)

    assert manifest == new_manifest
    assert new_manifest.timestamp.tzinfo is not None

def test_no_tzinfo():
    """Testing manifest serialization with no timezone
    """
    with pytest.raises(Exception):
        manifest = Metadata(
            timestamp=dt.datetime.now(),
            device='test',
            country='USA',
            region='California',
            site='San Diego',
            mission='test_manifest_serialization',
            properties={
                'seed': 123,
                'random_float': 3.14,
                'random_bool': True,
                'random_string': 'asdf',
                'random_null': None
            },
            notes='Random Note'
        )
