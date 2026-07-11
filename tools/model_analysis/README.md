# Model Analysis Tools

These utilities inspect token probabilities, attention matrices, and hidden-state
summaries for focused model experiments. Run them from the repository root.

```bash
python tools/model_analysis/extract_probabilities.py --help
python tools/model_analysis/extract_attention.py --help
python tools/model_analysis/generate_texture_pack.py --help
python tools/model_analysis/generate_tree_data.py --help
```

The dataset generators default to `reports/model_analysis/`, which is intentionally
ignored by Git. Pass `--output` to retain an artifact elsewhere.
