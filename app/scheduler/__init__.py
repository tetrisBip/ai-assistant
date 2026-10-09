# app/scheduler/__init__.py
from app.scheduler.jobs import register_jobs

__all__ = ["register_jobs"]