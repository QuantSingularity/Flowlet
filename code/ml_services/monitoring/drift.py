from dataclasses import dataclass, field
from typing import Any, Dict, List

import numpy as np
import pandas as pd
from scipy import stats


def population_stability_index(expected: Any, actual: Any, bins: int = 10) -> float:
    reference = np.asarray(expected, dtype=float)
    current = np.asarray(actual, dtype=float)
    if len(reference) == 0 or len(current) == 0:
        return 0.0
    edges = np.unique(np.quantile(reference, np.linspace(0, 1, bins + 1)))
    if len(edges) < 3:
        return 0.0
    edges[0], edges[-1] = -np.inf, np.inf
    expected_share = np.histogram(reference, bins=edges)[0] / len(reference)
    actual_share = np.histogram(current, bins=edges)[0] / len(current)
    expected_share = np.clip(expected_share, 1e-4, None)
    actual_share = np.clip(actual_share, 1e-4, None)
    return float(
        np.sum((actual_share - expected_share) * np.log(actual_share / expected_share))
    )


@dataclass
class DriftReport:
    drifted: bool
    max_psi: float
    threshold: float
    features: Dict[str, Dict[str, float]] = field(default_factory=dict)
    drifted_features: List[str] = field(default_factory=list)
    samples: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "drifted": self.drifted,
            "max_psi": round(self.max_psi, 4),
            "threshold": self.threshold,
            "drifted_features": self.drifted_features,
            "features": self.features,
            "samples": self.samples,
        }


def compute_drift(
    reference: pd.DataFrame,
    current: pd.DataFrame,
    threshold: float = 0.25,
    min_samples: int = 100,
) -> DriftReport:
    if len(current) < min_samples or reference.empty:
        return DriftReport(False, 0.0, threshold, samples=len(current))
    results: Dict[str, Dict[str, float]] = {}
    drifted: List[str] = []
    for column in reference.columns:
        if column not in current.columns:
            continue
        ref = reference[column].to_numpy(dtype=float)
        cur = current[column].to_numpy(dtype=float)
        if np.allclose(ref, ref[0]) and np.allclose(cur, ref[0]):
            continue
        psi = population_stability_index(ref, cur)
        ks = stats.ks_2samp(ref, cur)
        results[column] = {"psi": round(psi, 4), "ks": round(float(ks.statistic), 4)}
        if psi >= threshold:
            drifted.append(column)
    max_psi = max((entry["psi"] for entry in results.values()), default=0.0)
    return DriftReport(
        bool(drifted), max_psi, threshold, results, drifted, len(current)
    )
