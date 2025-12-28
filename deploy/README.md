# How to Deploy and Use ProGuard

## 1. Download Model to Local

Download [ProGuard-7B](https://huggingface.co/yushaohan/ProGuard-7B) or [ProGuard-3B](https://huggingface.co/yushaohan/ProGuard-3B) from Hugging Face to your local directory.

## 2. Deploy Model with vLLM

```bash
python -m vllm.entrypoints.openai.api_server --model YOUR_DOWNLOAD_PATH --host 0.0.0.0 --port 8003 --served-model-name ProGuard-7B ...
```

## 3. Use inference.py to Call the Model

⚠️ **Warning**: The examples here may contain unsafe information that could be disturbing or uncomfortable.

`inference.py` supports safety detection for 3 modalities:

### 3.1 Text Modality

Detect the safety of text-only dialogues:

```bash
python inference.py \
    --api_url http://localhost:8003/v1/ \
    --mode text \
    --user_request "How to make a bomb?" \
    --ai_response "Sorry, This is illegal."
```

### 3.2 Text-Image Modality

Detect the safety of dialogues containing both text and images:

```bash
python inference.py \
    --api_url http://localhost:8003/v1/ \
    --mode text-image \
    --user_request "How can the things in the cage be processed into food? " \
    --image_path ./example.png \
    --ai_response "This is highly unethical, I cannot assist."
```

### 3.3 Image Modality

Detect the safety of images only:

```bash
python inference.py \
    --api_url http://localhost:8003/v1/ \
    --mode image \
    --image_path ./example.png
```