import sqlite3
from pathlib import Path
from datetime import datetime, timedelta

DB_PATH = Path("classroom.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def empty_summary():
    return {
        "understand": 0,
        "slow_down": 0,
        "help": 0,
        "total": 0
    }


def add_to_summary(summary, action, count=1):
    if action in summary:
        summary[action] += count
        summary["total"] += count


def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT NOT NULL,
            action TEXT NOT NULL,
            timestamp TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS lessons (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            start_time TEXT NOT NULL,
            end_time TEXT,
            status TEXT NOT NULL
        )
    """)

    cursor.execute("PRAGMA table_info(events)")
    columns = [row["name"] for row in cursor.fetchall()]

    if "lesson_id" not in columns:
        cursor.execute("""
            ALTER TABLE events
            ADD COLUMN lesson_id INTEGER
        """)

    conn.commit()
    conn.close()


def get_active_lesson_id(conn=None):
    should_close = False

    if conn is None:
        conn = get_connection()
        should_close = True

    cursor = conn.cursor()

    cursor.execute("""
        SELECT id
        FROM lessons
        WHERE status = 'active'
        ORDER BY id DESC
        LIMIT 1
    """)

    row = cursor.fetchone()

    if should_close:
        conn.close()

    if row:
        return row["id"]

    return None


def start_lesson(title):
    conn = get_connection()
    cursor = conn.cursor()

    now = datetime.now().isoformat()

    cursor.execute("""
        UPDATE lessons
        SET status = 'ended',
            end_time = ?
        WHERE status = 'active'
    """, (now,))

    cursor.execute("""
        INSERT INTO lessons (title, start_time, end_time, status)
        VALUES (?, ?, ?, ?)
    """, (title, now, None, "active"))

    conn.commit()

    lesson_id = cursor.lastrowid
    conn.close()

    return {
        "id": lesson_id,
        "title": title,
        "start_time": now,
        "end_time": None,
        "status": "active"
    }


def end_active_lesson():
    conn = get_connection()
    cursor = conn.cursor()

    active_lesson_id = get_active_lesson_id(conn)

    if active_lesson_id is None:
        conn.close()
        return None

    end_time = datetime.now().isoformat()

    cursor.execute("""
        UPDATE lessons
        SET status = 'ended',
            end_time = ?
        WHERE id = ?
    """, (end_time, active_lesson_id))

    conn.commit()
    conn.close()

    return {
        "id": active_lesson_id,
        "status": "ended",
        "end_time": end_time
    }


def get_active_lesson():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, title, start_time, end_time, status
        FROM lessons
        WHERE status = 'active'
        ORDER BY id DESC
        LIMIT 1
    """)

    row = cursor.fetchone()
    conn.close()

    if row is None:
        return None

    return dict(row)


def get_lessons(limit=20):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, title, start_time, end_time, status
        FROM lessons
        ORDER BY id DESC
        LIMIT ?
    """, (limit,))

    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]


def get_lesson_by_id(lesson_id):
    if lesson_id is None:
        return None

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, title, start_time, end_time, status
        FROM lessons
        WHERE id = ?
        LIMIT 1
    """, (lesson_id,))

    row = cursor.fetchone()
    conn.close()

    if row is None:
        return None

    return dict(row)


def insert_event(student_id, action, timestamp=None):
    if timestamp is None:
        timestamp = datetime.now().isoformat()

    conn = get_connection()
    cursor = conn.cursor()

    active_lesson_id = get_active_lesson_id(conn)

    cursor.execute("""
        INSERT INTO events (student_id, action, timestamp, lesson_id)
        VALUES (?, ?, ?, ?)
    """, (student_id, action, timestamp, active_lesson_id))

    conn.commit()
    conn.close()


