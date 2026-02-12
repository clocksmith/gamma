#!/usr/bin/env python3
"""Fetch Wikipedia text and write JSONL files.

Modes:
- api: strict network control via MediaWiki API (recommended for capped downloads)
- hf:  Hugging Face datasets (may download large shard files before row caps apply)
"""

from __future__ import annotations

import argparse
import collections
import json
import random
import re
import time
import urllib.parse
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


def _clean_text(s: str) -> str:
    return " ".join((s or "").split())


TOPIC_BUCKETS_DEFAULT = ("news", "science", "culture", "law", "health", "finance", "informal")

TOPIC_QUERIES: dict[str, dict[str, tuple[str, ...]]] = {
    "default": {
        "news": ("current events", "latest developments", "public affairs"),
        "science": ("scientific research", "biology", "physics", "chemistry"),
        "culture": ("music", "literature", "cinema", "folklore"),
        "law": ("law", "constitution", "court", "regulation"),
        "health": ("medicine", "public health", "disease prevention"),
        "finance": ("economics", "banking", "financial markets", "trade"),
        "informal": ("daily life", "community traditions", "popular culture"),
    },
    "en": {
        "news": ("current events", "breaking news", "public policy"),
        "science": ("scientific method", "biomedical research", "space science"),
        "culture": ("visual arts", "popular music", "food culture"),
        "law": ("constitutional law", "criminal procedure", "civil law"),
        "health": ("epidemiology", "mental health", "clinical care"),
        "finance": ("macroeconomics", "stock market", "fiscal policy"),
        "informal": ("neighborhood life", "street culture", "social customs"),
    },
    "es": {
        "news": ("actualidad", "política pública", "noticias internacionales"),
        "science": ("investigación científica", "biología", "física"),
        "culture": ("arte contemporáneo", "música popular", "tradiciones locales"),
        "law": ("derecho constitucional", "jurisprudencia", "regulación"),
        "health": ("salud pública", "epidemiología", "atención clínica"),
        "finance": ("economía", "mercados financieros", "política fiscal"),
        "informal": ("vida cotidiana", "barrios", "costumbres sociales"),
    },
    "fr": {
        "news": ("actualité", "politique publique", "affaires internationales"),
        "science": ("recherche scientifique", "biologie", "physique"),
        "culture": ("arts visuels", "musique populaire", "patrimoine local"),
        "law": ("droit constitutionnel", "jurisprudence", "réglementation"),
        "health": ("santé publique", "épidémiologie", "soins cliniques"),
        "finance": ("économie", "marchés financiers", "politique budgétaire"),
        "informal": ("vie quotidienne", "culture urbaine", "coutumes sociales"),
    },
    "pt": {
        "news": ("atualidades", "política pública", "notícias internacionais"),
        "science": ("pesquisa científica", "biologia", "física"),
        "culture": ("artes visuais", "música popular", "tradições locais"),
        "law": ("direito constitucional", "jurisprudência", "regulação"),
        "health": ("saúde pública", "epidemiologia", "cuidados clínicos"),
        "finance": ("economia", "mercados financeiros", "política fiscal"),
        "informal": ("vida cotidiana", "bairros", "costumes sociais"),
    },
    "ar": {
        "news": ("الأحداث الجارية", "السياسة العامة", "الأخبار الدولية"),
        "science": ("بحث علمي", "البيولوجيا", "الفيزياء"),
        "culture": ("الفنون", "الموسيقى الشعبية", "التراث المحلي"),
        "law": ("القانون الدستوري", "الاجتهاد القضائي", "التنظيم"),
        "health": ("الصحة العامة", "علم الأوبئة", "الرعاية السريرية"),
        "finance": ("الاقتصاد", "الأسواق المالية", "السياسة المالية"),
        "informal": ("الحياة اليومية", "الثقافة المحلية", "العادات الاجتماعية"),
    },
    "hi": {
        "news": ("समसामयिक घटनाएं", "सार्वजनिक नीति", "अंतरराष्ट्रीय समाचार"),
        "science": ("वैज्ञानिक शोध", "जीवविज्ञान", "भौतिकी"),
        "culture": ("कला संस्कृति", "लोक परंपरा", "लोकप्रिय संगीत"),
        "law": ("संवैधानिक कानून", "न्यायिक निर्णय", "नियमन"),
        "health": ("सार्वजनिक स्वास्थ्य", "महामारी विज्ञान", "चिकित्सकीय देखभाल"),
        "finance": ("अर्थशास्त्र", "वित्तीय बाजार", "राजकोषीय नीति"),
        "informal": ("दैनिक जीवन", "स्थानीय समुदाय", "सामाजिक रीति"),
    },
    "zh": {
        "news": ("时事", "公共政策", "国际新闻"),
        "science": ("科学研究", "生物学", "物理学"),
        "culture": ("文化艺术", "流行音乐", "地方传统"),
        "law": ("宪法", "司法判例", "监管政策"),
        "health": ("公共卫生", "流行病学", "临床护理"),
        "finance": ("经济学", "金融市场", "财政政策"),
        "informal": ("日常生活", "社区文化", "社会习俗"),
    },
    "ja": {
        "news": ("時事", "公共政策", "国際ニュース"),
        "science": ("科学研究", "生物学", "物理学"),
        "culture": ("文化芸術", "大衆音楽", "地域の伝統"),
        "law": ("憲法", "判例", "規制"),
        "health": ("公衆衛生", "疫学", "臨床医療"),
        "finance": ("経済", "金融市場", "財政政策"),
        "informal": ("日常生活", "地域社会", "社会習慣"),
    },
}

