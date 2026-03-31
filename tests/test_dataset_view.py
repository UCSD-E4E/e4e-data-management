"""Tests for _DatasetView properties"""
import datetime as dt
from pathlib import Path
from typing import Tuple
from unittest.mock import Mock

import pytest

from e4e_data_management.core import DataManager
from e4e_data_management.metadata import Metadata


@pytest.fixture(name='multi_mission_app')
def create_multi_mission_app(test_app: Tuple[Mock, DataManager, Path]):
    """App with one dataset and two missions with distinct metadata."""
    _, app, root_dir = test_app

    app.initialize_dataset(
        date=dt.date(2024, 1, 15),
        project='ReefLaser',
        location='Palmyra',
        directory=root_dir,
    )

    app.initialize_mission(
        metadata=Metadata(
            timestamp=dt.datetime.fromisoformat('2024-01-15T08:00:00+00:00'),
            device='Raven',
            country='USA',
            region='California',
            site='SD',
            mission='M001',
        )
    )

    app.initialize_mission(
        metadata=Metadata(
            timestamp=dt.datetime.fromisoformat('2024-01-15T14:00:00+00:00'),
            device='Anaconda',
            country='USA',
            region='Hawaii',
            site='Palmyra',
            mission='M002',
        )
    )

    yield app


def test_dataset_view_sites(multi_mission_app: DataManager):
    ds = multi_mission_app.active_dataset
    assert ds.sites == {'SD', 'Palmyra'}


def test_dataset_view_countries(multi_mission_app: DataManager):
    ds = multi_mission_app.active_dataset
    assert ds.countries == {'USA'}


def test_dataset_view_regions(multi_mission_app: DataManager):
    ds = multi_mission_app.active_dataset
    assert ds.regions == {'California', 'Hawaii'}


def test_dataset_view_devices(multi_mission_app: DataManager):
    ds = multi_mission_app.active_dataset
    assert ds.devices == {'Raven', 'Anaconda'}


def test_dataset_view_sites_empty_when_no_missions(test_app: Tuple[Mock, DataManager, Path]):
    _, app, root_dir = test_app
    app.initialize_dataset(
        date=dt.date(2024, 2, 1),
        project='Empty',
        location='Nowhere',
        directory=root_dir,
    )
    ds = app.active_dataset
    assert ds.sites == set()
    assert ds.countries == set()
    assert ds.regions == set()
    assert ds.devices == set()
