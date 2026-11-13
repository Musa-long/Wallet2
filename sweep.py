import sys

import httpx
from eth_account import Account

from core.scan import CHAINS


def _rpc(url, method, params):
    r = httpx.post(url, json={"jsonrpc": "2.0", "id": 1, "method": method, "params": params}, timeout=30)
    j = r.json()
    if "error" in j:
        raise RuntimeError(j["error"])
    return j["result"]


def sweep(privkey, chain, dest):
    cfg = CHAINS[chain]
    acct = Account.from_key(privkey)
    nonce = int(_rpc(cfg["rpc"], "eth_getTransactionCount", [acct.address, "pending"]), 16)
    gas_price = int(_rpc(cfg["rpc"], "eth_gasPrice", []), 16)
    bal = int(_rpc(cfg["rpc"], "eth_getBalance", [acct.address, "latest"]), 16)
    cost = 21000 * gas_price
    if bal <= cost:
        return f"no gas: balance {bal} <= cost {cost}. Fund it first."
    tx = {
        "nonce": nonce,
        "to": dest,
        "value": bal - cost,
        "gas": 21000,
        "gasPrice": gas_price,
        "chainId": cfg["id"],
    }
    signed = acct.sign_transaction(tx)
    raw = getattr(signed, "raw_transaction", None) or signed.rawTransaction
    txhash = _rpc(cfg["rpc"], "eth_sendRawTransaction", ["0x" + raw.hex()])
    return f"sent on {chain}: {txhash}"


if __name__ == "__main__":
    key, chain, dest = sys.argv[1], sys.argv[2], sys.argv[3]
    print(sweep(key, chain, dest))
