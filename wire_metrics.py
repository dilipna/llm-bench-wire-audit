"""Recompute benchmark metrics from a wire_proxy.py log.

Definitions used for the ground truth (stated so they can be argued with):
  token event  = a streamed event that carries a choice (the server sends one per token)
  text event   = a token event whose decoded text is not empty
  TTFT  = arrival of the first token (or text) event, minus request arrival
  ITL   = gap between consecutive token (or text) events of one request, one per gap
  TPOT  = (last token event - first token event) / (output_tokens - 1)
  E2E   = last event minus request arrival
  output tokens = usage.completion_tokens when the server reports it
Throughput is measured from the first request arrival to the last request's end.
Only generation requests (/v1/completions, /v1/chat/completions) are counted; the
tools' own /tokenize and /metrics calls are ignored.
"""

import json
import statistics
import sys

GENERATION_PATHS = ("/v1/completions", "/v1/chat/completions")


def pct(values, q):
    if not values:
        return float("nan")
    values = sorted(values)
    k = (len(values) - 1) * q / 100
    lo, hi = int(k), min(int(k) + 1, len(values) - 1)
    return values[lo] + (values[hi] - values[lo]) * (k - lo)


def load(path):
    with open(path) as f:
        return [json.loads(line) for line in f if line.strip()]


def summarize(records, kinds=(1, 2)):
    """kinds=(1, 2): every token event. kinds=(1,): only events with visible text."""
    records = [r for r in records if r["path"].split("?")[0] in GENERATION_PATHS]
    ttft, itl, tpot, e2e = [], [], [], []
    out_tokens = 0
    ok = [r for r in records if r["status"] == 200 and any(e[2] in kinds for e in r["events"])]
    for r in ok:
        times = [e[0] for e in r["events"] if e[2] in kinds]
        t0 = r["t_arrival"]
        last = max(e[0] for e in r["events"])
        n_tok = (r.get("usage") or {}).get("completion_tokens") or len(times)
        out_tokens += n_tok
        ttft.append(times[0] - t0)
        itl.extend(b - a for a, b in zip(times, times[1:]))
        if n_tok > 1:
            tpot.append((times[-1] - times[0]) / (n_tok - 1))
        e2e.append(last - t0)
    span = (max(r["t_done"] for r in ok) - min(r["t_arrival"] for r in ok)) if ok else 0
    stat = lambda xs: {
        "mean": statistics.fmean(xs) * 1000 if xs else float("nan"),
        "median": statistics.median(xs) * 1000 if xs else float("nan"),
        "p99": pct(xs, 99) * 1000,
    }
    return {
        "requests_ok": len(ok),
        "requests_total": len(records),
        "span_s": span,
        "output_tokens": out_tokens,
        "output_tok_per_s": out_tokens / span if span else float("nan"),
        "req_per_s": len(ok) / span if span else float("nan"),
        "ttft_ms": stat(ttft),
        "itl_ms": {**stat(itl), "count": len(itl)},
        "tpot_ms": stat(tpot),
        "e2e_ms": stat(e2e),
    }


if __name__ == "__main__":
    records = load(sys.argv[1])
    print(json.dumps({"token_events": summarize(records), "text_events_only": summarize(records, (1,))}, indent=2))
