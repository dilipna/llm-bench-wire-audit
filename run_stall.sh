#!/usr/bin/env bash
# Fault-injection check: freeze every stream for 300 ms at token 20 (via the wire proxy),
# then ask each tool how bad its inter-token-latency tail is. Both tools see the same fault.
set -euo pipefail
export MSYS_NO_PATHCONV=1
N=${1:-3}
MODEL=Qwen/Qwen3-0.6B
VLLM_IP=$(docker inspect -f '{{.NetworkSettings.Networks.bridge.IPAddress}}' vllm-ws)

docker cp "$(dirname "$0")/wire_proxy.py" vllm-ws:/tmp/audit/
docker exec vllm-ws bash -c 'pkill -f "wire_proxy.py --listen 800[34]" || true; rm -rf /tmp/audit/stall && mkdir -p /tmp/audit/stall'
docker exec -d vllm-ws bash -c 'cd /tmp/audit && (/ws/vllm/.venv/bin/python wire_proxy.py --listen 8003 --upstream http://127.0.0.1:8000 --log vb_stall.jsonl --stall-ms 300 --stall-at 20 > p3.log 2>&1 &); (/ws/vllm/.venv/bin/python wire_proxy.py --listen 8004 --upstream http://127.0.0.1:8000 --log gl_stall.jsonl --stall-ms 300 --stall-at 20 > p4.log 2>&1 &); sleep 1'
sleep 4
docker exec gl-ws bash -c 'rm -rf /tmp/gl/stall && mkdir -p /tmp/gl/stall'

for i in $(seq 1 "$N"); do
  docker exec vllm-ws bash -c 'cd /tmp/audit && rm -f vb_stall.jsonl gl_stall.jsonl'
  docker exec vllm-ws bash -c "cd /tmp/audit && PYTHONPATH=/ws/upstream /ws/vllm/.venv/bin/python -m vllm.entrypoints.cli.main bench serve \
    --backend openai --endpoint /v1/completions --base-url http://127.0.0.1:8003 --model $MODEL \
    --dataset-name random --random-input-len 128 --random-output-len 64 --num-prompts 64 \
    --max-concurrency 8 --ignore-eos --seed $i --save-result --result-dir /tmp/audit/stall \
    --result-filename vllm_$i.json > /dev/null 2>&1; mv vb_stall.jsonl stall/vllm_$i.jsonl"
  docker exec gl-ws bash -c "cd /tmp/gl && /venv/bin/guidellm run \
    --backend kind=openai_http,target=http://$VLLM_IP:8004,model=$MODEL,request_format=/v1/completions \
    --profile kind=concurrent,streams=8 --constraint kind=max_requests,count=64 \
    --data kind=synthetic_text,prompt_tokens=128,output_tokens=64 \
    --output kind=json,path=/tmp/gl/stall/gl_$i.json --disable-console-interactive > /dev/null 2>&1"
  docker exec vllm-ws bash -c "cd /tmp/audit && mv gl_stall.jsonl stall/gl_$i.jsonl"
  docker cp gl-ws:/tmp/gl/stall/gl_$i.json - | docker cp - vllm-ws:/tmp/audit/stall/ 2>/dev/null || true
done
docker exec vllm-ws pkill -f "wire_proxy.py --listen 800[34]" || true
echo "stall runs finished"
