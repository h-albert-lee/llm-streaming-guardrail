import time
import threading
from concurrent.futures import Future
from app.guardrail import LlamaGuardModel
from app.config import BATCH_INTERVAL

class BatchAggregator:
    """
    여러 텍스트 요청을 in-memory 큐에 쌓고, BATCH_INTERVAL마다 배치 추론을 수행하여
    각 요청에 대해 Future 객체로 결과를 전달합니다.
    """
    def __init__(self):
        self.model = LlamaGuardModel()
        self.queue = []  # (text, Future) 튜플 리스트
        self.lock = threading.Lock()
        self.stop_event = threading.Event()
        self.worker_thread = threading.Thread(target=self._batch_worker)
        self.worker_thread.start()

    def enqueue(self, text: str) -> Future:
        fut = Future()
        with self.lock:
            self.queue.append((text, fut))
        return fut

    def _batch_worker(self):
        while not self.stop_event.is_set():
            time.sleep(BATCH_INTERVAL)
            with self.lock:
                if self.queue:
                    texts, futures = [], []
                    for (t, f) in self.queue:
                        texts.append(t)
                        futures.append(f)
                    self.queue.clear()
            if texts:
                results = self.model.predict_batch(texts)
                for f, r in zip(futures, results):
                    f.set_result(r)

    def shutdown(self):
        self.stop_event.set()
        self.worker_thread.join()
