#!/usr/bin/env python3
"""
Generate multilingual seed corpora JSONL using Gemini generateContent API.

Output format per line:
{"text":"...","lang":"...","domain":"...","register":"...","style":"..."}
"""

from __future__ import annotations

import argparse
import concurrent.futures as cf
import datetime as dt
import json
import os
import random
import re
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Iterable


DOMAINS = ("news", "science", "finance", "health", "education", "travel", "culture", "technology", "policy")
REGISTERS = ("formal", "colloquial", "technical", "instructional", "narrative")
STYLES = ("summary", "qa", "checklist", "memo", "opinion", "report", "analysis")

LANG_LABEL = {
    "en": "English",
    "es": "Spanish",
    "zh": "Simplified Chinese",
    "ja": "Japanese",
    "ar": "Arabic",
    "fr": "French",
    "pt": "Portuguese",
    "hi": "Hindi",
}

WRITING_PROFILES_FALLBACK = (
    {
        "id": "field_notes",
        "instruction": "Write like direct field notes: concrete observations, sparse interpretation, high specificity.",
    },
    {
        "id": "investigative_brief",
        "instruction": "Write like an investigative brief: evidence-led, cross-checked claims, careful qualification.",
    },
    {
        "id": "historical_narrative",
        "instruction": "Write with historical narrative cadence: temporal anchors, contextual transitions, grounded detail.",
    },
    {
        "id": "policy_memorandum",
        "instruction": "Write as a policy memo: constraints, trade-offs, and implementation implications.",
    },
    {
        "id": "technical_postmortem",
        "instruction": "Write as a technical postmortem: failure chain, root causes, mitigations, verification steps.",
    },
    {
        "id": "community_oral",
        "instruction": "Write in a community oral-storytelling register: lived experience, local references, vivid voice.",
    },
    {
        "id": "scientific_abstract",
        "instruction": "Write like a scientific abstract: objective framing, method hints, measured conclusions.",
    },
    {
        "id": "trade_journal",
        "instruction": "Write as a specialist trade journal entry with domain terms and practical constraints.",
    },
    {
        "id": "courtroom_digest",
        "instruction": "Write as a courtroom digest: procedural sequence, contested points, narrowly scoped inferences.",
    },
    {
        "id": "travel_dispatch",
        "instruction": "Write like a travel dispatch: place-rich sensory detail, logistical nuance, local texture.",
    },
    {
        "id": "editorial_argument",
        "instruction": "Write as an editorial argument: clear stance, counterpoints, persuasive structure.",
    },
    {
        "id": "instructional_walkthrough",
        "instruction": "Write as an instructional walkthrough: operational steps, caveats, and expected outcomes.",
    },
    {
        "id": "dialogic_reflection",
        "instruction": "Write as reflective dialogue prose without direct quotes: alternating perspectives and tensions.",
    },
    {
        "id": "cultural_critique",
        "instruction": "Write as cultural critique: symbolic interpretation, social context, careful generalization.",
    },
    {
        "id": "economic_snapshot",
        "instruction": "Write as an economic snapshot: indicators, comparison windows, uncertainty-aware claims.",
    },
    {
        "id": "speculative_scenario",
        "instruction": "Write as a plausible speculative scenario: near-future framing, constraints, concrete impacts.",
    },
)


def _load_writing_profiles(path: Path) -> list[dict]:
    if not path.exists():
        return [{"id": str(p["id"]), "instructions": {"default": str(p["instruction"])}} for p in WRITING_PROFILES_FALLBACK]
    try:
        obj = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return [{"id": str(p["id"]), "instructions": {"default": str(p["instruction"])}} for p in WRITING_PROFILES_FALLBACK]
    raw = obj.get("profiles", [])
    out: list[dict] = []
    if not isinstance(raw, list):
        return [{"id": str(p["id"]), "instructions": {"default": str(p["instruction"])}} for p in WRITING_PROFILES_FALLBACK]
    for p in raw:
        if not isinstance(p, dict):
            continue
        pid = str(p.get("id", "")).strip()
        inst = p.get("instructions", {})
        if not pid or not isinstance(inst, dict):
            continue
        norm: dict[str, str] = {}
        for k, v in inst.items():
            if not isinstance(k, str):
                continue
            if isinstance(v, str) and v.strip():
                norm[k.strip()] = v.strip()
        if not norm:
            continue
        out.append({"id": pid, "instructions": norm})
    if not out:
        return [{"id": str(p["id"]), "instructions": {"default": str(p["instruction"])}} for p in WRITING_PROFILES_FALLBACK]
    return out


