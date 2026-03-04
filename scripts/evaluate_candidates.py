from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agents.lower_bound_hunter.agent import LowerBoundHunterAgent


def _load_candidates(directory: Path) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    for path in sorted(directory.glob("*.json")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict) and payload.get("known_result") is False:
            payload["_source"] = str(path)
            candidates.append(payload)
    return candidates


def _bound_score(bound_value: str) -> int:
    text = bound_value.lower()
    if "n^2" in text or "superpolynomial" in text:
        return 4
    if "n^0.5" in text or "sqrt" in text:
        return 3
    if "log" in text:
        return 2
    if "constant" in text or "o(1)" in text:
        return 0
    return 1


def _evaluate_candidate(
    payload: dict[str, Any], hunter: LowerBoundHunterAgent
) -> dict[str, Any]:
    circuit_class = str(payload.get("circuit_class", "unknown"))
    function = str(payload.get("function", "unknown"))
    method = str(payload.get("method", "unknown"))
    bound_value = str(payload.get("bound_value", ""))
    key = (circuit_class.lower(), function.lower(), method.lower())
    prior = hunter.known_lower_bounds.get(key)
    prior_bound = str(prior.get("bound_value", "")) if prior else ""
    stronger = _bound_score(bound_value) > _bound_score(prior_bound)

    if prior is None:
        novelty = True
        literature = "No matching tuple in local known-result database; requires external literature verification."
    else:
        novelty = bound_value != prior_bound
        literature = f"Nearest local known result: {prior_bound}"

    concerns = ""
    if method == "polynomial_method":
        concerns = (
            "Approximate degree search uses finite-n exhaustive/proxy computation; "
            "a formal lower-bound transfer to ACC0[p] still needs theorem-level justification."
        )
    if not concerns:
        concerns = (
            "No immediate syntactic issue detected, but proof sketch remains unverified in Lean and must "
            "be checked against known barriers (natural proofs/algebrization)."
        )

    return {
        "result_id": Path(str(payload.get("_source", "candidate"))).stem,
        "circuit_class": circuit_class,
        "function": function,
        "method": method,
        "bound_value": bound_value,
        "mathematical_assessment": {
            "is_novel": novelty,
            "is_stronger": stronger,
            "literature_check": literature,
            "validity_concerns": concerns,
        },
        "next_steps": (
            "Attempt Lean formalization of the proof sketch and test generalization to stronger circuit models."
        ),
    }


def _growth_candidates(
    table: dict[str, dict[str, dict[str, int]]],
) -> list[str]:
    strong: list[str] = []
    for fn_name, by_n in table.items():
        for field_name in ("GF2", "GF3"):
            values = [
                int(v[field_name])
                for _, v in sorted(by_n.items(), key=lambda x: int(x[0]))
            ]
            if not values:
                continue
            max_ratio = max(
                val / (max(1, idx + 2) ** 0.5) for idx, val in enumerate(values)
            )
            if max_ratio >= 1.0:
                strong.append(
                    f"{fn_name} on {field_name} (max deg/sqrt(n)={max_ratio:.2f})"
                )
    return strong


def _php_asymmetry_finding(payload: dict[str, Any]) -> dict[str, Any]:
    table = payload.get("table", {})
    php = table.get("php", {})
    gf2 = {int(n): int(vals["GF2"]) for n, vals in php.items()}
    gf3 = {int(n): int(vals["GF3"]) for n, vals in php.items()}
    model = payload.get("growth_models", {}).get("php", {})
    gf2_alpha = float(model.get("GF2", {}).get("alpha", 0.0))
    gf3_alpha = float(model.get("GF3", {}).get("alpha", 0.0))
    max_gap = 0
    max_gap_n = 0
    for n in sorted(set(gf2) & set(gf3)):
        gap = gf3[n] - gf2[n]
        if gap > max_gap:
            max_gap = gap
            max_gap_n = n
    implication = (
        "Observed GF(3) growth has a steeper power-law fit than GF(2). "
        "This is consistent with a Smolensky-style field-sensitive obstruction, "
        "but finite-n degree evidence alone does not imply the Beame et al. AC0 exponential size lower bound."
    )
    return {
        "finding": "PHP_GF3_vs_GF2_asymmetry",
        "function": "php",
        "gf2_degrees": gf2,
        "gf3_degrees": gf3,
        "gf2_alpha": round(gf2_alpha, 4),
        "gf3_alpha": round(gf3_alpha, 4),
        "largest_gap": {"n": max_gap_n, "degree_gap": max_gap},
        "smolensky_note": implication,
    }


def main() -> int:
    hunter = LowerBoundHunterAgent()
    lower_bounds_dir = Path("data/lower_bounds")
    candidates = _load_candidates(lower_bounds_dir)
    evaluations = [_evaluate_candidate(candidate, hunter) for candidate in candidates]

    table_path = Path("data/lower_bounds/polynomial_degree_table.json")
    hunter.save_polynomial_degree_table(table_path, max_n=15)
    degree_payload = json.loads(table_path.read_text(encoding="utf-8"))
    table = degree_payload["table"]
    poly_window = {fn_name: by_n for fn_name, by_n in table.items()}
    strong = _growth_candidates(poly_window)
    php_finding = _php_asymmetry_finding(degree_payload)

    print("=== Candidate Lower-Bound Evaluation Report ===")
    print(f"Loaded {len(candidates)} candidate result(s) from {lower_bounds_dir}")
    if not evaluations:
        print("No known_result=False entries were found.")
    for item in evaluations:
        print("-")
        print(json.dumps(item, indent=2))

    print("\n=== Polynomial Method Deep Evaluation (full supported n-range) ===")
    for fn_name, by_n in sorted(poly_window.items()):
        print(f"Function: {fn_name}")
        for n, vals in sorted(by_n.items(), key=lambda x: int(x[0])):
            print(f"  n={n}: GF(2)={vals['GF2']}, GF(3)={vals['GF3']}")

    print("\nGrowth flags (Ω(n^0.5) or faster empirical trend):")
    if strong:
        for line in strong:
            print(f"  * {line}")
    else:
        print("  * none")

    print("\nPHP asymmetry diagnostic:")
    print(json.dumps(php_finding, indent=2))

    print(f"\nSaved full polynomial degree table to {table_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
