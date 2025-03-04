import httpx
import asyncio
from app.config import VLLM_SERVER_URL

async def stream_vllm_request(payload: dict, retries: int = 3):
    """
    vLLM 서버에 비동기 스트리밍 요청을 보내고, 응답 라인을 비동기 generator로 반환합니다.
    재시도 로직(최대 retries회)을 포함합니다.
    """
    attempt = 0
    while attempt < retries:
        try:
            async with httpx.AsyncClient(timeout=None) as client:
                async with client.stream("POST", VLLM_SERVER_URL, json=payload) as resp:
                    async for line in resp.aiter_lines():
                        yield line
            break
        except Exception as e:
            attempt += 1
            await asyncio.sleep(2 ** attempt * 0.1)
            if attempt >= retries:
                raise e