LANG_SCRIPT_EXPECTED = {
    "en": "latin",
    "es": "latin",
    "fr": "latin",
    "pt": "latin",
    "ar": "arabic",
    "hi": "devanagari",
    "zh": "han",
    "ja": "japanese",
}

BOILERPLATE_PATTERNS = (
    "may refer to",
    "can refer to",
    "disambiguation",
    "this article is about",
    "this page is about",
)


def _norm_text(s: str) -> str:
    return " ".join((s or "").strip().lower().split())


def _near_signature(s: str) -> str:
    t = _norm_text(s)
    if not t:
        return ""
    # Stable, inexpensive near-duplicate signature from lexical and character cues.
    words = re.findall(r"[^\W_]+", t, flags=re.UNICODE)
    head = words[:96]
    if head:
        freq = collections.Counter(head)
        top = sorted(freq.items(), key=lambda kv: (-kv[1], kv[0]))[:24]
        lex = " ".join(f"{w}:{c}" for w, c in top)
    else:
        chars = [ch for ch in t if not ch.isspace()]
        grams = [("".join(chars[i : i + 3])) for i in range(max(0, len(chars) - 2))]
        freq = collections.Counter(grams)
        top = sorted(freq.items(), key=lambda kv: (-kv[1], kv[0]))[:24]
        lex = " ".join(f"{g}:{c}" for g, c in top)
    return lex


def _lang_script_of_char(ch: str) -> str | None:
    cp = ord(ch)
    if (0x0041 <= cp <= 0x007A) or (0x00C0 <= cp <= 0x024F):
        return "latin"
    if 0x0600 <= cp <= 0x06FF:
        return "arabic"
    if 0x0900 <= cp <= 0x097F:
        return "devanagari"
    if 0x4E00 <= cp <= 0x9FFF:
        return "han"
    if (0x3040 <= cp <= 0x309F) or (0x30A0 <= cp <= 0x30FF):
        return "kana"
    return None


def _language_purity(text: str, lang: str) -> float:
    expected = LANG_SCRIPT_EXPECTED.get(lang, "latin")
    counts = collections.Counter()
    for ch in text:
        s = _lang_script_of_char(ch)
        if s:
            counts[s] += 1
    total = sum(counts.values())
    if total <= 0:
        return 0.0
    if expected == "japanese":
        return float((counts.get("han", 0) + counts.get("kana", 0)) / total)
    return float(counts.get(expected, 0) / total)