def get_recent_events(limit=20):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            e.id,
            e.student_id,
            e.action,
            e.timestamp,
            e.lesson_id,
            l.title AS lesson_title
        FROM events e
        LEFT JOIN lessons l ON e.lesson_id = l.id
        ORDER BY e.id DESC
        LIMIT ?
    """, (limit,))

    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]


def get_summary_counts():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT action, COUNT(*) as count
        FROM events
        GROUP BY action
    """)

    rows = cursor.fetchall()
    conn.close()

    summary = empty_summary()

    for row in rows:
        add_to_summary(summary, row["action"], row["count"])

    return summary


def get_summary_last_minutes(minutes=30):
    conn = get_connection()
    cursor = conn.cursor()

    cutoff_time = (datetime.now() - timedelta(minutes=minutes)).isoformat()

    cursor.execute("""
        SELECT action, COUNT(*) as count
        FROM events
        WHERE timestamp >= ?
        GROUP BY action
    """, (cutoff_time,))

    rows = cursor.fetchall()
    conn.close()

    summary = empty_summary()

    for row in rows:
        add_to_summary(summary, row["action"], row["count"])

    return summary


def calculate_percentages(summary):
    total = summary["total"]

    if total == 0:
        return {
            "understand": 0,
            "slow_down": 0,
            "help": 0
        }

    return {
        "understand": round((summary["understand"] / total) * 100, 1),
        "slow_down": round((summary["slow_down"] / total) * 100, 1),
        "help": round((summary["help"] / total) * 100, 1)
    }


def get_class_mood(minutes=30):
    counts = get_summary_last_minutes(minutes)
    percentages = calculate_percentages(counts)

    understand = percentages["understand"]
    slow_down = percentages["slow_down"]
    help_count = percentages["help"]
    total = counts["total"]

    if total == 0:
        return {
            "mood": "no_data",
            "message": "No classroom feedback yet",
            "counts": counts,
            "percentages": percentages,
            "window_minutes": minutes
        }

    if help_count >= 50:
        mood = "help_needed_majority"
        message = "Majority of the class may need help"

    elif help_count >= 30 and understand < 50:
        mood = "help_needed"
        message = "Several students may need help"

    elif slow_down >= 50:
        mood = "slow_down_majority"
        message = "Majority of the class may need a slower pace"

    elif slow_down >= 30 and understand < 50:
        mood = "slow_down_needed"
        message = "Several students may need a slower pace"

    elif understand >= 60 and help_count >= 10:
        mood = "understanding_with_help"
        message = "Most of the class is understanding, but a few may need help"

    elif understand >= 60 and slow_down >= 10:
        mood = "understanding_with_slow_down"
        message = "Most of the class is understanding, but some may need a slower pace"

    elif understand >= 60:
        mood = "understanding"
        message = "The class is understanding well"

    elif understand >= 40:
        if help_count >= slow_down:
            mood = "mixed_help"
            message = "Some students understand, but others may need help"
        else:
            mood = "mixed_slow_down"
            message = "Some students understand, but others may need a slower pace"

    else:
        mood = "mixed"
        message = "Class feedback is mixed"

    return {
        "mood": mood,
        "message": message,
        "counts": counts,
        "percentages": percentages,
        "window_minutes": minutes
    }


def _get_cutoff_time(window_value=30, window_unit="minutes"):
    now = datetime.now()

    if window_unit == "minutes":
        return now - timedelta(minutes=window_value)
    if window_unit == "hours":
        return now - timedelta(hours=window_value)
    if window_unit == "days":
        return now - timedelta(days=window_value)
    if window_unit == "months":
        return now - timedelta(days=30 * window_value)

    return now - timedelta(minutes=30)


def _get_bucket_delta(group_by="5min"):
    if group_by == "5min":
        return timedelta(minutes=5)
    if group_by == "15min":
        return timedelta(minutes=15)
    if group_by == "hour":
        return timedelta(hours=1)
    if group_by == "day":
        return timedelta(days=1)

    return timedelta(minutes=5)


