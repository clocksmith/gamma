"""Fresh multi-token executable task generators across three distinct domains.

Domains:
1. kv_registry: Dense 110-record identifier lookup with hyphenated multi-token hex values.
2. cipher_codebook: Request-local 48-entry nonce lexicon mapping (`term_xxxx -> CIPHER=xx-yy0`).
3. state_trace: Request-local 22-register mutable event log (`SET` + `UPDATE` overrides -> `STATE=xx00`).

Every task separates `context_text` (the permitted evidence span for prompt-conditioned transforms)
from `query_text` (the final completion prompt) so no transform ever observes query answers,
ensures synthesized outputs for `cipher_codebook` and `state_trace` never appear verbatim inside
`context_text`, and provides balanced half-context splits (`half_a_prompt`, `half_b_prompt`) for
matched-compute controls.
"""

from __future__ import annotations

import hashlib
import random

DOMAINS = ("kv_registry", "cipher_codebook", "state_trace")

SYLLABLES = [
    "ka", "mo", "ti", "ru", "ve", "zo", "na", "pe", "lu", "fi",
    "da", "so", "mi", "re", "tu", "va", "no", "bi", "ce", "gu",
    "ha", "ji", "ko", "la", "qu", "wa", "xi", "yo", "ze", "ba",
]


def normalize_line(output: str) -> str:
    if not isinstance(output, str):
        return ""
    first = output.strip().split("\n", 1)[0].strip()
    first = first.rstrip("`. ,;")
    return " ".join(first.split())


def score_domain_output(domain: str, output: str, expected: str) -> bool:
    norm = normalize_line(output)
    if not norm or not expected:
        return False
    if domain in DOMAINS:
        return norm == expected
    raise ValueError(f"Unsupported domain: {domain}")


def is_valid_domain_format(domain: str, output: str) -> bool:
    norm = normalize_line(output)
    if domain == "kv_registry":
        return norm.startswith("tok_") and "-" in norm
    if domain == "cipher_codebook":
        return norm.startswith("CIPHER=") and "-" in norm
    if domain == "state_trace":
        return norm.startswith("STATE=") and len(norm) >= 9
    return False


