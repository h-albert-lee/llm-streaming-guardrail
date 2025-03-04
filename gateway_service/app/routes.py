import json
import time
import asyncio
import httpx
import re
from fastapi import APIRouter, Request, Depends
from fastapi.responses import StreamingResponse
from app.config import SAFETY_SERVICE_URL, BUFFER_SIZE, FLUSH_INTERVAL, SAFETY_MODE, VLLM_SERVER_URL
from app.vllm_client import stream_vllm_request
from app.dependencies import verify_api_key

router = APIRouter(dependencies=[Depends(verify_api_key)])

class StreamingBufferManager:
    """
    누적된 텍스트를 BUFFER_SIZE 단위로 반환하거나, FLUSH_INTERVAL마다 잔여 데이터를 반환합니다.
    """
    def __init__(self, buffer_size: int):
        self.buffer_size = buffer_size
        self.current_buffer = ""

    def add(self, content: str) -> str:
        self.current_buffer += content
        if len(self.current_buffer) >= self.buffer_size:
            chunk = self.current_buffer[:self.buffer_size]
            self.current_buffer = self.current_buffer[self.buffer_size:]
            return chunk
        return None

    def flush(self) -> str:
        ret = self.current_buffer
        self.current_buffer = ""
        return ret

def parse_safety_output(content: str) -> bool:
    """
    정규표현식을 사용하여 Safety Service의 출력 텍스트를 분석합니다.
    - "\n\nunsafe" 또는 "\n\nunsafe\nS1" ~ "\n\nunsafe\nS15"가 있으면 unsafe로 판단
    - "\n\nsafe"가 있으면 safe로 판단
    """
    if re.search(r"\n\nunsafe(?:\nS(?:[1-9]|1[0-5]))?", content, re.IGNORECASE):
        return False
    if re.search(r"\n\nsafe", content, re.IGNORECASE):
        return True
    return True  # 기본적으로 safe로 판단

async def check_safety(text: str, retries: int = 3) -> bool:
    """
    Safety 검증을 수행합니다.
    SAFETY_MODE에 따라:
      - "separate": 별도의 Safety Service에 호출
      - "vllm": vLLM 서버에 "llama-guard" 모델로 호출
    재시도 로직 포함.
    """
    target_url = SAFETY_SERVICE_URL if SAFETY_MODE == "separate" else VLLM_SERVER_URL
    payload = {
        "model": "llama-guard",
        "messages": [
            {"role": "system", "content": "You are a safety guard. Evaluate the following text and respond with a single word: safe or unsafe, optionally followed by additional text."},
            {"role": "user", "content": text}
        ],
        "max_tokens": 20,
        "stream": False
    }
    attempt = 0
    while attempt < retries:
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(target_url, json=payload)
            if resp.status_code != 200:
                raise Exception(f"Safety Service HTTP {resp.status_code}")
            data = resp.json()
            content = data["choices"][0]["message"]["content"].strip()
            return parse_safety_output(content)
        except Exception as e:
            attempt += 1
            await asyncio.sleep(2 ** attempt * 0.1)
            if attempt >= retries:
                # 재시도 실패 시 기본 safe로 판단
                return True

@router.post("/v1/chat/completions")
async def completions(request: Request):
    """
    OpenAI Compatible API 엔드포인트.
    1) 클라이언트 요청을 받아 vLLM 서버에 스트리밍 요청을 보냄.
    2) 응답 청크를 BUFFER_SIZE 또는 FLUSH_INTERVAL에 따라 누적하여,
       Safety 검증을 수행합니다.
    3) 안전하면 그대로, unsafe이면 "[UNSAFE]" 태그를 붙여 SSE로 전송합니다.
    """
    payload = await request.json()
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
            except Exception as e:
                print(f"Error decoding line: {e}")
                continue

            if decoded.startswith("data: "):
                data_str = decoded[len("data: "):]
                if data_str == "[DONE]":
                    leftover = buffer_manager.flush()
                    if leftover:
                        safe = await check_safety(leftover)
                        if safe:
                            yield f"data: {leftover}\n\n"
                        else:
                            yield f"data: [UNSAFE] {leftover}\n\n"
                    yield "data: [DONE]\n\n"
                    break

                try:
                    chunk_json = json.loads(data_str)
                except json.JSONDecodeError as e:
                    print(f"JSON decode error: {e} - Raw line: {decoded}")
                    continue

                choices = chunk_json.get("choices", [])
                if not choices:
                    continue
                message = choices[0].get("message", {})
                content = message.get("content", "")

                buffered_chunk = buffer_manager.add(content)
                if buffered_chunk:
                    safe = await check_safety(buffered_chunk)
                    if safe:
                        yield f"data: {buffered_chunk}\n\n"
                    else:
                        yield f"data: [UNSAFE] {buffered_chunk}\n\n"

            if FLUSH_INTERVAL > 0:
                now = time.time()
                if now - last_flush_time >= FLUSH_INTERVAL:
                    leftover = buffer_manager.flush()
                    if leftover:
                        safe = await check_safety(leftover)
                        if safe:
                            yield f"data: {leftover}\n\n"
                        else:
                            yield f"data: [UNSAFE] {leftover}\n\n"
                    last_flush_time = now
            await asyncio.sleep(0.01)

    return StreamingResponse(event_generator(), media_type="text/event-stream")
