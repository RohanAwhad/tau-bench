#!/usr/bin/env bash
set -euo pipefail

export OPENAI_BASE_URL='http://10.241.128.17:30310/v1'
export OPENAI_API_KEY='empty'
export VLLM_BASE_URL='http://localhost:8082/v1'

# Loop over temperatures from 0.4 to 1.8 in steps of 0.1
for temp in $(seq 0.5 0.1 1.8); do
  printf ">>> Testing temperature: %.1f\n" "$temp"
  python run.py \
    --agent-strategy tool-calling \
    --env retail \
    --model surgical_adapter_v27_qwen3_8b_step_15_modified_template \
    --model-provider hosted_vllm \
    --user-model "qwen25-32b" \
    --user-model-provider openai \
    --user-strategy llm \
    --max-concurrency 55 \
    --temperature "$temp" \
    --num-trials 1 \
    --log-dir "temperature_check" \
    --task-split test \
    --best-of-n 32
done
