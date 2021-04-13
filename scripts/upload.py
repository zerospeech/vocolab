#!/usr/bin/env python

import getpass
import json
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Union, List, Tuple

import pandas as pd
import requests
from Crypto.Hash import MD5
from fsplit.filesplit import Filesplit
from rich import print
from rich.prompt import Prompt

SERVER_LOCATION: str = "http://127.0.0.1:8000/v1"
CLIENT_ID: str = "cli_uploader"
CLIENT_SECRET: str = 'cli_uploader'
NB_RETRY_ATTEMPTS: int = 2


@dataclass
class SplitManifest:
    filename: str
    tmp_location: Path
    hash: str
    index: Optional[Union[List[Tuple[str, int, str]], List[Tuple[str, int]]]]
    multipart: bool = True
    hashed_parts: bool = True
    completed: int = 0


class UploadManifest:
    """ Fail-safe multi-part upload"""

    @classmethod
    def load(cls, filename: Path, retries: int = 2):
        with filename.open('r') as fp:
            dd = json.load(fp)
        return cls(dd, filename, retries)

    def __init__(self, list_manifest, save_file: Path, retries: int = 2):
        if isinstance(list_manifest, dict):
            self.man = list_manifest
        else:
            self.man = {
                f"{name}": 'todo'
                for name in list_manifest
            }
        self.save_file = save_file
        self.retries = retries
        self.save()

    def __iter__(self):
        return self

    def __next__(self):
        for k, v in self.man.items():
            if v == 'todo':
                return k
        for k, v in self.man.items():
            if v == 'waiting':
                return k
        for k, v in self.man.items():
            if 'retry' in v:
                return k
        raise StopIteration

    def status(self, key):
        return self.man[key]

    def set_waiting(self, key):
        if self.man[key] == 'todo':
            self.man[key] = "waiting"
            self.save()

    def set_done(self, key):
        self.man[key] = "done"
        self.save()

    def set_failed(self, key):
        k = self.man[key]
        if k in ["waiting", "todo"]:
            self.man[key] = "retry_1"
        elif "retry" in k:
            nb = int(k.split('_')[1])
            nb += 1
            if nb > self.retries:
                st = 'failed'
            else:
                st = f"retry_{nb}"
            self.man[key] = st
        self.save()

    def save(self):
        with self.save_file.open('w') as fp:
            json.dump(self.man, fp)

    def is_complete(self):
        for k, v in self.man.items():
            if v != "done":
                return False
        return True

    def get_failed(self):
        return [k for k, v in self.man.items() if v == 'failed']

    def clear(self):
        # remove checkpoint file
        self.save_file.unlink()


def md5sum(file_path: Path, chunk_size: int = 8192):
    """ Return a md5 hash of a files content """
    h = MD5.new()

    with file_path.open('rb') as f:
        while True:
            chunk = f.read(chunk_size)
            if len(chunk):
                h.update(chunk)
            else:
                break
    return h.hexdigest()


def login():
    """ Create a session in zerospeech.com

    :returns: token<str> token used to authentify the current session
    """
    user = input('Username: ')
    pwd = getpass.getpass("Password: ")

    # request login from server
    response = requests.post(
        f'{SERVER_LOCATION}/auth/login',
        data={
            "grant_type": "password",
            "username": user,
            "password": pwd,
            "scopes": [],
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET
        }
    )

    return response.json().get("access_token")


def select_challenge():
    """..."""
    response = requests.get(
        f"{SERVER_LOCATION}/challenges/", params={"include_inactive": "true"})
    if response.status_code != 200:
        raise ValueError('Request to server Failed !!')

    challenges = response.json()
    choices = [ch.get('label') for ch in challenges]
    name = Prompt.ask("Choose one of the available challenges: ",
                      choices=choices, default=choices[0])
    return next((
        (v.get('id'), v.get('label'))
        for v in challenges if v.get('label') == name), None)


def create_multipart_submission(challenge_id: int, manifest: SplitManifest, _token: str):
    """..."""
    response = requests.post(
        f'{SERVER_LOCATION}/v1/challenges/{challenge_id}/submission/create',
        data={
            "filename": manifest.filename,
            "hash": manifest.hash,
            "multipart": 'true',
            "index": manifest.index
        },
        headers={
            'Authentication': f'BEARER {_token}'
        })
    return response


def create_single_part_submission(challenge_id: int, filename: Path, _hash: str, _token: str):
    """..."""
    response = requests.post(
        f'{SERVER_LOCATION}/v1/challenges/{challenge_id}/submission/create',
        data={
            "filename": f"{filename}",
            "hash": _hash,
        },
        headers={
            'Authentication': f'BEARER {_token}'
        })

    if response.status_code != 200:
        raise ValueError('Request to server Failed !!')

    return response.text


def split_zip_v2(zipfile: Path, chunk_max_size: int = 500000000, hash_parts: bool = True):
    """..."""
    assert zipfile.is_file(), f"entry file ({zipfile}) was not found"

    tmp_loc = Path(tempfile.mkdtemp(dir=f"{zipfile.parents[0]}"))
    fs = Filesplit()
    fs.split(file=f"{zipfile}", split_size=chunk_max_size, output_dir=str(tmp_loc))
    df = pd.read_csv(tmp_loc / 'fs_manifest.csv')
    if hash_parts:
        df['hash'] = df.apply(lambda row: md5sum(
            (tmp_loc / row['filename'])), axis=1)
        index: List[Tuple[str, int, str]] = list(
            zip(df['filename'], df['filesize'], df['hash']))
    else:
        index: List[Tuple[str, int]] = list(
            zip(df['filename'], df['filesize']))

    return SplitManifest(
        filename=zipfile.name,
        tmp_location=tmp_loc,
        hash=md5sum(zipfile),
        index=index,
        hashed_parts=hash_parts
    )


def multipart_upload(challenge_id: int, zipfile: Path, _token: str):
    manifest = split_zip_v2(zipfile)
    response = create_multipart_submission(ch_id, manifest, _token)
    file_list = [i[0] for i in manifest.index]
    checkpoint = zipfile.parents[0] / f"{zipfile.stem}.checkpoint.json"

    if checkpoint.is_file():
        file_list = UploadManifest.load(checkpoint, retries=NB_RETRY_ATTEMPTS)
    else:
        file_list = UploadManifest(file_list, checkpoint, retries=NB_RETRY_ATTEMPTS)

    for item in file_list:
        file_list.set_waiting(item)
        # todo upload request
        response = ...

        if response.status_code == 200:
            file_list.set_done(item)
        else:
            file_list.set_failed(item)

    if file_list.is_complete():
        return []
    else:
        return file_list.get_failed()


def single_part_upload(challenge_id: int, zipfile: Path, _token: str):
    zip_hash = md5sum(zipfile)
    response = create_single_part_submission(challenge_id, filename=zipfile, _hash=zip_hash, _token=_token)

    # todo upload request
    response = ...


if __name__ == '__main__':
    print("testing")
    multipart = ...
    archive_path = ...
    token = login()
    ch_id, _ = select_challenge()
    if multipart:
        multipart_upload(ch_id, ..., ...)
    else:
        single_part_upload(ch_id, archive_path, token)
    # todo: create submission session
    # todo: split file
    # todo: upload parts
