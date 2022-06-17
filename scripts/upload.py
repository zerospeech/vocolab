#!/usr/bin/env python

import getpass
import json
import shutil
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, List

import pandas as pd
import requests
from Crypto.Hash import MD5
from fsplit.filesplit import Filesplit
from rich import print, inspect
from rich.progress import Progress
from rich.prompt import Prompt

SERVER_LOCATION: str = "http://localhost:8000"
CHALLENGE_ID: int = 1
CLIENT_ID: str = "cli_uploader"
CLIENT_SECRET: str = 'cli_uploader'
NB_RETRY_ATTEMPTS: int = 2
MULTIPART_THRESHOLD: int = 500000000  # in bytes


class ZrApiException(Exception):
    pass


@dataclass
class ManifestFileIndexItem:
    file_name: str
    file_size: int
    file_hash: Optional[str] = None

    def dict(self):
        return {f"{x}": getattr(self, x) for x in self.__dataclass_fields__.keys()}  # noqa: __dataclass_fields__ is dynamicly set

    @classmethod
    def from_dict(cls, data):
        return cls(**data)


@dataclass
class SplitManifest:
    """ A class containing information about archive split"""
    filename: str
    tmp_location: Path
    hash: str
    index: Optional[List[ManifestFileIndexItem]]
    multipart: bool = True
    hashed_parts: bool = True
    completed: int = 0

    def dict(self):
        data = {f"{x}": f"{getattr(self, x)}" for x in self.__dataclass_fields__.keys()} # noqa: __dataclass_fields__ is dynamicly set
        if "index" in data.keys():
            data["index"] = [
                item.dict() for item in self.index
            ]

        return data

    @classmethod
    def from_dict(cls, data):
        if "index" in data.keys():
            data["index"] = [
                ManifestFileIndexItem.from_dict(item) for item in data["index"]
            ]
        return cls(**data)


class UploadManifest:
    """ Fail-safe multi-part upload"""

    @classmethod
    def load(cls, filename: Path, retries: int = 2):
        with filename.open('r') as fp:
            dd = json.load(fp)
        return cls(dd["manifest"], filename, metadata=dd["metadata"], retries=retries)

    def __init__(self, list_manifest, save_file: Path, metadata=None, retries: int = 2):
        if isinstance(list_manifest, dict):
            self.man = list_manifest
        else:
            self.man = {
                f"{name}": 'todo'
                for name in list_manifest
            }
        self.save_file = save_file
        self.retries = retries
        if metadata:
            self._metadata = metadata
        else:
            self._metadata = {}
        self.save()

    def __iter__(self):
        return self

    @property
    def metadata(self):
        return self._metadata

    @metadata.setter
    def metadata(self, data):
        self._metadata.update(data)
        self.save()

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
            json.dump({
                "manifest": self.man,
                "metadata": self.metadata
            }, fp)

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
    if response.status_code != 200:
        print(f"[red]:x:{response.status_code}[/red]: {response.json().get('detail')}")
        sys.exit(1)

    return response.json().get("access_token")


def create_multipart_submission(challenge_id: int, file_meta: dict, _token: str):
    """..."""
    data = {
        "filename": file_meta["filename"],
        "hash": file_meta["hash"],
        "multipart": True,
        "index": file_meta['index']
    }

    return requests.post(
        f'{SERVER_LOCATION}/challenges/{challenge_id}/submission/create',
        json=data,
        headers={
            'Authorization': f'Bearer {_token}'
        })


def create_single_part_submission(challenge_id: int, filename: Path, _hash: str, _token: str):
    """..."""
    return requests.post(
        f'{SERVER_LOCATION}/challenges/{challenge_id}/submission/create',
        json={
            "filename": f"{filename}",
            "hash": _hash,
            "multipart": False
        },
        headers={
            'Authorization': f'Bearer {_token}'
        })


def submission_upload(challenge_id: int, submission_id: str, file: Path, _token: str):
    """..."""
    response = requests.put(
        f'{SERVER_LOCATION}/challenges/{challenge_id}/submission/upload',
        params={
            "part_name": file.name,
            "submission_id": f"{submission_id}"
        },
        files={f'file_data': file.open('rb').read()},
        headers={
            'Authorization': f'Bearer {_token}'
        }
    )
    return response


