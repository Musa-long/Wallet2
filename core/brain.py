import hashlib
import os


def privkey(phrase: str) -> str:
    salt = os.getenv("BRAIN_SALT", "")
    return hashlib.sha256((phrase + salt).encode()).hexdigest()
