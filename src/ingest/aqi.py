"""Read locality-level ambient AQI as non-attributable context."""

from pathlib import Path

import pandas as pd

NOVA_LOCALITIES = {
    "Alexandria City",
    "Arlington",
    "Fairfax",
    "Fauquier",
    "Loudoun",
    "Prince William",
    "Stafford",
}


def load_aqi_context(path: Path) -> pd.DataFrame:
    frame = pd.read_csv(path)
    frame["date"] = pd.to_datetime(frame["date"], errors="coerce")
    frame["aqi"] = pd.to_numeric(frame["aqi"], errors="coerce")
    frame = frame.loc[
        frame["county_or_city_name"].isin(NOVA_LOCALITIES)
        & frame["date"].notna()
        & frame["aqi"].notna()
        & frame["date"].ge("2015-01-01")
    ].copy()
    frame["year"] = frame["date"].dt.year
    grouped = (
        frame.groupby(["county_or_city_name", "year"], as_index=False)
        .agg(
            value_low=("aqi", "min"),
            value_high=("aqi", "max"),
            observation_days=("aqi", "size"),
            source_url=("source_dataset_url", "first"),
            downloaded_on=("source_downloaded_on", "first"),
        )
        .sort_values(["county_or_city_name", "year"])
    )
    return grouped
