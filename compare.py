"""Compare what each benchmark tool reported with what the wire proxy measured, per run.

    python compare.py runs/

Expects runs/vllm_<i>.json + vllm_<i>.jsonl and runs/gl_<i>.json + gl_<i>.jsonl.
Prints a markdown table: tool value, wire value, and the percentage gap per metric,
averaged over runs with the worst single run alongside.
"""

import glob
import json
import os
import statistics
import sys

from wire_metrics import load, summarize


def vllm_reported(path):
    d = json.load(open(path))
    return {
        "ttft mean (ms)": d["mean_ttft_ms"],
        "ttft median (ms)": d["median_ttft_ms"],
        "ttft p99 (ms)": d["p99_ttft_ms"],
        "itl mean (ms)": d["mean_itl_ms"],
        "itl p99 (ms)": d["p99_itl_ms"],
        "tpot mean (ms)": d["mean_tpot_ms"],
        "output tok/s": d["output_throughput"],
        "req/s": d["request_throughput"],
        "requests ok": d["completed"],
    }


def gl_reported(path):
    b = json.load(open(path))["benchmarks"][0]
    m = b["metrics"]
    s = lambda name: m[name]["successful"]
    pct = lambda name, p: s(name)["percentiles"][p]
    return {
        "ttft mean (ms)": s("time_to_first_token_ms")["mean"],
        "ttft median (ms)": s("time_to_first_token_ms")["median"],
        "ttft p99 (ms)": pct("time_to_first_token_ms", "p99"),
        "itl mean (ms)": s("inter_token_latency_ms")["mean"],
        "itl p99 (ms)": pct("inter_token_latency_ms", "p99"),
        "tpot mean (ms)": s("time_per_output_token_ms")["mean"],
        "e2e mean (ms)": s("request_latency")["mean"] * 1000,
        "output tok/s": s("output_tokens_per_second")["mean"],
        "output tok/s (tokens / duration)": s("output_token_count")["total_sum"] / b["duration"],
        "req/s": s("requests_per_second")["mean"],
        "requests ok": s("request_latency")["count"],
    }


def aiperf_reported(path):
    d = json.load(open(path))
    return {
        "ttft mean (ms)": d["time_to_first_token"]["avg"],
        "ttft median (ms)": d["time_to_first_token"]["p50"],
        "ttft p99 (ms)": d["time_to_first_token"]["p99"],
        # AIPerf ships both conventions: inter_chunk_latency is every raw gap (compare with
        # the wire's raw gaps), inter_token_latency is one average per request (compare
        # with the wire's per-request average, which is what the "tpot" rows below hold).
        "itl mean (ms)": d["inter_chunk_latency"]["avg"],
        "itl p99 (ms)": d["inter_chunk_latency"]["p99"],
        "tpot mean (ms)": d["inter_token_latency"]["avg"],
        "tpot p99 (ms)": d["inter_token_latency"]["p99"],
        "e2e mean (ms)": d["request_latency"]["avg"],
        "output tok/s": d["output_token_throughput"]["avg"],
        "req/s": d["request_throughput"]["avg"],
        "requests ok": d["completed_request_count"]["avg"],
    }


def wire_values(path):
    w = summarize(load(path))
    return {
        "tpot p99 (ms)": w["tpot_ms"]["p99"],
        "ttft mean (ms)": w["ttft_ms"]["mean"],
        "ttft median (ms)": w["ttft_ms"]["median"],
        "ttft p99 (ms)": w["ttft_ms"]["p99"],
        "itl mean (ms)": w["itl_ms"]["mean"],
        "itl p99 (ms)": w["itl_ms"]["p99"],
        "tpot mean (ms)": w["tpot_ms"]["mean"],
        "e2e mean (ms)": w["e2e_ms"]["mean"],
        "output tok/s": w["output_tok_per_s"],
        "output tok/s (tokens / duration)": w["output_tok_per_s"],
        "req/s": w["req_per_s"],
        "requests ok": w["requests_ok"],
    }


def main(folder):
    for tool, prefix, reported in (
        ("vllm bench serve", "vllm", vllm_reported),
        ("GuideLLM", "gl", gl_reported),
        ("AIPerf", "ap", aiperf_reported),
    ):
        runs = sorted(glob.glob(os.path.join(folder, f"{prefix}_*.json")))
        gaps, rows = {}, {}
        for jpath in runs:
            lpath = jpath[:-5] + ".jsonl"
            if not os.path.exists(lpath):
                continue
            rep, wire = reported(jpath), wire_values(lpath)
            for k, v in rep.items():
                if k in wire and wire[k]:
                    rows.setdefault(k, []).append((v, wire[k]))
                    gaps.setdefault(k, []).append((v - wire[k]) / wire[k] * 100)
        print(f"\n### {tool} ({len(runs)} runs)\n")
        print("| metric | tool reports (mean) | wire (mean) | gap, mean | gap, worst run |")
        print("| --- | ---: | ---: | ---: | ---: |")
        for k, pairs in rows.items():
            tv = statistics.fmean(p[0] for p in pairs)
            wv = statistics.fmean(p[1] for p in pairs)
            g = gaps[k]
            worst = max(g, key=abs)
            print(f"| {k} | {tv:.2f} | {wv:.2f} | {statistics.fmean(g):+.1f}% | {worst:+.1f}% |")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "runs")
