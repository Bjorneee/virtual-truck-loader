from fastapi import APIRouter, HTTPException
from python.vtl_core.schemas import PackingRequest, PackingResponse
from python.services.packing_services import run_packing

router = APIRouter()

@router.get("/")
def root():
    return {"Hello": "World"}

@router.get("/health")
def health_check():
    return {"status": "ok"}

@router.post("/pack", response_model=PackingResponse)
def pack_truck(request: PackingRequest):
    try:
        return run_packing(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
