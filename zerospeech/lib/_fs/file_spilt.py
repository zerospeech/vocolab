import shutil
import subprocess
import tempfile
from pathlib import Path
from shutil import which
from typing import List, Tuple

import numpy as np
import pandas as pd
from fsplit.filesplit import Filesplit

from zerospeech.db import models
from .commons import md5sum


def split_zip_v1(zipfile: Path, chunk_max_size: str = "500m", hash_parts: bool = False):
    """Splits a big zip file into smaller ones for easier uploads/downloads
    USES: linux split command.

    Zip chunks are placed in a temp folder named with the following scheme :
    0: split.zip
    1: split.z01
    ...
    n: split.z(n)

    where n is the number of chunks minus 1 (starts at 0).
    Split function will try to approximate the chunk_max_size for each chunk.
    :returns {
        location: the location of the splitted items (useful for later clean-up)
        items: the list of file parts (with their individual (md5) hashes if hash_parts is True)
        hash: the md5 of original archive to verify integrity when joining
    }
    """
    assert zipfile.is_file(), f"entry file ({zipfile}) was not found"
    tmp_loc = Path(tempfile.mkdtemp(dir=f"{zipfile.parents[0]}"))
    # todo add try for possible errors
    subprocess.run([which("split"), '-b', f"{chunk_max_size}", f"{zipfile}", f"{tmp_loc}/part_"])

    if hash_parts:
        item_list = []
        for x in tmp_loc.rglob("split.*"):
            item_list.append((x.name, md5sum(x)))
    else:
        item_list = [x.name for x in tmp_loc.rglob("split.*")]

    return dict(
        location=tmp_loc,
        items=item_list,
        hash=md5sum(zipfile)
    )


# noinspection PyTypeChecker
def split_zip_v2(zipfile: Path, chunk_max_size: int = 500000000, hash_parts: bool = False):
    assert zipfile.is_file(), f"entry file ({zipfile}) was not found"
    tmp_loc = Path(tempfile.mkdtemp(dir=f"{zipfile.parents[0]}"))
    fs = Filesplit()
    fs.split(file=f"{zipfile}", split_size=chunk_max_size, output_dir=tmp_loc)
    df = pd.read_csv(tmp_loc / 'fs_manifest.csv')
    if hash_parts:
        df['hash'] = df.apply(lambda row: md5sum((tmp_loc / row['filename'])), axis=1)
        index: List[Tuple[str, int, str]] = list(zip(df['filename'], df['filesize'], df['hash']))
    else:
        index: List[Tuple[str, int]] = list(zip(df['filename'], df['filesize']))

    return models.file_split.SplitManifest(
        filename=zipfile.name,
        tmp_location=tmp_loc,
        hash=md5sum(zipfile),
        index=index,
        hashed_parts=hash_parts
    )


def merge_zip_v2(manifest: models.file_split.SplitManifest, output_location: Path, clean: bool = True):
    if manifest.hashed_parts:
        for item in manifest.index:
            assert md5sum(manifest.tmp_location / item.file_name) == item.file_hash, \
                f"file {item.file_name} does not match md5"

    df = pd.DataFrame([
        (i.file_name, i.file_size)
        for i in manifest.index
    ])
    df.columns = ['filename', 'filesize']
    df['encoding'] = np.nan
    df['header'] = np.nan
    df.to_csv((manifest.tmp_location / 'fs_manifest.csv'))
    fs = Filesplit()
    fs.merge(input_dir=f"{manifest.tmp_location}", output_file=f"{output_location / manifest.filename}")
    assert md5sum(output_location / manifest.filename) == manifest.hash, "output file does not match original md5"

    if clean:
        shutil.rmtree(manifest.tmp_location)
    return output_location / manifest.filename


""" V2 is the preferred method to be used 
Notes: 
    - V2 depends on https://pypi.org/project/filesplit/
    - V1 should probably not be used and exists as a note in case i need an example implementation

If the dependency on filesplit must be removed its better to create a more stable V3 based on V1

!!! Always use same split as merge as merge_v2 depends on manifest created during split

Normalized function names to hide versioning to external users
"""
split_zip = split_zip_v2
merge_zip = merge_zip_v2
