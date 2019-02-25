import binascii
import hashlib
import random


def get_random_hash():
    """Get a randomized hash."""
    return "%040x" % random.getrandbits(40 * 4)


# def hash_password(password):
#     """Convert a password to being hashed."""
#     dk = hashlib.pbkdf2_hmac(
#         PASSWORD_ALGORITHM,
#         password.encode("utf-8"),
#         PASSWORD_SALT.encode("utf-8"),
#         PASSWORD_ROUNDS,
#     )
#     return binascii.hexlify(dk).decode("utf-8")


# def password_is_valid(password, hashed):
#     return hash_password(password) == hashed
