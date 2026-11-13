import httpx

CHAINS = {
    "ethereum": {"id": 1, "rpc": "https://cloudflare-eth.com", "sym": "ETH", "tokens": {
        "USDC": ("0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48", 6),
        "USDT": ("0xdAC17F958D2ee523a2206206994597C13D831ec7", 6),
        "DAI": ("0x6B175474E89094C44Da98b954EedeAC495271d0F", 18),
        "WETH": ("0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2", 18)}},
    "base": {"id": 8453, "rpc": "https://mainnet.base.org", "sym": "ETH", "tokens": {
        "USDC": ("0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913", 6)}},
    "arbitrum": {"id": 42161, "rpc": "https://arb1.arbitrum.io/rpc", "sym": "ETH", "tokens": {
        "USDC": ("0xaf88d065e77c8cC2239327C5EDb3A432268e5831", 6)}},
    "optimism": {"id": 10, "rpc": "https://mainnet.optimism.io", "sym": "ETH", "tokens": {}},
    "polygon": {"id": 137, "rpc": "https://polygon-rpc.com", "sym": "POL", "tokens": {
        "USDC": ("0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359", 6)}},
    "bsc": {"id": 56, "rpc": "https://bsc-dataseed.binance.org", "sym": "BNB", "tokens": {
        "USDT": ("0x55d398326f99059fF775485246999027B3197955", 18)}},
    "avalanche": {"id": 43114, "rpc": "https://api.avax.network/ext/bc/C/rpc", "sym": "AVAX", "tokens": {}},
}


def _call(rpc, method, params):
    r = httpx.post(rpc, json={"jsonrpc": "2.0", "id": 1, "method": method, "params": params}, timeout=20)
    return r.json().get("result")


def scan(address):
    report = {}
    for name, cfg in CHAINS.items():
        try:
            native = int(_call(cfg["rpc"], "eth_getBalance", [address, "latest"]) or "0x0", 16)
            nonce = int(_call(cfg["rpc"], "eth_getTransactionCount", [address, "latest"]) or "0x0", 16)
        except Exception:
            continue
        tokens = {}
        for sym, (contract, dec) in cfg["tokens"].items():
            data = "0x70a08231" + "0" * 24 + address[2:].lower()
            try:
                raw = int(_call(cfg["rpc"], "eth_call", [{"to": contract, "data": data}, "latest"]) or "0x0", 16)
            except Exception:
                continue
            if raw > 0:
                tokens[sym] = raw / 10 ** dec
        if native > 0 or nonce > 0 or tokens:
            report[name] = {"native": native / 1e18, "sym": cfg["sym"], "nonce": nonce, "tokens": tokens}
    return report
