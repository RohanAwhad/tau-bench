#!/usr/bin/env bash
set -euo pipefail

export OPENAI_BASE_URL='http://10.241.128.20:30310/v1'
export OPENAI_API_KEY='empty'
export VLLM_BASE_URL='http://localhost:8080/v1'

for i in {1..5}; do
  echo ">>> Run $i/5"
  python run.py \
    --agent-strategy tool-calling \
    --env retail \
    --model surgical_adapter_v27_qwen3_8b_step_0 \
    --model-provider hosted_vllm \
    --user-model "qwen25-32b" \
    --user-model-provider openai \
    --user-strategy llm \
    --max-concurrency 24 \
    --temperature 0.72 \
    --num-trials 1 \
    --log-dir "surgical_adapter_v27_qwen3_8b_step_0_temp_0.72" \
    --task-split test
done

