"""Read Virginia EIA-861 utility context records."""

from pathlib import Path

import pandas as pd

UTILITY_NAMES = {
    "Virginia Electric & Power Co": "Dominion",
    "Northern Virginia Elec Coop": "NOVEC",
}


def load_eia861_context(path: Path) -> pd.DataFrame:
    usecols = [
        "year",
        "data_status",
        "utility_name",
        "state",
        "sector",
        "service_type",
        "average_price_cents_per_kwh",
        "source_file",
    ]
    frame = pd.read_csv(path, usecols=usecols)
    frame = frame.loc[
        frame["state"].eq("VA")
        & frame["sector"].eq("residential")
        & frame["service_type"].eq("Bundled")
        & frame["utility_name"].isin(UTILITY_NAMES)
    ].copy()
    frame["utility_territory"] = frame["utility_name"].map(UTILITY_NAMES)
    frame["average_price_cents_per_kwh"] = pd.to_numeric(
        frame["average_price_cents_per_kwh"], errors="coerce"
    )
    return frame.sort_values(["utility_territory", "year"]).reset_index(drop=True)
