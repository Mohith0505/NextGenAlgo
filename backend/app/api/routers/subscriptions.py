from fastapi import APIRouter

from app.schemas.auth import Message

router = APIRouter(prefix="", tags=[""])


@router.get("", response_model=Message, summary="")
def read_() -> Message:
    return Message(detail="")
