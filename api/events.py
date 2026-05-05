from fastapi import APIRouter
from database.database import get_recent_events

router = APIRouter(prefix="/events", tags=["events"])


@router.get("/recent")
def get_recent_events_api(limit: int = 20):
    return {
        "status": "success",
        "count": limit,
        "events": get_recent_events(limit=limit)
    }