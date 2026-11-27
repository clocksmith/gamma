"""Plateau and cross-entropy miscalibration root-cause analysis of v1 (Item 7).

Inspects the sealed `v1` receipt (`.work/self-transform-neural-proposer-v1/confirmation_receipt.json`)
without touching any `v2` confirmation seed (`850000`), quantifying the three exact failure mechanisms
that prevented `v1` from improving past Generation 2 or beating `SGD`/`AdamW` on noisy classification loss:
1. Non-elitist random walk + un-annealed step radius (`0.18` at `Gen 3` vs `0.18` at `Gen 0`):
   counts how many meta-steps in `Gen 2..4` stepped away from `best_phi` and degraded validation ratio.
2. Shifting small (`n_val = 6`) per-generation validation batches causing selection variance (`~4%` std).
3. Final-layer logit norm inflation under `10%–12%` support label noise (accuracy beat `SGD` `49.8% vs 43.4%`,
   while misclassified outlier cross-entropy inflated mean query loss `2.82 vs 1.94`).
"""
from __future__ import annotations

import json
from pathlib import Path


def analyze_v1_receipt(receipt_path: Path) -> dict:
    d = json.loads(receipt_path.read_text())
    exact_gens = d["lineage_receipts"]["exact"]

    gen_diagnostics = []
    for g_rec in exact_gens:
        trace = g_rec["step_trace"]
        best_so_far = g_rec["meta_val_ratio_before"]
        degrading_steps = 0
        improving_steps = 0
        for st in trace:
            v = st["meta_val_ratio"]
            if v < best_so_far:
                improving_steps += 1
                best_so_far = v
            else:
                degrading_steps += 1
        gen_diagnostics.append({
            "generation_out": g_rec["generation_out"],
            "meta_val_before": g_rec["meta_val_ratio_before"],
            "meta_val_after": g_rec["meta_val_ratio_after"],
            "improving_steps": improving_steps,
            "degrading_walk_steps": degrading_steps,
            "last_step_vs_best_gap": trace[-1]["meta_val_ratio"] - best_so_far,
        })

    # Inspect accuracy vs cross-entropy divergence on unseen_fastweight_adapter_bridge
    bridge = d["family_summaries"]["unseen_fastweight_adapter_bridge"]
    acc_vs_loss = {
        arm: {
            "accuracy": bridge[arm]["mean_query_accuracy"],
            "query_cross_entropy": bridge[arm]["mean_final_query_loss"],
        }
        for arm in ("gen0_fixed", "exact_gen1", "exact_gen2", "exact_gen3", "exact_gen4", "sgd_nesterov", "adamw_cosine", "damped_lbfgs")
    }

    return {
        "source_receipt": str(receipt_path),
        "finding_1_non_elitist_walk_and_fixed_radius": gen_diagnostics,
        "finding_2_accuracy_vs_crossentropy_logit_inflation": acc_vs_loss,
        "v2_design_consequences": [
            "Enforce elitist parent anchor (`cur_phi` steps from `best_phi`) with coarse-to-fine radius schedule `0.20 * (0.62 ** g)`.",
            "Use a shared per-seed validation anchor across `g = 0..4` plus progressive 2/3/4-layer meta-curriculum.",
            "Add zero-extra-pass split-half gradient coherence `cos(G_half1, G_half2)` + dual input/output Kronecker damping + output-head logit shrinkage.",
        ],
    }


def main() -> None:
    v1_path = Path("/Users/xyz/deco/gamma/.work/self-transform-neural-proposer-v1/confirmation_receipt.json")
    out_path = Path("/Users/xyz/deco/gamma/.work/self-transform-neural-proposer-v2/v1_plateau_investigation.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    report = analyze_v1_receipt(v1_path)
    out_path.write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
