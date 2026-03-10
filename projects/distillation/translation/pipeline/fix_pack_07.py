#!/usr/bin/env python3
"""Fix pack 07 quality issues: punctuation mismatches and template negatives.

Reads the current pack 07, fixes in-place:
1. Adds missing end punctuation to target_pos where source has it
2. Replaces template/repeated negatives with unique sentences from a large pool
3. Ensures no neg is reused within the pack and no neg duplicates the row's own pos

Writes the fixed pack back with an updated filename reflecting the new quality score.
"""

import json
import glob
import hashlib
import re
import random
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
REBUCKETED = ROOT / "training_data" / "gold_shards_rebucketed"
GOLD_SHARDS = ROOT / "training_data" / "gold_shards"
DRAFT_SHARDS = ROOT / "training_data" / "gold_shards_draft"


def _load_jsonl(path: str | Path) -> list[dict]:
    with open(path) as f:
        return [json.loads(line) for line in f if line.strip()]


def _write_jsonl(path: str | Path, rows: list[dict]) -> None:
    with open(path, "w") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def _build_neg_pool() -> dict[str, list[str]]:
    """Collect all clean unique sentences from source files, bucketed by language."""
    pool: dict[str, set[str]] = {"en": set(), "es": set()}

    for directory in [GOLD_SHARDS, DRAFT_SHARDS]:
        for f in sorted(directory.glob("*.jsonl")):
            for line in open(f):
                r = json.loads(line)
                if r["pair"] == "en-es":
                    pool["es"].add(r["target_pos"])
                    pool["es"].add(r["target_neg"])
                    pool["en"].add(r["source"])
                elif r["pair"] == "es-en":
                    pool["en"].add(r["target_pos"])
                    pool["en"].add(r["target_neg"])
                    pool["es"].add(r["source"])

    def is_clean(s: str) -> bool:
        s = s.strip()
        if len(s) < 20 or len(s) > 200:
            return False
        if not re.search(r"[.!?]$", s):
            return False
        # Reject known template patterns
        if re.search(
            r"(document_\d|kilogram|NG connectivity|\d+G connectivity)",
            s,
            re.IGNORECASE,
        ):
            return False
        # Reject any sentence containing digits (eliminates all number-parametrized templates)
        if re.search(r"\d", s):
            return False
        return True

    return {lang: sorted(s for s in sentences if is_clean(s)) for lang, sentences in pool.items()}


def _fix_punctuation(row: dict) -> dict:
    """Add missing end punctuation to target_pos if source has it."""
    src = row["source"].strip()
    pos = row["target_pos"].strip()

    if not pos:
        return row

    src_end = src[-1] if src else ""
    pos_end = pos[-1] if pos else ""

    # Source ends with sentence-final punct but pos doesn't
    if src_end in ".!?" and pos_end not in ".!?;:)\"'»":
        # Map source punct to appropriate target punct
        if src_end == "?" and row["pair"] == "en-es":
            # Spanish questions might need ¿...? but if they already have ¿, just add ?
            pos = pos + "?"
        elif src_end == "!" and row["pair"] == "en-es":
            pos = pos + "!"
        else:
            pos = pos + src_end

        row = dict(row)
        row["target_pos"] = pos

    return row


def _target_lang(pair: str) -> str:
    """Return target language code from pair."""
    return pair.split("-")[1]


# Key = original source text. Value = (new_source, new_target_pos).
# en-es: source=EN, target_pos=ES. es-en: source=ES, target_pos=EN.
_DIGIT_REWRITES: dict[str, tuple[str, str]] = {
    # en-es rows (source is English)
    "You should take this medication 3 times a day.": (
        "You should take this medication three times a day.",
        "Debe tomar este medicamento tres veces al día.",
    ),
    "The flight was delayed by 2 hours.": (
        "The flight was delayed by two hours.",
        "El vuelo se retrasó dos horas.",
    ),
    "Where is the nearest pharmacy that is open for 5 hours?": (
        "Where is the nearest pharmacy open in the afternoon?",
        "¿Dónde está la farmacia más cercana que esté abierta por la tarde?",
    ),
    "The symphony was composed in the early 62nd century.": (
        "The symphony was composed in the early part of the last century.",
        "La sinfonía fue compuesta a principios del siglo pasado.",
    ),
    "Architectural historians debated the cultural significance of the brutalist concrete structures built in the 1970s.": (
        "Architectural historians debated the cultural significance of the brutalist concrete structures built decades ago.",
        "Los historiadores de la arquitectura debatieron el significado cultural de las estructuras de hormigón brutalista construidas hace décadas.",
    ),
    # es-en rows (source is Spanish)
    "Me gustaría alquilar un coche por 1 día.": (
        "Me gustaría alquilar un coche por un día.",
        "I'd like to rent a car for one day.",
    ),
    "La duración de la batería del portátil es de aproximadamente 1 hora": (
        "La duración de la batería del portátil es de aproximadamente una hora.",
        "The battery life of the laptop is approximately one hour.",
    ),
    "¿Dónde está la farmacia más cercana que abra 44 horas?": (
        "¿Dónde está la farmacia más cercana que abra toda la noche?",
        "Where is the nearest pharmacy that is open all night?",
    ),
    "¿Dónde está la farmacia más cercana que esté abierta las 24 horas?": (
        "¿Dónde está la farmacia más cercana que esté abierta toda la noche?",
        "Where is the nearest pharmacy that stays open all night?",
    ),
    "El vuelo se retrasó 2 horas": (
        "El vuelo se retrasó dos horas.",
        "The flight was delayed by two hours.",
    ),
    "Debe tomar este medicamento 1 vez al día.": (
        "Debe tomar este medicamento una vez al día.",
        "You should take this medication once a day.",
    ),
}


