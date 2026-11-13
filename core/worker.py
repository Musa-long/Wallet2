import threading

from . import bip39, chain, derive, jobs, brain, login

BATCH = 40


def _probe(job, batch, cache):
    fresh = [a for a, _ in batch if a not in cache]
    found = chain.probe(fresh) if fresh else {}
    for a, meta in batch:
        if a in found:
            cache.add(a)
            job.hit(a, found[a], meta.get("mnemonic"), meta.get("secret"))


def _check(job, cache, batch, mn=None, secret=None):
    try:
        a = derive.address(mn) if mn else secret
    except Exception:
        return
    batch.append((a, {"mnemonic": mn, "secret": secret}))
    if len(batch) >= BATCH:
        _probe(job, batch, cache)
        batch.clear()


def run_seed(job):
    W = bip39.words()
    IX = bip39.index_map()
    tpl = job.params["template"].strip().lower().split()
    mode = job.params.get("mode", "one_wrong")
    n = len(tpl)
    if n not in (12, 15, 18, 21, 24):
        raise ValueError("phrase must be 12/15/18/21/24 words")

    if mode == "one_wrong":
        idx = [IX.get(w, -1) for w in tpl]
        unknown = [i for i, v in enumerate(idx) if v < 0]
        if unknown:
            raise ValueError("one_wrong needs all 12 words valid; use 'missing' for ?")
        job.total = n * 2048
        cands = ([v if k != p else s for k, v in enumerate(idx)] for p in range(n) for s in range(2048))
    elif mode == "missing":
        idx = [IX.get(w, -1) for w in tpl]
        holes = [i for i, v in enumerate(idx) if v < 0]
        if len(holes) == 1:
            job.total = 2048
            h = holes[0]
            cands = ([v if k != h else s for k, v in enumerate(idx)] for s in range(2048))
        elif len(holes) == 2:
            job.total = 2048 * 2048
            a, b = holes
            def gen():
                for s1 in range(2048):
                    for s2 in range(2048):
                        yield [v if k not in holes else (s1 if k == a else s2) for k, v in enumerate(idx)]
            cands = gen()
        else:
            raise ValueError("missing supports 1 or 2 unknown positions")
    elif mode == "swap":
        idx = [IX.get(w, -1) for w in tpl]
        if any(v < 0 for v in idx):
            raise ValueError("swap needs all words valid")
        pairs = [(i, j) for i in range(n) for j in range(i + 1, n)]
        job.total = len(pairs)
        def gen():
            for i, j in pairs:
                c = list(idx)
                c[i], c[j] = c[j], c[i]
                yield c
        cands = gen()
    else:
        raise ValueError("unknown mode")

    cache, batch = set(), []
    job.note(f"mode={mode} theoretical={job.total}")
    for c in cands:
        if job.stop_flag.is_set():
            break
        job.checked += 1
        if not bip39.checksum_ok(c):
            continue
        _check(job, cache, batch, mn=bip39.to_mnemonic(c))
        if job.checked % 4000 == 0:
            job.note(f"checked {job.checked}")
    if batch:
        _probe(job, batch, cache)
    job.note("done")


def run_brain(job):
    words = [w.strip() for w in job.params["words"].splitlines() if w.strip()]
    joiners = job.params.get("joiners", " ,.,_,-")
    patterns = job.params.get("patterns", "{a}{b}")
    suffixes = [s.strip() for s in job.params.get("suffixes", "").split(",") if s.strip()]
    idx = 0
    cache, batch = set(), []
    job.total = len(words) ** 2 * len(suffixes or [""])
    for a in words:
        for b in words:
            for p in patterns.split("|"):
                for s in (suffixes or [""]):
                    if job.stop_flag.is_set():
                        return
                    phrase = p.replace("{a}", a).replace("{b}", b) + s
                    idx += 1
                    job.checked += 1
                    try:
                        key = brain.privkey(phrase)
                        from bip_utils import EthPrivateKey
                        addr = EthPrivateKey.FromHex(key).PublicKey().ToAddress()
                    except Exception:
                        continue
                    batch.append((addr, {"secret": phrase}))
                    if len(batch) >= BATCH:
                        _probe(job, batch, cache)
                        batch.clear()
                    if idx % 5000 == 0:
                        job.note(f"{idx} phrases")
    if batch:
        _probe(job, batch, cache)
    job.note("done")


def run_login(job):
    login.run(job)


RUNNERS = {"seed": run_seed, "brain": run_brain, "login": run_login}


def start(job):
    def boot():
        try:
            RUNNERS[job.mode](job)
            job.state = "finished" if not job.stop_flag.is_set() else "stopped"
        except Exception as e:
            job.state = "error"
            job.note(f"ERROR {e}")
    t = threading.Thread(target=boot, daemon=True)
    t.start()
    return job


def stop(job):
    job.stop_flag.set()
