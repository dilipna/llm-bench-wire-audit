"""A transparent logging proxy that records ground truth for streamed LLM requests.

Every benchmark tool talks to this proxy instead of the server. For each request it
writes one JSON line with the time the request arrived and the arrival time of every
server-sent event, so TTFT, ITL, TPOT and throughput can be recomputed from the wire,
independently of how any benchmark tool defines or computes them.

    python wire_proxy.py --listen 8001 --upstream http://127.0.0.1:8000 --log run.jsonl
"""

import argparse
import asyncio
import json
import time

import aiohttp
from aiohttp import web


def _content_of(event):
    """Return (text, usage, has_choice) from one parsed completion or chat-completion event.

    has_choice is true for any event that carries a choice, even with empty text: the
    server emits one such event per generated token, and a token that is only part of a
    multi-byte character decodes to an empty string.
    """
    usage = event.get("usage")
    choices = event.get("choices") or []
    if not choices:
        return "", usage, False
    choice = choices[0]
    text = choice.get("text")
    if text is None:
        delta = choice.get("delta") or {}
        text = (delta.get("content") or "") + (delta.get("reasoning_content") or "")
    return text or "", usage, True


async def handle(request: web.Request) -> web.StreamResponse:
    state = request.app["state"]
    body = await request.read()
    t_arrival = time.perf_counter()
    state["count"] += 1
    record = {
        "req": state["count"],
        "path": request.path,
        "t_arrival": t_arrival,
        "wall_arrival": time.time(),
        "body": body[:2000].decode("utf-8", "replace") if state["count"] <= 3 else None,
        "body_bytes": len(body),
        "events": [],
        "status": None,
        "usage": None,
    }
    headers = {
        k: v
        for k, v in request.headers.items()
        if k.lower() not in ("host", "content-length", "connection")
    }
    try:
        async with state["session"].request(
            request.method, state["upstream"] + request.path_qs, data=body, headers=headers
        ) as upstream:
            record["status"] = upstream.status
            resp = web.StreamResponse(
                status=upstream.status,
                headers={
                    k: v
                    for k, v in upstream.headers.items()
                    if k.lower() not in ("content-length", "transfer-encoding", "connection")
                },
            )
            await resp.prepare(request)
            data_lines = 0
            async for line in upstream.content:
                if line.startswith(b"data:"):
                    data_lines += 1
                    if state["stall_ms"] and data_lines == state["stall_at"]:
                        # fault injection: every request freezes once, mid-stream
                        await asyncio.sleep(state["stall_ms"] / 1000)
                now = time.perf_counter()
                await resp.write(line)
                stripped = line.strip()
                if stripped.startswith(b"data:"):
                    payload = stripped[5:].strip()
                    if payload == b"[DONE]":
                        record["events"].append([now, -1, 0])
                        continue
                    try:
                        text, usage, has_choice = _content_of(json.loads(payload))
                    except ValueError:
                        text, usage, has_choice = "", None, False
                    if usage:
                        record["usage"] = usage
                    # kind: 1 = text, 2 = choice with empty text, 0 = neither (usage only)
                    record["events"].append([now, len(text), 1 if text else (2 if has_choice else 0)])
            await resp.write_eof()
    finally:
        record["t_done"] = time.perf_counter()
        with open(state["log"], "a") as f:
            f.write(json.dumps(record) + "\n")
    return resp


async def main(args):
    open(args.log, "w").close()
    app = web.Application(client_max_size=1 << 30)
    app["state"] = {
        "count": 0,
        "upstream": args.upstream.rstrip("/"),
        "log": args.log,
        "stall_ms": args.stall_ms,
        "stall_at": args.stall_at,
        "session": aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=None),
            connector=aiohttp.TCPConnector(limit=0),
        ),
    }
    app.router.add_route("*", "/{tail:.*}", handle)
    runner = web.AppRunner(app, access_log=None)
    await runner.setup()
    await web.TCPSite(runner, "0.0.0.0", args.listen).start()
    print(f"proxy on :{args.listen} -> {args.upstream}, log {args.log}", flush=True)
    await asyncio.Event().wait()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--listen", type=int, default=8001)
    ap.add_argument("--upstream", default="http://127.0.0.1:8000")
    ap.add_argument("--log", default="run.jsonl")
    ap.add_argument("--stall-ms", type=float, default=0, help="freeze every stream once for this long")
    ap.add_argument("--stall-at", type=int, default=20, help="...before forwarding this data event")
    asyncio.run(main(ap.parse_args()))
