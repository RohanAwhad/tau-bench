#!/usr/bin/env bash
set -euo pipefail

# Record start time
START_TIME=$(date +%s)

# user model
export OPENAI_BASE_URL='http://10.241.128.20:30310/v1'
export OPENAI_API_KEY='empty'
USER_MODEL="qwen25-32b"

# assistant model
export VLLM_BASE_URL='http://localhost:8080/v1'
ASSISTANT_MODEL="surgical_adapter_v27_qwen3_8b_step_0_with_explicit_think"

# extra params
MAX_CONCURRENCY=24
TEMPERATURE=0.72
LOG_DIR="results/$ASSISTANT_MODEL"

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

# Calculate and log total execution time
END_TIME=$(date +%s)
TOTAL_TIME=$((END_TIME - START_TIME))
HOURS=$((TOTAL_TIME / 3600))
MINUTES=$(((TOTAL_TIME % 3600) / 60))
SECONDS=$((TOTAL_TIME % 60))

echo "============================================"
echo "Total execution time: ${HOURS}h ${MINUTES}m ${SECONDS}s"
echo "Total seconds: ${TOTAL_TIME}s"
echo "============================================"
