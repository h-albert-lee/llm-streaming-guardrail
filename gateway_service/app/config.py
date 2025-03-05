import os

# 일반 vLLM 서버 설정
VLLM_SERVER_URL = os.getenv("VLLM_SERVER_URL", "http://localhost:8001/v1/chat/completions")
VLLM_MODEL = os.getenv("VLLM_MODEL", "gpt-3.5-turbo")
VLLM_API_KEY = os.getenv("VLLM_API_KEY", None)

# Safety Service 별도 운영 시 설정 (SAFETY_MODE == "separate")
SAFETY_SERVICE_URL = os.getenv("SAFETY_SERVICE_URL", "http://localhost:8002/v1/chat/completions")
SAFETY_MODEL = os.getenv("SAFETY_MODEL", "llama-guard")
SAFETY_API_KEY = os.getenv("SAFETY_API_KEY", None)

# SAFETY_MODE: "separate" (별도 Safety Service 사용) 또는 "vllm" (vLLM 서버를 통해 Llama Guard 호출)
SAFETY_MODE = os.getenv("SAFETY_MODE", "separate")

# 스트리밍 관련 설정
BUFFER_SIZE = int(os.getenv("BUFFER_SIZE", "5"))  # 예시: 5자
FLUSH_INTERVAL = float(os.getenv("FLUSH_INTERVAL", "0.5"))

# 선택적 Gateway API Key (요청 검증)
API_KEY = os.getenv("API_KEY", "mysecretapikey")
