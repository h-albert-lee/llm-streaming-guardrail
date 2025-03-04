import os

# vLLM 서버(OpenAI Compatible API) 주소
VLLM_SERVER_URL = os.getenv("VLLM_SERVER_URL", "http://localhost:8001/v1/chat/completions")
# Safety Service 주소 (별도 서비스로 운영할 경우)
SAFETY_SERVICE_URL = os.getenv("SAFETY_SERVICE_URL", "http://localhost:8002/v1/chat/completions")
# SAFETY_MODE: "separate" (별도 Safety Service 사용) 또는 "vllm" (vLLM 서버를 통해 Llama Guard 호출)
SAFETY_MODE = os.getenv("SAFETY_MODE", "separate")
# 청크 크기: 테스트용으로 5자 (실제 운영에서는 적절히 조정)
BUFFER_SIZE = int(os.getenv("BUFFER_SIZE", "5"))
# 시간 기반 flush 간격 (초)
FLUSH_INTERVAL = float(os.getenv("FLUSH_INTERVAL", "0.5"))
# 선택적 API Key (환경변수 API_KEY를 확인)
API_KEY = os.getenv("API_KEY", "mysecretapikey")
