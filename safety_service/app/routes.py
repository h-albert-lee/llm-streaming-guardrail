import asyncio
from fastapi import APIRouter, HTTPException
from app.batch_aggregator import AsyncBatchAggregator

router = APIRouter()
batch_agg = AsyncBatchAggregator()

@router.on_event("startup")
async def startup_event():
    await batch_agg.start()

@router.on_event("shutdown")
async def shutdown_event():
    await batch_agg.shutdown()

@router.post("/safecheck")
async def safecheck(text: str):
    try:
        result = await batch_agg.enqueue(text)
        return {"result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/safecheck_batch")
async def safecheck_batch(texts: list[str]):
    try:
        results = []
        for text in texts:
            res = await batch_agg.enqueue(text)
            results.append(res)
        return {"results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
