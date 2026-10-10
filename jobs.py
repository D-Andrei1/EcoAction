"""
jobs.py - runs background jobs once a minute while the app is running.
PROVIDED COMPLETE - type it in exactly and do not change it.
"""
import threading
import time
import traceback

JOBS = []
def every_minute(job):
    """Use as a decorator: @jobs.every_minute above a function with no arguments."""
    JOBS.append(job)
    return job

def run_all_once():
    for job in JOBS:
        try:
            job()
        except Exception:
            traceback.print_exc()

def run_soon(job):
    """Run one job straight away in the background (e.g. make a report now)."""
    threading.Thread(target=job, daemon=True).start()

def start():
    def loop():
        while True:
            run_all_once()
            time.sleep(60)
    threading.Thread(target=loop, daemon=True, name="jobs").start()

    
