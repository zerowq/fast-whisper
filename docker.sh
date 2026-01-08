#!/bin/bash
 docker run -d \
  --name faster-whisper-asr \
  --gpus all \
  -p 8898:8898 \
  -e DEVICE=cuda \
  -e COMPUTE_TYPE=float16 \
  -e PORT=8898 \
  -v ~/.cache/huggingface:/root/.cache/huggingface \
  faster-whisper-asr:latest
