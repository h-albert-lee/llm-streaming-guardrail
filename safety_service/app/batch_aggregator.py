import asyncio
from app.guardrail import LlamaGuardModel
from app.config import BATCH_INTERVAL

class AsyncBatchAggregator:
    """
    asyncio.Queue를 사용하여 배치 추론을 수행하는 비동기 BatchAggregator.
    BATCH_INTERVAL마다 큐에 있는 요청들을 모아 LlamaGuardModel.predict_batch를 호출합니다.
    """
    def __init__(self):
        self.queue = asyncio.Queue()
        self.model = LlamaGuardModel()
        self._task = None
        self._shutdown_event = asyncio.Event()
    
    async def start(self):
        self._task = asyncio.create_task(self._batch_worker())
    
    async def shutdown(self):
        self._shutdown_event.set()
        if self._task:
            await self._task

    async def enqueue(self, text: str) -> str:
        loop = asyncio.get_event_loop()
        fut = loop.create_future()
        await self.queue.put((text, fut))
        return await fut

    async def _batch_worker(self):
        while not self._shutdown_event.is_set():
            await asyncio.sleep(BATCH_INTERVAL)
            items = []
            while not self.queue.empty():
                items.append(await self.queue.get())
            if items:
                texts, futures = zip(*items)
                try:
                    results = await asyncio.get_event_loop().run_in_executor(None, self.model.predict_batch, list(texts))
                except Exception as e:
                    for _, fut in items:
                        if not fut.done():
                            fut.set_exception(e)
                    continue
                for fut, res in zip(futures, results):
                    if not fut.done():
                        fut.set_result(res)
