'''Mission creation tests
'''
import datetime as dt
import json
from pathlib import Path
from typing import Tuple
from unittest.mock import Mock

from e4e_data_management.core import DataManager
from e4e_data_management.metadata import Metadata


def test_create_multiple_missions(test_app: Tuple[Mock, DataManager, Path]):
    """Tests creating multiple missions
    """
    _, app, root = test_app
    app.initialize_dataset(
        date=dt.date(2023, 3, 1),
        project='TEST',
        location='San Diego',
        directory=root
    )

    app.initialize_mission(
        metadata=Metadata(
        timestamp=dt.datetime.fromisoformat('2023-03-01T23:59-08:00'),
        device='Device 1',
        country='USA',
        region='California',
        site='Site 1',
        mission='TCMM001',
        )
    )

    app.initialize_mission(
        metadata=Metadata(
        timestamp=dt.datetime.fromisoformat('2023-03-02T00:00-08:00'),
        device='Device 1',
        country='USA',
        region='California',
        site='Site 2',
        mission='TCMM002',
        )
    )

    app.initialize_mission(
        metadata=Metadata(
        timestamp=dt.datetime.fromisoformat('2023-03-02T00:02-08:00'),
        device='Device 1',
        country='USA',
        region='California',
        site='Site 2',
        mission='TCMM003',
        )
    )
    dataset_dir = root.joinpath('2023.03.01.TEST.San Diego')
    current_files = sorted([file.relative_to(dataset_dir) for file in dataset_dir.rglob('*')])
    expected_files = sorted([
        Path('.e4edm.pkl'),
        Path('manifest.json'),
        Path('ED-00'),
        Path('ED-00', 'TCMM001'),
        Path('ED-00', 'TCMM001', 'metadata.json'),
        Path('ED-00', 'TCMM001', 'manifest.json'),
        Path('ED-01'),
        Path('ED-01', 'TCMM002'),
        Path('ED-01', 'TCMM002', 'metadata.json'),
        Path('ED-01', 'TCMM002', 'manifest.json'),
        Path('ED-01', 'TCMM003'),
        Path('ED-01', 'TCMM003', 'metadata.json'),
        Path('ED-01', 'TCMM003', 'manifest.json'),
    ])
    assert current_files == expected_files

    assert len(app.active_dataset.missions) == 3
    assert app.active_dataset.sites == {'Site 1', 'Site 2'}
    assert app.active_dataset.root == dataset_dir
    assert app.active_dataset.name == '2023.03.01.TEST.San Diego'
    assert app.active_mission.path == dataset_dir.joinpath('ED-01', 'TCMM003')


def test_create_mission(test_app: Tuple[Mock, DataManager, Path]):
    """Tests creating a mission
    """
    _, app, root = test_app
    app.initialize_dataset(
        date=dt.date(2023, 3, 1),
        project='TEST',
        location='San Diego',
        directory=root
    )

    assert root.joinpath('2023.03.01.TEST.San Diego').exists()
    assert app.status().find('2023.03.01.TEST.San Diego') != -1
    assert '2023.03.01.TEST.San Diego' in app.list_datasets()
    app.prune()
    assert '2023.03.01.TEST.San Diego' in app.list_datasets()
    assert app.status().find('2023.03.01.TEST.San Diego') != -1

    timestamp = dt.datetime.fromisoformat('2023-03-01T09:05T-08:00')
    app.initialize_mission(
        metadata=Metadata(
            timestamp=timestamp,
            device='Device 1',
            country='USA',
            region='San Diego',
            site='Site 1',
            mission='TCM001'
        )
    )

    dataset_dir = root.joinpath('2023.03.01.TEST.San Diego')
    current_files = sorted([file.relative_to(dataset_dir) for file in dataset_dir.rglob('*')])
    expected_files = sorted([
        Path('.e4edm.pkl'),
        Path('manifest.json'),
        Path('ED-00'),
        Path('ED-00', 'TCM001'),
        Path('ED-00', 'TCM001', 'metadata.json'),
        Path('ED-00', 'TCM001', 'manifest.json')
    ])
    assert current_files == expected_files

    manifest_path = root.joinpath('2023.03.01.TEST.San Diego', 'manifest.json')
    with open(manifest_path, 'r', encoding='ascii') as handle:
        manifest = json.load(handle)

    metadata = root.joinpath('2023.03.01.TEST.San Diego', 'ED-00', 'TCM001', 'metadata.json')
    assert metadata.relative_to(root.joinpath('2023.03.01.TEST.San Diego')).as_posix() in manifest

    config = root.joinpath('2023.03.01.TEST.San Diego', '.e4edm.pkl')
    config_entry = config.relative_to(root.joinpath('2023.03.01.TEST.San Diego')).as_posix()
    assert config_entry not in manifest

    assert 'USA' in app.active_dataset.countries
    assert 'San Diego' in app.active_dataset.regions
    assert 'Site 1' in app.active_dataset.sites

    assert app.active_dataset.last_country == 'USA'
    assert app.active_dataset.last_region == 'San Diego'
    assert app.active_dataset.last_site == 'Site 1'

    assert app.active_dataset.root == dataset_dir
    assert app.active_dataset.name == '2023.03.01.TEST.San Diego'
    assert app.active_mission.path == dataset_dir.joinpath('ED-00', 'TCM001')

def test_activate(test_app: Tuple[Mock, DataManager, Path]):
    """Tests activate

    Args:
        test_app (Tuple[Mock, DataManager, Path]): Test app
    """
    _, app, root_dir = test_app

    app.initialize_dataset(
        date=dt.date(2023, 3, 3),
        project='test_mission_activate',
        location='Location1',
        directory=root_dir
    )
    assert app.active_dataset.name == '2023.03.03.test_mission_activate.Location1'

    app.initialize_dataset(
        date=dt.date(2023, 3, 3),
        project='Test',
        location='Location2',
        directory=root_dir
    )

    assert app.active_dataset.name == '2023.03.03.Test.Location2'

    app.activate(
        dataset='2023.03.03.test_mission_activate.Location1'
    )
    assert app.active_dataset.name == '2023.03.03.test_mission_activate.Location1'

    app.initialize_mission(
        metadata=Metadata(
        timestamp=dt.datetime.fromisoformat('2023-03-03T22:37-08:00'),
        device='device1',
        country='country1',
        region='region1',
        site='site1',
        mission='mission1'
        )
    )
    assert app.active_mission.name == 'ED-00 mission1'

    app.initialize_mission(
        metadata=Metadata(
        timestamp=dt.datetime.fromisoformat('2023-03-03T22:39-08:00'),
        device='device1',
        country='country1',
        region='region1',
        site='site1',
        mission='mission2'
        )
    )
    assert app.active_mission.name == 'ED-00 mission2'

    app.activate(
        dataset='2023.03.03.test_mission_activate.Location1',
        day=0,
        mission='mission1'
    )

    assert app.active_mission.name == 'ED-00 mission1'

    app.activate(
        dataset='2023.03.03.Test.Location2',
        day=None,
        mission=None
    )

    assert app.active_mission is None
