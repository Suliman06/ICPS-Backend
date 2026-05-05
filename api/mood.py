from fastapi import APIRouter
from database.database import get_class_mood

router = APIRouter(prefix="/mood", tags=["mood"])


@router.get("")
def get_mood(minutes: int = 30):
    return {
        "status": "success",
        "data": get_class_mood(minutes)
    }