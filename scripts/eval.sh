#!/usr/bin/env bash
set -euo pipefail

# user model
export OPENAI_BASE_URL='http://10.241.128.20:30310/v1'
export OPENAI_API_KEY='empty'
USER_MODEL="qwen25-32b"

# assistant model
export VLLM_BASE_URL='http://localhost:8080/v1'
ASSISTANT_MODEL="surgical_adapter_v27_qwen3_8b_step_0"

# extra params
MAX_CONCURRENCY=9
TEMPERATURE=0.72
LOG_DIR="results/surgical_adapter_v27_qwen3_8b_step_0_temp_0.72_trial_2"

for i in {1..5}; do
  echo ">>> Run $i/5"
  python run.py \
    --agent-strategy tool-calling \
    --env retail \
    --model $ASSISTANT_MODEL \
    --model-provider hosted_vllm \
    --user-model $USER_MODEL \
    --user-model-provider openai \
    --user-strategy llm \
    --max-concurrency $MAX_CONCURRENCY \
    --temperature $TEMPERATURE \
    --num-trials 1 \
    --log-dir $LOG_DIR \
    --task-split test
done

python scripts/get_metrics.py $LOG_DIR
