import json
import shutil
from pathlib import Path
from typing import Generator, Optional, Any

from pydantic import BaseModel
from vocolab_ext.leaderboards import LeaderboardRegistry, LeaderboardManager

from vocolab import get_settings

_settings = get_settings()

# Load leaderboard manager from extensions
leaderboard_manager: LeaderboardManager = LeaderboardRegistry().load(_settings.extensions.leaderboards_extension)


class LeaderboardDir(BaseModel):
    """ Handler class for disk storage of Leaderboards """
    location: Path
    sorting_key: Optional[str]
    leaderboard_type: str

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
    def entries(self) -> Generator[Any, None, None]:
        """ Generator containing entry objects """
        for item in self.entry_dir.glob("*.json"):
            with item.open() as fp:
                yield leaderboard_manager.load_entry_from_obj(self.leaderboard_type, json.load(fp))

    @property
    def static_dir(self):
        """ Location containing static items of leaderboard """
        return self.location / 'static'

    def has_static(self):
        """ Boolean checking whether this leaderboard has static files """
        return self.static_dir.is_dir()

    def load_object(self, from_cache: bool = True, raw: bool = False):
        """ Loads leaderboard object (cached or from entries)"""
        if self.cached_store.is_file():
            if raw:
                with self.cached_store.open() as fp:
                    return json.load(fp)
            if from_cache:
                with self.cached_store.open() as fp:
                    data = json.load(fp)
                return leaderboard_manager.load_leaderboard_from_obj(name=self.leaderboard_type, obj=data)

        # leaderboard file not found, build it
        self.mkcache()
        # recall function
        return self.load_object(from_cache=True, raw=raw)

    def mkcache(self):
        """ Create cached version of final leaderboard """
        # load entries into object
        ld_m: LeaderboardManager = leaderboard_manager.create_from_entry_folder(self.leaderboard_type, self.entry_dir)
        # export as json
        ld_m.export_as_csv(self.cached_store)

    @classmethod
    def load(cls, label: str, sorting_key: Optional[str] = None):
        """ Load leaderboard dir  """
        loc = _settings.leaderboard_dir / label
        if not loc.is_dir():
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
