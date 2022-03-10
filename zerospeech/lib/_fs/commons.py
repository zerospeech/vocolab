import json
import shlex
import shutil
import subprocess
from pathlib import Path
from shutil import which
from typing import Union, Dict, List, Optional, Tuple
from zipfile import ZipFile

import yaml
from Crypto.Hash import MD5

from zerospeech import out


def load_dict_file(location: Path) -> Union[Dict, List]:
    """ Load a dict type file (json, yaml, toml)"""
    with location.open() as fp:
        if location.suffix == '.json':
            return json.load(fp)
        elif location.suffix in ('.yaml', 'yml'):
            return yaml.load(fp, Loader=yaml.FullLoader)
        else:
            raise ValueError('Not a known file type !!!')


def scp(src: Path, host: str, dest: Path, recursive=True):
    """ Copy files over using scp """
    if not src.is_file() and not src.is_dir():
        raise ValueError(f"Input {src} does not appear to exist as a file or directory !")

    return subprocess.run([which("scp"), f"{'-r' if recursive else ''}", f"{src}", f"{host}:{dest}"],
                          capture_output=True)


def rsync(*, src_host: Optional[str] = None, src: Path, dest_host: Optional[str] = None, dest: Path,
          flags: str = 'ahbuzP'):
    """ Synchronise two folders using the rsync tool.

    uses the following options in transfer:
        --delete   delete extraneous files from dest dirs
        -e ssh     Use ssh for resolving remote transfers
        --exclude=*.log Exclude log files from being transferred

    :param src_host: Hostname of containing source directory, if None directory is on localhost
    :param src: Path to source directory
    :param dest_host: Hostname of destination directory,
    :param dest:
    :param flags: flags to pass to rsync process  [ default ahbuzPe ]
        -a archive mode; sync whole directory as an archive
        -h human readable output
        -u makes rsync transfer skip files which are newer in dest than in src
        -b makes rsync backup files that exist in both folders, appending ~ to the old file.
           You can control this suffix with --suffix .suf
        -z turns on compression, which is useful when transferring easily-compressible files over slow links
        -P turns on --partial and --progress
            --partial makes rsync keep partially transferred files if the transfer is interrupted
            --progress shows a progress bar for each transfer, useful if you transfer big files
    :raises ...
    """
    source_path = f"{src}"
    if src_host:
        source_path = f"{src_host}:{src}"

    dest_path = f"{dest}"
    if dest_host:
        dest_path = f"{dest_host}:{dest}"

    cmd = f"{which('rsync')} -{flags}e ssh " \
          f"--delete --exclude=*.log --exclude=*.lock --exclude=*.zip " \
          f"{source_path}/ {dest_path}/"

    out.log.debug(f"> {cmd}")
    return subprocess.run(shlex.split(cmd), capture_output=True)


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


def unzip(archive: Path, output: Path):
    """ Unzips contents of a zip archive into the output directory """
    # create folder if it does not exist
    output.mkdir(exist_ok=True, parents=True)
    # open & extract
    with ZipFile(archive, 'r') as zipObj:
        zipObj.extractall(output)


def zip_folder(archive_file: Path, location: Path):
    with ZipFile(archive_file, 'w') as zip_obj:
        for file in filter(lambda x: x.is_file(), location.rglob("*")):
            zip_obj.write(file, str(file.relative_to(location)))


def ssh_exec(host, cmd: List[str]) -> Tuple[int, str]:
    """ Execute a command remotely via ssh

    :param host Name of the host to connect to
    :param cmd List containing command & arguments to execute on remote host
    :returns return_code<int>, output<str>

    :output is stdout if return code is success or stderr otherwise
    """
    ssh_cmd = which('ssh')
    if not ssh_cmd:
        raise EnvironmentError('SSH was not found on system')

    cmd = [ssh_cmd, f"{host}", *cmd]
    result = subprocess.run(cmd, capture_output=True)
    if result.returncode == 0:
        return result.returncode, result.stdout.decode()
    return result.returncode, result.stderr.decode()


def check_host(host):
    """ Checks if a remote host is reachable raises ConnectionError if not"""
    ssh_cmd = which('ssh')
    if not ssh_cmd:
        raise EnvironmentError('SSH was not found on system')

    res = subprocess.run(
        [ssh_cmd, "-q", f"{host}", "exit"]
    )
    if res.returncode != 0:
        raise ConnectionError(f'Service was unable to connect to Host({host})')


def copy_all_contents(source: Path, target: Path, *, prefix: Optional[str] = None):
    """ Copy all files included in source directory

    :param source: directory from which to copy files
    :param target: directory to copy files to
    :param prefix: prefix to add to all copied files
    """
    if not source.is_dir():
        raise ValueError(f'Source {source} must be a directory')

    if not target.is_dir():
        raise ValueError(f'Target {target} must be a directory')

    for file in [f for f in source.rglob("*") if f.is_file()]:
        if prefix is not None:
            shutil.copyfile(file, target / f"{prefix}_{file.name}")
        else:
            shutil.copyfile(file, target / file.name)

