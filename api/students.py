from fastapi import APIRouter
from database.database import (
    get_students,
    get_student_recent_events,
    get_student_summary,
    get_student_graph_data
)

router = APIRouter(prefix="/students", tags=["students"])


@router.get("")
def list_students():
    return {
        "status": "success",
        "students": get_students()
    }


@router.get("/{student_id}/events")
def student_events(student_id: str):
    return {
        "status": "success",
        "events": get_student_recent_events(student_id)
    }


@router.get("/{student_id}/summary")
def student_summary(student_id: str):
    return {
        "status": "success",
        "summary": get_student_summary(student_id)
    }


@router.get("/{student_id}/graph")
def student_graph(
    student_id: str,
    window_value: int = 30,
    window_unit: str = "minutes",
    group_by: str = "5min"
):
    return {
        "status": "success",
        "data": get_student_graph_data(
            student_id,
            window_value,
            window_unit,
            group_by
        )
    }