def _latin_ratio(text: str) -> float:
    counts = collections.Counter()
    for ch in text:
        s = _lang_script_of_char(ch)
        if s:
            counts[s] += 1
    total = sum(counts.values())
    if total <= 0:
        return 0.0
    return float(counts.get("latin", 0) / total)


def _is_boilerplate(title: str, text: str) -> bool:
    t = _norm_text(text)
    tt = _norm_text(title)
    if "(disambiguation)" in tt:
        return True
    if len(t) < 240 and any(p in t for p in BOILERPLATE_PATTERNS):
        return True
    return False


def _load_existing_api_state(path: Path) -> tuple[int, int, set[int], set[str], set[str], dict[str, int]]:
    rows = 0
    written_bytes = 0
    seen_pageids: set[int] = set()
    seen_exact: set[str] = set()
    seen_near: set[str] = set()
    topic_counts: dict[str, int] = {}
    if not path.exists():
        return rows, written_bytes, seen_pageids, seen_exact, seen_near, topic_counts
    with path.open("r", encoding="utf-8", errors="replace") as f:
        for line in f:
            if not line.strip():
                continue
            rows += 1
            written_bytes += len(line.encode("utf-8"))
            try:
                obj = json.loads(line)
                pid = int(obj.get("pageid", -1))
                if pid >= 0:
                    seen_pageids.add(pid)
                txt = _clean_text(str(obj.get("text", "")))
                if txt:
                    seen_exact.add(_norm_text(txt))
                    sig = _near_signature(txt)
                    if sig:
                        seen_near.add(sig)
                topic = str(obj.get("topic_bucket", "")).strip()
                if topic:
                    topic_counts[topic] = topic_counts.get(topic, 0) + 1
            except Exception:
                continue
    return rows, written_bytes, seen_pageids, seen_exact, seen_near, topic_counts


def _fetch_api_batch(lang: str, *, limit: int, timeout_s: float) -> list[dict[str, Any]]:
    base = f"https://{lang}.wikipedia.org/w/api.php"
    params = {
        "action": "query",
        "format": "json",
        "generator": "random",
        "grnnamespace": "0",
        "grnlimit": str(limit),
        "prop": "extracts",
        "explaintext": "1",
        "exsectionformat": "plain",
        "exlimit": "max",
        "redirects": "1",
    }
    url = f"{base}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "embeddinggemma-subsets-fetcher/1.0"},
    )
    with urllib.request.urlopen(req, timeout=timeout_s) as resp:
        data = json.loads(resp.read().decode("utf-8", errors="replace"))
    pages = data.get("query", {}).get("pages", {})
    out: list[dict[str, Any]] = []
    for page in pages.values():
        title = str(page.get("title", "")).strip()
        extract = _clean_text(str(page.get("extract", "")))
        if not title or not extract:
            continue
        out.append({"title": title, "text": extract, "pageid": int(page.get("pageid", -1))})
    return out


def _fetch_api_search_batch(lang: str, *, query: str, limit: int, timeout_s: float) -> list[dict[str, Any]]:
    base = f"https://{lang}.wikipedia.org/w/api.php"
    params = {
        "action": "query",
        "format": "json",
        "generator": "search",
        "gsrnamespace": "0",
        "gsrlimit": str(limit),
        "gsrsearch": query,
        "prop": "extracts",
        "explaintext": "1",
        "exsectionformat": "plain",
        "exlimit": "max",
        "redirects": "1",
    }
    url = f"{base}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "embeddinggemma-subsets-fetcher/1.0"},
    )
    with urllib.request.urlopen(req, timeout=timeout_s) as resp:
        data = json.loads(resp.read().decode("utf-8", errors="replace"))
    pages = data.get("query", {}).get("pages", {})
    out: list[dict[str, Any]] = []
    for page in pages.values():
        title = str(page.get("title", "")).strip()
        extract = _clean_text(str(page.get("extract", "")))
        if not title or not extract:
            continue
        out.append({"title": title, "text": extract, "pageid": int(page.get("pageid", -1)), "query": query})
    return out