def _pick_profile_instruction(profile: dict, lang: str) -> str:
    inst = profile.get("instructions", {})
    if not isinstance(inst, dict):
        return "balanced neutral prose"
    for key in (lang, "default", "en"):
        val = inst.get(key)
        if isinstance(val, str) and val.strip():
            return val.strip()
    for _, val in inst.items():
        if isinstance(val, str) and val.strip():
            return val.strip()
    return "balanced neutral prose"


def _load_env_file(path: Path) -> None:
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        s = line.strip()
        if not s or s.startswith("#") or "=" not in s:
            continue
        k, v = s.split("=", 1)
        k = k.strip()
        v = v.strip()
        if (v.startswith('"') and v.endswith('"')) or (v.startswith("'") and v.endswith("'")):
            v = v[1:-1]
        if k and k not in os.environ:
            os.environ[k] = v


def _extract_text(resp: dict) -> str:
    parts = resp.get("candidates", [{}])[0].get("content", {}).get("parts", [])
    return "\n".join(str(p.get("text", "")) for p in parts if isinstance(p, dict))


def _strip_fences(s: str) -> str:
    s = s.strip()
    s = re.sub(r"^```(?:json)?\s*", "", s, flags=re.IGNORECASE)
    s = re.sub(r"\s*```$", "", s)
    return s.strip()


def _iter_seed_texts(path: Path) -> Iterable[str]:
    if not path.exists():
        return []
    out: list[str] = []
    with path.open("r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except Exception:
                continue
            txt = str(obj.get("text", "")).strip()
            if txt:
                out.append(txt)
    return out


def _norm(s: str) -> str:
    return " ".join(s.split()).strip().lower()


def _call_gemini(
    *,
    api_key: str,
    model: str,
    prompt: str,
    temperature: float,
    timeout_s: float,
) -> dict:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    body = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": float(temperature)},
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout_s) as r:
        return json.loads(r.read().decode("utf-8", errors="replace"))


def _usage_tokens(resp: dict) -> tuple[int, int, int]:
    md = resp.get("usageMetadata", {}) if isinstance(resp, dict) else {}
    if not isinstance(md, dict):
        return (0, 0, 0)
    prompt = int(md.get("promptTokenCount", 0) or 0)
    cand = int(md.get("candidatesTokenCount", 0) or 0)
    total = int(md.get("totalTokenCount", 0) or (prompt + cand))
    return (prompt, cand, total)


def _build_prompt(
    *,
    lang: str,
    domain: str,
    register: str,
    style: str,
    n: int,
    min_chars: int,
    max_chars: int,
    seed_examples: list[str],
    prompt_style: str,
    writing_profile_instruction: str,
) -> str:
    label = LANG_LABEL.get(lang, lang)
    seeds = "\n".join(f"- {x[:700].replace(chr(10), ' ')}" for x in seed_examples) if seed_examples else "- (none)"
    style_block = ""
    if str(prompt_style).strip().lower() == "exotic":
        style_block = (
            "- Be highly creative and culturally rich: include regional idioms, niche domains, "
            "uncommon settings, and varied rhetorical voice.\n"
            "- Prefer less-generic content over bland summaries; avoid repetitive corporate phrasing.\n"
            "- Use diverse within-language variants (regional tone/register) without switching language.\n"
        )
    elif str(prompt_style).strip().lower() == "creative":
        style_block = (
            "- Be creative and varied in tone/topic, but remain coherent and realistic.\n"
            "- Prefer specific imagery/examples over generic filler.\n"
        )

    return (
        f"Generate {n} diverse paragraph texts in {label} only.\n"
        f"Constraints:\n"
        f"- Language purity: ONLY {label}; no English unless lang=en.\n"
        f"- Domain: {domain}\n"
        f"- Register: {register}\n"
        f"- Style: {style}\n"
        f"- Writing profile: {writing_profile_instruction}\n"
        f"- Length: each text {min_chars} to {max_chars} characters.\n"
        f"- No bullet lists, no markdown, no tags, no metadata in text.\n"
        f"- Avoid repeating exact phrases.\n\n"
        f"{style_block}"
        f"- Be topically and stylistically distinct from every seed example.\n"
        f"- Do not reuse seed entities, phrase patterns, or scenario structure.\n\n"
        f"Use these seed examples as style/topic anchors (do not copy verbatim):\n{seeds}\n\n"
        f"Return STRICT JSON only, as an array of objects with one key: text.\n"
        f"Example: [{{\"text\":\"...\"}},{{\"text\":\"...\"}}]"
    )


