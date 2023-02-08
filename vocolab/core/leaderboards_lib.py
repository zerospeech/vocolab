import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Generator, Optional

from pydantic import BaseModel

from vocolab import get_settings
from vocolab.data import models

_settings = get_settings()


class LeaderboardDir(BaseModel):
    """ Handler class for disk storage of Leaderboards """
    location: Path
    sorting_key: Optional[str]

    @property
    def label(self) -> str:
        """ Leaderboard label """
        return self.location.name

    @property
    def cached_store(self):
        """ Object used to cache build leaderboard (for faster serving) """
        return self.location / 'leaderboard.json'

    @property
    def entry_dir(self) -> Path:
        """ Location where all leaderboard entries are stored """
        return self.location / 'entries'

    @property
    def entries(self) -> Generator[models.api.LeaderboardEntryItem, None, None]:
        """ Generator containing entry objects """
        for item in self.entry_dir.glob("*.json"):
            with item.open() as fp:
                yield models.api.LeaderboardEntryItem.parse_obj(json.load(fp))

    @property
    def static_dir(self):
        """ Location containing static items of leaderboard """
        return self.location / 'static'

    def has_static(self):
        """ Boolean checking whether this leaderboard has static files """
        return self.static_dir.is_dir()

    def load_object(self, from_cache: bool) -> models.api.LeaderboardObj:
        """ Loads leaderboard object (cached or from entries)"""
        if from_cache and self.cached_store.is_file():
            with self.cached_store.open() as fp:
                return models.api.LeaderboardObj.parse_obj(json.load(fp))
        return models.api.LeaderboardObj(
            updatedOn=datetime.now(),
            data=[item for item in self.entries],
            sorting_key=self.sorting_key
        )

    def mkcache(self):
        """ Create cached version of final leaderboard """
        data = self.load_object(from_cache=False)
        with self.cached_store.open('w') as fp:
            fp.write(data.json(indent=4))

    @classmethod
    def load(cls, label: str, sorting_key: str):
        """ Load leaderboard dir  """
        loc = _settings.leaderboard_dir / label
        if not loc.is_file():
            raise ValueError(f'Leaderboard named {label} does not exist')
        return cls(
            location=loc,
            sorting_key=sorting_key
        )

    @classmethod
    def create(cls, label, sorting_key: str, static_files: bool = False) -> "LeaderboardDir":
        """ Creates necessary files/architecture to store a leaderboard on disk """
        loc = _settings.leaderboard_dir / label
        if loc.is_dir():
            raise ValueError(f'Leaderboard with {label} already exists')

        lead = cls(location=loc, sorting_key=sorting_key)

        lead.location.mkdir(parents=True)
        lead.entry_dir.mkdir(parents=True)
        if static_files:
            lead.static_dir.mkdir(parents=True)

        return lead

    def delete(self):
        """ Remove all files relative to this leaderboard """
        shutil.rmtree(self.location)
