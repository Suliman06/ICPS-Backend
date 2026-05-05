from fastapi import APIRouter
from database.database import get_summary_counts

router = APIRouter(prefix="/summary", tags=["summary"])


@router.get("")
def get_summary():
    return {
        "status": "success",
        "summary": get_summary_counts()
    }