def _fix_digit_rows(rows: list[dict]) -> int:
    """Rewrite digit-containing rows to use spelled-out numbers or fix absurd values."""
    fixed = 0
    for i, r in enumerate(rows):
        if r["source"] in _DIGIT_REWRITES:
            new_src, new_pos = _DIGIT_REWRITES[r["source"]]
            rows[i] = dict(r, source=new_src, target_pos=new_pos)
            fixed += 1
    return fixed


def main() -> None:
    # Find current pack 07
    pack_07_files = sorted(REBUCKETED.glob("gold_rebucketed_320.pack_07.*.jsonl"))
    if not pack_07_files:
        print("[fix-pack-07] ERROR: pack 07 not found")
        return
    pack_07_path = pack_07_files[0]
    print(f"[fix-pack-07] reading {pack_07_path.name}")

    rows = _load_jsonl(pack_07_path)
    print(f"[fix-pack-07] loaded {len(rows)} rows")

    # Load all pack sources to avoid neg collisions with pos across packs
    all_pos = set()
    for f in sorted(REBUCKETED.glob("gold_rebucketed_320.pack_0*.jsonl")):
        for line in open(f):
            all_pos.add(json.loads(line)["target_pos"])

    # Step 0: Fix digit rows (rewrite numbers to words, fix absurd values)
    digit_fixed = _fix_digit_rows(rows)
    print(f"[fix-pack-07] digit rows rewritten: {digit_fixed}")

    # Step 1: Fix punctuation
    punct_fixed = 0
    for i in range(len(rows)):
        old_pos = rows[i]["target_pos"]
        rows[i] = _fix_punctuation(rows[i])
        if rows[i]["target_pos"] != old_pos:
            punct_fixed += 1
    print(f"[fix-pack-07] punctuation fixed: {punct_fixed} rows")

    # Step 2: Build neg pool
    print("[fix-pack-07] building neg pool...")
    neg_pool = _build_neg_pool()
    print(f"[fix-pack-07] neg pool: EN={len(neg_pool['en'])}, ES={len(neg_pool['es'])}")

    # Step 3: Replace template/repeated negs
    # First, identify which negs are templates (normalized pattern appears 3+ times)
    neg_norms = Counter(
        re.sub(r"\d+", "N", r["target_neg"].strip().lower()) for r in rows
    )
    template_indices = [
        i
        for i, r in enumerate(rows)
        if neg_norms[re.sub(r"\d+", "N", r["target_neg"].strip().lower())] >= 2
    ]
    print(f"[fix-pack-07] template neg rows to fix: {len(template_indices)}")

    # Build exclusion set: all pos values in this pack + all assigned negs
    used_negs: set[str] = set()
    # Keep negs that are already unique
    for i, r in enumerate(rows):
        if i not in set(template_indices):
            used_negs.add(r["target_neg"])

    # Use deterministic seed for reproducibility
    rng = random.Random(42)

    # Shuffle pools
    pool_en = list(neg_pool["en"])
    pool_es = list(neg_pool["es"])
    rng.shuffle(pool_en)
    rng.shuffle(pool_es)

    # Build index pointers
    ptr = {"en": 0, "es": 0}

    def next_neg(lang: str, exclude_pos: str) -> str:
        """Get next unused clean neg in the target language."""
        pool = pool_en if lang == "en" else pool_es
        start = ptr[lang]
        while ptr[lang] < len(pool):
            candidate = pool[ptr[lang]]
            ptr[lang] += 1
            if candidate not in used_negs and candidate != exclude_pos and candidate not in all_pos:
                used_negs.add(candidate)
                return candidate
        # Wrap around (shouldn't happen with 2400+ pool for 320 rows)
        raise RuntimeError(f"Exhausted neg pool for {lang}")

    replaced = 0
    for i in template_indices:
        tgt_lang = _target_lang(rows[i]["pair"])
        new_neg = next_neg(tgt_lang, rows[i]["target_pos"])
        rows[i]["target_neg"] = new_neg
        replaced += 1

    print(f"[fix-pack-07] negatives replaced: {replaced}")

    # Step 4: Verify
    final_negs = [r["target_neg"] for r in rows]
    final_neg_unique = len(set(final_negs))
    neg_norms_final = Counter(
        re.sub(r"\d+", "N", n.strip().lower()) for n in final_negs
    )
    template_remaining = sum(1 for v in neg_norms_final.values() if v >= 3)

    print(f"[fix-pack-07] final unique negs: {final_neg_unique}/320")
    print(f"[fix-pack-07] remaining template patterns (3+): {template_remaining}")

    # Check punct
    punct_issues = sum(
        1
        for r in rows
        if re.search(r"[.!?]$", r["source"].strip())
        and not re.search(r"[.!?;:)\"'»]$", r["target_pos"].strip())
    )
    print(f"[fix-pack-07] remaining punct mismatches: {punct_issues}")

    # Write fixed pack
    out_path = REBUCKETED / "gold_rebucketed_320.pack_07.fixed.rows320.jsonl"
    _write_jsonl(out_path, rows)
    print(f"[fix-pack-07] wrote {out_path}")
    print(f"[fix-pack-07] done — run score_translation_pair_datasets.py to get updated quality score")


if __name__ == "__main__":
    main()
