from datetime import datetime
from pathlib import Path

from zerospeech import get_settings

_settings = get_settings()


def get_submission_dir(submission_id: str) -> Path:
    """ Returns the directory containing the submission data based on the given id"""
    return _settings.SUBMISSION_DIR / submission_id


class SubmissionLogger:
    """ Class managing individual logging of submissions """

    @classmethod
    def log_filename(cls):
        return 'submission.log'

    def __init__(self, submission_id):
        self.id = submission_id
        self.submission_dir = get_submission_dir(submission_id)
        self.submission_log = self.submission_dir / self.log_filename()
        self.fp = None

    def __enter__(self):
        self.fp = self.submission_log.open('a')
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.fp is not None:
            self.fp.close()
            self.fp = None

    @staticmethod
    def when():
        return f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

    def header(self, who, what, multipart):
        with self.submission_log.open('w') as fp:
            fp.write(f"[{self.when()}]: Submission {self.id} was created\n")
            fp.write(f"--> user: {who}\n")
            fp.write(f"--> challenge: {what}\n")
            fp.write(f"--> as multipart: {multipart}")

    def append_eval(self, eval_output):
        with self.submission_log.open('a') as fp:
            fp.write(f"-------- start of evaluation output --------\n")
            fp.write(f"{eval_output.rstrip()}\n")
            fp.write(f"-------- end of evaluation output ----------\n")

    def log(self, msg, append=False):
        if not append:
            msg = f"[{self.when()}] {msg}"

        if self.fp:
            self.fp.write(f"{msg}\n")
        else:
            with self.submission_log.open('a') as fp:
                fp.write(f"{msg}\n")

    def get_text(self):
        with self.submission_log.open('r') as fp:
            return fp.readlines()

