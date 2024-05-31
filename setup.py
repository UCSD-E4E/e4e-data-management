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
            'e4edm = e4e_data_management.cli:main'
        ]
    },
    packages=find_packages(),
    install_requires=[
        'schema',
        'appdirs',
        'wakepy',
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
