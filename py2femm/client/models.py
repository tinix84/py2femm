"""Shared data models for py2femm client-agent communication."""

from __future__ import annotations

from datetime import datetime
from io import StringIO
from typing import Literal

import pandas as pd
from pydantic import BaseModel, Field


class JobRequest(BaseModel):
    """Request to run a FEMM Lua script."""

    lua_script: str
    timeout_s: int = 300
    metadata: dict[str, str] = Field(default_factory=dict)


class JobResult(BaseModel):
    """Result of a completed FEMM simulation."""

    csv_data: str = ""

    def to_dataframe(self) -> pd.DataFrame:
        """Parse CSV data into a pandas DataFrame."""
        if not self.csv_data.strip():
            return pd.DataFrame()
        return pd.read_csv(StringIO(self.csv_data))


class JobStatus(BaseModel):
    """Status of a FEMM simulation job."""

    job_id: str
    status: Literal["submitted", "queued", "running", "completed", "failed"]
    submitted_at: datetime
    completed_at: datetime | None = None
    result: JobResult | None = None
    error: str | None = None

    @property
    def elapsed_s(self) -> float | None:
        """Elapsed time in seconds, or None if not completed."""
        if self.completed_at is None or self.submitted_at is None:
            return None
        return (self.completed_at - self.submitted_at).total_seconds()
