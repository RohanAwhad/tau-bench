USER_MODEL="Qwen/Qwen2.5-32B-Instruct"
USER_MODEL_NAME="qwen25-32b"
USER_MODEL_TENSOR_PARALLEL_SIZE=2
USER_MODEL_PORT=30310

PRIMARY_MODEL="Qwen/Qwen2.5-32B-Instruct"
PRIMARY_MODEL_NAME="qwen25-32b"
PRIMARY_MODEL_TENSOR_PARALLEL_SIZE=2
PRIMARY_MODEL_PORT=30311

REFINER_MODEL="Qwen/Qwen3-8B"
REFINER_MODEL_NAME="qwen3-8b"
REFINER_MODEL_TENSOR_PARALLEL_SIZE=2
REFINER_MODEL_PORT=30312


nohup CUDA_VISIBLE_DEVICES=0,1 vllm serve \
  $USER_MODEL \
  --served-model-name $USER_MODEL_NAME \
  --tensor-parallel-size $USER_MODEL_TENSOR_PARALLEL_SIZE \
  --host 0.0.0.0 \
  --port $USER_MODEL_PORT 2>&1 | tee user_model.log &

nohup CUDA_VISIBLE_DEVICES=2,3 vllm serve \
  $PRIMARY_MODEL \
  --served-model-name $PRIMARY_MODEL_NAME \
  --tensor-parallel-size $PRIMARY_MODEL_TENSOR_PARALLEL_SIZE \
  --enable-auto-tool-choice \
  --tool-call-parser hermes \
  --host 0.0.0.0 \
  --port $PRIMARY_MODEL_PORT 2>&1 | tee primary_model.log &

nohup CUDA_VISIBLE_DEVICES=4,5 vllm serve \
  $REFINER_MODEL \
  --served-model-name $REFINER_MODEL_NAME \
  --tensor-parallel-size $REFINER_MODEL_TENSOR_PARALLEL_SIZE \
  --host 0.0.0.0 \
  --port $REFINER_MODEL_PORT 2>&1 | tee refiner_model.log &
