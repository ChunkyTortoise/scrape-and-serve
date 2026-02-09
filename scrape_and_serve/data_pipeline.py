"""Data pipeline for composable DataFrame transformations."""

from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass, field

import pandas as pd


@dataclass
class PipelineStage:
    """A single stage in a data pipeline."""

    name: str
    transform_fn: Callable[[pd.DataFrame], pd.DataFrame]
    validate_fn: Callable[[pd.DataFrame], bool] | None = None


@dataclass
class PipelineResult:
    """Result of running a data pipeline."""

    output: pd.DataFrame
    stages_completed: int
    stage_timings: dict[str, float] = field(default_factory=dict)
    rows_in: int = 0
    rows_out: int = 0
    validation_passed: bool = True


class DataPipeline:
    """Composable data pipeline with validation and timing."""

    def __init__(self) -> None:
        self._stages: list[PipelineStage] = []

    def add_stage(
        self,
        name: str,
        transform_fn: Callable[[pd.DataFrame], pd.DataFrame],
        validate_fn: Callable[[pd.DataFrame], bool] | None = None,
    ) -> None:
        """Add a stage to the pipeline."""
        self._stages.append(PipelineStage(name=name, transform_fn=transform_fn, validate_fn=validate_fn))

    def run(self, df: pd.DataFrame) -> PipelineResult:
        """Execute all pipeline stages in order."""
        rows_in = len(df)
        current = df.copy()
        timings: dict[str, float] = {}
        stages_completed = 0

        for stage in self._stages:
            start = time.monotonic()
            try:
                current = stage.transform_fn(current)
            except Exception:
                return PipelineResult(
                    output=current,
                    stages_completed=stages_completed,
                    stage_timings=timings,
                    rows_in=rows_in,
                    rows_out=len(current),
                    validation_passed=False,
                )
            elapsed = (time.monotonic() - start) * 1000
            timings[stage.name] = round(elapsed, 2)
            stages_completed += 1

            if stage.validate_fn is not None and not stage.validate_fn(current):
                return PipelineResult(
                    output=current,
                    stages_completed=stages_completed,
                    stage_timings=timings,
                    rows_in=rows_in,
                    rows_out=len(current),
                    validation_passed=False,
                )

        return PipelineResult(
            output=current,
            stages_completed=stages_completed,
            stage_timings=timings,
            rows_in=rows_in,
            rows_out=len(current),
            validation_passed=True,
        )

    def dry_run(self, df: pd.DataFrame) -> list[str]:
        """Preview stage names without executing transforms."""
        return [s.name for s in self._stages]

    def get_stage_names(self) -> list[str]:
        """Return names of all stages."""
        return [s.name for s in self._stages]

    def remove_stage(self, name: str) -> bool:
        """Remove a stage by name. Returns True if found and removed."""
        for i, stage in enumerate(self._stages):
            if stage.name == name:
                self._stages.pop(i)
                return True
        return False
