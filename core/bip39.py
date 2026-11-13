import hashlib
import os
import urllib.request

URL = "https://raw.githubusercontent.com/bitcoin/bips/master/bip-0039/english.txt"
PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "english.txt")

_W = None
_IX = None


def words():
    global _W
    if _W is None:
        if not os.path.exists(PATH):
            os.makedirs(os.path.dirname(PATH), exist_ok=True)
            urllib.request.urlretrieve(URL, PATH)
        with open(PATH, "r", encoding="utf-8") as f:
            _W = [w.strip() for w in f if w.strip()]
        assert len(_W) == 2048, "bad wordlist"
    return _W


def index_map():
    global _IX
    if _IX is None:
        _IX = {w: i for i, w in enumerate(words())}
    return _IX


def checksum_ok(idxs):
    bits = 0
    for i in idxs:
        bits = (bits << 11) | i
    total = 11 * len(idxs)
    cs_len = total - (total * 32 // 33)
    ent_len = total - cs_len
    ent = bits >> cs_len
    cs = bits & ((1 << cs_len) - 1)
    h = hashlib.sha256(ent.to_bytes(ent_len // 8, "big")).digest()
    return (h[0] >> (8 - cs_len)) == cs


def to_mnemonic(idxs):
    W = words()
    return " ".join(W[i] for i in idxs)
