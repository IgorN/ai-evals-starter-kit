#!/usr/bin/env python3
"""Small offline grader demo. No agent, network, framework or model is invoked."""
import argparse
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent


def grade(case, output):
    """Return (passed, explanation). A pass covers this exact code contract only."""
    if not isinstance(output, dict):
        return False, "output must be a JSON object"
    expected, grader = case["expected"], case["grader"]
    kind = grader["type"]
    if kind == "decision_equals":
        wanted = expected["decision"]
        if not isinstance(wanted, str) or not wanted:
            raise ValueError("expected.decision must be a nonempty string")
        actual = output.get("decision")
        return actual == wanted, f"decision={actual!r}; expected={wanted!r}"
    if kind == "hit_at_k":
        k, wanted = grader["k"], expected["any_of_doc_ids"]
        if type(k) is not int or k < 1:
            raise ValueError("k must be a positive integer")
        if not isinstance(wanted, list) or not wanted or not all(isinstance(x, str) for x in wanted):
            raise ValueError("any_of_doc_ids must be a nonempty list of strings")
        ids = output.get("doc_ids")
        if not isinstance(ids, list) or not all(isinstance(x, str) for x in ids):
            return False, "output.doc_ids must be a list of strings in ranking order"
        hit = next((i for i, doc in enumerate(ids[:k], 1) if doc in wanted), None)
        return hit is not None, f"first expected document rank={hit}; k={k}"
    raise ValueError(f"Unknown grader: {kind}")


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def replay(dataset_path, results_path):
    dataset, saved = read_json(dataset_path), read_json(results_path)
    cases, rows = dataset["cases"], saved["results"]
    if not cases:
        raise ValueError("An empty dataset does not count as a successful run")
    case_ids = [c["id"] for c in cases]
    row_ids = [r["case_id"] for r in rows]
    if len(set(case_ids)) != len(case_ids) or len(set(row_ids)) != len(row_ids):
        raise ValueError("Duplicate case IDs are not allowed")
    unknown = set(row_ids) - set(case_ids)
    if unknown:
        raise ValueError(f"Results contain unknown case IDs: {sorted(unknown)}")
    version = saved["metadata"]["dataset_version"]
    if dataset["dataset_version"] != version:
        raise ValueError("Dataset and results versions differ")
    if saved.get("kind") == "handwritten_demo":
        print("OFFLINE DEMO: handwritten outputs; no model was run.")
    else:
        print("SAVED RESULTS: evaluating saved outputs; no model is run here.")
    outputs = {r["case_id"]: r["output"] for r in rows}
    passed = 0
    for case in cases:
        ok, message = grade(case, outputs.get(case["id"]))
        passed += int(ok)
        print(f"{'PASS' if ok else 'FAIL'} {case['id']}: {message}")
    print(f"Code contracts passed: {passed}/{len(cases)}. This is not overall agent accuracy.")
    return 0 if passed == len(cases) else 1


def selftest():
    """Independent literal known answers, not generated from the dataset."""
    decision = {"expected": {"decision": "REVISE"}, "grader": {"type": "decision_equals"}}
    retrieval = {"expected": {"any_of_doc_ids": ["doc-A"]}, "grader": {"type": "hit_at_k", "k": 3}}
    probes = [
        (decision, {"decision": "REVISE"}, True),
        (decision, {"decision": "APPROVE"}, False),
        (decision, {}, False),
        (decision, None, False),
        (retrieval, {"doc_ids": ["x", "y", "doc-A"]}, True),
        (retrieval, {"doc_ids": ["x", "y", "z", "doc-A"]}, False),
        (retrieval, {"doc_ids": []}, False),
        (retrieval, {"doc_ids": "doc-A"}, False),
    ]
    failures = 0
    for index, (case, output, wanted) in enumerate(probes, 1):
        actual, _ = grade(case, output)
        failures += int(actual != wanted)
        print(f"{'PASS' if actual == wanted else 'FAIL'} known-answer probe {index}")
    print(f"Grader selftest: {len(probes) - failures}/{len(probes)} probes.")
    return 1 if failures else 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cases", type=Path, default=HERE / "cases.json")
    parser.add_argument("--results", type=Path, default=HERE / "demo-results.json")
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args()
    try:
        return selftest() if args.selftest else replay(args.cases, args.results)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
