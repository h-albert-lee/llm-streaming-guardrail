import json
import time
import asyncio
import httpx
import re
import logging
import uuid
from fastapi import APIRouter, Request, Depends
from fastapi.responses import StreamingResponse
from app.config import (
    SAFETY_SERVICE_URL, BUFFER_SIZE, FLUSH_INTERVAL, SAFETY_MODE,
    VLLM_SERVER_URL, SAFETY_MODEL, SAFETY_API_KEY
)
from app.vllm_client import stream_vllm_request
from app.dependencies import verify_api_key
from app.prompt_builder import load_safety_categories

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

router = APIRouter(dependencies=[Depends(verify_api_key)])

def create_chunk_response(content: str) -> dict:
    """
    생성할 chunk를 OpenAI Compatible API 스트리밍 형식의 JSON 객체로 변환합니다.
    각 chunk는 새로운 UUID와 현재 타임스탬프를 포함합니다.
    """
    return {
        "id": "chat-" + uuid.uuid4().hex,
        "object": "chat.completion.chunk",
        "created": int(time.time()),
        "choices": [
            {"index": 0, "delta": {"content": content}}
        ]
    }

class StreamingBufferManager:
    """
    누적된 텍스트를 BUFFER_SIZE 단위로 반환하거나, FLUSH_INTERVAL마다 잔여 데이터를 반환합니다.
    """
    def __init__(self, buffer_size: int):
        self.buffer_size = buffer_size
        self.current_buffer = ""

    def add(self, content: str) -> str:
        logger.debug("Adding content to buffer. Current length: %d", len(self.current_buffer))
        self.current_buffer += content
        if len(self.current_buffer) >= self.buffer_size:
            chunk = self.current_buffer[:self.buffer_size]
            self.current_buffer = self.current_buffer[self.buffer_size:]
            logger.info("Buffer full, emitting chunk: %s", chunk)
            return chunk
        return None

    def flush(self) -> str:
        ret = self.current_buffer
        if ret:
            logger.info("Flushing buffer: %s", ret)
        self.current_buffer = ""
        return ret

def parse_safety_output(content: str) -> bool:
    """
    정규표현식을 사용하여 Safety 검증 출력 텍스트를 분석합니다.
    - "\n\nunsafe" 또는 "\n\nunsafe\nS1" ~ "\n\nunsafe\nS15"가 있으면 unsafe로 판단
    - "\n\nsafe"가 있으면 safe로 판단
    """
    logger.debug("Parsing safety output: %s", content)
    unsafe_pattern = re.compile(r"unsafe(?:\nS(?:[1-9]|1[0-5]))?", re.IGNORECASE)
    safe_pattern = re.compile(r"safe", re.IGNORECASE)
    if unsafe_pattern.search(content):
        logger.info("Safety output indicates unsafe.")
        return False
    if safe_pattern.search(content):
        logger.info("Safety output indicates safe.")
        return True
    logger.info("No explicit safety indication; defaulting to safe.")
    return True  # 기본 safe

async def check_safety(text: str, retries: int = 3) -> bool:
    """
    Safety 검증을 수행합니다.
    클라이언트의 텍스트(버퍼 청크)를 safety vLLM 서버에 전달하여 검증합니다.
    SAFETY_SERVICE_URL, SAFETY_MODEL, SAFETY_API_KEY를 사용하며, 재시도 로직을 포함합니다.
    """
    headers = {}
    if SAFETY_API_KEY:
        headers["Authorization"] = f"Bearer {SAFETY_API_KEY}"
    try:
        safety_categories = load_safety_categories()
        categories_str = "\n".join(
            [f"S{i+1}: {cat.name} - {cat.description}" for i, cat in enumerate(safety_categories)]
        )
    except Exception as e:
        logger.exception("Failed to load safety categories: %s", e)
        categories_str = "No safety categories available."
    system_message = (
        "Classify the given prompt as safe or unsafe. For unsafe responses, specify the category (e.g., S1, S13) "
        "and provide reasoning behind your choice. Below is the safety policy with the following categories:\n"
        f"{categories_str}"
    )
    messages = [
        {"role": "user", "content": ""},
        {"role": "system", "content": system_message},
        {"role": "user", "content": f"User: {text}"}
    ]
    payload = {
        "model": SAFETY_MODEL,
        "messages": messages,
        "max_tokens": 10,
        "temperature": 1.0,
        "stream": False
    }
    target_url = SAFETY_SERVICE_URL
    attempt = 0
    while attempt < retries:
        try:
            logger.info("Sending safety check request (attempt %d) to %s", attempt+1, target_url)
            async with httpx.AsyncClient(timeout=10.0, headers=headers) as client:
                resp = await client.post(target_url, json=payload)
            if resp.status_code != 200:
                raise Exception(f"Safety Service HTTP {resp.status_code}")
            data = resp.json()
            content = data["choices"][0]["message"]["content"].strip()
            logger.info("Safety check response: %s", content)
            return parse_safety_output(content)
        except Exception as e:
            attempt += 1
            logger.warning("Safety check attempt %d failed: %s", attempt, e)
            await asyncio.sleep(2 ** attempt * 0.1)
            if attempt >= retries:
                logger.error("Safety check failed after %d attempts, defaulting to safe.", attempt)
                return True

