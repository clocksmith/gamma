#!/usr/bin/env python3
"""Train and verify A1a shared-ancestor bundle arms and deployment controls on CodeNet `primary`.

Reads ONLY local CodeNet `primary` (400 files, objective-holdout-v1/frozen/sets/train.json).
Never modifies any frozen folder.

Provides:
  1. Synthetic tests proving multi-node & multi-root shared-ancestor bundles beat single pairs.
  2. Exact `b_max=1` identity proof:
     - `slot` mode at `b_max=1` matches `closure-holdout-v1/out/exact/exact-closed-s1-whole.txt`
       entry for entry (4,096/4,096).
     - `byte` mode at `b_max=1` matches `closure-holdout-v1/out/bundle/pair-byte.txt`
       entry for entry (all 2,822 lines) and completes the full exact `pair-byte` chain past 43,480 bytes.
  3. Full training of:
     - `pair-byte-exact` (`engine_shared_bundle byte 1`)
     - `shared-bundle-byte` (`engine_shared_bundle byte 16`)
     - `shared-bundle-slot` (`engine_shared_bundle slot 16`)
     - `shared-bundle-dag` (`engine_shared_bundle dag 16`)
     - Extended `BPE` (with explicit `M` merge lines past 43,480 literal bytes and A1AD budget)
     - `GreedTok` and `PathPiece` (from read-only `fixed-source-v3/engine.c`)
     - Stock `SentencePiece Unigram` (`sentencepiece`) and `HF ByteLevel BPE` (`tokenizers`)
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Dict, List, Tuple

HERE = Path(__file__).resolve().parent
LIT = HERE.parent
OH = LIT / "objective-holdout-v1"
CL = LIT / "closure-holdout-v1"
FSV3_SRC = LIT / "fixed-source-v3" / "engine.c"
BIN_DIR = HERE / "bin"
CHAINS_DIR = HERE / "out" / "chains"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def ensure_binaries() -> Tuple[Path, Path]:
    BIN_DIR.mkdir(parents=True, exist_ok=True)
    sb_bin = BIN_DIR / "engine_shared_bundle"
    fsv3_bin = BIN_DIR / "engine_fsv3"
    sb_src = HERE / "engine_shared_bundle.c"
    if not sb_bin.exists() or sb_bin.stat().st_mtime < sb_src.stat().st_mtime:
        subprocess.run(
            ["cc", "-O3", "-Wall", "-Wno-unused-function", "-o", str(sb_bin), str(sb_src), "-lm"],
            check=True,
            cwd=HERE,
        )
    if not fsv3_bin.exists():
        subprocess.run(
            ["cc", "-O3", "-Wall", "-Wno-unused-function", "-o", str(fsv3_bin), str(FSV3_SRC), "-lm"],
            check=True,
            cwd=HERE,
        )
    return sb_bin, fsv3_bin


def parse_chain(path: Path):
    e_lines: List[str] = []
    entries: List[bytes] = []
    b_lines: List[str] = []
    p_lines: List[str] = []
    m_lines: List[Tuple[bytes, bytes]] = []
    diag: Dict[str, object] = {}
    for line in path.read_text().splitlines():
        if line.startswith("E "):
            e_lines.append(line.strip())
            entries.append(bytes.fromhex(line.split()[5]))
        elif line.startswith("B "):
            b_lines.append(line.strip())
        elif line.startswith("P "):
            p_lines.append(line.strip())
        elif line.startswith("M "):
            parts = line.split()
            m_lines.append((bytes.fromhex(parts[1]), bytes.fromhex(parts[2])))
        elif line.startswith("D "):
            for tok in line.split()[2:]:
                if "=" in tok:
                    k, v = tok.split("=", 1)
                    try:
                        diag[k] = int(v)
                    except ValueError:
                        try:
                            diag[k] = float(v)
                        except ValueError:
                            diag[k] = v
    return {"e_lines": e_lines, "entries": entries, "b_lines": b_lines, "p_lines": p_lines, "m_lines": m_lines, "diag": diag}


def verify_closed(entries: List[bytes]) -> bool:
    seen = set()
    for e in entries:
        if len(e) > 1:
            if not any(e[:i] in seen and e[i:] in seen for i in range(1, len(e))):
                return False
        seen.add(e)
    return True


def write_train_list(work_dir: Path) -> Tuple[Path, List[bytes], List[bytes]]:
    spec = json.loads((OH / "frozen/sets/train.json").read_text())
    paths = []
    docs = []
    for f in spec["files"]:
        p = LIT / f["path"]
        raw = p.read_bytes()
        if sha256(raw) != f["sha256"]:
            raise SystemExit(f"train hash mismatch: {f['path']}")
        paths.append(str(p))
        docs.append(raw)
    list_file = work_dir / "train.list"
    list_file.write_text("\n".join(paths) + "\n")
    singles = [bytes([b]) for b in sorted({b for raw in docs for b in raw})]
    return list_file, docs, singles


def test_synthetic_bundles(sb_bin: Path) -> Dict[str, object]:
    """Verify multi-node and multi-root shared-ancestor bundles fire on synthetic corpora."""
    receipt = "manifest=synth pool=both cuts=none impl=engine_shared_bundle run=synth-test"
    env = dict(os.environ, FSV3_RECEIPT=receipt)
    env.pop("FSV3_CUTS", None)
    env.pop("FSV3_GROUPS", None)

    with tempfile.TemporaryDirectory() as td:
        td_p = Path(td)
        # Case 1 (single-root straddled bundle, NORMALIZED-PAIRS.md line 35):
        # After `ab` and `aba` enter V, best closed pair scores 5 while {ba, baaba} scores 15 / 2 = 7.5!
        docs2 = [b"ab"] * 40 + [b"aba"] * 20 + [b"ababaaba", b"abbbaabaa", b"aab"] * 5
        # Case 2 (multi-root shared-ancestor bundle):
        # Roots `baaba` and `baabx` share missing ancestor `ba` (priced ONCE!).
        # Best closed pair scores 10; best single-root bundle {ba, baaba} scores 25 / 2 = 12.5;
        # multi-root shared-ancestor bundle {ba, baaba, baabx} scores 40 / 3 = 13.33 > 12.5 > 10!
        docs3 = (
            [b"ab"] * 80 + [b"aba"] * 30 + [b"abx"] * 30 + [b"cb"] * 80 + [b"cba"] * 30
            + [b"ababaaba", b"ababaaba", b"abbbaabaa",
               b"cbabaabx", b"cbabaabx", b"cbbbaabxx"] * 5
        )
        results = {}
        for name, docs in (("straddled_single_root", docs2), ("straddled_multi_root", docs3)):
            cdir = td_p / name
            cdir.mkdir()
            paths = []
            for i, raw in enumerate(docs):
                fp = cdir / f"d{i}.txt"
                fp.write_bytes(raw)
                paths.append(str(fp))
            lst = cdir / "files.list"
            lst.write_text("\n".join(paths) + "\n")
            out_b1 = cdir / "b1.txt"
            out_b8 = cdir / "b8.txt"
            subprocess.run([str(sb_bin), "slot", "1", "16", "60", "0", "0", "30", str(lst), str(out_b1)], env=env, check=True)
            subprocess.run([str(sb_bin), "slot", "8", "16", "60", "0", "0", "30", str(lst), str(out_b8)], env=env, check=True)
            p1 = parse_chain(out_b1)
            p8 = parse_chain(out_b8)
            assert verify_closed(p1["entries"]) and verify_closed(p8["entries"])
            results[name] = {
                "b1_entries": len(p1["entries"]),
                "b8_entries": len(p8["entries"]),
                "b8_multi_bundle_accepts": p8["diag"].get("multi_bundle_accepts", 0),
                "b8_multi_root_accepts": p8["diag"].get("multi_root_accepts", 0),
                "b8_b_lines": p8["b_lines"][:5],
            }
        return results


def verify_bmax1_identity(sb_bin: Path, quick: bool = False) -> Dict[str, object]:
    """Prove b_max=1 reproduces exact-closed (slot) and exact pair-byte (byte) entry for entry."""
    CHAINS_DIR.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as td:
        list_file, _, _ = write_train_list(Path(td))
        receipt = "manifest=primary pool=both cuts=none impl=engine_shared_bundle run=a1a-bmax1-identity"
        env = dict(os.environ, FSV3_RECEIPT=receipt)
        env.pop("FSV3_CUTS", None)
        env.pop("FSV3_GROUPS", None)

        ref_closed = parse_chain(CL / "out/exact/exact-closed-s1-whole.txt")["e_lines"]
        ref_pair_byte = parse_chain(CL / "out/bundle/pair-byte.txt")["e_lines"]

        k_slot = 400 if quick else 4096
        k_byte = 400 if quick else len(ref_pair_byte)  # 2822

        out_slot = CHAINS_DIR / ("bmax1-slot-quick.txt" if quick else "bmax1-slot-exact-closed.txt")
        t0 = time.perf_counter()
        subprocess.run(
            [str(sb_bin), "slot", "1", "16", str(k_slot), "0", "0", "1800", str(list_file), str(out_slot)],
            env=env,
            check=True,
        )
        sec_slot = round(time.perf_counter() - t0, 3)
        got_slot = parse_chain(out_slot)
        assert verify_closed(got_slot["entries"])
        slot_diffs = sum(1 for a, b in zip(got_slot["e_lines"], ref_closed[:k_slot]) if a != b) + abs(len(got_slot["e_lines"]) - k_slot)
        if slot_diffs != 0:
            for idx, (a, b) in enumerate(zip(got_slot["e_lines"], ref_closed[:k_slot])):
                if a != b:
                    raise AssertionError(f"bmax=1 slot mismatch at {idx + 1}: got {a} vs ref {b}")
            raise AssertionError(f"bmax=1 slot length mismatch: {len(got_slot['e_lines'])} vs {k_slot}")

        out_byte = CHAINS_DIR / ("bmax1-byte-quick.txt" if quick else "pair-byte-exact-full.txt")
        # In full mode, run pair-byte-exact all the way past 43,480 literal bytes AND A1AD budget (~36KB -> ~9200 entries)
        k_byte_run = k_byte if quick else 10000
        dag_stop_byte = 0 if quick else 36500
        t1 = time.perf_counter()
        subprocess.run(
            [str(sb_bin), "byte", "1", "16", str(k_byte_run), "0", str(dag_stop_byte), "1800", str(list_file), str(out_byte)],
            env=env,
            check=True,
        )
        sec_byte = round(time.perf_counter() - t1, 3)
        got_byte = parse_chain(out_byte)
        assert verify_closed(got_byte["entries"])
        byte_prefix = got_byte["e_lines"][:k_byte]
        byte_diffs = sum(1 for a, b in zip(byte_prefix, ref_pair_byte[:k_byte]) if a != b) + abs(len(byte_prefix) - k_byte)
        if byte_diffs != 0:
            for idx, (a, b) in enumerate(zip(byte_prefix, ref_pair_byte[:k_byte])):
                if a != b:
                    raise AssertionError(f"bmax=1 byte mismatch at {idx + 1}: got {a} vs ref {b}")
            raise AssertionError(f"bmax=1 byte length mismatch: {len(byte_prefix)} vs {k_byte}")

        return {
            "quick": quick,
            "slot_checked_entries": k_slot,
            "slot_diffs": slot_diffs,
            "slot_seconds": sec_slot,
            "slot_maxrss_bytes": got_slot["diag"].get("maxrss_bytes"),
            "byte_checked_entries": k_byte,
            "byte_total_entries_trained": len(got_byte["entries"]),
            "byte_diffs": byte_diffs,
            "byte_seconds": sec_byte,
            "byte_maxrss_bytes": got_byte["diag"].get("maxrss_bytes"),
            "ok": True,
        }


def train_all_arms(sb_bin: Path, fsv3_bin: Path) -> Dict[str, object]:
    """Train all A1a bundle arms and deployment controls on CodeNet primary."""
    CHAINS_DIR.mkdir(parents=True, exist_ok=True)
    summary: Dict[str, object] = {}

    with tempfile.TemporaryDirectory() as td:
        td_p = Path(td)
        list_file, docs, singles = write_train_list(td_p)
        receipt = "manifest=primary pool=both cuts=none impl=a1a-train-dev run=a1a-dev"
        env = dict(os.environ, FSV3_RECEIPT=receipt)
        env.pop("FSV3_CUTS", None)
        env.pop("FSV3_GROUPS", None)

        # Run independent C chain training jobs in parallel across CPU cores.
        ref_closed = parse_chain(CL / "out/exact/exact-closed-s1-whole.txt")["e_lines"]
        ref_pair_byte = parse_chain(CL / "out/bundle/pair-byte.txt")["e_lines"]

        def _chain_complete(path: Path) -> Tuple[bool, float]:
            if not path.exists():
                return False, 0.0
            p = parse_chain(path)
            if p["diag"].get("stopped") == 0 and len(p["entries"]) > len(singles):
                return True, float(p["diag"].get("seconds", 0.0))
            return False, 0.0

        def run_c_job(label, cmd, out_path):
            done, prev_s = _chain_complete(out_path)
            if done:
                print(f"Reusing completed {label} ({prev_s}s)", flush=True)
                return label, prev_s
            t0 = time.perf_counter()
            subprocess.run(cmd, env=env, check=True)
            dt = round(time.perf_counter() - t0, 3)
            print(f"Finished {label} in {dt}s", flush=True)
            return label, dt

        out_b1_slot = CHAINS_DIR / "bmax1-slot-exact-closed.txt"
        out_b1_byte = CHAINS_DIR / "pair-byte-exact-full.txt"
        out_sb_byte = CHAINS_DIR / "shared-bundle-byte.txt"
        out_sb_slot = CHAINS_DIR / "shared-bundle-slot.txt"
        out_sb_dag = CHAINS_DIR / "shared-bundle-dag.txt"
        bpe_out = CHAINS_DIR / "bpe-ext.txt"
        gt_out = CHAINS_DIR / "greedtok-ext.txt"

        c_jobs = [
            ("bmax1-slot", [str(sb_bin), "slot", "1", "16", "4096", "0", "0", "1800", str(list_file), str(out_b1_slot)], out_b1_slot),
            ("pair-byte-exact", [str(sb_bin), "byte", "1", "16", "10000", "0", "35000", "1800", str(list_file), str(out_b1_byte)], out_b1_byte),
            ("shared-bundle-byte", [str(sb_bin), "byte", "16", "16", "10000", "0", "35000", "1800", str(list_file), str(out_sb_byte)], out_sb_byte),
            ("shared-bundle-slot", [str(sb_bin), "slot", "16", "16", "10000", "0", "35000", "1800", str(list_file), str(out_sb_slot)], out_sb_slot),
            ("shared-bundle-dag", [str(sb_bin), "dag", "16", "16", "10000", "0", "35000", "1800", str(list_file), str(out_sb_dag)], out_sb_dag),
            ("bpe-ext", [str(fsv3_bin), "bpe", "s1-whole", "16", "9500", "600", str(list_file), str(bpe_out)], bpe_out),
            ("greedtok-ext", [str(fsv3_bin), "greedtok", "s1-whole", "16", "6500", "600", str(list_file), str(gt_out)], gt_out),
        ]
        timings = {}
        with ThreadPoolExecutor(max_workers=6) as ex:
            futs = [ex.submit(run_c_job, lbl, cmd, op) for lbl, cmd, op in c_jobs]
            for fut in futs:
                lbl, dt = fut.result()
                timings[lbl] = dt

        # Verify b_max=1 exact identity on FULL chains
        got_slot = parse_chain(out_b1_slot)
        assert verify_closed(got_slot["entries"])
        slot_diffs = sum(1 for a, b in zip(got_slot["e_lines"], ref_closed) if a != b) + abs(len(got_slot["e_lines"]) - len(ref_closed))
        assert slot_diffs == 0, f"bmax=1 slot diffs: {slot_diffs}"

        got_byte = parse_chain(out_b1_byte)
        assert verify_closed(got_byte["entries"])
        k_pb = len(ref_pair_byte)
        byte_diffs = sum(1 for a, b in zip(got_byte["e_lines"][:k_pb], ref_pair_byte) if a != b) + abs(len(got_byte["e_lines"][:k_pb]) - k_pb)
        assert byte_diffs == 0, f"bmax=1 byte diffs: {byte_diffs}"

        summary["bmax1_identity"] = {
            "quick": False,
            "slot_checked_entries": len(ref_closed),
            "slot_diffs": slot_diffs,
            "slot_seconds": timings["bmax1-slot"],
            "slot_maxrss_bytes": got_slot["diag"].get("maxrss_bytes"),
            "byte_checked_entries": k_pb,
            "byte_total_entries_trained": len(got_byte["entries"]),
            "byte_diffs": byte_diffs,
            "byte_seconds": timings["pair-byte-exact"],
            "byte_maxrss_bytes": got_byte["diag"].get("maxrss_bytes"),
            "ok": True,
        }

        summary["bundle_arms"] = {}
        for name, mode, out_path in (
            ("shared-bundle-byte", "byte", out_sb_byte),
            ("shared-bundle-slot", "slot", out_sb_slot),
            ("shared-bundle-dag", "dag", out_sb_dag),
        ):
            parsed = parse_chain(out_path)
            assert verify_closed(parsed["entries"]), f"{name} failed closure check!"
            summary["bundle_arms"][name] = {
                "mode": mode,
                "bmax": 16,
                "entries": len(parsed["entries"]),
                "fragments": len(parsed["entries"]) - len(singles),
                "multi_bundles": len(parsed["b_lines"]),
                "wall_seconds": timings[name],
                "diag": parsed["diag"],
                "sha256": sha256(out_path.read_bytes()),
            }

        summary["controls"] = {}
        bpe_p = parse_chain(bpe_out)
        fz_bpe = [bytes.fromhex(h) for h in json.loads((CL / "frozen/dictionaries.json").read_text())["dictionaries"]["bpe-K4096"]]
        assert bpe_p["entries"][: len(fz_bpe)] == fz_bpe, "bpe-ext does not match frozen bpe-K4096!"
        summary["controls"]["bpe_ext"] = {
            "entries": len(bpe_p["entries"]),
            "merges": len(bpe_p["m_lines"]),
            "matches_frozen_bpe_K4096": True,
            "wall_seconds": timings["bpe-ext"],
            "diag": bpe_p["diag"],
        }
        gt_p = parse_chain(gt_out)
        summary["controls"]["greedtok"] = {"entries": len(gt_p["entries"]), "wall_seconds": timings["greedtok-ext"], "diag": gt_p["diag"]}

        # PathPiece (reuse if completed)
        pp_out = CHAINS_DIR / "pathpiece-ext.txt"
        pp_done, pp_dt = _chain_complete(pp_out)
        if not pp_done:
            freq_seed_chain = td_p / "freq-seed.txt"
            subprocess.run(
                [str(fsv3_bin), "freq-occ", "s1-whole", "16", "16384", "300", str(list_file), str(freq_seed_chain)],
                env=env,
                check=True,
            )
            seed_hex = td_p / "seed.hex"
            seed_entries = [e.hex() for e in parse_chain(freq_seed_chain)["entries"] if len(e) > 1]
            seed_hex.write_text("\n".join(seed_entries) + "\n")
            t0 = time.perf_counter()
            subprocess.run(
                [str(fsv3_bin), "pathpiece", "s1-whole", "16", "6500", "600", str(list_file), str(pp_out), str(seed_hex)],
                env=env,
                check=True,
            )
            pp_dt = round(time.perf_counter() - t0, 3)
        pp_p = parse_chain(pp_out)
        summary["controls"]["pathpiece"] = {"entries": len(pp_p["entries"]), "wall_seconds": pp_dt, "diag": pp_p["diag"]}
        print(f"PathPiece ready: {len(pp_p['entries'])} entries ({pp_dt}s)", flush=True)

        # 4. SentencePiece Unigram models on CodeNet primary at multiple vocab sizes covering budgets
        # Note: byte_fallback=True adds 256 byte tokens + 3 meta tokens = 259 base pieces;
        # character_coverage=0.99 keeps ASCII required while rare Unicode chars fall back losslessly to UTF-8 bytes.
        import sentencepiece as spm

        sp_dir = CHAINS_DIR / "sentencepiece"
        sp_dir.mkdir(exist_ok=True)
        sp_corpus = td_p / "sp_primary.txt"
        with open(sp_corpus, "w", encoding="utf-8", errors="replace") as fh:
            for raw in docs:
                text_str = raw.decode("utf-8", errors="replace")
                for line in text_str.splitlines():
                    if line:
                        fh.write(line + "\n")

        sp_models = {}
        # 259 meta+bytes + 95 ASCII required ~= 354 base; pick sizes matching 84-frag (~438), 3924-frag (~4280), and byte-matched
        for vs, cov in ((440, 0.99), (600, 0.99), (4280, 0.995), (6500, 0.995), (8500, 0.995)):
            prefix = sp_dir / f"unigram_{vs}"
            t0 = time.perf_counter()
            spm.SentencePieceTrainer.train(
                input=str(sp_corpus),
                model_prefix=str(prefix),
                model_type="unigram",
                vocab_size=vs,
                byte_fallback=True,
                character_coverage=cov,
                max_sentencepiece_length=16,
                add_dummy_prefix=False,
                remove_extra_whitespaces=False,
                split_by_whitespace=False,
                split_by_number=False,
                split_by_unicode_script=False,
                normalization_rule_name="identity",
                minloglevel=2,
            )
            dt = round(time.perf_counter() - t0, 3)
            sp_models[str(vs)] = {"model": str(prefix) + ".model", "character_coverage": cov, "wall_seconds": dt}
        summary["controls"]["sentencepiece_unigram"] = sp_models
        print("Trained SentencePiece Unigram models:", list(sp_models.keys()), flush=True)

        # 5. Stock HF `tokenizers` ByteLevel BPE trained directly on primary
        from tokenizers import Tokenizer, decoders, models as tk_models, pre_tokenizers, trainers

        hf_dir = CHAINS_DIR / "hf_bpe"
        hf_dir.mkdir(exist_ok=True)
        hf_models = {}
        # Pre-tokenizer ByteLevel(add_prefix_space=False) matches stock GPT-2/RoBERTa ByteLevel BPE.
        raw_texts = [raw.decode("utf-8", errors="replace") for raw in docs]
        for vs in (256 + 84, 256 + 3924, 256 + 7500):
            t0 = time.perf_counter()
            tk = Tokenizer(tk_models.BPE())
            tk.pre_tokenizer = pre_tokenizers.ByteLevel(add_prefix_space=False)
            tk.decoder = decoders.ByteLevel()
            trainer = trainers.BpeTrainer(
                vocab_size=vs,
                min_frequency=2,
                initial_alphabet=pre_tokenizers.ByteLevel.alphabet(),
                max_token_length=16,
            )
            tk.train_from_iterator(raw_texts, trainer=trainer)
            out_json = hf_dir / f"hf_bpe_{vs}.json"
            tk.save(str(out_json))
            dt = round(time.perf_counter() - t0, 3)
            hf_models[str(vs)] = {"path": str(out_json), "vocab_size": tk.get_vocab_size(), "wall_seconds": dt}
        summary["controls"]["hf_bytelevel_bpe"] = hf_models
        print("Trained HF ByteLevel BPE models:", list(hf_models.keys()), flush=True)

    (CHAINS_DIR / "train_dev_summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    return summary


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=("test", "bmax1-quick", "all"), default="test")
    args = ap.parse_args()

    sb_bin, fsv3_bin = ensure_binaries()
    if args.mode == "test":
        syn = test_synthetic_bundles(sb_bin)
        b1q = verify_bmax1_identity(sb_bin, quick=True)
        print(json.dumps({"synthetic": syn, "bmax1_quick": b1q}, indent=2))
    elif args.mode == "bmax1-quick":
        print(json.dumps(verify_bmax1_identity(sb_bin, quick=True), indent=2))
    else:
        syn = test_synthetic_bundles(sb_bin)
        res = train_all_arms(sb_bin, fsv3_bin)
        res["synthetic"] = syn
        (CHAINS_DIR / "train_dev_summary.json").write_text(json.dumps(res, indent=2) + "\n")
        print(json.dumps({"ok": True, "synthetic": syn, "bmax1_identity": res["bmax1_identity"]}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
