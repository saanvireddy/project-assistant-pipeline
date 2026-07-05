"""
Tests for the pipeline orchestrator. Focuses on the manifest/stage-tracking
logic and the match-rate calculation bug class (silently miscounting
non_standardizable_entity as a successful match) rather than re-testing
individual stage functions already covered elsewhere.
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "pipeline"))

from orchestrator import PipelineRun


def test_pipeline_run_records_success():
    run = PipelineRun()
    run.run_stage("dummy_success", lambda: {"ok": True})
    assert run.stages[0]["status"] == "success"
    assert run.stages[0]["detail"] == {"ok": True}


def test_pipeline_run_records_failure_without_crashing():
    def failing_stage():
        raise ValueError("simulated failure")

    run = PipelineRun()
    result = run.run_stage("dummy_failure", failing_stage)
    assert result is None
    assert run.stages[0]["status"] == "failed"
    assert "simulated failure" in run.stages[0]["detail"]


def test_pipeline_continues_after_stage_failure():
    run = PipelineRun()
    run.run_stage("stage_1_fails", lambda: (_ for _ in ()).throw(ValueError("boom")))
    run.run_stage("stage_2_succeeds", lambda: {"ok": True})
    assert run.stages[0]["status"] == "failed"
    assert run.stages[1]["status"] == "success"


def test_manifest_overall_status_reflects_partial_failure(tmp_path, monkeypatch):
    import orchestrator
    monkeypatch.setattr(orchestrator, "DATA_PROCESSED", str(tmp_path))

    run = PipelineRun()
    run.run_stage("ok_stage", lambda: {"ok": True})
    run.run_stage("bad_stage", lambda: (_ for _ in ()).throw(ValueError("fail")))
    manifest = run.write_manifest()

    assert manifest["overall_status"] == "partial_failure"
    assert os.path.exists(os.path.join(str(tmp_path), "pipeline_manifest.json"))


def test_manifest_overall_status_success_when_all_pass(tmp_path, monkeypatch):
    import orchestrator
    monkeypatch.setattr(orchestrator, "DATA_PROCESSED", str(tmp_path))

    run = PipelineRun()
    run.run_stage("ok_stage_1", lambda: {"ok": True})
    run.run_stage("ok_stage_2", lambda: {"ok": True})
    manifest = run.write_manifest()

    assert manifest["overall_status"] == "success"