def _topic_queries_for(lang: str, topic: str) -> tuple[str, ...]:
    lang_map = TOPIC_QUERIES.get(lang, {})
    if topic in lang_map:
        return tuple(lang_map[topic])
    return tuple(TOPIC_QUERIES["default"].get(topic, (topic,)))


def _pick_topic_bucket(topic_counts: dict[str, int], buckets: list[str]) -> str:
    if not buckets:
        return "general"
    # Prefer underrepresented topics for better balance.
    return min(buckets, key=lambda b: (topic_counts.get(b, 0), random.random()))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--langs", default="en,es,zh,ja,ar,fr,pt,hi")
    ap.add_argument("--mode", choices=["api", "hf"], default="api")
    ap.add_argument("--snapshot", default="20220301", help="Wikipedia snapshot prefix, e.g. 20220301")
    ap.add_argument("--dataset", default="wikimedia/wikipedia", help="HF dataset id (default: wikimedia/wikipedia)")
    ap.add_argument("--out-dir", default="/tmp/wiki_jsonl")
    ap.add_argument("--max-rows", type=int, default=64, help="Per-language row cap (default: 64). Set 0 for no cap.")
    ap.add_argument("--max-output-mb", type=int, default=0, help="Per-language output cap in MB (0 means no cap).")
    ap.add_argument("--max-requests", type=int, default=500, help="API mode: max HTTP requests per language.")
    ap.add_argument("--batch-pages", type=int, default=20, help="API mode: random pages per request (1-20).")
    ap.add_argument("--min-chars", type=int, default=200, help="Drop tiny extracts in API mode.")
    ap.add_argument("--sleep-ms", type=int, default=100, help="API mode: sleep between requests.")
    ap.add_argument("--timeout-s", type=float, default=20.0, help="API mode: request timeout seconds.")
    ap.add_argument("--retry-429-base-s", type=float, default=2.0, help="API mode: initial backoff on HTTP 429.")
    ap.add_argument("--retry-429-max-s", type=float, default=120.0, help="API mode: maximum backoff on HTTP 429.")
    ap.add_argument("--max-consecutive-errors", type=int, default=50, help="API mode: stop lang after too many consecutive errors.")
    ap.add_argument("--api-source", choices=["random", "search", "hybrid"], default="hybrid", help="API mode source strategy.")
    ap.add_argument(
        "--topic-buckets",
        default="news,science,culture,law,health,finance,informal",
        help="Comma-separated topic buckets for balanced sampling in search/hybrid modes.",
    )
    ap.add_argument("--wiki-dedupe-near", dest="wiki_dedupe_near", action="store_true", help="Enable near-duplicate filtering.")
    ap.add_argument("--no-wiki-dedupe-near", dest="wiki_dedupe_near", action="store_false", help="Disable near-duplicate filtering.")
    ap.add_argument("--purity-mode", choices=["off", "basic"], default="basic", help="Language purity filtering mode.")
    ap.add_argument("--purity-threshold", type=float, default=0.55, help="Minimum script purity score to keep a row.")
    ap.add_argument("--max-latin-ratio-nonlatin", type=float, default=0.35, help="Max Latin-script ratio for non-Latin languages.")
    ap.add_argument("--drop-boilerplate", dest="drop_boilerplate", action="store_true", help="Drop likely boilerplate/disambiguation rows.")
    ap.add_argument("--no-drop-boilerplate", dest="drop_boilerplate", action="store_false", help="Keep boilerplate/disambiguation rows.")
    ap.set_defaults(wiki_dedupe_near=True, drop_boilerplate=True)
    args = ap.parse_args()

    langs = [x.strip() for x in str(args.langs).split(",") if x.strip()]
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    for lang in langs:
        out_path = out_dir / f"{lang}.jsonl"
        cfg = f"{args.snapshot}.{lang}"
        n = 0
        written_bytes = 0
        max_bytes = int(args.max_output_mb) * 1024 * 1024 if int(args.max_output_mb) > 0 else 0
        seen_pageids: set[int] = set()
        req_count = 0
        consecutive_errors = 0
        backoff_s = float(args.retry_429_base_s)
        topic_buckets = [x.strip() for x in str(args.topic_buckets).split(",") if x.strip()]
        topic_counts: dict[str, int] = {}
        seen_exact: set[str] = set()
        seen_near: set[str] = set()

        if args.mode == "hf":
            print(f"[{lang}] loading {args.dataset}/{cfg} ...")
            from datasets import load_dataset

            ds = load_dataset(args.dataset, cfg, split="train")
            # Resume-safe append behavior to avoid data loss on partial/failed reruns.
            mode = "a" if out_path.exists() else "w"
            if out_path.exists():
                with out_path.open("r", encoding="utf-8", errors="replace") as rf:
                    for line in rf:
                        if line.strip():
                            n += 1
                            written_bytes += len(line.encode("utf-8"))
            if int(args.max_rows) > 0 and n >= int(args.max_rows):
                print(f"[{lang}] resume skip: existing rows={n} >= max_rows={int(args.max_rows)}")
                continue
            if max_bytes > 0 and written_bytes >= max_bytes:
                print(f"[{lang}] resume skip: existing size={written_bytes/(1024*1024):.1f} MB >= max_output_mb={int(args.max_output_mb)}")
                continue
            with out_path.open(mode, encoding="utf-8") as f:
                for row in ds:
                    txt = _clean_text(str(row.get("text", "")))
                    if not txt:
                        continue
                    line = json.dumps({"text": txt}, ensure_ascii=False) + "\n"
                    line_bytes = len(line.encode("utf-8"))
                    if max_bytes > 0 and (written_bytes + line_bytes) > max_bytes:
                        break
                    f.write(line)
                    written_bytes += line_bytes
                    n += 1
                    if int(args.max_rows) > 0 and n >= int(args.max_rows):
                        break
            print(f"[{lang}] wrote {n} rows ({written_bytes/(1024*1024):.1f} MB) -> {out_path}")
            continue

        # API mode: resume-safe append + dedupe via pageid when available.
        n, written_bytes, seen_pageids, seen_exact, seen_near, topic_counts = _load_existing_api_state(out_path)
        if int(args.max_rows) > 0 and n >= int(args.max_rows):
            print(f"[{lang}] resume skip: existing rows={n} >= max_rows={int(args.max_rows)}")
            continue
        if max_bytes > 0 and written_bytes >= max_bytes:
            print(f"[{lang}] resume skip: existing size={written_bytes/(1024*1024):.1f} MB >= max_output_mb={int(args.max_output_mb)}")
            continue

        print(
            f"[{lang}] api mode: max_requests={int(args.max_requests)} "
            f"batch_pages={int(args.batch_pages)} max_rows={int(args.max_rows)} "
            f"max_output_mb={int(args.max_output_mb)} existing_rows={n} "
            f"api_source={args.api_source} topics={','.join(topic_buckets) if topic_buckets else '-'}"
        )
        with out_path.open("a", encoding="utf-8") as f:
            while True:
                if int(args.max_rows) > 0 and n >= int(args.max_rows):
                    break
                if max_bytes > 0 and written_bytes >= max_bytes:
                    break
                if req_count >= int(args.max_requests):
                    break

                req_count += 1
                req_topic = _pick_topic_bucket(topic_counts, topic_buckets) if topic_buckets else "general"
                try:
                    limit = max(1, min(20, int(args.batch_pages)))
                    mode = str(args.api_source)
                    if mode == "random":
                        pages = _fetch_api_batch(
                            lang,
                            limit=limit,
                            timeout_s=float(args.timeout_s),
                        )
                    elif mode == "search":
                        query = random.choice(_topic_queries_for(lang, req_topic))
                        pages = _fetch_api_search_batch(
                            lang,
                            query=query,
                            limit=limit,
                            timeout_s=float(args.timeout_s),
                        )
                    else:
                        if random.random() < 0.8:
                            query = random.choice(_topic_queries_for(lang, req_topic))
                            pages = _fetch_api_search_batch(
                                lang,
                                query=query,
                                limit=limit,
                                timeout_s=float(args.timeout_s),
                            )
                        else:
                            pages = _fetch_api_batch(
                                lang,
                                limit=limit,
                                timeout_s=float(args.timeout_s),
                            )
                    consecutive_errors = 0
                    backoff_s = float(args.retry_429_base_s)
                except Exception as e:
                    consecutive_errors += 1
                    if isinstance(e, urllib.error.HTTPError) and int(getattr(e, "code", 0)) == 429:
                        jitter = random.uniform(0.0, min(1.0, backoff_s * 0.2))
                        wait_s = min(float(args.retry_429_max_s), backoff_s + jitter)
                        print(f"[{lang}] request error #{req_count}: HTTP 429; sleeping {wait_s:.1f}s")
                        time.sleep(max(0.0, wait_s))
                        backoff_s = min(float(args.retry_429_max_s), max(0.5, backoff_s * 1.7))
                    else:
                        print(f"[{lang}] request error #{req_count}: {e}")
                        time.sleep(max(0.0, float(args.sleep_ms) / 1000.0))
                    if consecutive_errors >= int(args.max_consecutive_errors):
                        print(f"[{lang}] too many consecutive errors ({consecutive_errors}); stopping this language")
                        break
                    continue

                new_rows = 0
                hit_max_bytes = False
                for p in pages:
                    pid = int(p.get("pageid", -1))
                    if pid in seen_pageids:
                        continue
                    txt = _clean_text(str(p.get("text", "")))
                    if len(txt) < int(args.min_chars):
                        continue
                    title = str(p.get("title", ""))
                    if bool(args.drop_boilerplate) and _is_boilerplate(title, txt):
                        continue

                    purity = _language_purity(txt, lang)
                    if str(args.purity_mode) == "basic":
                        if purity < float(args.purity_threshold):
                            continue
                        expected = LANG_SCRIPT_EXPECTED.get(lang, "latin")
                        if expected != "latin" and _latin_ratio(txt) > float(args.max_latin_ratio_nonlatin):
                            continue

                    key = _norm_text(txt)
                    if key in seen_exact:
                        continue
                    if bool(args.wiki_dedupe_near):
                        sig = _near_signature(txt)
                        if sig and sig in seen_near:
                            continue
                    seen_pageids.add(pid)
                    seen_exact.add(key)
                    if bool(args.wiki_dedupe_near):
                        sig = _near_signature(txt)
                        if sig:
                            seen_near.add(sig)

                    topic = req_topic
                    query = str(p.get("query", ""))
                    obj = {
                        "text": txt,
                        "title": title,
                        "pageid": pid,
                        "topic_bucket": topic,
                        "topic_query": query,
                        "purity_score": round(float(purity), 4),
                        "source_mode": str(args.api_source),
                    }
                    line = json.dumps(obj, ensure_ascii=False) + "\n"
                    line_bytes = len(line.encode("utf-8"))
                    if max_bytes > 0 and (written_bytes + line_bytes) > max_bytes:
                        hit_max_bytes = True
                        break
                    f.write(line)
                    written_bytes += line_bytes
                    n += 1
                    new_rows += 1
                    topic_counts[topic] = topic_counts.get(topic, 0) + 1
                    if int(args.max_rows) > 0 and n >= int(args.max_rows):
                        break

                if hit_max_bytes:
                    break

                if req_count % 20 == 0:
                    print(
                        f"[{lang}] req={req_count} rows={n} "
                        f"mb={written_bytes/(1024*1024):.1f}"
                    )
                if new_rows == 0:
                    # avoid hot looping on low-yield responses
                    time.sleep(max(0.0, float(args.sleep_ms) / 1000.0))
                else:
                    time.sleep(max(0.0, float(args.sleep_ms) / 1000.0))

        print(
            f"[{lang}] wrote {n} rows ({written_bytes/(1024*1024):.1f} MB), "
            f"requests={req_count} -> {out_path}"
        )
        if topic_counts:
            by_topic = ",".join(f"{k}:{topic_counts.get(k, 0)}" for k in topic_buckets if k in topic_counts)
            print(f"[{lang}] topic_balance {by_topic}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
