import os

GUARDRAIL_MODEL_NAME = os.getenv("GUARDRAIL_MODEL_NAME", "meta-llama/LlamaGuard")
BATCH_INTERVAL = float(os.getenv("BATCH_INTERVAL", "0.05"))  # 50ms
