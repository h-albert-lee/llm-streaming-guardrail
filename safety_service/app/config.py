import os

# LLaMA Guard 모델 이름 (Hugging Face에 등록된 모델)
GUARDRAIL_MODEL_NAME = os.getenv("GUARDRAIL_MODEL_NAME", "meta-llama/LlamaGuard")

# 배치 추론 주기 (초) – 기본 0.05초 (50ms)
BATCH_INTERVAL = float(os.getenv("BATCH_INTERVAL", "0.05"))
