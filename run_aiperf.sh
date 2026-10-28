#!/usr/bin/env bash
# Run AIPerf N times through its own wire proxy, once clean (port 8005) and once with the
# 300 ms stall injected (port 8006), on the same workload as run_audit.sh / run_stall.sh.
# AIPerf is installed in gl-ws at /aiperf-venv (pip install aiperf).
set -euo pipefail
export MSYS_NO_PATHCONV=1
N=${1:-5}
MODEL=Qwen/Qwen3-0.6B
VLLM_IP=$(docker inspect -f '{{.NetworkSettings.Networks.bridge.IPAddress}}' vllm-ws)

docker cp "$(dirname "$0")/wire_proxy.py" vllm-ws:/tmp/audit/
docker exec vllm-ws bash -c 'pkill -f "wire_proxy.py --listen 800[56]" || true; mkdir -p /tmp/audit/runs /tmp/audit/stall'
docker exec -d vllm-ws bash -c 'cd /tmp/audit && (/ws/vllm/.venv/bin/python wire_proxy.py --listen 8005 --upstream http://127.0.0.1:8000 --log ap_clean.jsonl > p5.log 2>&1 &); (/ws/vllm/.venv/bin/python wire_proxy.py --listen 8006 --upstream http://127.0.0.1:8000 --log ap_stall.jsonl --stall-ms 300 --stall-at 20 > p6.log 2>&1 &); sleep 1'
sleep 4
docker exec gl-ws bash -c 'rm -rf /tmp/ap_runs && mkdir -p /tmp/ap_runs'

one_run() { # $1 = port, $2 = label, $3 = iteration, $4 = proxy log, $5 = destination folder
  docker exec vllm-ws bash -c "rm -f /tmp/audit/$4"
  docker exec gl-ws bash -c "cd /tmp && timeout 600 /aiperf-venv/bin/aiperf profile -m $MODEL \
    --url http://$VLLM_IP:$1 --endpoint-type completions --streaming --concurrency 8 \
    --request-count 64 --isl 128 --isl-stddev 0 --osl 64 --osl-stddev 0 \
    --extra-inputs ignore_eos:true --tokenizer $MODEL --no-server-metrics --no-gpu-telemetry \
    --random-seed $3 --output-artifact-dir /tmp/ap_runs/$2_$3 --ui-type none > /dev/null 2>&1"
  docker exec vllm-ws bash -c "mv /tmp/audit/$4 /tmp/audit/$5/ap_$3.jsonl"
  docker cp gl-ws:/tmp/ap_runs/$2_$3/profile_export_aiperf.json - | docker cp - vllm-ws:/tmp/audit/ 2>/dev/null
  docker exec vllm-ws bash -c "mv /tmp/audit/profile_export_aiperf.json /tmp/audit/$5/ap_$3.json"
}

for i in $(seq 1 "$N"); do
  echo "== clean run $i"; one_run 8005 clean "$i" ap_clean.jsonl runs
done
for i in $(seq 1 3); do
  echo "== stall run $i"; one_run 8006 stall "$i" ap_stall.jsonl stall
done
docker exec vllm-ws pkill -f "wire_proxy.py --listen 800[56]" || true
echo "aiperf runs finished"
