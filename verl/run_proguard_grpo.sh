#!/bin/bash
set -x
ENGINE=${1:-vllm}

cd YOUR_PATH_TO_VERL

TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
LOG_DIR=YOUR_PATH_TO_VERL/logs
EVAL_DIR=YOUR_PATH_TO_VERL/eval

mkdir -p $LOG_DIR
mkdir -p $EVAL_DIR

LOG_FILE="$LOG_DIR/proguard_grpo_${TIMESTAMP}.log"

DATA_PATH=YOUR_PATH_TO_VERL/data/proguard_train.parquet"
VAL_DATA_PATH=YOUR_PATH_TO_VERL/data/proguard_val.parquet"

# Sentence Transformer API configuration
SENTENCE_TRANSFORMER_URL="YOUR_SENTENCE_TRANSFORMER_URL"
SENTENCE_TRANSFORMER_TIMEOUT=30
SENTENCE_TRANSFORMER_THRESHOLD=0.7
SENTENCE_TRANSFORMER_MAX_CONCURRENT=64

# Model configuration
MODEL_PATH="YOUR_MODEL_PATH/Qwen2.5-VL-7B-Instruct"
TENSOR_PARALLEL_SIZE=4        
GPU_MEMORY_UTILIZATION=0.6

# Training configuration
TRAIN_BATCH_SIZE=512
MAX_PROMPT_LENGTH=3072
MAX_RESPONSE_LENGTH=1024
PPO_MINI_BATCH_SIZE=32
PPO_MICRO_BATCH_SIZE_PER_GPU=4
ROLLOUT_N=16  # GRPO group size
DEFAULT_LOCAL_DIR="YOUR_CHECKPOINT_PATH"


# Learning rate and optimization
LEARNING_RATE=1e-6
KL_LOSS_COEF=0.01
CLIP_RATIO=0.1
ACTOR_ENTROPY_COEF=0.01     

# Training duration
TOTAL_EPOCHS=1
SAVE_FREQ=10
TEST_FREQ=10

# Hardware configuration
N_GPUS_PER_NODE=8
NNODES=1            

python3 -m verl.trainer.main_ppo \
    algorithm.adv_estimator=grpo \
    data.train_files=$DATA_PATH \
    data.val_files=$VAL_DATA_PATH \
    data.train_batch_size=$TRAIN_BATCH_SIZE \
    data.max_prompt_length=$MAX_PROMPT_LENGTH \
    data.max_response_length=$MAX_RESPONSE_LENGTH \
    data.filter_overlong_prompts=True \
    data.truncation='error' \
    data.image_key=images \
    \
    actor_rollout_ref.model.path=$MODEL_PATH \
    actor_rollout_ref.model.enable_gradient_checkpointing=True \
    actor_rollout_ref.model.use_remove_padding=False \
    \
    actor_rollout_ref.actor.optim.lr=$LEARNING_RATE \
    actor_rollout_ref.actor.ppo_mini_batch_size=$PPO_MINI_BATCH_SIZE \
    actor_rollout_ref.actor.ppo_micro_batch_size_per_gpu=$PPO_MICRO_BATCH_SIZE_PER_GPU \
    actor_rollout_ref.actor.use_kl_loss=True \
    actor_rollout_ref.actor.entropy_coeff=$ACTOR_ENTROPY_COEF \
    actor_rollout_ref.actor.kl_loss_coef=$KL_LOSS_COEF \
    actor_rollout_ref.actor.kl_loss_type=low_var_kl \
    actor_rollout_ref.actor.clip_ratio=$CLIP_RATIO \
    actor_rollout_ref.actor.loss_agg_mode=token-mean \
    actor_rollout_ref.actor.fsdp_config.param_offload=False \
    actor_rollout_ref.actor.fsdp_config.optimizer_offload=False \
    actor_rollout_ref.actor.checkpoint.save_contents="['model']"\
    \
    actor_rollout_ref.rollout.log_prob_micro_batch_size_per_gpu=$PPO_MICRO_BATCH_SIZE_PER_GPU \
    actor_rollout_ref.rollout.tensor_model_parallel_size=$TENSOR_PARALLEL_SIZE \
    actor_rollout_ref.rollout.name=vllm \
    actor_rollout_ref.rollout.gpu_memory_utilization=$GPU_MEMORY_UTILIZATION \
    actor_rollout_ref.rollout.n=$ROLLOUT_N \
    actor_rollout_ref.rollout.enable_chunked_prefill=False \
    actor_rollout_ref.rollout.enforce_eager=False \
    actor_rollout_ref.rollout.free_cache_engine=False \
    \
    actor_rollout_ref.ref.log_prob_micro_batch_size_per_gpu=$PPO_MICRO_BATCH_SIZE_PER_GPU \
    actor_rollout_ref.ref.fsdp_config.param_offload=True \
    \
    algorithm.use_kl_in_reward=True \
    algorithm.norm_adv_by_std_in_grpo=True \
    \
    reward_model.sentence_transformer.url=$SENTENCE_TRANSFORMER_URL \
    reward_model.sentence_transformer.timeout=$SENTENCE_TRANSFORMER_TIMEOUT \
    reward_model.sentence_transformer.similarity_threshold=$SENTENCE_TRANSFORMER_THRESHOLD \
    reward_model.sentence_transformer.max_concurrent=$SENTENCE_TRANSFORMER_MAX_CONCURRENT \
    \
    trainer.logger=console \
    trainer.project_name='verl_proguard_grpo' \
    trainer.experiment_name='proguard_qwen2_5_7b_grpo' \
    trainer.n_gpus_per_node=$N_GPUS_PER_NODE \
    trainer.nnodes=$NNODES \
    trainer.save_freq=$SAVE_FREQ \
    trainer.test_freq=$TEST_FREQ \
    trainer.total_epochs=$TOTAL_EPOCHS \
    trainer.device=cuda \
    trainer.default_local_dir=$DEFAULT_LOCAL_DIR \
    trainer.validation_data_dir=$EVAL_DIR \
    trainer.log_val_generations=100 \
    $@ 2>&1 | tee $LOG_FILE

echo "Training completed. Log saved to: $LOG_FILE"
echo "Evaluation results saved to: $EVAL_DIR"
