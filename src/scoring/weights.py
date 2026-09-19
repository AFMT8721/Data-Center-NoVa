"""Single source of truth for heuristic weights."""

WEIGHTS = {
    "bill": {
        "utility_territory_match": 0.35,
        "rate_vintage_match": 0.25,
        "scale_mw_proximity": 0.25,
        "timing_proximity": 0.15,
    },
    "air": {
        "distance_to_residence": 0.35,
        "generator_capacity": 0.30,
        "permit_status": 0.20,
        "cluster_density": 0.15,
    },
}


def validate_weights(weights: dict[str, dict[str, float]] = WEIGHTS) -> None:
    for domain, domain_weights in weights.items():
        if any(weight < 0 for weight in domain_weights.values()):
            raise ValueError(f"{domain}: weights must be nonnegative")
        if abs(sum(domain_weights.values()) - 1.0) > 1e-9:
            raise ValueError(f"{domain}: weights must sum to 1.0")


validate_weights()
