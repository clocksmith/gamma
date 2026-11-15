"""Fresh development fixture builder; tokenization is supplied by a pinned client."""

import hashlib
import json
import random

SEED = 831709


def score_answer(output, expected):
    """Exact normalized free answer; explanations and partial matches fail."""
    return " ".join(output.split()) == expected


def build_tasks(encode):
    rng = random.Random(SEED)
    tasks = []
    for budget in (4096, 8192):
        for case in range(8):
            key = f"key_{rng.getrandbits(64):016x}"
            answer = f"value_{rng.getrandbits(64):016x}"
            needle = f"{key} = {answer}\n"
            position = (0.1, 0.5, 0.9)[case % 3]
            prefix = (
                "Read the records. Return only the exact value for the requested key.\n"
            )
            suffix = f"\nRequested key: {key}\nValue:"
            rows = []
            for _ in range(budget):
                row = f"key_{rng.getrandbits(64):016x} = value_{rng.getrandbits(64):016x}\n"
                candidate = rows + [row]
                index = round(len(candidate) * position)
                body = "".join(candidate[:index]) + needle + "".join(candidate[index:])
                prompt = prefix + body + suffix
                ids = encode(prompt)
                if len(ids) > budget:
                    break
                rows = candidate
            index = round(len(rows) * position)
            body = "".join(rows[:index]) + needle + "".join(rows[index:])
            prompt = prefix + body + suffix
            ids = encode(prompt)
            if not rows or len(ids) > budget:
                raise ValueError("Tokenizer cannot fit this fixture contract")
            tasks.append(
                {
                    "id": f"retrieval-{budget}-{case}",
                    "budget": budget,
                    "prompt": prompt,
                    "input_ids": ids,
                    "expected": answer,
                    "key": key,
                    "needle_record_fraction": index / len(rows),
                    "prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest(),
                }
            )
    return tasks


def freeze(tasks, output):
    """Exclusive creation prevents replacing exposed fixtures in place."""
    with output.open("x") as stream:
        json.dump({"seed": SEED, "population": "development", "tasks": tasks}, stream)
