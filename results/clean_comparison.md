
### vllm bench serve (5 runs)

| metric | tool reports (mean) | wire (mean) | gap, mean | gap, worst run |
| --- | ---: | ---: | ---: | ---: |
| ttft mean (ms) | 126.34 | 123.12 | +2.6% | +3.0% |
| ttft median (ms) | 91.72 | 88.87 | +3.3% | +4.5% |
| ttft p99 (ms) | 398.11 | 392.76 | +1.4% | +1.5% |
| itl mean (ms) | 10.92 | 10.92 | +0.1% | +0.1% |
| itl p99 (ms) | 20.52 | 21.14 | -2.7% | -9.2% |
| tpot mean (ms) | 10.92 | 10.92 | +0.1% | +0.1% |
| output tok/s | 627.91 | 628.38 | -0.1% | -0.1% |
| req/s | 9.81 | 9.82 | -0.1% | -0.1% |
| requests ok | 64.00 | 64.00 | +0.0% | +0.0% |

### GuideLLM (5 runs)

| metric | tool reports (mean) | wire (mean) | gap, mean | gap, worst run |
| --- | ---: | ---: | ---: | ---: |
| ttft mean (ms) | 137.67 | 136.68 | +0.7% | +0.9% |
| ttft median (ms) | 107.05 | 106.17 | +0.8% | +1.2% |
| ttft p99 (ms) | 414.14 | 413.02 | +0.3% | +0.6% |
| itl mean (ms) | 10.92 | 10.93 | -0.0% | -0.1% |
| itl p99 (ms) | 17.58 | 15.56 | +13.0% | +19.4% |
| tpot mean (ms) | 12.90 | 10.93 | +18.1% | +18.9% |
| e2e mean (ms) | 825.92 | 825.09 | +0.1% | +0.1% |
| output tok/s | 617.71 | 617.63 | +0.0% | +0.0% |
| output tok/s (tokens / duration) | 617.74 | 617.63 | +0.0% | +0.0% |
| req/s | 9.56 | 9.65 | -0.9% | -3.1% |
| requests ok | 64.00 | 64.00 | +0.0% | +0.0% |

### AIPerf (5 runs)

| metric | tool reports (mean) | wire (mean) | gap, mean | gap, worst run |
| --- | ---: | ---: | ---: | ---: |
| ttft mean (ms) | 136.07 | 134.30 | +1.3% | +1.5% |
| ttft median (ms) | 104.92 | 103.94 | +1.0% | +1.4% |
| ttft p99 (ms) | 412.81 | 404.88 | +2.0% | +3.6% |
| itl mean (ms) | 11.00 | 10.99 | +0.0% | +0.0% |
| itl p99 (ms) | 22.21 | 22.22 | -0.0% | +0.3% |
| tpot mean (ms) | 11.00 | 10.99 | +0.0% | +0.1% |
| tpot p99 (ms) | 15.39 | 15.36 | +0.2% | +0.9% |
| e2e mean (ms) | 828.78 | 827.11 | +0.2% | +0.3% |
| output tok/s | 616.33 | 617.15 | -0.1% | -0.2% |
| req/s | 9.63 | 9.64 | -0.1% | -0.2% |
| requests ok | 64.00 | 64.00 | +0.0% | +0.0% |
