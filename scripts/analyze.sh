export OPENAI_BASE_URL='https://api.deepseek.com/'
export OPENAI_API_KEY="$DEEPSEEK_API_KEY"

RESULTS_DIR="$1"

if [ -z "$RESULTS_DIR" ]; then
    echo "Usage: $0 <results_directory>"
    exit 1
fi

if [ ! -d "$RESULTS_DIR" ]; then
    echo "Error: Directory $RESULTS_DIR does not exist"
    exit 1
fi

MAX_CONCURRENCY=115
MAX_NUM_FAILED_RESULTS=115

# Find all JSON files in the results directory
for json_file in "$RESULTS_DIR"/*.json; do
    if [ -f "$json_file" ]; then
        echo "Processing: $json_file"
        python auto_error_identification.py \
            --env retail \
            --platform openai \
            --model deepseek-reasoner \
            --results-path "$json_file" \
            --max-concurrency $MAX_CONCURRENCY \
            --output-path "./analysis/$json_file" \
            --max-num-failed-results $MAX_NUM_FAILED_RESULTS
    fi
done