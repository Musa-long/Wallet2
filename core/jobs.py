import threading
import time
import uuid


class Job:
    def __init__(self, mode, params):
        self.id = uuid.uuid4().hex[:12]
        self.mode = mode
        self.params = params
        self.state = "running"
        self.checked = 0
        self.total = 0
        self.hits = []
        self.log = []
        self.started = time.time()
        self.stop_flag = threading.Event()

    def note(self, msg):
        self.log.append(f"[{time.strftime('%H:%M:%S')}] {msg}")
        self.log[:] = self.log[-300:]

    def hit(self, addr, info, mnemonic=None, secret=None):
        self.hits.append({
            "address": addr,
            "balance_eth": info["balance_wei"] / 1e18,
            "nonce": info["nonce"],
            "mnemonic": mnemonic,
            "secret": secret,
        })
        self.note(f"HIT {addr} bal={info['balance_wei']/1e18:.6f} nonce={info['nonce']}")

    def snapshot(self):
        el = max(time.time() - self.started, 0.001)
        return {
            "id": self.id,
            "mode": self.mode,
            "state": self.state,
            "checked": self.checked,
            "total": self.total,
            "rate": round(self.checked / el, 1),
            "elapsed": round(el, 1),
            "hits": self.hits,
            "log": self.log,
        }


JOBS = {}


def create(mode, params):
    j = Job(mode, params)
    JOBS[j.id] = j
    return j
