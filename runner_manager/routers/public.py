from fastapi import APIRouter

router = APIRouter(prefix="/public")


@router.get("/")
def public():
    """A public endpoint that does not require any authentication."""
    return "Public Endpoint"
