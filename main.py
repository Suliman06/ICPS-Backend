from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database.database import init_db
from mqtt.listener import start_listener_in_thread

from api.events import router as events_router
from api.summary import router as summary_router
from api.mood import router as mood_router
from api.graphs import router as graphs_router
from api.students import router as students_router
from api.lessons import router as lessons_router

app = FastAPI(title="Classroom Feedback API")

# -------------------------
# CORS
# -------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # fine for local development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# -------------------------
# STARTUP
# -------------------------
@app.on_event("startup")
def startup_event():
    print("Starting system...")

    # Initialize database and create required tables
    init_db()
    print("Database ready")

    # Start MQTT listener in background
    start_listener_in_thread()
    print("MQTT listener started")


# -------------------------
# ROUTES
# -------------------------
app.include_router(events_router)
app.include_router(summary_router)
app.include_router(mood_router)
app.include_router(graphs_router)
app.include_router(students_router)
app.include_router(lessons_router)


@app.get("/")
def root():
    return {"message": "Classroom Feedback API running"}