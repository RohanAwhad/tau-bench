#!/usr/bin/env bash
set -euo pipefail

# Check if argument is provided
if [ $# -ne 1 ]; then
    echo "Usage: $0 <debug|prod>"
    exit 1
fi

# Set END_INDEX based on argument
if [ "$1" = "debug" ]; then
    END_INDEX=1
elif [ "$1" = "prod" ]; then
    END_INDEX=-1
else
    echo "Invalid argument. Use 'debug' or 'prod'"
    exit 1
fi


# Record start time
START_TIME=$(date +%s)

# user model
export OPENAI_BASE_URL='https://api.openai.com/v1'
export OPENAI_API_KEY="$ROPENAI_API_KEY"
USER_MODEL="openai/gpt-4.1-2025-04-14"

# assistant model
export VLLM_BASE_URL='http://localhost:8080/v1'
ASSISTANT_MODEL="surgical_adapter_v27_qwen3_8b_step_0"

# extra params
MAX_CONCURRENCY=24
LOG_DIR="results/gpt_4.1-$ASSISTANT_MODEL"


# constant
TEMPERATURE=0.72

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
    --task-split test \
    --end-index $END_INDEX
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
