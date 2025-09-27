USER_MODEL="Qwen/Qwen2.5-32B-Instruct"
USER_MODEL_NAME="qwen25-32b"
USER_MODEL_TENSOR_PARALLEL_SIZE=2
USER_MODEL_PORT=30310
USER_MODEL_GPU_IDS=0,1

PRIMARY_MODEL="Qwen/Qwen2.5-32B-Instruct"
PRIMARY_MODEL_NAME="qwen25-32b"
PRIMARY_MODEL_TENSOR_PARALLEL_SIZE=2
PRIMARY_MODEL_PORT=30311
PRIMARY_MODEL_GPU_IDS=2,3

REFINER_MODEL="Qwen/Qwen3-8B"
REFINER_MODEL_NAME="qwen3-8b"
REFINER_MODEL_TENSOR_PARALLEL_SIZE=2
REFINER_MODEL_PORT=30312
REFINER_MODEL_GPU_IDS=4,5

# Start servers and capture their PIDs correctly
CUDA_VISIBLE_DEVICES=$USER_MODEL_GPU_IDS nohup vllm serve \
  $USER_MODEL \
  --served-model-name $USER_MODEL_NAME \
  --tensor-parallel-size $USER_MODEL_TENSOR_PARALLEL_SIZE \
  --host 0.0.0.0 \
  --port $USER_MODEL_PORT 2>&1 | tee user_model.log &
USER_PID=$!

CUDA_VISIBLE_DEVICES=$PRIMARY_MODEL_GPU_IDS nohup vllm serve \
  $PRIMARY_MODEL \
  --served-model-name $PRIMARY_MODEL_NAME \
  --tensor-parallel-size $PRIMARY_MODEL_TENSOR_PARALLEL_SIZE \
  --enable-auto-tool-choice \
  --tool-call-parser hermes \
  --host 0.0.0.0 \
  --port $PRIMARY_MODEL_PORT 2>&1 | tee primary_model.log &
PRIMARY_PID=$!

CUDA_VISIBLE_DEVICES=$REFINER_MODEL_GPU_IDS nohup vllm serve \
  $REFINER_MODEL \
  --served-model-name $REFINER_MODEL_NAME \
  --tensor-parallel-size $REFINER_MODEL_TENSOR_PARALLEL_SIZE \
  --host 0.0.0.0 \
  --port $REFINER_MODEL_PORT 2>&1 | tee refiner_model.log &
REFINER_PID=$!

echo "Started servers with PIDs:"
echo "User model server: $USER_PID"
echo "Primary model server: $PRIMARY_PID" 
echo "Refiner model server: $REFINER_PID"

echo "Press Ctrl+C to stop all servers..."
trap 'echo "Stopping all servers..."; kill $USER_PID $PRIMARY_PID $REFINER_PID 2>/dev/null; exit' INT

# Wait for any of the background processes to exit
wait