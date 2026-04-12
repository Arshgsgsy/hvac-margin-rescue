import os
import threading
import time

from config import get_available_files
from pipeline_jobs import enqueue_pipeline_job, get_active_pipeline_job, scheduler_guard


_scheduler_started = False


def _interval_seconds() -> int:
    raw = os.getenv("PIPELINE_SCHEDULE_MINUTES", "").strip()
    if not raw:
        return 0
    try:
        minutes = int(raw)
    except ValueError:
        return 0
    return max(0, minutes) * 60


def _scheduler_loop(interval_seconds: int):
    next_run = time.time() + interval_seconds

    while True:
        now = time.time()
        sleep_for = max(1, min(30, int(next_run - now)))
        time.sleep(sleep_for)

        if time.time() < next_run:
            continue

        next_run = time.time() + interval_seconds

        if get_active_pipeline_job():
            continue

        file_status = get_available_files()
        if not file_status["can_run_pipeline"]:
            continue

        try:
            enqueue_pipeline_job(
                available_files=file_status["available"],
                trigger="scheduler",
            )
        except RuntimeError:
            continue


def start_pipeline_scheduler():
    global _scheduler_started

    interval_seconds = _interval_seconds()
    if interval_seconds <= 0 or _scheduler_started:
        return

    with scheduler_guard():
        if _scheduler_started:
            return

        thread = threading.Thread(
            target=_scheduler_loop,
            args=(interval_seconds,),
            daemon=True,
            name="pipeline-scheduler",
        )
        thread.start()
        _scheduler_started = True