def build_domain_tasks(seed: int, count_per_domain: int = 12) -> list[dict]:
    rng = random.Random(seed)
    all_tasks = []

    # 1. kv_registry: 110 records (~1,750 tokens), needle balanced at early/mid/late depths
    for idx in range(count_per_domain):
        n_records = 110
        pos_frac = (0.15, 0.50, 0.85)[idx % 3]
        target_idx = int(round((n_records - 1) * pos_frac))
        records = []
        target_key = None
        target_val = None
        used_keys = set()
        for r_i in range(n_records):
            while True:
                k = f"id_{rng.getrandbits(32):08x}"
                if k not in used_keys:
                    used_keys.add(k)
                    break
            v = f"tok_{rng.getrandbits(24):06x}-{rng.getrandbits(24):06x}"
            line = f"{k} = {v}\n"
            records.append(line)
            if r_i == target_idx:
                target_key = k
                target_val = v

        header = "Registry table:\n"
        context_text = header + "".join(records)
        query_text = f"{target_key} ="
        mid = n_records // 2
        half_a = header + "".join(records[:mid]) + query_text
        half_b = header + "".join(records[mid:]) + query_text
        full_prompt = context_text + query_text
        all_tasks.append({
            "id": f"kv_registry-{seed}-{idx}",
            "domain": "kv_registry",
            "context_text": context_text,
            "query_text": query_text,
            "prompt": full_prompt,
            "half_a_prompt": half_a,
            "half_b_prompt": half_b,
            "expected": target_val,
            "prompt_sha256": hashlib.sha256(full_prompt.encode()).hexdigest(),
        })

    # 2. cipher_codebook: 48 nonce terms -> two-syllable+digit code formatted as CIPHER=xx-yy0
    for idx in range(count_per_domain):
        n_terms = 48
        pos_frac = (0.15, 0.50, 0.85)[idx % 3]
        used_terms = set()
        terms = []
        for _ in range(n_terms):
            while True:
                t_name = f"term_{rng.getrandbits(16):04x}"
                if t_name not in used_terms:
                    used_terms.add(t_name)
                    break
            terms.append(t_name)

        used_codes = set()
        codes = {}
        for t_name in terms:
            while True:
                c_val = f"{rng.choice(SYLLABLES)}-{rng.choice(SYLLABLES)}{rng.randint(1, 9)}"
                if c_val not in used_codes:
                    used_codes.add(c_val)
                    break
            codes[t_name] = c_val

        ex1, ex2 = terms[0], terms[1]
        RulePool = terms[2:]
        rng.shuffle(RulePool)
        target_pos = int(round((len(RulePool) - 1) * pos_frac))
        target_term = RulePool[target_pos]

        ordered_rules = [ex1, ex2] + RulePool
        rng.shuffle(ordered_rules)
        # Re-place target_term at balanced depth in rule list
        ordered_rules.remove(target_term)
        ins_idx = int(round(len(ordered_rules) * pos_frac))
        ordered_rules.insert(ins_idx, target_term)

        rule_lines = [
            f"Lexicon ({rng.getrandbits(12):03x}): {w} maps to {codes[w]}\n"
            for w in ordered_rules
        ]
        ex_text = (
            f"Encode {ex1} => CIPHER={codes[ex1]}\n"
            f"Encode {ex2} => CIPHER={codes[ex2]}\n"
        )
        header = "Session cipher lexicon:\n"
        context_text = header + "".join(rule_lines) + ex_text
        query_text = f"Encode {target_term} =>"
        mid = len(rule_lines) // 2
        half_a = header + "".join(rule_lines[:mid]) + ex_text + query_text
        half_b = header + "".join(rule_lines[mid:]) + ex_text + query_text
        full_prompt = context_text + query_text
        all_tasks.append({
            "id": f"cipher_codebook-{seed}-{idx}",
            "domain": "cipher_codebook",
            "context_text": context_text,
            "query_text": query_text,
            "prompt": full_prompt,
            "half_a_prompt": half_a,
            "half_b_prompt": half_b,
            "expected": f"CIPHER={codes[target_term]}",
            "prompt_sha256": hashlib.sha256(full_prompt.encode()).hexdigest(),
        })

    # 3. state_trace: 22 registers SET + 20 UPDATE overrides -> READ REG_xx => STATE=<syl><dd>
    for idx in range(count_per_domain):
        n_regs = 22
        accts = [f"REG_{i:02d}" for i in range(n_regs)]
        rng.shuffle(accts)
        target_acct = accts[idx % len(accts)]
        sample_acct = [x for x in accts if x != target_acct][0]

        used_vals = set()

        def fresh_state_val() -> str:
            while True:
                val = f"{rng.choice(SYLLABLES)}{rng.randint(10, 99)}"
                if val not in used_vals:
                    used_vals.add(val)
                    return val

        state = {}
        init_lines = []
        for a in accts:
            v = fresh_state_val()
            state[a] = v
            init_lines.append(f"SET {a} = {v}\n")

        # 20 updates: target_acct and sample_acct each updated once amidst 18 distractor updates
        distractors = [x for x in accts if x not in (target_acct, sample_acct)]
        sched = [target_acct, sample_acct] + [rng.choice(distractors) for _ in range(18)]
        rng.shuffle(sched)
        update_lines = []
        for a in sched:
            v = fresh_state_val()
            state[a] = v
            update_lines.append(f"UPDATE {a} = {v}\n")

        ex_line = f"READ {sample_acct} => STATE={state[sample_acct]}\n"
        header = "State transition log:\n"
        context_text = header + "".join(init_lines) + "".join(update_lines) + ex_line
        query_text = f"READ {target_acct} =>"
        mid_u = len(update_lines) // 2
        half_a = header + "".join(init_lines) + "".join(update_lines[:mid_u]) + ex_line + query_text
        half_b = header + "".join(init_lines) + "".join(update_lines[mid_u:]) + ex_line + query_text
        full_prompt = context_text + query_text
        all_tasks.append({
            "id": f"state_trace-{seed}-{idx}",
            "domain": "state_trace",
            "context_text": context_text,
            "query_text": query_text,
            "prompt": full_prompt,
            "half_a_prompt": half_a,
            "half_b_prompt": half_b,
            "expected": f"STATE={state[target_acct]}",
            "prompt_sha256": hashlib.sha256(full_prompt.encode()).hexdigest(),
        })

    return all_tasks
