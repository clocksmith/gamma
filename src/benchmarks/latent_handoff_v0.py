"""CLI for the isolated Latent Handoff v0 scientific harness."""

from __future__ import annotations

import argparse
from pathlib import Path

from src.mind_meld.latent_handoff.experiment import (
    evaluate_from_config,
    fingerprint_from_config,
    fit_from_config,
    load_config,
    phase1_from_config,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    validate = subparsers.add_parser("validate-config")
    validate.add_argument("--config", type=Path, required=True)
    fit = subparsers.add_parser("fit")
    fit.add_argument("--config", type=Path, required=True)
    fit.add_argument("--output", type=Path, required=True)
    evaluate = subparsers.add_parser("evaluate")
    evaluate.add_argument("--config", type=Path, required=True)
    evaluate.add_argument("--mapper", type=Path, required=True)
    evaluate.add_argument("--output", type=Path, required=True)
    phase1 = subparsers.add_parser("phase1")
    phase1.add_argument("--config", type=Path, required=True)
    phase1.add_argument("--side", choices=("source", "target"), required=True)
    phase1.add_argument("--output", type=Path, required=True)
    fingerprint = subparsers.add_parser("fingerprint")
    fingerprint.add_argument("--config", type=Path, required=True)
    fingerprint.add_argument("--side", choices=("source", "target"), required=True)
    fingerprint.add_argument("--output", type=Path, required=True)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.command == "validate-config":
        load_config(args.config, require_materialized=False)
    elif args.command == "fit":
        fit_from_config(args.config, args.output)
    elif args.command == "evaluate":
        evaluate_from_config(args.config, args.mapper, args.output)
    elif args.command == "phase1":
        phase1_from_config(args.config, args.side, args.output)
    elif args.command == "fingerprint":
        fingerprint_from_config(args.config, args.side, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
