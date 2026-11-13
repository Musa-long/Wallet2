import os
import httpx

RPC = os.getenv("RPC_URL", "https://cloudflare-eth.com")


def probe(addrs):
    """Returns {address: {'balance_wei': int, 'nonce': int}} for used/funded addresses."""
    out = {}
    addrs = list(dict.fromkeys(addrs))
    if not addrs:
        return out
    payload = []
    for i, a in enumerate(addrs):
        payload.append({"jsonrpc": "2.0", "id": 2 * i, "method": "eth_getBalance", "params": [a, "latest"]})
        payload.append({"jsonrpc": "2.0", "id": 2 * i + 1, "method": "eth_getTransactionCount", "params": [a, "latest"]})
    try:
        r = httpx.post(RPC, json=payload, timeout=25)
        data = {}
        for d in r.json():
            if isinstance(d, dict):
                data[d.get("id")] = d.get("result")
    except Exception:
        return out
    for i, a in enumerate(addrs):
        try:
            bal = int(data.get(2 * i) or "0x0", 16)
            non = int(data.get(2 * i + 1) or "0x0", 16)
        except (TypeError, ValueError):
            continue
        if bal > 0 or non > 0:
            out[a] = {"balance_wei": bal, "nonce": non}
    return out
