'''Data Generator for tests
'''
import random
from pathlib import Path
from tempfile import TemporaryDirectory
from e4e_data_management.validator import Dataset
import pytest

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
    dataset = Dataset(single_run)
    dataset.generate_manifest()
    yield single_run

@pytest.fixture(name='single_validated_day')
def create_validated_day(single_day: Path) -> Path:
    run_folders = single_day.glob('RUN*')
    for run in run_folders:
        dataset = Dataset(run)
        dataset.generate_manifest()
    yield single_day

@pytest.fixture(name='single_validated_expedition')
def create_validated_expedition(single_expedition: Path) -> Path:
    day_folders = single_expedition.glob('ED*')
    for day in day_folders:
        run_folders = day.glob('RUN*')
        for run in run_folders:
            Dataset(run).generate_manifest()
    yield single_expedition
