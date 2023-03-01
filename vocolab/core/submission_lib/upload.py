import json
import shutil
from hmac import compare_digest
from pathlib import Path
from typing import List, Optional

from fastapi import UploadFile
from fsplit.filesplit import Filesplit
from pydantic import BaseModel
import pandas as pd
import numpy as np

from vocolab import exc
from ..commons import md5sum
from .logs import SubmissionLogger

"""
####### File Splitting Note #######
Splitting & Merging of archives uses the protocol defined by the filesplit package.
This protocol requires the split to use the same method as a manifest is created which 
then allows to merge the parts into the original file.

For more information see documentation : https://pypi.org/project/filesplit/

NOTE: v3.0.2 is currently used, an update to v4 needs to be implemented.
"""


class SinglepartUploadHandler(BaseModel):
    root_dir: Path

    @property
    def target_file(self):
        return self.root_dir / 'content_archive.zip'

    @property
    def hash_file_location(self) -> Path:
        """ singlepart upload can be verified by the checksum inside this file """
        return self.root_dir / 'archive.hash'

    @property
    def file_hash(self):
        """ Load promised md5sum of content archive """
        with self.hash_file_location.open() as fp:
            return fp.read().replace('\n', '')

    def completed(self) -> bool:
        return self.target_file.is_file()

    def write_data(self, logger: SubmissionLogger, file_name: str, data: UploadFile):
        logger.log(f"adding a new part to upload: {file_name}")


        # Add the part
        with self.target_file.open('wb') as fp:
            for d in data.file:
                fp.write(d)

        calc_hash = md5sum(self.target_file)

        if not self.file_hash == calc_hash:
            # todo: more stuff see multipart fail
            self.target_file.unlink()
            raise exc.ValueNotValid("Hash does not match expected!")

        logger.log(f" --> file was uploaded successfully", date=False)


class ManifestIndexItem(BaseModel):
    """ Model representing a file item in the SplitManifest """
    file_name: str
    file_size: int
    file_hash: str

    def __eq__(self, other: 'ManifestIndexItem'):
        return self.file_hash == other.file_hash

    def __hash__(self):
        return int(self.file_hash, 16)


class MultipartUploadHandler(BaseModel):
    """ Data Model used for the binary split function as a manifest to allow merging """
    store_location: Path
    merge_hash: str
    index: Optional[List[ManifestIndexItem]]
    received: Optional[List[ManifestIndexItem]] = []
    multipart: bool = True
    hashed_parts: bool = True
    target_location: Path


    @property
    def target_file(self):
        return self.target_location / 'submission.zip'

    @property
    def success(self):
        return self.target_file.is_file()

    @property
    def remaining_items(self) -> set[ManifestIndexItem]:
        """ Return a set with remaining items """
        return set(self.index) - set(self.received)

    @property
    def remaining_nb(self) -> int:
        return len(self.remaining_items)

    def completed(self) -> bool:
        return len(self.received) == len(self.index)

    @classmethod
    def load_from_index(cls, file: Path):
        """ Load """
        with file.open() as fp:
            return cls.parse_obj(json.load(fp))

    def dump_to_index(self, file: Path):
        with file.open("w") as fp:
            fp.write(self.json(indent=4))

    def add_part(self, logger: SubmissionLogger, file_name: str, data: UploadFile):
        """ Add a part to a multipart upload type submission.

        - Write the data into a file inside the submission folder.

        :raises
            - JSONError, ValidationError: If manifest is not properly formatted
            - ResourceRequestedNotFound: if file not present in the manifest
            - ValueNotValid if md5 hash of file does not match md5 recorded in the manifest
        """
        logger.log(f"adding a new part to upload: {self.store_location / file_name}")
        # todo load information from index and name ???

        # write data on disk
        file_part = self.store_location / file_name
        with file_part.open('wb') as fp:
            for d in data.file:
                fp.write(d)

        calc_hash = md5sum(file_part)
        new_item_mf = ManifestIndexItem(
            file_name=file_name,
            file_hash=calc_hash,
            file_size=file_part.stat().st_size
        )

        if new_item_mf not in self.index:
            logger.log(f"(ERROR) file {file_name} was not found in manifest, upload canceled!!")
            file_part.unlink()
            logger.log(f"(ERROR) {data}, upload canceled!!")
            raise exc.ResourceRequestedNotFound(f"Part {file_name} is not part of submission {logger.submission_id}!!")

        # up count of received parts
        self.received.append(new_item_mf)
        logger.log(f" --> part was added successfully", date=False)

    def merge_parts(self):
        """ Merge parts into the target file using filesplit protocol """
        # TODO: update filesplit==3.0.2 to 4.0.0 (breaking upgrade)
        # for update see https://pypi.org/project/filesplit/
        if self.hashed_parts:
            for item in self.index:
                assert md5sum(self.store_location / item.file_name) == item.file_hash, \
                    f"file {item.file_name} does not match md5"

        df = pd.DataFrame([
            (i.file_name, i.file_size)
            for i in self.index
        ])
        df.columns = ['filename', 'filesize']
        df['encoding'] = np.nan
        df['header'] = np.nan
        df.to_csv((self.store_location / 'fs_manifest.csv'))
        fs = Filesplit()
        fs.merge(input_dir=f"{self.store_location}", output_file=str(self.target_file))
        assert md5sum(self.target_file) == self.merge_hash, "output file does not match original md5"


    def clean(self):
        """ Delete index & parts used for multipart upload """
        shutil.rmtree(self.store_location)
