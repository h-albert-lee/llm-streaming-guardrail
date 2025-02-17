import asyncio
from fastapi import APIRouter, HTTPException
from app.batch_aggregator import BatchAggregator

router = APIRouter()
batch_agg = BatchAggregator()

@router.on_event("shutdown")
def shutdown_event():
    batch_agg.shutdown()

@router.post("/safecheck")
async def safecheck(text: str):
    """
    단일 텍스트 안전성 검사.
    최대 BATCH_INTERVAL 정도의 딜레이가 있을 수 있음.
    """
    try:
        fut = batch_agg.enqueue(text)
        result = await asyncio.wrap_future(fut)
        return {"result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/safecheck_batch")
async def safecheck_batch(texts: list[str]):
    """
    다중 텍스트 안전성 검사.
    """
    try:
        futures = [batch_agg.enqueue(t) for t in texts]
        results = await asyncio.gather(*(asyncio.wrap_future(f) for f in futures))
        return {"results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
