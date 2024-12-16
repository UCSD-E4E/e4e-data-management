'''Tests zipping
'''
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Tuple
from unittest.mock import Mock
import zipfile
from e4e_data_management.core import DataManager

SingleMissionFixture = Tuple[Tuple[Mock,
                                   DataManager, Path], Tuple[Path, int, int]]


def test_zip_to_dir(single_mission_data: SingleMissionFixture,
                    test_readme: Path):
    """Tests zipping data

    Args:
        single_mission(SingleMissionFixture): Single Mission test fixture
        test_readme (Path): Test Readme
    """
    test_app, _ = single_mission_data
    _, app, _ = test_app

    app.add([test_readme], readme=True)
    app.commit(readme=True)
    with TemporaryDirectory() as target_dir:
        zip_path = Path(target_dir)
        app.zip(zip_path)

        final_path = zip_path.joinpath(app.active_dataset.name + '.zip')
        assert final_path.is_file()

        with zipfile.ZipFile(file=final_path, mode='r') as handle:
            assert handle.testzip() is None
            manifest = app.active_dataset.manifest.get_dict()
            for name in handle.filelist:
                ar_name = Path(name.filename).relative_to(
                    app.active_dataset.name)
                assert ar_name.as_posix() in manifest

            handle.extractall(target_dir)

            app.active_dataset.manifest.validate(
                manifest=manifest,
                files=Path(app.active_dataset.name).rglob('*')
            )
