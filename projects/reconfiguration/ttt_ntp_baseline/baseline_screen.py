"""No-write development gate using installed Transformers, never remote code."""

import argparse
import hashlib
import json
from pathlib import Path
import time

from artifact_contract import LAYERS, qualify
from retrieval_tasks import score_answer


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("model", type=Path)
    parser.add_argument("tasks", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--device", choices=("cpu", "mps"), required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError("Refusing to replace an existing result")
    artifact = qualify(args.model)
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer

    torch.set_num_threads(4)
    start = time.monotonic()
    model, info = AutoModelForCausalLM.from_pretrained(
        args.model,
        local_files_only=True,
        trust_remote_code=False,
        dtype=torch.bfloat16,
        attn_implementation="sdpa",
        output_loading_info=True,
    )
    expected = {f"model.layers.{i}.mlp.ttt_proj.weight" for i in LAYERS}
    if set(info["unexpected_keys"]) != expected or info["missing_keys"]:
        raise ValueError(f"Unexpected backbone load coverage: {info}")
    if info.get("mismatched_keys") or info.get("error_msgs"):
        raise ValueError(f"Backbone loading errors: {info}")
    model = model.to(args.device).eval()
    tokenizer = AutoTokenizer.from_pretrained(
        args.model,
        local_files_only=True,
        trust_remote_code=False,
        fix_mistral_regex=False,
    )

    def sync():
        if args.device == "mps":
            torch.mps.synchronize()

    sync()
    load_seconds = time.monotonic() - start
    raw = args.tasks.read_bytes()
    tasks = json.loads(raw)["tasks"]
    if len(tasks) != 16:
        raise ValueError("Frozen development contract requires sixteen tasks")
    receipt = {
        "artifact": artifact,
        "fixture_sha256": hashlib.sha256(raw).hexdigest(),
        "device": args.device,
        "dtype": "bfloat16",
        "max_new_tokens": 32,
        "arm": "trained-backbone-no-write",
        "load_seconds": load_seconds,
        "torch": torch.__version__,
        "rows": [],
        "claim": "development only; no inference-time write or RSI",
    }
    # Exclusive receipt creation also prevents two screens owning the same result.
    with args.output.open("x") as stream:
        json.dump(receipt, stream)
    with torch.inference_mode():
        for task in tasks:
            ids = torch.tensor([task["input_ids"]], device=args.device)
            if (
                tokenizer.encode(task["prompt"], add_special_tokens=False)
                != task["input_ids"]
            ):
                raise ValueError("Frozen tokenization changed")
            sync()
            begin = time.monotonic()
            result = model(input_ids=ids, use_cache=True, logits_to_keep=1)
            next_id = result.logits[:, -1].argmax(dim=-1, keepdim=True)
            generated = [int(next_id.item())]
            sync()
            first = time.monotonic()
            cache = result.past_key_values
            del result
            while len(generated) < 32 and generated[-1] != tokenizer.eos_token_id:
                result = model(
                    input_ids=next_id,
                    past_key_values=cache,
                    use_cache=True,
                    logits_to_keep=1,
                )
                cache = result.past_key_values
                next_id = result.logits[:, -1].argmax(dim=-1, keepdim=True)
                generated.append(int(next_id.item()))
                del result
            sync()
            end = time.monotonic()
            text = tokenizer.decode(generated, skip_special_tokens=True)
            row = {
                "id": task["id"],
                "input_tokens": len(task["input_ids"]),
                "generated_ids": generated,
                "output": text,
                "correct": score_answer(text, task["expected"]),
                "first_token_seconds": first - begin,
                "decode_interval_seconds": end - first,
                "total_seconds": end - begin,
            }
            receipt["rows"].append(row)
            args.output.write_text(json.dumps(receipt, indent=2))
            print(json.dumps(row), flush=True)
            del cache, ids, next_id
    correct = sum(row["correct"] for row in receipt["rows"])
    receipt["correct"] = correct
    receipt["development_gate"] = "pass" if 4 <= correct <= 14 else "stop"
    args.output.write_text(json.dumps(receipt, indent=2))


if __name__ == "__main__":
    main()
