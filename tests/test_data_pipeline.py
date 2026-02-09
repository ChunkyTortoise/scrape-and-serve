"""Tests for data pipeline."""

from __future__ import annotations

import pandas as pd

from scrape_and_serve.data_pipeline import DataPipeline, PipelineResult, PipelineStage


class TestDataPipeline:
    def test_single_stage(self) -> None:
        pipe = DataPipeline()
        pipe.add_stage("double", lambda df: df * 2)
        df = pd.DataFrame({"a": [1, 2, 3]})
        result = pipe.run(df)
        assert isinstance(result, PipelineResult)
        assert result.stages_completed == 1
        assert list(result.output["a"]) == [2, 4, 6]

    def test_multi_stage(self) -> None:
        pipe = DataPipeline()
        pipe.add_stage("add_col", lambda df: df.assign(b=df["a"] + 1))
        pipe.add_stage("filter", lambda df: df[df["a"] > 1])
        df = pd.DataFrame({"a": [1, 2, 3]})
        result = pipe.run(df)
        assert result.stages_completed == 2
        assert len(result.output) == 2
        assert "b" in result.output.columns

    def test_validation_stops_pipeline(self) -> None:
        pipe = DataPipeline()
        pipe.add_stage(
            "filter",
            lambda df: df[df["a"] > 10],
            validate_fn=lambda df: len(df) > 0,
        )
        pipe.add_stage("should_not_run", lambda df: df.assign(x=99))
        df = pd.DataFrame({"a": [1, 2, 3]})
        result = pipe.run(df)
        assert result.validation_passed is False
        assert result.stages_completed == 1
        assert "x" not in result.output.columns

    def test_timing_recorded(self) -> None:
        pipe = DataPipeline()
        pipe.add_stage("passthrough", lambda df: df)
        df = pd.DataFrame({"a": [1]})
        result = pipe.run(df)
        assert "passthrough" in result.stage_timings
        assert result.stage_timings["passthrough"] >= 0

    def test_row_count_tracking(self) -> None:
        pipe = DataPipeline()
        pipe.add_stage("filter", lambda df: df[df["a"] > 1])
        df = pd.DataFrame({"a": [1, 2, 3]})
        result = pipe.run(df)
        assert result.rows_in == 3
        assert result.rows_out == 2

    def test_empty_dataframe(self) -> None:
        pipe = DataPipeline()
        pipe.add_stage("noop", lambda df: df)
        df = pd.DataFrame()
        result = pipe.run(df)
        assert result.stages_completed == 1
        assert result.rows_in == 0
        assert result.rows_out == 0

    def test_no_stages(self) -> None:
        pipe = DataPipeline()
        df = pd.DataFrame({"a": [1, 2]})
        result = pipe.run(df)
        assert result.stages_completed == 0
        assert result.rows_in == 2
        assert result.rows_out == 2
        assert result.validation_passed is True

    def test_remove_stage(self) -> None:
        pipe = DataPipeline()
        pipe.add_stage("first", lambda df: df)
        pipe.add_stage("second", lambda df: df)
        assert pipe.remove_stage("first") is True
        assert pipe.get_stage_names() == ["second"]

    def test_remove_nonexistent(self) -> None:
        pipe = DataPipeline()
        assert pipe.remove_stage("missing") is False

    def test_dry_run(self) -> None:
        pipe = DataPipeline()
        pipe.add_stage("step1", lambda df: df)
        pipe.add_stage("step2", lambda df: df)
        df = pd.DataFrame({"a": [1]})
        names = pipe.dry_run(df)
        assert names == ["step1", "step2"]

    def test_get_stage_names(self) -> None:
        pipe = DataPipeline()
        pipe.add_stage("a", lambda df: df)
        pipe.add_stage("b", lambda df: df)
        pipe.add_stage("c", lambda df: df)
        assert pipe.get_stage_names() == ["a", "b", "c"]

    def test_transform_error_caught(self) -> None:
        def bad_transform(df: pd.DataFrame) -> pd.DataFrame:
            msg = "Transform broke"
            raise ValueError(msg)

        pipe = DataPipeline()
        pipe.add_stage("bad", bad_transform)
        df = pd.DataFrame({"a": [1]})
        result = pipe.run(df)
        assert result.validation_passed is False
        assert result.stages_completed == 0

    def test_validation_passes(self) -> None:
        pipe = DataPipeline()
        pipe.add_stage(
            "ok",
            lambda df: df,
            validate_fn=lambda df: len(df) > 0,
        )
        df = pd.DataFrame({"a": [1, 2]})
        result = pipe.run(df)
        assert result.validation_passed is True
        assert result.stages_completed == 1

    def test_original_df_not_mutated(self) -> None:
        pipe = DataPipeline()
        pipe.add_stage("modify", lambda df: df.assign(b=1))
        df = pd.DataFrame({"a": [1, 2]})
        pipe.run(df)
        assert "b" not in df.columns

    def test_pipeline_stage_dataclass(self) -> None:
        fn = lambda df: df  # noqa: E731
        stage = PipelineStage(name="test", transform_fn=fn)
        assert stage.name == "test"
        assert stage.validate_fn is None

    def test_multiple_timings(self) -> None:
        pipe = DataPipeline()
        pipe.add_stage("s1", lambda df: df)
        pipe.add_stage("s2", lambda df: df)
        pipe.add_stage("s3", lambda df: df)
        df = pd.DataFrame({"a": [1]})
        result = pipe.run(df)
        assert len(result.stage_timings) == 3
        assert all(v >= 0 for v in result.stage_timings.values())

    def test_large_dataframe(self) -> None:
        pipe = DataPipeline()
        pipe.add_stage("sum_col", lambda df: df.assign(total=df.sum(axis=1)))
        df = pd.DataFrame({"a": range(1000), "b": range(1000)})
        result = pipe.run(df)
        assert result.rows_in == 1000
        assert result.rows_out == 1000
        assert result.stages_completed == 1

    def test_chained_filters(self) -> None:
        pipe = DataPipeline()
        pipe.add_stage("gt5", lambda df: df[df["a"] > 5])
        pipe.add_stage("lt8", lambda df: df[df["a"] < 8])
        df = pd.DataFrame({"a": range(10)})
        result = pipe.run(df)
        assert result.rows_in == 10
        assert result.rows_out == 2  # 6, 7
        assert list(result.output["a"]) == [6, 7]

    def test_dry_run_empty_pipeline(self) -> None:
        pipe = DataPipeline()
        assert pipe.dry_run(pd.DataFrame()) == []

    def test_error_in_second_stage(self) -> None:
        pipe = DataPipeline()
        pipe.add_stage("ok", lambda df: df.assign(x=1))

        def fail(df: pd.DataFrame) -> pd.DataFrame:
            msg = "oops"
            raise RuntimeError(msg)

        pipe.add_stage("fail", fail)
        df = pd.DataFrame({"a": [1]})
        result = pipe.run(df)
        assert result.stages_completed == 1
        assert result.validation_passed is False
        assert "x" in result.output.columns
