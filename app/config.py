import os

# 일반 vLLM 서버 설정 (클라이언트 payload를 그대로 사용)
VLLM_SERVER_URL = os.getenv("VLLM_SERVER_URL", "http://localhost:8001/v1/chat/completions")
# 클라이언트 요청에 모델명이 포함되어 있다면, 이 값은 기본값으로 사용될 수 있습니다.
VLLM_MODEL = os.getenv("VLLM_MODEL", None)  # None으로 둘 수 있습니다.

VLLM_API_KEY = os.getenv("VLLM_API_KEY", None)

# Safety vLLM 서버 설정 (안전성 모델을 서빙하는 vLLM 인스턴스)
SAFETY_SERVICE_URL = os.getenv("SAFETY_SERVICE_URL", "http://localhost:8002/v1/chat/completions")
SAFETY_MODEL = os.getenv("SAFETY_MODEL", "llama-guard")
SAFETY_API_KEY = os.getenv("SAFETY_API_KEY", None)

# SAFETY_MODE 옵션 ("vllm" 모드 사용 시, safety 전용 vLLM 호출)
SAFETY_MODE = os.getenv("SAFETY_MODE", "vllm")

# 스트리밍 관련 설정
BUFFER_SIZE = int(os.getenv("BUFFER_SIZE", "5"))  # 예: 5자 단위
FLUSH_INTERVAL = float(os.getenv("FLUSH_INTERVAL", "0.5"))

# 선택적 Gateway API Key (요청 검증)
API_KEY = os.getenv("API_KEY", "mysecretapikey")
