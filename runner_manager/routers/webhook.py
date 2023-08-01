from fastapi import APIRouter, Response

router = APIRouter(prefix="/webhook")

@router.get("/")
def get():
    return Response(200)