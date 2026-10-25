"""Review the completed study from one entry point; never fit or reopen test data."""

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def cached_results(root=ROOT):
    folder = root / "research/reports"
    receipt = json.loads((folder / "final_release.json").read_text(encoding="utf-8"))
    if receipt["status"] != "completed" or receipt["evaluation_runs"] != 1 or receipt["test_csv_reads"] != 1:
        raise ValueError("A completed single-release receipt is required; no evaluation will be started")
    aggregate = (folder / "final_holdout.json").read_bytes()
    if hashlib.sha256(aggregate).hexdigest() != receipt["aggregate_sha256"]:
        raise ValueError("Cached aggregate differs from its release receipt; no evaluation will be started")
    result = json.loads(aggregate)
    return {"cached_result_only": True, "freeze_commit": result["freeze_commit"],
            "population": result["all_rows"]["population"],
            "model_ap": {key: row["average_precision"] for key, row in result["all_rows"]["models"].items()},
            "policies": result["all_rows"]["policies"], "evaluation_runs": receipt["evaluation_runs"]}


def show_results(result):
    population = result["population"]
    print("Completed final evaluation (cached aggregates only)")
    print(f"{population['rows']:,} cell-days; {population['positives']} positive next-day detection targets")
    print("Policy                    Recall    Precision    False alerts    Missed targets")
    for name, row in result["policies"].items():
        print(f"{name:<25} {row['recall']:>7.1%}    {row['precision']:>7.1%}    {row['false_positives']:>12,}    {row['false_negatives']:>14,}")
    print("80%/90% names are development targets. Scores are not validated probabilities.")
    print("Full results: research/reports/final_holdout.md; report contribution: report/ml_sections.md")


def run_tests():
    for directory in [ROOT / "research", ROOT]:
        completed = subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"], cwd=directory)
        if completed.returncode:
            return completed.returncode
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    verify = commands.add_parser("verify", help="Check frozen source, evidence, exports and links")
    verify.add_argument("--local-artifacts", action="store_true", help="Also hash existing private files; never parse them")
    results = commands.add_parser("results", help="Display the completed result without ML dependencies or private data")
    results.add_argument("--json", action="store_true", help="Print exact cached values as JSON")
    commands.add_parser("test", help="Run original research tests, then delivery tests; synthetic data only")
    args = parser.parse_args(argv)
    try:
        if args.command == "verify":
            from tools.verify_handover import verify as verify_package
            print(json.dumps(verify_package(local_artifacts=args.local_artifacts), indent=2))
        elif args.command == "results":
            result = cached_results()
            if args.json:
                print(json.dumps(result, indent=2))
            else:
                show_results(result)
        else:
            return run_tests()
    except (OSError, ValueError, KeyError) as error:
        print(f"Review failed: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
