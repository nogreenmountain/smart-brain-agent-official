"""Deterministic state machine for asynchronous v3 shadow indexing."""
from __future__ import annotations

from dataclasses import dataclass, replace


@dataclass(frozen=True)
class JobState:
    status: str
    processed_items: int
    total_items: int | None
    retry_count: int
    max_retries: int
    error: str | None = None

    @property
    def progress_percent(self) -> int:
        if not self.total_items:
            return 0
        return min(100, max(0, int(self.processed_items * 100 / self.total_items)))


def transition_job(state: JobState, event: str, *, processed_items: int | None = None, error: str | None = None) -> JobState:
    allowed = {
        "queued": {"start", "cancel"},
        "running": {"progress", "pause", "fail", "cancel", "complete"},
        "paused": {"resume", "cancel"},
        "cancelling": {"cancel"},
        "failed": {"retry", "cancel"},
        "completed": set(),
        "cancelled": set(),
    }
    if event not in allowed.get(state.status, set()):
        if event == "resume" and state.status == "failed" and state.retry_count < state.max_retries:
            return replace(state, status="running", error=None)
        raise ValueError(f"invalid job transition: {state.status} + {event}")
    if event == "start" or event == "resume":
        return replace(state, status="running", error=None)
    if event == "progress":
        next_count = state.processed_items if processed_items is None else processed_items
        if next_count < state.processed_items or (state.total_items is not None and next_count > state.total_items):
            raise ValueError("processed_items must be monotonic and within total_items")
        return replace(state, processed_items=next_count)
    if event == "pause":
        return replace(state, status="paused")
    if event == "fail":
        if state.retry_count < state.max_retries:
            return replace(state, status="queued", retry_count=state.retry_count + 1, error=error)
        return replace(state, status="failed", error=error)
    if event == "retry":
        if state.retry_count >= state.max_retries:
            raise ValueError("maximum retries exceeded")
        return replace(state, status="queued", retry_count=state.retry_count + 1, error=None)
    if event == "cancel":
        return replace(state, status="cancelled")
    if event == "complete":
        return replace(state, status="completed", processed_items=state.total_items or state.processed_items, error=None)
    raise ValueError(f"unknown job event: {event}")
