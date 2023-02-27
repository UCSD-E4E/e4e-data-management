"""E4E Data Management Tools
"""
from setuptools import find_packages, setup

from e4e_data_management import __version__

setup(
    name='e4e_data_management',
    version=__version__,
    author='UCSD Engineers for Exploration',
    author_email='e4e@eng.ucsd.edu',
    entry_points={
        'console_scripts': [
            'E4EDuplicator = e4e_data_management.duplicator:gui',
            'E4EDataWrangler = e4e_data_management.data_wrangler:gui',
            'E4ECommitter = e4e_data_management.storage:gui',
            'E4EArchiver = e4e_data_management.archive:gui',
            'E4EDuplicatorCli = e4e_data_management.duplicator:cli',
            'E4EDataWranglerCli = e4e_data_management.data_wrangler:cli',
            'E4ECommitterCli = e4e_data_management.storage:cli',
            'E4EArchiverCli = e4e_data_management.archive:cli'
        ]
    },
    packages=find_packages(),
    install_requires=[
        'schema'
    ],
    extras_require={
        'dev': [
            'pytest',
            'coverage',
            'pylint',
            'wheel',
        ]
    },
)
