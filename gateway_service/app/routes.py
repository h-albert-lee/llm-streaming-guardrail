import json
import time
import asyncio
import httpx
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from app.config import SAFETY_SERVICE_URL, BUFFER_SIZE, FLUSH_INTERVAL
from app.vllm_client import stream_vllm_request

router = APIRouter()

class StreamingBufferManager:
    """
    누적된 텍스트를 BUFFER_SIZE 단위로 flush하거나, FLUSH_INTERVAL마다 잔여 데이터를 반환합니다.
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

async def check_safety(text: str) -> bool:
    """
    비동기 HTTP 클라이언트를 사용하여 Safety Service에 텍스트 안전성 검사를 요청합니다.
    safe이면 True, unsafe이면 False를 반환.
    """
    payload = {"text": text}
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(SAFETY_SERVICE_URL, json=payload)
    except Exception:
        return False
    if resp.status_code != 200:
        return False
    data = resp.json()
    return data.get("result") == "safe"

@router.post("/v1/chat/completions")
async def completions(request: Request):
    """
    OpenAI 호환 API 엔드포인트.
    1) 클라이언트 요청을 받아 vLLM 서버에 스트리밍 요청을 보냄.
    2) 응답 청크를 BUFFER_SIZE 또는 FLUSH_INTERVAL에 따라 누적하여,
       Safety Service에 비동기 검사를 수행한 후,
       안전하면 그대로, unsafe면 [Filtered]로 반환.
    3) 최종적으로 SSE로 클라이언트에 스트리밍 전송.
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
            decoded = line.strip()
            if decoded.startswith("data: "):
                data_str = decoded[len("data: "):]
                if data_str == "[DONE]":
                    leftover = buffer_manager.flush()
                    if leftover:
                        if await check_safety(leftover):
                            yield f"data: {leftover}\n\n"
                        else:
                            yield "data: [Filtered]\n\n"
                    yield "data: [DONE]\n\n"
                    break

                try:
                    chunk_json = json.loads(data_str)
                except json.JSONDecodeError:
                    continue

                choices = chunk_json.get("choices", [])
                if not choices:
                    continue
                message = choices[0].get("message", {})
                content = message.get("content", "")

                buffered_chunk = buffer_manager.add(content)
                if buffered_chunk:
                    if await check_safety(buffered_chunk):
                        yield f"data: {buffered_chunk}\n\n"
                    else:
                        yield "data: [Filtered]\n\n"

            # 시간 기반 flush 처리
            if FLUSH_INTERVAL > 0:
                now = time.time()
                if now - last_flush_time >= FLUSH_INTERVAL:
                    leftover = buffer_manager.flush()
                    if leftover:
                        if await check_safety(leftover):
                            yield f"data: {leftover}\n\n"
                        else:
                            yield "data: [Filtered]\n\n"
                    last_flush_time = now
            await asyncio.sleep(0.01)

    return StreamingResponse(event_generator(), media_type="text/event-stream")
