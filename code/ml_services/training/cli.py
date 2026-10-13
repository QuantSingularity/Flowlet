import argparse
import json
import sys
from typing import List, Optional

import pandas as pd

from ..config import get_settings
from ..core.registry import ModelRegistry
from ..data.synthetic import generate_labeled_features
from .pipeline import build_training_frame, train_ensemble

MODEL_NAME = "fraud_ensemble"


def _registry() -> ModelRegistry:
    settings = get_settings()
    return ModelRegistry(
        settings.model_dir,
        settings.signing_key,
        settings.keep_versions,
        require_key=settings.is_production,
    )


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m ml_services.training.cli")
    sub = parser.add_subparsers(dest="command", required=True)
    synth = sub.add_parser("train-synthetic")
    synth.add_argument("--samples", type=int, default=get_settings().bootstrap_samples)
    synth.add_argument(
        "--fraud-rate", type=float, default=get_settings().bootstrap_fraud_rate
    )
    synth.add_argument("--seed", type=int, default=get_settings().random_state)
    tx = sub.add_parser("train-transactions")
    tx.add_argument("path")
    tx.add_argument("--label-key", default="is_fraud")
    feat = sub.add_parser("train-features")
    feat.add_argument("path")
    feat.add_argument("--label-column", default="is_fraud")
    sub.add_parser("list")
    promote = sub.add_parser("promote")
    promote.add_argument("version")
    args = parser.parse_args(argv)
    registry = _registry()
    settings = get_settings()
    if args.command == "list":
        current = registry.current_version(MODEL_NAME)
        for version in registry.list_versions(MODEL_NAME):
            marker = "*" if version == current else " "
            print(f"{marker} {version}")
        return 0
    if args.command == "promote":
        registry.promote(MODEL_NAME, args.version)
        print(f"promoted {args.version}")
        return 0
    if args.command == "train-synthetic":
        features, labels = generate_labeled_features(
            args.samples, args.fraud_rate, args.seed
        )
        source = "synthetic"
    elif args.command == "train-transactions":
        with open(args.path, "r", encoding="utf-8") as handle:
            records = json.load(handle)
        features, labels = build_training_frame(records, args.label_key, settings)
        source = "transactions"
    else:
        table = pd.read_csv(args.path)
        labels = table.pop(args.label_column)
        features = table
        source = "features"
    result = train_ensemble(features, labels, settings=settings, training_source=source)
    version = registry.save(
        MODEL_NAME,
        result.model,
        {
            "training_source": source,
            "training_samples": result.training_samples,
            "metrics": result.metrics,
            "feature_columns": result.model.feature_columns,
        },
    )
    print(
        json.dumps(
            {"version": version, "metrics": result.metrics}, indent=2, default=str
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
