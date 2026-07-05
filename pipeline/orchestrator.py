"""
End-to-end pipeline orchestrator: ties together ingestion, standardization,
schema validation, quality checks, and (optionally) Census enrichment and
RAG indexing into one automated run.

Produces a run manifest (data/processed/pipeline_manifest.json) recording
what ran, how long each stage took, and pass/fail status per stage - this
is the "metadata generation" and "reproducibility" piece of the pipeline.

Design: each stage is wrapped so a failure in one (e.g. Census API being
unreachable) doesn't silently corrupt downstream stages or the manifest -
it's recorded as a failed stage and the pipeline continues where it safely
can, rather than either crashing everything or pretending nothing went wrong.
"""

import sys
import os
import json
import time
import logging
from datetime import datetime, timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "etl"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "modules"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "census"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "rag"))

import pandas as pd

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("pipeline")

DATA_RAW = os.path.join(os.path.dirname(__file__), "..", "data", "raw")
DATA_PROCESSED = os.path.join(os.path.dirname(__file__), "..", "data", "processed")


class PipelineRun:
    """Tracks stage results and timing for the manifest output."""

    def __init__(self):
        self.stages = []
        self.started_at = datetime.now(timezone.utc).isoformat()

    def run_stage(self, name: str, func, *args, **kwargs):
        logger.info(f"Starting stage: {name}")
        start = time.time()
        result = {"stage": name, "status": "failed", "duration_seconds": None, "detail": None}
        try:
            output = func(*args, **kwargs)
            result["status"] = "success"
            result["detail"] = output if isinstance(output, (dict, str, int, float)) else str(output)
            logger.info(f"Completed stage: {name} ({time.time() - start:.2f}s)")
            self.stages.append({**result, "duration_seconds": round(time.time() - start, 2)})
            return output
        except Exception as e:
            result["detail"] = str(e)
            result["duration_seconds"] = round(time.time() - start, 2)
            logger.error(f"Stage failed: {name} - {e}")
            self.stages.append(result)
            return None

    def write_manifest(self):
        manifest = {
            "started_at": self.started_at,
            "completed_at": datetime.now(timezone.utc).isoformat(),
            "stages": self.stages,
            "overall_status": "success" if all(s["status"] == "success" for s in self.stages) else "partial_failure",
        }
        path = os.path.join(DATA_PROCESSED, "pipeline_manifest.json")
        with open(path, "w") as f:
            json.dump(manifest, f, indent=2)
        logger.info(f"Manifest written to {path}")
        return manifest


def stage_ingest_raw_data() -> dict:
    """Ingest raw country records CSV."""
    path = os.path.join(DATA_RAW, "sample_country_records.csv")
    df = pd.read_csv(path)
    if df.empty:
        raise ValueError("Ingested dataframe is empty")
    return {"rows_ingested": len(df)}


def stage_standardize_countries() -> dict:
    """Run the ETL country standardization step."""
    from country_standardizer import standardize_dataframe

    path = os.path.join(DATA_RAW, "sample_country_records.csv")
    df = pd.read_csv(path)
    result_df = standardize_dataframe(df)
    out_path = os.path.join(DATA_PROCESSED, "standardized_countries.csv")
    result_df.to_csv(out_path, index=False)

    matched = (~result_df["match_method"].isin(["unmatched", "non_standardizable_entity"])).sum()
    return {
        "rows_processed": len(result_df),
        "match_rate_pct": round(matched / len(result_df) * 100, 1),
    }


def stage_validate_and_quality_check() -> dict:
    """Schema validation + quality checks on the standardized output."""
    from schema_validator import build_schema_report
    from quality_checks import run_quality_report

    path = os.path.join(DATA_PROCESSED, "standardized_countries.csv")
    df = pd.read_csv(path)

    schema = {
        "country_name": {"required": True},
        "canonical_name": {"required": True},
        "match_method": {
            "required": True,
            "allowed_values": ["alias_override", "historical_successor_override",
                               "exact_match", "fuzzy_match", "unmatched", "non_standardizable_entity"],
        },
    }
    schema_report = build_schema_report(df, schema)
    quality_report = run_quality_report(
        df,
        missing_check_columns=["country_name"],
        duplicate_subset=["record_id"],
    )

    if not schema_report["passed"]:
        raise ValueError(f"Schema validation failed: {schema_report}")

    return {"schema_passed": schema_report["passed"], "quality_passed": quality_report["passed"]}


def stage_build_rag_index() -> dict:
    """Index the standardized dataset into the vector store for semantic search."""
    from pipeline import build_vector_store_from_csv

    path = os.path.join(DATA_PROCESSED, "standardized_countries.csv")
    store = build_vector_store_from_csv(path, collection_name="pipeline_run_records")
    return {"records_indexed": store.count()}


def run_full_pipeline(include_rag: bool = True) -> dict:
    run = PipelineRun()

    run.run_stage("ingest_raw_data", stage_ingest_raw_data)
    run.run_stage("standardize_countries", stage_standardize_countries)
    run.run_stage("validate_and_quality_check", stage_validate_and_quality_check)

    if include_rag:
        run.run_stage("build_rag_index", stage_build_rag_index)

    manifest = run.write_manifest()
    logger.info(f"Pipeline finished with status: {manifest['overall_status']}")
    return manifest


if __name__ == "__main__":
    run_full_pipeline(include_rag=True)