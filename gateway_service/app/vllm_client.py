import httpx
from app.config import VLLM_SERVER_URL

async def stream_vllm_request(payload: dict):
    """
    vLLM 서버에 비동기 스트리밍 요청을 보내고, 응답 라인을 비동기 generator로 반환합니다.
    """
    async with httpx.AsyncClient(timeout=None) as client:
        async with client.stream("POST", VLLM_SERVER_URL, json=payload) as resp:
            async for line in resp.aiter_lines():
                yield line
