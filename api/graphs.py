from fastapi import APIRouter
from database.database import get_graph_data

router = APIRouter(prefix="/graphs", tags=["graphs"])


@router.get("")
def get_graph(
    window_value: int = 30,
    window_unit: str = "minutes",
    group_by: str = "5min"
):
    return {
        "status": "success",
        "data": get_graph_data(window_value, window_unit, group_by)
    }