def _run_lang(
    *,
    lang: str,
    args: argparse.Namespace,
    api_key: str,
    out_dir: Path,
    seed_dir: Path,
    writing_profiles: list[dict],
) -> None:
    worker = threading.current_thread().name
    started_at = dt.datetime.now().isoformat(timespec="seconds")
    out_path = out_dir / f"{lang}.jsonl"
    seed_pool = list(_iter_seed_texts(seed_dir / f"{lang}.jsonl"))
    seen: set[str] = set()
    written = 0
    call_idx = 0
    cum_prompt_tok = 0
    cum_cand_tok = 0
    cum_total_tok = 0

    # Keep per-language RNG deterministic and independent for parallel runs.
    lang_seed = int(args.seed) + sum(ord(ch) for ch in str(lang))
    rng = random.Random(lang_seed)

    mode = "w"
    if out_path.exists():
        mode = "a"
        with out_path.open("r", encoding="utf-8", errors="replace") as r:
            for line in r:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except Exception:
                    continue
                txt = str(obj.get("text", "")).strip()
                if not txt:
                    continue
                seen.add(_norm(txt))
                written += 1
    print(
        f"[{lang}] worker={worker} started_at={started_at} "
        f"seed_examples={len(seed_pool)} existing={written} target={int(args.rows_per_lang)}"
    )
    with out_path.open(mode, encoding="utf-8") as f:
        while written < int(args.rows_per_lang):
            call_idx += 1
            call_start = time.time()
            domain = rng.choice(DOMAINS)
            register = rng.choice(REGISTERS)
            style = rng.choice(STYLES)
            need = min(int(args.batch_size), int(args.rows_per_lang) - written)
            if seed_pool:
                k = min(len(seed_pool), max(1, int(args.seed_examples_per_call)))
                seed_examples = rng.sample(seed_pool, k=k)
            else:
                seed_examples = []
            profile_id = "none"
            profile_instruction = "balanced neutral prose"
            if str(args.writing_profile_mode) == "random":
                profile = rng.choice(writing_profiles)
                profile_id = str(profile["id"])
                profile_instruction = _pick_profile_instruction(profile, lang)
            prompt = _build_prompt(
                lang=lang,
                domain=domain,
                register=register,
                style=style,
                n=need,
                min_chars=int(args.min_chars),
                max_chars=int(args.max_chars),
                seed_examples=seed_examples,
                prompt_style=str(args.prompt_style),
                writing_profile_instruction=profile_instruction,
            )

            payload = None
            retries_used = 0
            resp_obj: dict | None = None
            for attempt in range(int(args.max_retries)):
                try:
                    resp_obj = _call_gemini(
                        api_key=api_key,
                        model=str(args.model),
                        prompt=prompt,
                        temperature=float(args.temperature),
                        timeout_s=float(args.timeout_s),
                    )
                    txt = _strip_fences(_extract_text(resp_obj))
                    payload = json.loads(txt)
                    break
                except urllib.error.HTTPError as e:
                    retries_used = attempt + 1
                    wait_s = min(90.0, 2.0 * (1.8**attempt))
                    if int(getattr(e, "code", 0)) == 429:
                        print(f"[{lang}] 429 rate limit; retry in {wait_s:.1f}s")
                    else:
                        print(f"[{lang}] HTTP {getattr(e,'code',0)}; retry in {wait_s:.1f}s")
                    time.sleep(wait_s)
                except Exception:
                    retries_used = attempt + 1
                    wait_s = min(30.0, 1.5 * (1.6**attempt))
                    time.sleep(wait_s)

            if not isinstance(payload, list):
                print(f"[{lang}] skip batch: invalid JSON payload")
                time.sleep(max(0.0, int(args.sleep_ms) / 1000.0))
                continue

            accepted = 0
            for obj in payload:
                if not isinstance(obj, dict):
                    continue
                text = str(obj.get("text", "")).strip()
                if len(text) < int(args.min_chars):
                    continue
                key = _norm(text)
                if key in seen:
                    continue
                row = {
                    "text": text,
                    "lang": lang,
                    "domain": domain,
                    "register": register,
                    "style": style,
                    "writing_profile": profile_id,
                }
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
                seen.add(key)
                written += 1
                accepted += 1
                if written >= int(args.rows_per_lang):
                    break

            ptok, ctok, ttok = _usage_tokens(resp_obj or {})
            cum_prompt_tok += ptok
            cum_cand_tok += ctok
            cum_total_tok += ttok
            elapsed = time.time() - call_start
            print(
                f"[{lang}] worker={worker} call={call_idx} need={need} accepted={accepted} "
                f"written={written}/{int(args.rows_per_lang)} retries={retries_used} "
                f"profile={profile_id} seeds={len(seed_examples)} "
                f"tok_in={ptok} tok_out={ctok} tok_total={ttok} "
                f"cum_tok={cum_total_tok} sec={elapsed:.2f}"
            )

            # Persist rows durably per batch so external row counts reflect progress.
            if accepted > 0:
                f.flush()
                os.fsync(f.fileno())

            if accepted == 0:
                print(f"[{lang}] batch produced 0 accepted rows; continuing")
            if written % 500 == 0 or written < 50:
                print(f"[{lang}] wrote {written}/{int(args.rows_per_lang)}")
            time.sleep(max(0.0, int(args.sleep_ms) / 1000.0))

    ended_at = dt.datetime.now().isoformat(timespec="seconds")
    print(
        f"[{lang}] worker={worker} ended_at={ended_at} complete -> {out_path} (rows={written}, "
        f"cum_prompt_tok={cum_prompt_tok}, cum_out_tok={cum_cand_tok}, cum_total_tok={cum_total_tok})"
    )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--langs", default="en,es,zh,ja,ar,fr,pt,hi")
    ap.add_argument("--out-dir", default="/tmp/llm_seed_jsonl")
    ap.add_argument("--model", default="gemini-3-flash-preview")
    ap.add_argument("--rows-per-lang", type=int, default=20000)
    ap.add_argument("--batch-size", type=int, default=12, help="Texts requested per API call.")
    ap.add_argument("--min-chars", type=int, default=300)
    ap.add_argument("--max-chars", type=int, default=1200)
    ap.add_argument("--temperature", type=float, default=1.0)
    ap.add_argument("--timeout-s", type=float, default=60.0)
    ap.add_argument("--sleep-ms", type=int, default=200)
    ap.add_argument("--max-retries", type=int, default=5)
    ap.add_argument("--env-file", default=str(Path.home() / ".env"))
    ap.add_argument("--seed-jsonl-dir", default="gamma/projects/embeddinggemma_subsets/data/raw_wikipedia")
    ap.add_argument("--seed-examples-per-call", type=int, default=4)
    ap.add_argument("--prompt-style", choices=["balanced", "creative", "exotic"], default="exotic")
    ap.add_argument("--writing-profile-mode", choices=["off", "random"], default="random")
    ap.add_argument("--writing-profiles-file", default=str(Path(__file__).with_name("writing_profiles.json")))
    ap.add_argument("--parallel-workers", type=int, default=1, help="Number of languages to process concurrently.")
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    _load_env_file(Path(args.env_file))
    api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not api_key:
        raise SystemExit("Missing GEMINI_API_KEY (set env or provide --env-file with key).")

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    seed_dir = Path(args.seed_jsonl_dir)
    writing_profiles = _load_writing_profiles(Path(args.writing_profiles_file))
    langs = [x.strip() for x in str(args.langs).split(",") if x.strip()]
    workers = max(1, int(args.parallel_workers))
    if workers == 1 or len(langs) <= 1:
        for lang in langs:
            _run_lang(
                lang=lang,
                args=args,
                api_key=api_key,
                out_dir=out_dir,
                seed_dir=seed_dir,
                writing_profiles=writing_profiles,
            )
        return 0

    print(f"[multi] running {len(langs)} languages with parallel_workers={workers}")
    with cf.ThreadPoolExecutor(max_workers=workers) as ex:
        futs = [
            ex.submit(
                _run_lang,
                lang=lang,
                args=args,
                api_key=api_key,
                out_dir=out_dir,
                seed_dir=seed_dir,
                writing_profiles=writing_profiles,
            )
            for lang in langs
        ]
        for fut in cf.as_completed(futs):
            fut.result()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
