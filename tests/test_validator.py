'''Test validators
'''
import random
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

from e4e_data_management.data import Manifest

N_FILES = 128
N_BYTES = 1024
def test_validation():
    """Tests the validation hash is SHA256

    Raises:
        NotImplementedError: Unsupported platform
    """
    with TemporaryDirectory() as temp_dir:
        run_dir = Path(temp_dir).resolve()
        for file_idx in range(N_FILES):
            with open(run_dir.joinpath(f'{file_idx:04d}.bin'), 'w', encoding='ascii') as handle:
                for _ in range(N_BYTES):
                    handle.write(f'{random.randint(0, 1024)}')
        manifest = Manifest(run_dir.joinpath('manifest.json'), run_dir)
        manifest.generate(run_dir.rglob('*.bin'))
        manifest_data = manifest.get_dict()

        for file in run_dir.rglob('*.bin'):
            manifest_key = file.relative_to(run_dir).as_posix()
            assert manifest_key in manifest_data

            if sys.platform == 'linux':
                output = subprocess.check_output(['sha256sum', file.as_posix()])
                cksum = output.decode().splitlines()[0].split()[0]
            elif sys.platform == 'win32':
                # Note: certUtil actually throws an error on empty string!  So we need to bypass...
                if file.lstat().st_size != 0:
                    output = subprocess.check_output(
                        ['certUtil', '-hashfile', file.resolve().as_posix(), 'SHA256'])
                    cksum = output.decode().splitlines()[1].strip()
                else:
                    cksum = 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855'
            else:
                raise NotImplementedError

            assert cksum == manifest_data[manifest_key]['sha256sum']