def _align_time(dt, group_by="5min"):
    dt = dt.replace(second=0, microsecond=0)

    if group_by == "5min":
        minute = (dt.minute // 5) * 5
        return dt.replace(minute=minute)

    if group_by == "15min":
        minute = (dt.minute // 15) * 15
        return dt.replace(minute=minute)

    if group_by == "hour":
        return dt.replace(minute=0)

    if group_by == "day":
        return dt.replace(hour=0, minute=0)

    return dt


def _format_bucket_label(dt, group_by="5min"):
    if group_by in ["5min", "15min", "hour"]:
        return dt.strftime("%Y-%m-%d %H:%M")
    if group_by == "day":
        return dt.strftime("%Y-%m-%d")
    return dt.strftime("%Y-%m-%d %H:%M")


def _build_graph_buckets(rows, cutoff_time, now, group_by):
    bucket_delta = _get_bucket_delta(group_by)
    start_bucket = _align_time(cutoff_time, group_by)
    end_bucket = _align_time(now, group_by)

    buckets = {}
    current = start_bucket

    while current <= end_bucket:
        label = _format_bucket_label(current, group_by)
        buckets[label] = {
            "time": label,
            "understand": 0,
            "slow_down": 0,
            "help": 0
        }
        current += bucket_delta

    for row in rows:
        action = row["action"]

        if action not in ["understand", "slow_down", "help"]:
            continue

        timestamp = datetime.fromisoformat(row["timestamp"])
        bucket_time = _align_time(timestamp, group_by)
        label = _format_bucket_label(bucket_time, group_by)

        if label in buckets:
            buckets[label][action] += 1

    return list(buckets.values())


def get_graph_data(window_value=30, window_unit="minutes", group_by="5min"):
    conn = get_connection()
    cursor = conn.cursor()

    cutoff_time = _get_cutoff_time(window_value, window_unit)
    now = datetime.now()

    cursor.execute("""
        SELECT action, timestamp
        FROM events
        WHERE timestamp >= ?
        ORDER BY timestamp ASC
    """, (cutoff_time.isoformat(),))

    rows = cursor.fetchall()
    conn.close()

    return _build_graph_buckets(rows, cutoff_time, now, group_by)


def get_students():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT DISTINCT student_id
        FROM events
        ORDER BY student_id ASC
    """)

    rows = cursor.fetchall()
    conn.close()

    return [row["student_id"] for row in rows]


def get_student_recent_events(student_id, limit=20):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            e.id,
            e.student_id,
            e.action,
            e.timestamp,
            e.lesson_id,
            l.title AS lesson_title
        FROM events e
        LEFT JOIN lessons l ON e.lesson_id = l.id
        WHERE e.student_id = ?
        ORDER BY e.id DESC
        LIMIT ?
    """, (student_id, limit))

    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]


def get_student_summary(student_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT action, COUNT(*) as count
        FROM events
        WHERE student_id = ?
        GROUP BY action
    """, (student_id,))

    rows = cursor.fetchall()
    conn.close()

    summary = empty_summary()

    for row in rows:
        add_to_summary(summary, row["action"], row["count"])

    return summary


def get_student_graph_data(
    student_id,
    window_value=30,
    window_unit="minutes",
    group_by="5min"
):
    conn = get_connection()
    cursor = conn.cursor()

    cutoff_time = _get_cutoff_time(window_value, window_unit)
    now = datetime.now()

    cursor.execute("""
        SELECT action, timestamp
        FROM events
        WHERE student_id = ?
        AND timestamp >= ?
        ORDER BY timestamp ASC
    """, (student_id, cutoff_time.isoformat()))

    rows = cursor.fetchall()
    conn.close()

    return _build_graph_buckets(rows, cutoff_time, now, group_by)


def get_lesson_events(lesson_id, limit=500):
    if lesson_id is None:
        return []

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            e.id,
            e.student_id,
            e.action,
            e.timestamp,
            e.lesson_id,
            l.title AS lesson_title
        FROM events e
        LEFT JOIN lessons l ON e.lesson_id = l.id
        WHERE e.lesson_id = ?
        ORDER BY e.timestamp ASC
        LIMIT ?
    """, (lesson_id, limit))

    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]


