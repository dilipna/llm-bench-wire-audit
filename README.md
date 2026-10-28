# Do LLM benchmark tools report what actually happened on the wire?

I put a small logging proxy between three benchmark tools and one vLLM server. The proxy
timestamps every streamed event as it passes, so for every run I have a record that does
not depend on how any tool defines or computes its metrics. Then I compared what each tool
reported with what the wire says.

Tools: `vllm bench serve` (vLLM main `90c4a1a73e`), GuideLLM `0.9.0.dev85` (main `0a883e7b`)
and NVIDIA AIPerf `0.13.0`. Server: unmodified vLLM main, Qwen3-0.6B in fp16, on a laptop
RTX 3050 Ti with 4 GB. Workload for all three: 64 requests, 128 input tokens, 64 output
tokens, 8 requests in flight, streaming `/v1/completions`. Five runs per tool. `vllm bench
serve` and GuideLLM alternated; AIPerf ran afterwards against the same server.

## Result 1: where the tools define a metric the same way, they match the wire

Mean gap between what the tool reported and what the wire shows, over 5 runs (worst single
run in brackets). Full tables: [results/clean_comparison.md](results/clean_comparison.md).

| metric | `vllm bench serve` | GuideLLM | AIPerf |
| --- | ---: | ---: | ---: |
| TTFT mean | +2.6% (+3.0%) | +0.7% (+0.9%) | +1.3% (+1.5%) |
| TTFT p99 | +1.4% (+1.5%) | +0.3% (+0.6%) | +2.0% (+3.6%) |
| mean inter-token latency | +0.1% (+0.1%) | -0.0% (-0.1%) | +0.0% (+0.0%) |
| end-to-end latency | not reported | +0.1% (+0.1%) | +0.2% (+0.3%) |
| output tokens/s | -0.1% (-0.1%) | +0.0% (+0.0%) | -0.1% (-0.2%) |
| requests/s | -0.1% (-0.1%) | -0.9% (-3.1%) | -0.1% (-0.2%) |

`vllm bench serve` reports about 3 ms more TTFT than the wire in every run (worst +3.0%). I
did not isolate the cause; time inside the client between its timestamp and the request
reaching the proxy is the likely one. GuideLLM's own TTFT overhead was about 1 ms here, at
8 streams on Linux. Its issue
[#1238](https://github.com/vllm-project/guidellm/issues/1238) reports that this overhead
grows with many streams per worker; I did not test that regime.

## Result 2: the tools answer different questions with the same names

Neither of these is a bug. GuideLLM's maintainers explained both choices in
[#1144](https://github.com/vllm-project/guidellm/issues/1144) and
[#1145](https://github.com/vllm-project/guidellm/issues/1145), reported by aiwantaozi. What
I add is the size of the effect, measured on the wire.

**TPOT.** GuideLLM's `time_per_output_token_ms` includes the first token, so it is
end-to-end latency divided by output tokens. `vllm bench serve` excludes the first token,
and so does AIPerf's per-request `inter_token_latency` (AIPerf has no metric called TPOT).
On this workload GuideLLM reports 12.90 ms and the wire gives 10.93 ms with the
exclusive definition: **+18.1%** (worst run +18.9%). The difference comes from the first
token's time being spread over the output, so it should be larger for shorter outputs; I
only measured 64 output tokens.

**Inter-token latency has two conventions.** They are different statistics:

| tool | metric | what a percentile is taken over |
| --- | --- | --- |
| `vllm bench serve` | `itl` | every gap between consecutive streamed events |
| GuideLLM | `inter_token_latency_ms` | one average per request, weighted by token count |
| AIPerf | `inter_chunk_latency` | every gap between consecutive streamed events |
| AIPerf | `inter_token_latency` | one average per request |

I checked the per-request convention against the wire: GuideLLM's p99 ITL equals the p99 of
per-request mean ITL, weighted by gap count, to within 0.03 ms in all five runs, and AIPerf's
`inter_token_latency` p99 matches the wire's per-request value to within 1%. With no fault
injected the two conventions were 13% apart at p99 for GuideLLM (17.58 ms vs 15.56 ms on the
wire's raw gaps).

## Result 3: what the difference means when something stalls

I made the proxy freeze every stream for 300 ms before token 20 and ran all three tools
again (3 runs each, [results/stall_comparison.md](results/stall_comparison.md)). The tokens
generated during the freeze are delivered right after it, which is consistent with the mean
per-token time barely moving (under 0.5 ms for every tool).

| p99 inter-token latency under the stall | reported | wire |
| --- | ---: | ---: |
| `vllm bench serve` `itl` (raw gaps) | 311.2 ms | 311.2 ms |
| AIPerf `inter_chunk_latency` (raw gaps) | 312.5 ms | 312.5 ms |
| AIPerf `inter_token_latency` (per request) | 15.6 ms | 15.6 ms |
| GuideLLM `inter_token_latency_ms` (per request) | 16.6 ms | 313.1 ms (raw gaps) |

A user watching the stream sees a 300 ms freeze in every response. A metric over raw gaps
reports it. A metric over per-request averages cannot, because averaging a request's gaps
spreads one 300 ms gap over 63 intervals. AIPerf reports both and each matches the wire for
what it is; GuideLLM reports only the averaged one. GuideLLM's maintainers have said that
individual token events are too noisy to read from a client
([#1145](https://github.com/vllm-project/guidellm/issues/1145)), which is a fair position,
but it means GuideLLM's ITL should not be used to look for stalls, and the two numbers
should not be compared across tools.

## What this does not show

- One model, one small GPU, loopback networking, 64 requests per run, 5 runs. Results at
  other concurrencies, longer outputs, other models and real networks may differ.
- The proxy sits in the path of every tool, so absolute latencies include its overhead. It is
  the same for all of them, and the wire values are measured after it.
- The tools generate their own prompts (random token ids and synthetic text), so I compare
  each tool with the wire for its own run, not one tool's numbers with another's.
- Three tools only. I make no claim about others.
- "Ground truth" here means the arrival times of events at the proxy. It does not mean when
  the GPU produced each token.
- A first trial run of AIPerf had a slow first wave of requests (TTFT p90 near 1.7 s). It did
  not recur in the five measured runs and I did not find the cause, so the trial is not in
  the data.

## Reproduce

Needs Docker and a GPU. `wire_proxy.py` logs one JSON line per request; `wire_metrics.py`
recomputes the metrics from it with the definitions at the top of the file; `compare.py`
lines each tool's report up against it.

```
python wire_proxy.py --listen 8001 --upstream http://127.0.0.1:8000 --log run.jsonl
# point a benchmark tool at :8001, then
python wire_metrics.py run.jsonl
```

`run_audit.sh` (vLLM bench and GuideLLM), `run_aiperf.sh` and `run_stall.sh` are the exact
scripts I used; the raw logs for all runs are in `results/`.

I used an AI assistant while building this and checked the numbers myself, including
re-running the experiment after my first harness left stale requests in a log.
