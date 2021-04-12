#!/usr/bin/env python

from typing import Optional, Union, List, Tuple
from pathlib import Path
from dataclasses import dataclass
import requests
import getpass
import tempfile


from rich import inspect, print
from rich.prompt import Prompt
from fsplit.filesplit import Filesplit
from Crypto.Hash import MD5
import pandas as pd


SERVER_LOCATION: str = "http://127.0.0.1:8000/v1"
CLIENT_ID: str = "cli_uploader"
CLIENT_SECRET: str = 'cli_uploader'


@dataclass
class SplitManifest:
    filename: str
    tmp_location: Path
    hash: str
    index: Optional[Union[List[Tuple[str, int, str]], List[Tuple[str, int]]]]
    multipart: bool = True
    hashed_parts: bool = True
    completed: int = 0


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

    :returns: token<str> token used to authetify the current session
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
        for v in challenges if v.get('label') == name
        ), None)


def create_submission(challenge_id):
    """..."""
    response = requests.post(
        f'{SERVER_LOCATION}/v1/challenges/{challenge_id}/submission/create')
    return response


def split_zip_v2(zipfile: Path, chunk_max_size: int = 500000000,
                 hash_parts: bool = False):
    """..."""
    assert zipfile.is_file(), f"entry file ({zipfile}) was not found"

    tmp_loc = Path(tempfile.mkdtemp(dir=f"{zipfile.parents[0]}"))
    fs = Filesplit()
    fs.split(file=f"{zipfile}", split_size=chunk_max_size, output_dir=tmp_loc)
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


if __name__ == '__main__':
    print("testing")
    # token = login()
    # todo: select - challenge
    # todo: create sumbission session
    # todo: split file
    # todo: upload parts
    pass
