import hashlib
import os
from zerospeech.lib import _fs

# export functions
update_user_data = _fs.users.update_user_data
get_user_data = _fs.users.get_user_data


def hash_pwd(*, password: str, salt=None):
    """ Creates a hash of the given password.
        If salt is None generates a random salt.

        :arg password<str> the password to hash
        :arg salt<bytes> a value to salt the hashing
        :returns hashed_password, salt
    """

    if salt is None:
        salt = os.urandom(32)  # make random salt

    hash_pass = hashlib.pbkdf2_hmac(
        'sha256',  # The hash digest algorithm for HMAC
        password.encode('utf-8'),  # Convert the password to bytes
        salt,  # Provide the salt
        100000  # It is recommended to use at least 100,000 iterations of SHA-256
    )
    return hash_pass, salt
