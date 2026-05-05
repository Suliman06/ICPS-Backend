from fastapi import APIRouter
from pydantic import BaseModel

from database.database import (
    start_lesson,
    end_active_lesson,
    get_active_lesson,
    get_lessons,
    get_lesson_by_id,
    get_lesson_events,
    get_lesson_summary,
    get_lesson_graph_data,
    get_lesson_report
)

router = APIRouter(prefix="/lessons", tags=["lessons"])


class StartLessonRequest(BaseModel):
    title: str


@router.get("")
def list_lessons(limit: int = 20):
    return {
        "status": "success",
        "lessons": get_lessons(limit)
    }


@router.get("/active")
def active_lesson():
    lesson = get_active_lesson()

    return {
        "status": "success",
        "lesson": lesson
    }


@router.post("/start")
def start_new_lesson(request: StartLessonRequest):
    lesson = start_lesson(request.title)

    return {
        "status": "success",
        "message": "Lesson started",
        "lesson": lesson
    }


@router.post("/end")
def end_lesson():
    lesson = end_active_lesson()

    if lesson is None:
        return {
            "status": "no_active_lesson",
            "message": "No active lesson to end",
            "lesson": None
        }

    return {
        "status": "success",
        "message": "Lesson ended",
        "lesson": lesson
    }


@router.get("/{lesson_id}")
def lesson_detail(lesson_id: int):
    lesson = get_lesson_by_id(lesson_id)

    if lesson is None:
        return {
            "status": "not_found",
            "lesson": None
        }

    return {
        "status": "success",
        "lesson": lesson
    }


@router.get("/{lesson_id}/events")
def lesson_events(lesson_id: int, limit: int = 500):
    return {
        "status": "success",
        "events": get_lesson_events(lesson_id, limit)
    }


@router.get("/{lesson_id}/summary")
def lesson_summary(lesson_id: int):
    return {
        "status": "success",
        "summary": get_lesson_summary(lesson_id)
    }


@router.get("/{lesson_id}/graph")
def lesson_graph(lesson_id: int, group_by: str = "5min"):
    return {
        "status": "success",
        "data": get_lesson_graph_data(lesson_id, group_by)
    }


@router.get("/{lesson_id}/report")
def lesson_report(lesson_id: int, group_by: str = "5min"):
    return {
        "status": "success",
        "data": get_lesson_report(lesson_id, group_by)
    }