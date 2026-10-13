from typing import Any, Dict

import numpy as np
import pandas as pd


def group_fairness_report(
    y_true: Any,
    scores: Any,
    groups: Any,
    threshold: float = 0.5,
    min_support: int = 30,
) -> Dict[str, Any]:
    frame = pd.DataFrame(
        {
            "y": np.asarray(y_true).astype(int).ravel(),
            "flag": (np.asarray(scores, dtype=float).ravel() >= threshold).astype(int),
            "group": np.asarray(groups).ravel(),
        }
    )
    report: Dict[str, Any] = {"groups": {}, "excluded_groups": []}
    rates = {}
    for name, part in frame.groupby("group"):
        if len(part) < min_support:
            report["excluded_groups"].append(str(name))
            continue
        negatives = part[part["y"] == 0]
        positives = part[part["y"] == 1]
        entry = {
            "samples": int(len(part)),
            "flag_rate": float(part["flag"].mean()),
            "false_positive_rate": (
                float(negatives["flag"].mean()) if len(negatives) else None
            ),
            "true_positive_rate": (
                float(positives["flag"].mean()) if len(positives) else None
            ),
        }
        report["groups"][str(name)] = entry
        rates[str(name)] = entry
    if len(rates) >= 2:
        flag_rates = [entry["flag_rate"] for entry in rates.values()]
        fprs = [
            e["false_positive_rate"]
            for e in rates.values()
            if e["false_positive_rate"] is not None
        ]
        tprs = [
            e["true_positive_rate"]
            for e in rates.values()
            if e["true_positive_rate"] is not None
        ]
        highest = max(flag_rates)
        report["disparity"] = {
            "demographic_parity_difference": float(highest - min(flag_rates)),
            "disparate_impact_ratio": (
                float(min(flag_rates) / highest) if highest else 1.0
            ),
            "false_positive_rate_gap": float(max(fprs) - min(fprs)) if fprs else None,
            "equal_opportunity_gap": float(max(tprs) - min(tprs)) if tprs else None,
        }
    return report
