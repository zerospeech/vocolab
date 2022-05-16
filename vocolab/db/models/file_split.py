from pathlib import Path
from typing import List, Optional

from pydantic import BaseModel


class ManifestIndexItem(BaseModel):
    """ Model representing a file item in the SplitManifest """
    file_name: str
    file_size: int
    file_hash: str

    def __eq__(self, other: 'ManifestIndexItem'):
        return self.file_hash == other.file_hash

    def __hash__(self):
        return int(self.file_hash, 16)


class SplitManifest(BaseModel):
    """ Data Model used for the binary split function as a manifest to allow merging """
    filename: str
    tmp_location: Path
    hash: str
    index: Optional[List[ManifestIndexItem]]
    received: Optional[List[ManifestIndexItem]] = []
    multipart: bool = True
    hashed_parts: bool = True




