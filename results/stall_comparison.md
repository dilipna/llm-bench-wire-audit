
### vllm bench serve (3 runs)

| metric | tool reports (mean) | wire (mean) | gap, mean | gap, worst run |
| --- | ---: | ---: | ---: | ---: |
| ttft mean (ms) | 126.67 | 122.89 | +3.1% | +3.3% |
| ttft median (ms) | 98.06 | 94.41 | +3.9% | +4.0% |
| ttft p99 (ms) | 392.29 | 383.42 | +2.3% | +2.7% |
| itl mean (ms) | 10.99 | 10.98 | +0.1% | +0.1% |
| itl p99 (ms) | 311.23 | 311.24 | -0.0% | -0.0% |
| tpot mean (ms) | 10.99 | 10.98 | +0.1% | +0.1% |
| output tok/s | 624.27 | 624.99 | -0.1% | -0.1% |
| req/s | 9.75 | 9.77 | -0.1% | -0.1% |
| requests ok | 64.00 | 64.00 | +0.0% | +0.0% |

### GuideLLM (3 runs)

| metric | tool reports (mean) | wire (mean) | gap, mean | gap, worst run |
| --- | ---: | ---: | ---: | ---: |
| ttft mean (ms) | 142.70 | 141.49 | +0.9% | +0.9% |
| ttft median (ms) | 117.90 | 117.01 | +0.8% | +1.0% |
| ttft p99 (ms) | 374.65 | 372.77 | +0.5% | +0.6% |
| itl mean (ms) | 11.31 | 11.31 | -0.0% | -0.0% |
| itl p99 (ms) | 16.55 | 313.14 | -94.7% | -94.8% |
| tpot mean (ms) | 13.36 | 11.31 | +18.1% | +18.5% |
| e2e mean (ms) | 855.18 | 853.99 | +0.1% | +0.2% |
| output tok/s | 596.50 | 596.55 | -0.0% | -0.0% |
| output tok/s (tokens / duration) | 596.50 | 596.55 | -0.0% | -0.0% |
| req/s | 9.32 | 9.32 | -0.0% | -0.0% |
| requests ok | 64.00 | 64.00 | +0.0% | +0.0% |

### AIPerf (3 runs)

| metric | tool reports (mean) | wire (mean) | gap, mean | gap, worst run |
| --- | ---: | ---: | ---: | ---: |
| ttft mean (ms) | 144.50 | 142.16 | +1.6% | +2.5% |
| ttft median (ms) | 114.89 | 113.68 | +1.1% | +1.3% |
| ttft p99 (ms) | 424.61 | 414.08 | +2.4% | +4.5% |
| itl mean (ms) | 11.12 | 11.11 | +0.0% | +0.0% |
| itl p99 (ms) | 312.48 | 312.53 | -0.0% | -0.0% |
| tpot mean (ms) | 11.12 | 11.11 | +0.0% | +0.1% |
| tpot p99 (ms) | 15.60 | 15.60 | +0.0% | +0.0% |
| e2e mean (ms) | 844.76 | 842.51 | +0.3% | +0.4% |
| output tok/s | 603.75 | 605.02 | -0.2% | -0.3% |
| req/s | 9.44 | 9.45 | -0.2% | -0.3% |
| requests ok | 64.00 | 64.00 | +0.0% | +0.0% |
