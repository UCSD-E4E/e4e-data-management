'''Data staging tests
'''
import datetime as dt
import random
from pathlib import Path
from tempfile import TemporaryDirectory

from e4e_data_management.core import DataManager
from e4e_data_management.metadata import Metadata

N_FILES = 64
N_BYTES = 1024

def test_stage_data():
    """Test staging data
    """
    with TemporaryDirectory() as root_dir:
        root = Path(root_dir)
        app = DataManager(
            app_config_dir=root
        )
        app.initialize_dataset(
            date=dt.date(2023, 3, 2),
            project='TestStaging',
            location='San Diego',
            directory=root
        )
        app.initialize_mission(
            metadata=Metadata(
                timestamp=dt.datetime.fromisoformat('2023-03-02T00:11-08:00'),
                device='Device 1',
                country='USA',
                region='California',
                site='Site 1',
                mission='RUN001'
            )
        )

        with TemporaryDirectory() as data_dir:
            data_folder = Path(data_dir)
            for file_idx in range(N_FILES):
                data_file = data_folder.joinpath(f'{file_idx:04d}.bin')
                with open(data_file, 'wb') as handle:
                    handle.write(random.randbytes(N_BYTES))
            app.add(list(data_folder.rglob('*.bin')))
