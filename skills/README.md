# GAMMA Shared Skills

`skills/` is the canonical skill registry for this repository.

Required aliases:
- `.claude/skills -> ../skills`
- `.codex/skills -> ../skills`
- `.gemini/skills -> ../skills`

Primary skills:
- `skills/gamma-development/SKILL.md`
- `skills/gamma-benchmarking/SKILL.md`
- `skills/gamma-distillation/SKILL.md`
- `skills/gamma-mind-meld-ops/SKILL.md`
- `skills/gamma-engine-compat/SKILL.md`
- `skills/gamma-codegen-ladder/SKILL.md`

Quick validation:

```bash
for d in skills/*/; do
  [ -f "${d}SKILL.md" ] || continue
  python3 /home/x/.codex/skills/.system/skill-creator/scripts/quick_validate.py "$d"
done
```
