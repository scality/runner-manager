from pydantic import BaseModel


class JobResponse(BaseModel):
    """Response model for rq jobs."""

    id: str
    status: str
