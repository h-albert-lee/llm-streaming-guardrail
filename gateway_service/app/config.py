import os

# 일반 vLLM 서버 설정
VLLM_SERVER_URL = os.getenv("VLLM_SERVER_URL", "http://localhost:8001/v1/chat/completions")
VLLM_MODEL = os.getenv("VLLM_MODEL", "gpt-3.5-turbo")
VLLM_API_KEY = os.getenv("VLLM_API_KEY", None)

# Safety vLLM 서버 설정 (안전성 모델을 서빙하는 vLLM 인스턴스)
SAFETY_SERVICE_URL = os.getenv("SAFETY_SERVICE_URL", "http://localhost:8002/v1/chat/completions")
SAFETY_MODEL = os.getenv("SAFETY_MODEL", "llama-guard")
SAFETY_API_KEY = os.getenv("SAFETY_API_KEY", None)

# SAFETY_MODE 옵션 (여기서는 safety vLLM 서버를 호출하도록 항상 사용)
SAFETY_MODE = os.getenv("SAFETY_MODE", "vllm")  # "vllm" 또는 "separate" (동일하게 처리)

# 스트리밍 관련 설정
BUFFER_SIZE = int(os.getenv("BUFFER_SIZE", "5"))  # 예시: 5자 단위
FLUSH_INTERVAL = float(os.getenv("FLUSH_INTERVAL", "0.5"))

# 선택적 Gateway API Key (요청 검증)
API_KEY = os.getenv("API_KEY", "mysecretapikey")