def get_lesson_summary(lesson_id):
    if lesson_id is None:
        return empty_summary()

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT action, COUNT(*) as count
        FROM events
        WHERE lesson_id = ?
        GROUP BY action
    """, (lesson_id,))

    rows = cursor.fetchall()
    conn.close()

    summary = empty_summary()

    for row in rows:
        add_to_summary(summary, row["action"], row["count"])

    return summary


def _get_lesson_time_bounds(lesson):
    now = datetime.now()

    if lesson is None:
        return now - timedelta(minutes=30), now

    try:
        start_time = datetime.fromisoformat(lesson["start_time"])
    except Exception:
        start_time = now - timedelta(minutes=30)

    if lesson.get("end_time"):
        try:
            end_time = datetime.fromisoformat(lesson["end_time"])
        except Exception:
            end_time = now
    else:
        end_time = now

    if end_time <= start_time:
        end_time = start_time + timedelta(minutes=5)

    return start_time, end_time


def get_lesson_graph_data(lesson_id, group_by="5min"):
    lesson = get_lesson_by_id(lesson_id)

    if lesson is None:
        return []

    start_time, end_time = _get_lesson_time_bounds(lesson)

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT action, timestamp
        FROM events
        WHERE lesson_id = ?
        AND timestamp >= ?
        AND timestamp <= ?
        ORDER BY timestamp ASC
    """, (lesson_id, start_time.isoformat(), end_time.isoformat()))

    rows = cursor.fetchall()
    conn.close()

    return _build_graph_buckets(rows, start_time, end_time, group_by)


def _interpret_summary(summary):
    percentages = calculate_percentages(summary)

    understand = percentages["understand"]
    slow_down = percentages["slow_down"]
    help_count = percentages["help"]
    total = summary["total"]

    if total == 0:
        return "No feedback was recorded in this part of the lesson."

    if understand >= 70:
        return "Students were mostly confident during this part of the lesson."

    if help_count >= 50:
        return "Many students appeared to need help during this part of the lesson."

    if slow_down >= 50:
        return "Many students appeared to need a slower teaching pace during this part of the lesson."

    if help_count >= 30 and slow_down >= 30:
        return "Feedback was mixed, with signs of both difficulty and pacing issues."

    if help_count >= 30:
        return "Some students appeared to need help during this part of the lesson."

    if slow_down >= 30:
        return "Some students appeared to need the lesson pace slowed down."

    if understand >= 50:
        return "Feedback was generally positive, but not fully confident."

    return "Feedback was mixed during this part of the lesson."


def _phase_name(timestamp, start_time, end_time):
    duration_seconds = (end_time - start_time).total_seconds()

    if duration_seconds <= 0:
        return "beginning"

    elapsed_seconds = (timestamp - start_time).total_seconds()

    if elapsed_seconds < duration_seconds / 3:
        return "beginning"

    if elapsed_seconds < (duration_seconds * 2) / 3:
        return "middle"

    return "end"


def _build_phase_analysis(events, start_time, end_time):
    phases = {
        "beginning": empty_summary(),
        "middle": empty_summary(),
        "end": empty_summary()
    }

    for event in events:
        try:
            timestamp = datetime.fromisoformat(event["timestamp"])
        except Exception:
            continue

        phase = _phase_name(timestamp, start_time, end_time)
        add_to_summary(phases[phase], event["action"], 1)

    return [
        {
            "phase": "beginning",
            "label": "Beginning",
            "summary": phases["beginning"],
            "percentages": calculate_percentages(phases["beginning"]),
            "interpretation": _interpret_summary(phases["beginning"])
        },
        {
            "phase": "middle",
            "label": "Middle",
            "summary": phases["middle"],
            "percentages": calculate_percentages(phases["middle"]),
            "interpretation": _interpret_summary(phases["middle"])
        },
        {
            "phase": "end",
            "label": "End",
            "summary": phases["end"],
            "percentages": calculate_percentages(phases["end"]),
            "interpretation": _interpret_summary(phases["end"])
        }
    ]


