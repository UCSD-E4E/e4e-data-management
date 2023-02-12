'''Data Generator for tests
'''
import datetime as dt
import json
import random
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from e4e_data_management.validator import Dataset

N_LINES = 1024
N_DAYS = 3
RUNS_PER_DAY = 4

@pytest.fixture(name='single_run')
def create_run() -> Path:
    """Creates a single test run

    Returns:
        Path: run directory

    Yields:
        Iterator[Path]: Path
    """
    with TemporaryDirectory() as temp_dir:
        run_dir = Path(temp_dir)
        with open(run_dir.joinpath('data.txt'), 'w', encoding='ascii') as handle:
            for _ in range(N_LINES):
                handle.write(f'{random.randint(0, 1024)}\n')
        yield run_dir

@pytest.fixture(name='single_day')
def create_day() -> Path:
    """Creates a single day's worth of runs

    Returns:
        Path: Day directory

    Yields:
        Iterator[Path]: Day directory
    """
    with TemporaryDirectory() as temp_dir:
        day_dir = Path(temp_dir)
        for run in range(RUNS_PER_DAY):
            run_dir = day_dir.joinpath(f'RUN{run:03d}')
            run_dir.mkdir()
            with open(run_dir.joinpath('data.txt'), 'w', encoding='ascii') as handle:
                for _ in range(N_LINES):
                    handle.write(f'{random.randint(0, 1024)}\n')
        yield day_dir

@pytest.fixture(name='single_expedition')
def create_expedition() -> Path:
    """Creates an expedition's worth of data

    Returns:
        Path: Expedition directory

    Yields:
        Iterator[Path]: Expedition directory
    """
    with TemporaryDirectory() as temp_dir:
        expedition_dir = Path(temp_dir)
        for day in range(N_DAYS):
            day_dir = expedition_dir.joinpath(f'ED-{day:02d}')
            day_dir.mkdir()

            for run in range(RUNS_PER_DAY):
                run_dir = day_dir.joinpath(f'RUN{run:03d}')
                run_dir.mkdir()
                with open(run_dir.joinpath('data.txt'), 'w', encoding='ascii') as handle:
                    for _ in range(N_LINES):
                        handle.write(f'{random.randint(0, 1024)}\n')
        yield expedition_dir

@pytest.fixture(name='single_validated_run')
def create_validated_run(single_run: Path) -> Path:
    """Validates the single run

    Args:
        single_run (Path): Run dataset

    Returns:
        Path: Run dataset

    Yields:
        Iterator[Path]: Validated dataset
    """
    dataset = Dataset(single_run)
    dataset.generate_manifest()
    current_tz = dt.datetime.now().astimezone().tzinfo
    atime = dt.datetime.fromtimestamp(
        single_run.joinpath('data.txt').lstat().st_atime,
        tz=current_tz
    )
    with open(single_run.joinpath('metadata.json'), 'w', encoding='ascii') as handle:
        metadata = {
            'timestamp': atime.isoformat(),
            'device': "data_generator.ipynb",
            'notes': "Randomly generated data",
            'properties': {},
            'country': 'USA',
            'region': 'California',
            'site': 'San Diego',
            'mission': single_run.name
        }
        json.dump(metadata, handle, indent=4)
    yield single_run

@pytest.fixture(name='single_validated_day')
def create_validated_day(single_day: Path) -> Path:
    """validates a single day

    Args:
        single_day (Path): Single day dataset

    Returns:
        Path: Validated dataset

    Yields:
        Iterator[Path]: Validated dataset
    """
    run_folders = single_day.glob('RUN*')
    current_tz = dt.datetime.now().astimezone().tzinfo
    for run in run_folders:
        dataset = Dataset(run)
        dataset.generate_manifest()
        atime = dt.datetime.fromtimestamp(
            run.joinpath('data.txt').lstat().st_atime,
            tz=current_tz
        )
        with open(run.joinpath('metadata.json'), 'w', encoding='ascii') as handle:
            metadata = {
                'timestamp': atime.isoformat(),
                'device': "data_generator.ipynb",
                'notes': "Randomly generated data",
                'properties': {},
                'country': 'USA',
                'region': 'California',
                'site': 'San Diego',
                'mission': run.name
            }
            json.dump(metadata, handle, indent=4)
    yield single_day

@pytest.fixture(name='single_validated_expedition')
def create_validated_expedition(single_expedition: Path) -> Path:
    """Completes an expedition dataset

    Args:
        single_expedition (Path): Expedition dataset

    Returns:
        Path: Completed dataset

    Yields:
        Iterator[Path]: Completed dataset
    """
    day_folders = single_expedition.glob('ED*')
    current_tz = dt.datetime.now().astimezone().tzinfo
    for day in day_folders:
        run_folders = day.glob('RUN*')
        for run in run_folders:
            Dataset(run).generate_manifest()
            atime = dt.datetime.fromtimestamp(
                run.joinpath('data.txt').lstat().st_atime,
                tz=current_tz
            )
            with open(run.joinpath('metadata.json'), 'w', encoding='ascii') as handle:
                metadata = {
                    'timestamp': atime.isoformat(),
                    'device': "data_generator.ipynb",
                    'notes': "Randomly generated data",
                    'properties': {},
                    'country': 'USA',
                    'region': 'California',
                    'site': 'San Diego',
                    'mission': run.name
                }
                json.dump(metadata, handle, indent=4)
    single_expedition.joinpath('readme.md').touch()
    Dataset(single_expedition).generate_manifest()
    yield single_expedition
