# ALWAYS:
#   - USER PORT: 30310
#   - PRIMARY MODEL PORT: 30311
#   - REFINER MODEL PORT: 30312


# # Start USER MODEL
# # Max concurrency: 37
# CUDA_VISIBLE_DEVICES=0,1,2,3,4,5,6,7 vllm serve \
#   "RedHatAI/Llama-3.3-70B-Instruct" \
#   --served-model-name llama33-70b \
#   --tensor-parallel-size 8 \
#   --host 0.0.0.0 \
#   --port 30310 \
#   --max-model-len 32768 ;
# USER MODEL IS GPT-4.1 NO OTHER MODEL WORKS!

PRIMARY_MODEL="Qwen/Qwen2.5-32B-Instruct"
PRIMARY_MODEL_NAME="qwen25-32b"
PRIMARY_MODEL_TENSOR_PARALLEL_SIZE=4
PRIMARY_MODEL_PORT=30311
PRIMARY_MODEL_GPU_IDS=0,1,2,3

REFINER_MODEL="Qwen/Qwen3-8B"
REFINER_MODEL_NAME="qwen3-8b"
REFINER_MODEL_TENSOR_PARALLEL_SIZE=4
REFINER_MODEL_PORT=30312
REFINER_MODEL_GPU_IDS=4,5,6,7

# Start servers and capture their PIDs correctly
# @Max concurrency: 24
CUDA_VISIBLE_DEVICES=$PRIMARY_MODEL_GPU_IDS nohup vllm serve \
  $PRIMARY_MODEL \
  --served-model-name $PRIMARY_MODEL_NAME \
  --tensor-parallel-size $PRIMARY_MODEL_TENSOR_PARALLEL_SIZE \
  --enable-auto-tool-choice \
  --tool-call-parser hermes \
  --host 0.0.0.0 \
  --port $PRIMARY_MODEL_PORT 2>&1 | tee primary_model.log &
PRIMARY_MODEL_PID=$!

# @Max concurrency: 37
CUDA_VISIBLE_DEVICES=$REFINER_MODEL_GPU_IDS nohup vllm serve \
  $REFINER_MODEL \
  --served-model-name $REFINER_MODEL_NAME \
  --tensor-parallel-size $REFINER_MODEL_TENSOR_PARALLEL_SIZE \
  --host 0.0.0.0 \
  --port $REFINER_MODEL_PORT 2>&1 | tee refiner_model.log &
REFINER_PID=$!

echo "Started servers with PIDs:"
echo "Primary model server: $PRIMARY_MODEL_PID"
echo "Refiner model server: $REFINER_PID"

echo "Press Ctrl+C to stop all servers..."
trap 'echo "Stopping all servers..."; kill $PRIMARY_MODEL_PID $REFINER_PID 2>/dev/null; exit' INT

# Wait for any of the background processes to exit
wait