@router.post("/v1/chat/completions")
async def completions(request: Request):
    """
    OpenAI Compatible API 엔드포인트.
    1) 클라이언트 요청을 받아 vLLM 서버에 스트리밍 요청을 보냅니다.
    2) 응답 청크를 BUFFER_SIZE 또는 FLUSH_INTERVAL에 따라 누적한 후, Safety 검증을 수행합니다.
    3) 안전하면 그대로, unsafe면 "[UNSAFE]" 태그를 붙여 SSE 형식으로 전송합니다.
       이때, 전송하는 메시지는 delta 형식의 JSON 객체(OpenAI Compatible API)를 사용합니다.
    """
    logger.info("Received completions request.")
    payload = await request.json()
    logger.debug("Request payload: %s", payload)
    vllm_stream = stream_vllm_request(payload)
    buffer_manager = StreamingBufferManager(BUFFER_SIZE)
    last_flush_time = time.time()

    async def event_generator():
        nonlocal last_flush_time
        async for line in vllm_stream:
            if not line:
                continue
            try:
                decoded = line.strip()
                logger.debug("Received raw line: %s", decoded)
            except Exception as e:
                logger.error("Error decoding line: %s", e)
                continue

            if decoded.startswith("data: "):
                data_str = decoded[len("data: "):]
                if data_str == "[DONE]":
                    logger.info("Received [DONE] signal from vLLM server.")
                    leftover = buffer_manager.flush()
                    if leftover:
                        safe = await check_safety(leftover)
                        if safe:
                            response = create_chunk_response(leftover)
                        else:
                            response = create_chunk_response("[UNSAFE] " + leftover)
                        yield f"data: {json.dumps(response)}\n\n"
                    yield "data: " + json.dumps(create_chunk_response("[DONE]")) + "\n\n"
                    break

                try:
                    # vLLM의 streaming chunk는 delta 필드에 내용이 들어있습니다.
                    chunk_json = json.loads(data_str)
                except json.JSONDecodeError as e:
                    logger.error("JSON decode error: %s - Raw line: %s", e, decoded)
                    continue

                choices = chunk_json.get("choices", [])
                if not choices:
                    logger.debug("No choices found in chunk.")
                    continue

                # delta 기반으로 content 추출
                delta = choices[0].get("delta")
                if delta is not None:
                    content = delta.get("content", "")
                else:
                    message = choices[0].get("message", {})
                    content = message.get("content", "")
                logger.debug("Extracted content: %s", content)

                buffered_chunk = buffer_manager.add(content)
                if buffered_chunk:
                    logger.info("Buffer chunk ready for safety check: %s", buffered_chunk)
                    safe = await check_safety(buffered_chunk)
                    if safe:
                        response = create_chunk_response(buffered_chunk)
                    else:
                        response = create_chunk_response("[UNSAFE] " + buffered_chunk)
                    yield f"data: {json.dumps(response)}\n\n"

            if FLUSH_INTERVAL > 0:
                now = time.time()
                if now - last_flush_time >= FLUSH_INTERVAL:
                    leftover = buffer_manager.flush()
                    if leftover:
                        logger.info("Time-based flush, checking safety for: %s", leftover)
                        safe = await check_safety(leftover)
                        if safe:
                            response = create_chunk_response(leftover)
                        else:
                            response = create_chunk_response("[UNSAFE] " + leftover)
                        yield f"data: {json.dumps(response)}\n\n"
                    last_flush_time = now
            await asyncio.sleep(0.01)

    return StreamingResponse(event_generator(), media_type="text/event-stream")
