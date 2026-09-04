# GAMMA Shared Skills

`skills/` is the canonical skill registry for this repository.

Required aliases:
- `.agents/skills -> ../skills`
- `.claude/skills -> ../skills`
- `.codex/skills -> ../skills`
- `.gemini/skills -> ../skills`

Primary skills:
- `skills/gamma-benchmarking/SKILL.md`
- `skills/gamma-translation-distill/SKILL.md`
- `skills/gamma-embedding-distill/SKILL.md`
- `skills/gamma-distill-report/SKILL.md`
- `skills/gamma-mind-meld-ops/SKILL.md`
- `skills/gamma-engine-compat/SKILL.md`
- `skills/gamma-codegen-ladder/SKILL.md`

Project-local skills remain owned by their nearest project instructions:

- `projects/enwiki9/skills/enwiki9-status/SKILL.md`
- `projects/enwiki9/skills/enwiki9-record-result/SKILL.md`

Open-ended Gamma development follows `AGENTS.md` and the applicable CATSCAN chain;
it is not registered as a catch-all skill.

Quick validation:

```bash
for d in skills/*/ projects/enwiki9/skills/*/; do
  [ -f "${d}SKILL.md" ] || continue
  python3 /home/x/.codex/skills/.system/skill-creator/scripts/quick_validate.py "$d"
done
```
