import httpx
import asyncio
import logging
from app.config import VLLM_SERVER_URL, VLLM_API_KEY

logger = logging.getLogger(__name__)

async def stream_vllm_request(payload: dict, retries: int = 3):
    """
    vLLM 서버에 비동기 스트리밍 요청을 보내고, 응답 라인을 비동기 generator로 반환합니다.
    재시도 로직(최대 retries회)을 포함하며, VLLM_API_KEY가 있으면 헤더에 포함합니다.
    """
    headers = {}
    if VLLM_API_KEY:
        headers["Authorization"] = f"Bearer {VLLM_API_KEY}"
    attempt = 0
    while attempt < retries:
        try:
            logger.info("Sending request to vLLM server (attempt %d)", attempt+1)
            async with httpx.AsyncClient(timeout=None, headers=headers) as client:
                async with client.stream("POST", VLLM_SERVER_URL, json=payload) as resp:
                    logger.info("Received response from vLLM server with status %d", resp.status_code)
                    async for line in resp.aiter_lines():
                        yield line
            break
        except Exception as e:
            attempt += 1
            logger.warning("vLLM stream request failed (attempt %d): %s", attempt, e)
            await asyncio.sleep(2 ** attempt * 0.1)
            if attempt >= retries:
                logger.error("vLLM stream request failed after %d attempts", attempt)
                raise e
