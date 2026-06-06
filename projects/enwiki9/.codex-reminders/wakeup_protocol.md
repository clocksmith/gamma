# enwiki9 Wake-Up Protocol

On each wake-up for the enwik9 graph-token diffusion compression research:

1. Decide whether helper roles are useful for the current step.
2. Select 0, 1, or 2 roles from `agents/` and merge them into a debating review frame:
   - `hutter_contender.md`: propose Hutter-valid compression attempts and report score as `compressed_size + program_size`.
   - `skeptic_referee.md`: falsify claims using roundtrip, cold-start decode, determinism, dependency inventory, and information-theoretic checks.
   - `lm_explorer.md`: design deterministic neural-LM / arithmetic-coding backends with small integer-quantized online-adapted models.
   - `empirical_reality.md`: force byte accounting, reversible transforms, backend deltas, and measured score impact before accepting extrapolations.
   - `dac_crackpot.md`: use only as an adversarial trap to keep the skeptic calibrated; never implement from it.
3. If roles are merged, force an internal debate:
   - contender or LM role proposes the next concrete experiment;
   - skeptic role tries to reject it before implementation;
   - proceed only with byte-exact, self-contained, deterministic ideas.
4. Preserve the recurring reminder by scheduling the next `60m` timer.

Default useful pairings:

- `hutter_contender.md` + `skeptic_referee.md` for scoring and validity decisions.
- `lm_explorer.md` + `skeptic_referee.md` for neural or diffusion-backed coding ideas.
- `hutter_contender.md` + `lm_explorer.md` for implementable model-backed compression experiments.
- `empirical_reality.md` + `hutter_contender.md` for turning ideas into measured scoring tables.
- `empirical_reality.md` + `lm_explorer.md` for keeping neural or graph-diffusion ideas inside the counted-byte envelope.
