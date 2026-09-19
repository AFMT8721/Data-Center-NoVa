from pathlib import Path

import pandas as pd

from src.schemas.corpus import CORPUS_SCHEMA

ROOT = Path(__file__).resolve().parents[1]


def test_processed_corpus_has_required_labels() -> None:
    corpus = pd.read_parquet(ROOT / "data/processed/outcome_corpus.parquet")
    validated = CORPUS_SCHEMA.validate(corpus)
    assert len(validated) > 0
    assert validated["record_id"].is_unique
    assert validated["carry_statement"].str.len().gt(0).all()


def test_aqi_is_context_not_project_attribution() -> None:
    corpus = pd.read_parquet(ROOT / "data/processed/outcome_corpus.parquet")
    aqi = corpus.loc[corpus["source_name"].eq("U.S. EPA daily AQI by county")]
    assert not aqi.empty
    assert aqi["is_context_only"].all()
    assert aqi["spatial_grain"].eq("locality").all()
    assert aqi["carry_statement"].str.contains("cannot be attributed").all()


def test_deq_permits_are_labeled_permitted_not_measured() -> None:
    corpus = pd.read_parquet(ROOT / "data/processed/outcome_corpus.parquet")
    permits = corpus.loc[
        corpus["source_name"].eq("Virginia DEQ issued data center air permits")
    ]
    assert not permits.empty
    assert permits["outcome_type"].eq("permitted").all()
    assert permits["permit_status"].eq("permitted").all()
    assert permits["notes"].str.contains("do not establish actual emissions").all()


def test_2015_deq_emissions_are_historical_facility_totals() -> None:
    corpus = pd.read_parquet(ROOT / "data/processed/outcome_corpus.parquet")
    emissions = corpus.loc[
        corpus["source_name"].eq("Virginia DEQ 2015 criteria emissions inventory")
    ]
    assert not emissions.empty
    assert emissions["outcome_type"].eq("measured").all()
    assert emissions["target_year"].eq(2015).all()
    assert emissions["notes"].str.contains("not generator-only").all()