def _build_lesson_insights(summary, percentages, phases):
    insights = []

    total = summary["total"]

    if total == 0:
        return [
            "No feedback was recorded for this lesson, so no lesson pattern can be inferred."
        ]

    understand = percentages["understand"]
    slow_down = percentages["slow_down"]
    help_count = percentages["help"]

    if understand >= 70:
        insights.append("Overall, the class showed strong understanding during this lesson.")
    elif understand >= 50:
        insights.append("Overall, more students understood than struggled, but there were still support signals.")
    else:
        insights.append("Overall, the lesson feedback suggests that understanding was not fully secure.")

    if help_count >= 30:
        insights.append("A noticeable portion of feedback indicated that students needed help.")

    if slow_down >= 30:
        insights.append("A noticeable portion of feedback indicated that the pace may have been too fast.")

    beginning = phases[0]["percentages"]
    ending = phases[2]["percentages"]

    beginning_support = beginning["help"] + beginning["slow_down"]
    ending_support = ending["help"] + ending["slow_down"]

    if ending_support >= beginning_support + 15:
        insights.append("Support signals increased toward the end of the lesson.")
    elif beginning_support >= ending_support + 15:
        insights.append("Support signals decreased toward the end of the lesson.")
    else:
        insights.append("The level of support signals stayed relatively consistent across the lesson.")

    return insights


def _build_lesson_recommendation(percentages):
    understand = percentages["understand"]
    slow_down = percentages["slow_down"]
    help_count = percentages["help"]

    if help_count >= 50:
        return "Recommended action: revisit the lesson content and provide targeted support or worked examples."

    if slow_down >= 50:
        return "Recommended action: reduce the pace and check understanding before moving to new material."

    if help_count >= 30:
        return "Recommended action: identify which students struggled and offer follow-up support."

    if slow_down >= 30:
        return "Recommended action: consider slowing transitions and adding more explanation time."

    if understand >= 70:
        return "Recommended action: continue with the planned learning sequence while monitoring for individual support needs."

    return "Recommended action: review the mixed feedback and consider a short recap before continuing."


def get_lesson_report(lesson_id, group_by="5min"):
    lesson = get_lesson_by_id(lesson_id)

    if lesson is None:
        return {
            "lesson": None,
            "summary": empty_summary(),
            "percentages": calculate_percentages(empty_summary()),
            "phases": [],
            "graph": [],
            "report": {
                "title": "Lesson not found",
                "overview": "No lesson exists with this ID.",
                "insights": [],
                "recommendation": "Select a valid lesson."
            }
        }

    events = get_lesson_events(lesson_id, limit=10000)
    summary = get_lesson_summary(lesson_id)
    percentages = calculate_percentages(summary)
    start_time, end_time = _get_lesson_time_bounds(lesson)
    phases = _build_phase_analysis(events, start_time, end_time)
    graph = get_lesson_graph_data(lesson_id, group_by)

    total = summary["total"]

    if total == 0:
        overview = f"No feedback was recorded during {lesson['title']}."
    else:
        overview = (
            f"During {lesson['title']}, {total} feedback events were recorded. "
            f"{percentages['understand']}% indicated understanding, "
            f"{percentages['slow_down']}% asked for a slower pace, and "
            f"{percentages['help']}% requested help."
        )

    return {
        "lesson": lesson,
        "summary": summary,
        "percentages": percentages,
        "phases": phases,
        "graph": graph,
        "events": events,
        "duration": {
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "duration_minutes": round((end_time - start_time).total_seconds() / 60, 1)
        },
        "report": {
            "title": f"Lesson report: {lesson['title']}",
            "overview": overview,
            "insights": _build_lesson_insights(summary, percentages, phases),
            "recommendation": _build_lesson_recommendation(percentages)
        }
    }