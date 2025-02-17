import os

# vLLM 서버의 OpenAI 호환 API 주소 (예: Docker 등으로 별도 배포)
VLLM_SERVER_URL = os.getenv("VLLM_SERVER_URL", "http://localhost:8001/v1/chat/completions")

# Safety Service 주소 (위 Safety Service가 8002 포트에서 동작)
SAFETY_SERVICE_URL = os.getenv("SAFETY_SERVICE_URL", "http://localhost:8002/safecheck")

# 청크 크기를 작게 잡아 5자 정도로 설정 (실제 서비스에 맞게 조정)
BUFFER_SIZE = int(os.getenv("BUFFER_SIZE", "5"))

# 시간 기반 flush 간격 (초)
FLUSH_INTERVAL = float(os.getenv("FLUSH_INTERVAL", "0.5"))