def split_zip_v2(zipfile: Path, chunk_max_size: int = 500000000, hash_parts: bool = True):
    """..."""
    assert zipfile.is_file(), f"entry file ({zipfile}) was not found"
    print(f"splitting {zipfile} into chunks...")

    tmp_loc = Path(tempfile.mkdtemp(dir=f"{zipfile.parents[0]}"))
    fs = Filesplit()
    fs.split(file=f"{zipfile}", split_size=chunk_max_size, output_dir=str(tmp_loc))
    df = pd.read_csv(tmp_loc / 'fs_manifest.csv')
    if hash_parts:
        df['hash'] = df.apply(lambda row: md5sum(
            (tmp_loc / row['filename'])), axis=1)
        index: List[ManifestFileIndexItem] = [ManifestFileIndexItem(file_name=x[0], file_size=x[1], file_hash=x[2])
                                              for x in zip(df['filename'], df['filesize'], df['hash'])]
    else:
        index: List[ManifestFileIndexItem] = [ManifestFileIndexItem(file_name=x[0], file_size=x[1])
                                              for x in zip(df['filename'], df['filesize'])]

    return SplitManifest(
        filename=zipfile.name,
        tmp_location=tmp_loc,
        hash=md5sum(zipfile),
        index=index,
        hashed_parts=hash_parts
    )


def ask_resume(file: Path):
    choice = "No"
    if file.is_file():
        choice = Prompt.ask("A checkpoint file was found. Do you wish to resume ?",
                            choices=["Yes", "No"])
        if choice == "No":
            file.unlink()

    return choice == "Yes"


def multipart_upload(challenge_id: int, zipfile: Path, _token: str, checkpoint: Path):
    print("preparing metadata....")

    # check for checkpoint
    if checkpoint.is_file():
        file_list = UploadManifest.load(checkpoint, retries=NB_RETRY_ATTEMPTS)
        tmp_location = Path(file_list.metadata.get("tmp_location"))
        _token = file_list.metadata.get('token')
        challenge_id = file_list.metadata.get("challenge_id")
    else:
        manifest = split_zip_v2(zipfile)
        file_list = [i.file_name for i in manifest.index]
        tmp_location = manifest.tmp_location
        meta = {
            "tmp_location": f"{tmp_location}",
            "filename": manifest.filename,
            "hash": manifest.hash,
            "index": [i.dict() for i in manifest.index],
            "token": _token,
            "challenge_id": challenge_id
        }
        file_list = UploadManifest(file_list, checkpoint, meta, retries=NB_RETRY_ATTEMPTS)

    # check if submission session exists
    if "submission_id" in file_list.metadata:
        submission_id = file_list.metadata.get('submission_id')
    else:
        response = create_multipart_submission(challenge_id, file_list.metadata, token)
        if response.status_code != 200:
            print(f'[red]:x:[/red][bold]Submission Creation Failed with code [red] {response.status_code}[/red][/bold]')
            inspect(response.json())
            sys.exit(1)

        submission_id = response.text.replace('"', '')
        file_list.metadata = {"submission_id": submission_id}

    with Progress() as progress:
        task1 = progress.add_task("[red]Uploading parts...", total=len(file_list.man))

        for item in file_list:
            file_list.set_waiting(item)
            progress.update(task1, advance=0.5)
            file_path = tmp_location / item
            print(f'uploading : {file_path.name}...')
            response = submission_upload(challenge_id, submission_id, file_path, _token)

            if response.status_code == 200:
                print(f'[green]:heavy_check_mark: {file_path}')
                file_list.set_done(item)
                progress.update(task1, advance=0.5)
            else:
                progress.update(task1, advance=-0.5)
                file_list.set_failed(item)

    if file_list.is_complete():
        checkpoint.unlink()
        shutil.rmtree(tmp_location)
        return []
    else:
        return file_list.get_failed()


def single_part_upload(challenge_id: int, zipfile: Path, _token: str):
    zip_hash = md5sum(zipfile)
    response = create_single_part_submission(challenge_id, filename=zipfile, _hash=zip_hash, _token=_token)

    if response.status_code != 200:
        print(f'[red]:x:[/red][bold]Submission Creation Failed with code [red] {response.status_code}[/red][/bold]')
        inspect(response.json())
        sys.exit(1)

    submission_id = response.text.replace('"', '').replace("'", '')
    response = submission_upload(challenge_id, submission_id, zipfile, _token)

    if response.status_code != 200:
        print(f'[red]:x:[/red][bold]Archive upload failed with code [red] {response.status_code}[/red][/bold]')
        inspect(response.json())
        sys.exit(1)


if __name__ == '__main__':
    archive_path = Path(sys.argv[1])
    if not archive_path.is_file() and archive_path.suffix != ".zip":
        raise ValueError(f"{archive_path} must be an existing zip file")

    multipart = archive_path.stat().st_size > MULTIPART_THRESHOLD * 2
    print(f"uploading as multipart: {multipart}")

    checkpoint_file = archive_path.parents[0] / f"{archive_path.stem}.checkpoint.json"
    if not ask_resume(checkpoint_file):
        token = login()
    else:
        token = ''

    if multipart:
        multipart_upload(CHALLENGE_ID, archive_path, token, checkpoint_file)
    else:
        single_part_upload(CHALLENGE_ID, archive_path, token)
