#!/usr/bin/env bash
# Alternate N runs of `vllm bench serve` and GuideLLM against one vLLM server, each through
# its own wire proxy, so every tool's reported numbers can be checked against the wire.
# Expects: vllm-ws serving Qwen/Qwen3-0.6B on :8000, wire proxies on :8001 (vllm bench)
# and :8002 (guidellm), and GuideLLM installed in gl-ws. Run from Git Bash on the host.
set -euo pipefail
export MSYS_NO_PATHCONV=1
N=${1:-5}
MODEL=Qwen/Qwen3-0.6B
VLLM_IP=$(docker inspect -f '{{.NetworkSettings.Networks.bridge.IPAddress}}' vllm-ws)
echo "vllm-ws at $VLLM_IP"

docker exec vllm-ws bash -c 'rm -rf /tmp/audit/runs && mkdir -p /tmp/audit/runs'
docker exec gl-ws bash -c 'rm -rf /tmp/gl/runs && mkdir -p /tmp/gl/runs'

for i in $(seq 1 "$N"); do
  # start every iteration with empty proxy logs so no earlier traffic leaks into a run
  docker exec vllm-ws bash -c 'cd /tmp/audit && rm -f vllm_bench.jsonl guidellm.jsonl'
  echo "== run $i: vllm bench serve"
  docker exec vllm-ws bash -c "cd /tmp/audit && PYTHONPATH=/ws/upstream /ws/vllm/.venv/bin/python -m vllm.entrypoints.cli.main bench serve \
    --backend openai --endpoint /v1/completions --base-url http://127.0.0.1:8001 --model $MODEL \
    --dataset-name random --random-input-len 128 --random-output-len 64 --num-prompts 64 \
    --max-concurrency 8 --ignore-eos --seed $i --save-result --result-dir /tmp/audit/runs \
    --result-filename vllm_$i.json > /dev/null 2>&1; mv vllm_bench.jsonl runs/vllm_$i.jsonl"
  echo "== run $i: guidellm"
  docker exec gl-ws bash -c "cd /tmp/gl && /venv/bin/guidellm run \
    --backend kind=openai_http,target=http://$VLLM_IP:8002,model=$MODEL,request_format=/v1/completions \
    --profile kind=concurrent,streams=8 --constraint kind=max_requests,count=64 \
    --data kind=synthetic_text,prompt_tokens=128,output_tokens=64 \
    --output kind=json,path=/tmp/gl/runs/gl_$i.json --disable-console-interactive > /dev/null 2>&1"
  docker exec vllm-ws bash -c "cd /tmp/audit && mv guidellm.jsonl runs/gl_$i.jsonl"
  docker cp gl-ws:/tmp/gl/runs/gl_$i.json - | docker cp - vllm-ws:/tmp/audit/runs/ 2>/dev/null || true
done
echo "all runs finished"
