from datetime import datetime
from pathlib import Path
from typing import Optional, TextIO

from pydantic import BaseModel

from ..commons import ssh_exec
from ...settings import get_settings

_settings = get_settings()


class SubmissionLogger(BaseModel, arbitrary_types_allowed=True):
    """ Class managing individual logging of submission life-cycle """
    root_dir: Path
    fp_write: Optional[TextIO] = None

    @property
    def submission_id(self) -> str:
        return self.root_dir.name

    @property
    def submission_log(self) -> Path:
        """ File storing generic submission_logs"""
        return self.root_dir / 'submission.log'

    @property
    def eval_log_file(self) -> Path:
        """ Logfile storing latest evaluation process """
        return self.root_dir /  'evaluation.log'

    @property
    def slurm_log_file(self) -> Path:
        """ Logfile storing latest slurm output (used during eval process)"""
        return  self.root_dir / "slurm.log"

    def __enter__(self):
        """ Logging context open """
        self.fp_write = self.submission_log.open('a')
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """ Logging context close """
        if self.fp_write is not None:
            self.fp_write.close()
            self.fp_write = None

    @staticmethod
    def when():
        return f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

    def header(self, who: str, task: str,
               multipart: bool = False, has_scores: bool = True, auto_eval: bool = False):
        """
        who: user that did the submission (should be owner or admin)
        task: the benchmark/task that the submission correspongs
        has_scores: whether the submission has scores
        multipart: whether the submission was uploaded as multipart
        auto_eval: whether an auto-evaluation pipeline is set up for this submission
        """
        with self.submission_log.open('w') as fp:
            fp.write(f"[{self.when()}]: Submission {self.submission_id} was created\n")
            fp.write(f"--> user: {who}\n")
            fp.write(f"--> challenge: {task}\n")
            fp.write(f"--> has_scores: {has_scores}")
            fp.write(f"--> is_multipart: {multipart}\n")
            fp.write(f"--> auto_eval: {auto_eval}\n")

    @property
    def slurm_logs(self):
        """ """
        lines = []
        if self.slurm_log_file.is_file():
            with self.slurm_log_file.open() as fp:
                lines = fp.readlines()
        return lines

    def append_eval(self, eval_output):
        with self.eval_log_file.open('a') as fp:
            fp.write(f"-------- start of evaluation output --------\n")
            fp.write(f"---> {datetime.now().isoformat()}")
            fp.write(f"{eval_output.rstrip()}\n")
            for line in self.slurm_logs:
                fp.write(f"{line.strip()}\n")
            fp.write(f"-------- end of evaluation output ----------\n")

    def log(self, msg, date: bool = True):
        """ Create a new log entry """
        if date:
            msg = f"[{self.when()}] {msg}"

        if self.fp_write:
            self.fp_write.write(f"{msg}\n")
        else:
            with self.submission_log.open('a') as fp:
                fp.write(f"{msg}\n")

    def get_text(self):
        """ Get full submission log """
        if self.submission_log.is_file():
            with self.submission_log.open('r') as fp:
                return fp.readlines()
        return []

    def fetch_remote(self, host, remote_submission_location):
        """ Fetch eval & append log from remote """
        return_code, result = ssh_exec(host, [f'cat', f'{remote_submission_location}/{self.eval_log_file}'])
        if return_code == 0:
            self.log(result, date=False)
        else:
            self.log(f"Failed to fetch {host}:{remote_submission_location}/{self.submission_log} !!")

