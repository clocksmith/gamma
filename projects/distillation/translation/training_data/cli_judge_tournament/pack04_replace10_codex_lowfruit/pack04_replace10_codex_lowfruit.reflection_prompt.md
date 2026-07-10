You are evolving EN<->ES data-filter recipes for a Gemma 1B translation distillation student.
Given this tournament scoreboard, propose the next generation of judge/filter recipes that should improve external WMT-like generalization without destroying indomain competence.
Prefer concrete mutations: stricter entity handling, external-reference style, rewrite policy, diversity, or synthetic-template rejection. Return exactly JSON with key next_generation_recipes.

Current champion: {
  "recipe_name": "entity_guard",
  "judge_profile": "entity_guard",
  "rewrite_mode": "queue",
  "min_adequacy": 4.0,
  "min_literalness": 3.5,
  "min_entity_number_preservation": 4.5,
  "min_confidence": 0.6,
  "processed_rows": 8,
  "keep_rows": 8,
  "drop_rows": 0,
  "review_rows": 0,
  "filtered_path": "projects/distillation/translation/training_data/cli_judge_tournament/pack04_replace10_codex_lowfruit/entity_guard/entity_guard.filtered.jsonl",
  "receipts_path": "projects/distillation/translation/training_data/cli_judge_tournament/pack04_replace10_codex_lowfruit/entity_guard/entity_guard.receipts.jsonl",
  "summary_path": "projects/distillation/translation/training_data/cli_judge_tournament/pack04_replace10_codex_lowfruit/entity_guard/entity_guard.summary.json",
  "quality_report": {
    "counts_by_pair": {
      "en-es": 4,
      "es-en": 4
    },
    "dataset_name": "entity_guard.filtered",
    "diagnostics": {
      "date_word_row_ratio": 0.0,
      "digit_row_ratio": 0.0,
      "direction_balance_score": 1.0,
      "exact_unique_ratio": 1.0,
      "length_bucket_entropy_norm": 0.862,
      "missing_fields_ratio": 0.0,
      "reasonable_length_ratio": 1.0,
      "same_language_ratio": 0.0,
      "semicolon_row_ratio": 0.0,
      "source_equals_target_ratio": 0.0,
      "source_token_entropy_norm": 0.9794,
      "source_unique_ratio": 1.0,
      "suspicious_length_ratio": 0.0,
      "target_pos_equals_neg_ratio": 0.0,
      "target_token_entropy_norm": 0.9723,
      "target_unique_ratio": 1.0,
      "time_marker_ratio": 0.0
    },
    "path": "projects/distillation/translation/training_data/cli_judge_tournament/pack04_replace10_codex_lowfruit/entity_guard/entity_guard.filtered.jsonl",
    "reference_similarity": {
      "external_eval2": {
        "length_profile_similarity": 71.0347,
        "source_token_similarity": 29.8131,
        "style_similarity": 44.1361,
        "target_token_similarity": 31.5604
      },
      "gold": {
        "exact_overlap_pct": 100.0,
        "exact_overlap_rows": 8.0,
        "length_profile_similarity": 98.9948,
        "loose_overlap_pct": 100.0,
        "loose_overlap_rows": 8.0,
        "score": 67.0979,
        "source_token_similarity": 31.88,
        "target_token_similarity": 36.5117
      },
      "indomain_eval3": {
        "length_profile_similarity": 52.0923,
        "source_token_similarity": 23.5099,
        "style_similarity": 35.2306,
        "target_token_similarity": 30.0897
      }
    },
    "rows": 8,
    "scores": {
      "alignment_quality": 100.0,
      "diversity": 95.3449,
      "duplication_hygiene": 100.0,
      "external_match": 44.1361,
      "gold_similarity": 67.0979,
      "indomain_match": 35.2306,
      "overall": 80.658
    }
  },
  "weighted_score": 71.3903,
  "pareto_frontier": true,
  "elo": 1016.0
}

Scoreboard: [
  {
    "recipe_name": "entity_guard",
    "judge_profile": "entity_guard",
    "weighted_score": 71.3903,
    "elo": 1016.0,
    "pareto_frontier": 1,
    "processed_rows": 8,
    "keep_rows": 8,
    "drop_rows": 0,
    "review_rows": 0,
    "overall": 80.658,
    "external_match": 44.1361,
    "alignment_quality": 100.0,
    "gold_similarity": 67.0979,
    "diversity": 95.3449,
    "indomain_match": 35.2306,
    "filtered_path": "projects/distillation/translation/training_data/cli_judge_tournament/pack04_replace10_codex_lowfruit/entity_guard/entity_guard.filtered.jsonl"
  },
  {
    "recipe_name": "strict_literal",
    "judge_profile": "strict_literal",
    "weighted_score": 71.3903,
    "elo": 1015.26,
    "pareto_frontier": 1,
    "processed_rows": 8,
    "keep_rows": 8,
    "drop_rows": 0,
    "review_rows": 0,
    "overall": 80.658,
    "external_match": 44.1361,
    "alignment_quality": 100.0,
    "gold_similarity": 67.0979,
    "diversity": 95.3449,
    "indomain_match": 35.2306,
    "filtered_path": "projects/distillation/translation/training_data/cli_judge_tournament/pack04_replace10_codex_lowfruit/strict_literal/strict_literal.filtered.jsonl"
  },
  {
    "recipe_name": "external_wmt",
    "judge_profile": "external_wmt",
    "weighted_score": 59.1798,
    "elo": 968.74,
    "pareto_frontier": 0,
    "processed_rows": 8,
    "keep_rows": 2,
    "drop_rows": 6,
    "review_rows": 0,
    "overall": 77.6918,
    "external_match": 34.6701,
    "alignment_quality": 100.0,
    "gold_similarity": 59.3201,
    "diversity": 98.4293,
    "indomain_match": 25.964,
    "filtered_path": "projects/distillation/translation/training_data/cli_judge_tournament/pack04_replace10_codex_lowfruit/external_wmt/external_wmt.filtered.jsonl"
  }
]

Recipe schema: {
  "name": "short_snake_case",
  "judge_profile": "balanced|strict_literal|entity_guard|external_wmt|rewrite_surgeon|adversarial",
  "rewrite_mode": "queue",
  "min_adequacy": 4.0,
  "min_literalness": 3.75,
  "min_entity_number_preservation": 4.25,
  "min_confidence": 0.6,
  "extra_instruction": "one precise mutation"
}
