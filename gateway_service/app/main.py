# gateway_service/app/main.py
from fastapi import FastAPI
from app.routes import router
import logging
import asyncio
import httpx
from app.config import (
    VLLM_SERVER_URL, VLLM_MODEL, VLLM_API_KEY,
    SAFETY_SERVICE_URL, SAFETY_MODEL, SAFETY_API_KEY
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Gateway Service - LLM Streaming with Safety Check")
app.include_router(router)

async def test_connection(url: str, payload: dict, headers: dict = None) -> None:
    """테스트 요청을 보내 연결 상태를 확인합니다."""
    try:
        async with httpx.AsyncClient(timeout=10.0, headers=headers) as client:
            response = await client.post(url, json=payload)
        if response.status_code != 200:
            logger.error("Test connection to %s failed with status %s", url, response.status_code)
        else:
            logger.info("Test connection to %s succeeded.", url)
    except Exception as e:
        logger.error("Test connection to %s encountered error: %s", url, e)

@app.on_event("startup")
async def startup_event():
    logger.info("Startup: Testing connections to vLLM and Safety servers using config settings.")

    # 테스트 요청: vLLM 서버
    test_payload_vllm = {
        "model": VLLM_MODEL if VLLM_MODEL is not None else "test-model",
        "messages": [{"role": "user", "content": "ping"}],
        "max_new_tokens": 1,
        "stream": False
    }
    vllm_headers = {}
    if VLLM_API_KEY:
        vllm_headers["Authorization"] = f"Bearer {VLLM_API_KEY}"
    await test_connection(VLLM_SERVER_URL, test_payload_vllm, headers=vllm_headers)

    # 테스트 요청: Safety vLLM 서버
    test_payload_safety = {
        "model": SAFETY_MODEL,
        "messages": [
            {"role": "system", "content": "Test safety check. Please classify as safe."},
            {"role": "user", "content": "ping"}
        ],
        "max_new_tokens": 1,
        "stream": False
    }
    safety_headers = {}
    if SAFETY_API_KEY:
        safety_headers["Authorization"] = f"Bearer {SAFETY_API_KEY}"
    await test_connection(SAFETY_SERVICE_URL, test_payload_safety, headers=safety_headers)
