from __future__ import annotations

import datetime as dt
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict

import schema


@dataclass
class Manifest:
    """Dataset Manifest

    Raises:
        RuntimeError: No timezone specified

    """
    timestamp: dt.datetime
    device: str
    country: str
    region: str
    site: str
    mission: str
    properties: Dict[str, Any] = field(default_factory=dict)
    notes: str = ''

    def __post_init__(self):
        if self.timestamp.tzinfo is None:
            raise RuntimeError('No timezone info specified!')

    def write(self, directory: Path):
        """Writes the manifest file to the specified directory

        Args:
            directory (Path): Directory in which to write the manifest file

        Raises:
            RuntimeError: No timezone specified
        """
        if self.timestamp.tzinfo is None:
            raise RuntimeError('No timezone info specified!')
        metadata = {
            'timestamp': self.timestamp.isoformat(),
            'device': self.device,
            'notes': self.notes,
            'properties': self.properties,
            'country': self.country,
            'region': self.region,
            'site': self.site,
            'mission': self.mission
        }
        with open(directory.joinpath('metadata.json'), 'w', encoding='ascii') as handle:
            json.dump(metadata, handle, indent=4)

    @classmethod
    def load(cls, directory: Path) -> Manifest:
        """Loads a manifest file from disk

        Args:
            directory (Path): Directory from which to load the manifest file

        Returns:
            Manifest: Loaded manifest file
        """
        metadata_schema = schema.Schema({
            'timestamp': str,
            'device': str,
            'country': str,
            'region': str,
            'site': str,
            'mission': str,
            'properties': dict,
            'notes': str
        })
        with open(directory.joinpath('metadata.json'), 'r', encoding='ascii') as handle:
            data = json.load(handle)
        metadata = metadata_schema.validate(data)
        return Manifest(
            timestamp=dt.datetime.fromisoformat(metadata['timestamp']),
            device=metadata['device'],
            country=metadata['country'],
            region=metadata['region'],
            site=metadata['site'],
            mission=metadata['mission'],
            properties=metadata['properties'],
            notes=metadata['notes']
        )
