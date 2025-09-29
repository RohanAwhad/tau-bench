export OPENAI_BASE_URL='https://api.deepseek.com/'
export OPENAI_API_KEY="$DEEPSEEK_API_KEY"

RESULT_PATH="results/gpt_4.1-surgical_adapter_v27_qwen3_8b_step_0_strict_format_check_step_level_best_of_8_gpt_5_judge_run_1/tool-calling-surgical_adapter_v27_qwen3_8b_step_0_strict_format_check_step_level_best_of_8_gpt_5_judge_run_1-1.3_range_0--1_user-gpt-4.1-2025-04-14-llm_0928200611.json"

MAX_CONCURRENCY=115
MAX_NUM_FAILED_RESULTS=115

python auto_error_identification.py \
    --env retail \
    --platform openai \
    --model deepseek-reasoner \
    --results-path $RESULT_PATH \
    --max-concurrency $MAX_CONCURRENCY \
    --output-path "./analysis/$RESULT_PATH" \
    --max-num-failed-results $MAX_NUM_FAILED_RESULTS