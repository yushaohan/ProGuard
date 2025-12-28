set -x
ENGINE=${1:-vllm}
export YOUR_WORKING_PATH = /your/working/path
cd $YOUR_WORKING_PATH
export PYTHONPATH=$YOUR_WORKING_PATH:$PYTHONPATH
export CUDA_DEVICE_MAX_CONNECTIONS=1
export VLLM_ALLREDUCE_USE_SYMM_MEM=0

GEN_TP=${GEN_TP:-4}
CP=${CP:-2}
TP=${TP:-2}
PP=${PP:-2}

SENTENCE_TRANSFORMER_URL=$YOUR_SENTENCE_TRANSFORMER_URL
SENTENCE_TRANSFORMER_TIMEOUT=30
SENTENCE_TRANSFORMER_THRESHOLD=0.7
SENTENCE_TRANSFORMER_MAX_CONCURRENT=64

MODEL_PATH=$YOUR_MODEL_PATH 
train_path=$YOUR_TRAIN_PATH
test_path=$YOUR_TEST_PATH

python3 -m verl.trainer.main_ppo --config-path=config \
    --config-name='ppo_megatron_trainer.yaml'\
    algorithm.adv_estimator=grpo \
    data.train_files="$train_path" \
    data.val_files="$test_path" \
    data.train_batch_size=256 \
    data.max_prompt_length=3072 \
    data.max_response_length=1024 \
    data.filter_overlong_prompts=True \
    data.truncation='error' \
    custom_reward_function.path="YOUR_WORKING_PATH/verl/utils/reward_score/safety_grm.py" \
    custom_reward_function.name="compute_score" \
    actor_rollout_ref.model.path=$MODEL_PATH \
    actor_rollout_ref.actor.optim.lr=1e-6 \
    actor_rollout_ref.actor.ppo_mini_batch_size=32 \
    actor_rollout_ref.actor.ppo_micro_batch_size_per_gpu=4 \
    actor_rollout_ref.actor.megatron.pipeline_model_parallel_size=$PP \
    actor_rollout_ref.actor.megatron.tensor_model_parallel_size=$TP \
    actor_rollout_ref.actor.megatron.context_parallel_size=$CP \
    actor_rollout_ref.actor.use_kl_loss=True \
    actor_rollout_ref.actor.kl_loss_coef=0.01 \
    actor_rollout_ref.actor.kl_loss_type=low_var_kl \
    actor_rollout_ref.actor.clip_ratio=0.1 \
    actor_rollout_ref.actor.entropy_coeff=0.01 \
    actor_rollout_ref.rollout.log_prob_micro_batch_size_per_gpu=4 \
    actor_rollout_ref.rollout.tensor_model_parallel_size=2 \
    actor_rollout_ref.actor.use_dynamic_bsz=True \
    actor_rollout_ref.actor.ppo_max_token_len_per_gpu=4096 \
    actor_rollout_ref.ref.log_prob_use_dynamic_bsz=True \
    actor_rollout_ref.ref.log_prob_max_token_len_per_gpu=4096 \
    actor_rollout_ref.rollout.log_prob_use_dynamic_bsz=True \
    actor_rollout_ref.rollout.log_prob_max_token_len_per_gpu=4096 \
    actor_rollout_ref.rollout.name=$ENGINE \
    +actor_rollout_ref.rollout.engine_kwargs.vllm.disable_mm_preprocessor_cache=True \
    actor_rollout_ref.rollout.gpu_memory_utilization=0.6 \
    actor_rollout_ref.rollout.n=16 \
    actor_rollout_ref.ref.log_prob_micro_batch_size_per_gpu=4 \
    actor_rollout_ref.actor.megatron.use_mbridge=True \
    actor_rollout_ref.actor.megatron.param_offload=False \
    actor_rollout_ref.actor.megatron.optimizer_offload=False \
    actor_rollout_ref.actor.megatron.grad_offload=False \
    actor_rollout_ref.ref.megatron.param_offload=False \
    actor_rollout_ref.actor.checkpoint.save_contents="['model']"\
    +actor_rollout_ref.actor.optim.override_optimizer_config.optimizer_offload_fraction=0 \
    +actor_rollout_ref.actor.optim.override_optimizer_config.overlap_cpu_optimizer_d2h_h2d=False \
    +actor_rollout_ref.actor.optim.override_optimizer_config.use_precision_aware_optimizer=False \
    +actor_rollout_ref.actor.optim.override_optimizer_config.optimizer_cpu_offload=False \
    +actor_rollout_ref.actor.megatron.override_transformer_config.moe_router_dtype=fp32 \
    +actor_rollout_ref.actor.megatron.override_transformer_config.moe_enable_deepep=True \
    +actor_rollout_ref.actor.megatron.override_transformer_config.moe_token_dispatcher_type=flex \
    +actor_rollout_ref.actor.megatron.override_transformer_config.recompute_method=uniform \
    +actor_rollout_ref.actor.megatron.override_transformer_config.recompute_granularity=full \
    +actor_rollout_ref.actor.megatron.override_transformer_config.recompute_num_layers=1 \
    +actor_rollout_ref.actor.megatron.override_transformer_config.gradient_accumulation_fusion=True \
    +actor_rollout_ref.actor.megatron.override_transformer_config.moe_permute_fusion=True \
    reward_model.sentence_transformer.url=$SENTENCE_TRANSFORMER_URL \
    reward_model.sentence_transformer.timeout=$SENTENCE_TRANSFORMER_TIMEOUT \
    reward_model.sentence_transformer.similarity_threshold=$SENTENCE_TRANSFORMER_THRESHOLD \
    reward_model.sentence_transformer.max_concurrent=$SENTENCE_TRANSFORMER_MAX_CONCURRENT \
    algorithm.use_kl_in_reward=True \
    algorithm.norm_adv_by_std_in_grpo=True \
    trainer.critic_warmup=0 \
    trainer.logger=console \
    trainer.project_name='verl_safety_grm_grpo' \
    trainer.experiment_name='safety_grm_qwen3vl_8b_megatron_grpo' \
    trainer.n_gpus_per_node=8 \
    trainer.nnodes=1 \
    trainer.save_freq=40 \
    trainer.test_freq=40 \
    trainer.total_epochs=1 \
    trainer.device=cuda \
    trainer.default_local_dir=$YOUR_CHECKPOINT_PATH \
    trainer.log_val_generations=100 \
    $@ 2>&1 | tee $LOG_FILE

echo "Training completed. Log saved to: $LOG_FILE"
echo "Evaluation results saved to: $EVAL_DIR"