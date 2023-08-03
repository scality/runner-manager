from fastapi import APIRouter, Response

router = APIRouter(prefix="/webhook")


@router.get("/")
def get():
    return Response(content="Success", status_code=200)
