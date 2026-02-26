#!/usr/bin/env python3
"""
Generate large, diverse synthetic corpora + hard retrieval datasets per language.

Outputs:
- data/raw/<lang>.jsonl: sharded text records with metadata
- data/corpora/<lang>.txt: one document per line
- datasets/<lang>/dataset.json: hard retrieval benchmark
"""

from __future__ import annotations

import argparse
import json
import random
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    import regex as re_u
except Exception:
    re_u = None


WORD_RE = re_u.compile(r"\p{L}+(?:[\p{Mn}\p{Mc}]*)", re_u.UNICODE) if re_u is not None else None

LANGS = ("en", "es", "zh", "ja", "ar", "fr", "pt", "hi")
DOMAINS = ("news", "science", "finance", "health", "education", "travel", "culture", "technology", "policy")
REGISTERS = ("formal", "colloquial", "technical", "instructional", "narrative")
STYLES = ("summary", "qa", "checklist", "memo", "opinion", "report", "analysis")

LANG_CONNECTORS = {
    "en": ["However", "Meanwhile", "In practice", "For example", "As a result", "At scale"],
    "es": ["Sin embargo", "Mientras tanto", "En la practica", "Por ejemplo", "Como resultado", "A gran escala"],
    "zh": ["然而", "与此同时", "在实践中", "例如", "因此", "在大规模场景下"],
    "ja": ["しかし", "一方で", "実務では", "例えば", "その結果", "大規模では"],
    "ar": ["ومع ذلك", "في الوقت نفسه", "عمليا", "على سبيل المثال", "ونتيجة لذلك", "على نطاق واسع"],
    "fr": ["Cependant", "Pendant ce temps", "En pratique", "Par exemple", "Par consequent", "A grande echelle"],
    "pt": ["No entanto", "Enquanto isso", "Na pratica", "Por exemplo", "Como resultado", "Em larga escala"],
    "hi": ["हालांकि", "इस बीच", "व्यवहार में", "उदाहरण के लिए", "नतीजतन", "बड़े पैमाने पर"],
}

LANG_OPENERS = {
    "en": [
        "The team reviewed field reports from three regions and compared outcomes across age groups.",
        "A pilot deployment showed that response quality changed when context windows were constrained.",
        "Operators documented recurring failure patterns and proposed mitigations with measurable impact.",
        "The dataset combines public records, user feedback, and long-form technical notes.",
    ],
    "es": [
        "El equipo reviso informes de campo de tres regiones y comparo resultados por grupos de edad.",
        "Un despliegue piloto mostro que la calidad de respuesta cambio con ventanas de contexto limitadas.",
        "Los operadores documentaron patrones de falla recurrentes y mitigaciones con impacto medible.",
        "El conjunto de datos combina registros publicos, comentarios de usuarios y notas tecnicas extensas.",
    ],
    "zh": [
        "团队审阅了来自三个地区的现场报告，并比较了不同年龄组的结果。",
        "试点部署显示，在上下文窗口受限时，响应质量会发生变化。",
        "运维人员记录了重复出现的故障模式，并提出了可量化的缓解方案。",
        "该数据集结合了公开记录、用户反馈和长篇技术说明。",
    ],
    "ja": [
        "チームは三つの地域の現場報告を確認し、年齢層ごとの結果を比較した。",
        "試験導入では、コンテキスト長を制限すると応答品質が変化した。",
        "運用担当は再発する障害パターンを記録し、効果を測定できる対策を提案した。",
        "このデータセットは公開記録、利用者の意見、長文の技術メモを統合している。",
    ],
    "ar": [
        "راجع الفريق تقارير ميدانية من ثلاث مناطق وقارن النتائج عبر الفئات العمرية.",
        "اظهر نشر تجريبي ان جودة الاستجابة تتغير عند تقييد نافذة السياق.",
        "وثق المشغلون انماط اعطال متكررة واقترحوا اجراءات تخفيف قابلة للقياس.",
        "تجمع مجموعة البيانات بين سجلات عامة وتعليقات المستخدمين وملاحظات تقنية مطولة.",
    ],
    "fr": [
        "L equipe a examine des rapports de terrain de trois regions et compare les resultats par tranche d age.",
        "Un deploiement pilote a montre que la qualite des reponses changeait avec une fenetre de contexte reduite.",
        "Les operateurs ont documente des pannes recurrentes et propose des mitigations mesurables.",
        "Le jeu de donnees combine des registres publics, des retours utilisateurs et des notes techniques longues.",
    ],
    "pt": [
        "A equipe revisou relatorios de campo de tres regioes e comparou resultados por faixa etaria.",
        "Uma implantacao piloto mostrou que a qualidade da resposta mudou com janelas de contexto menores.",
        "Operadores documentaram falhas recorrentes e propuseram mitigacoes com impacto mensuravel.",
        "O conjunto de dados combina registros publicos, feedback de usuarios e notas tecnicas extensas.",
    ],
    "hi": [
        "टीम ने तीन क्षेत्रों की फील्ड रिपोर्ट की समीक्षा की और आयु समूहों के अनुसार परिणामों की तुलना की।",
        "पायलट तैनाती से पता चला कि संदर्भ विंडो सीमित होने पर उत्तर की गुणवत्ता बदलती है।",
        "ऑपरेटरों ने बार-बार आने वाले विफलता पैटर्न दर्ज किए और मापने योग्य सुधार सुझाए।",
        "यह डेटा सेट सार्वजनिक अभिलेख, उपयोगकर्ता प्रतिक्रिया और लंबी तकनीकी टिप्पणियां जोड़ता है।",
    ],
}

LANG_TOPICS = {
    "en": ["grid reliability", "supply chain delays", "model calibration", "student attendance", "flood warnings", "pharmacy stock", "urban transit"],
    "es": ["estabilidad de la red", "demoras logisticas", "calibracion del modelo", "asistencia escolar", "alertas de inundacion", "inventario de farmacia", "transporte urbano"],
    "zh": ["电网可靠性", "供应链延迟", "模型校准", "学生出勤", "洪水预警", "药房库存", "城市交通"],
    "ja": ["電力網の安定性", "物流遅延", "モデル校正", "出席率", "洪水警報", "薬局在庫", "都市交通"],
    "ar": ["موثوقية الشبكة", "تاخيرات سلاسل الامداد", "معايرة النموذج", "حضور الطلاب", "انذارات الفيضانات", "مخزون الصيدليات", "النقل الحضري"],
    "fr": ["fiabilite du reseau", "retards logistiques", "calibration du modele", "presence scolaire", "alertes inondation", "stock pharmacie", "transport urbain"],
    "pt": ["confiabilidade da rede", "atrasos logistico", "calibracao do modelo", "frequencia escolar", "alertas de enchente", "estoque da farmacia", "transporte urbano"],
    "hi": ["ग्रिड विश्वसनीयता", "सप्लाई चेन देरी", "मॉडल कैलिब्रेशन", "छात्र उपस्थिति", "बाढ़ चेतावनी", "फार्मेसी स्टॉक", "शहरी परिवहन"],
}


@dataclass(frozen=True)
class Record:
    text: str
    domain: str
    register: str
    style: str
    lang: str


def tokenize_words(text: str) -> list[str]:
    out: list[str] = []
    if WORD_RE is not None:
        for m in WORD_RE.finditer(text):
            w = m.group(0).strip().lower()
            if len(w) >= 2:
                out.append(w)
        return out

    buf: list[str] = []
    have_letter = False
    for ch in str(text):
        cat = unicodedata.category(ch)
        is_letter = cat.startswith("L") or ch.isalpha()
        is_mark = cat in ("Mn", "Mc", "Me")
        if is_letter:
            buf.append(ch)
            have_letter = True
            continue
        if is_mark and have_letter:
            buf.append(ch)
            continue
        if buf:
            w = "".join(buf).strip().lower()
            if len(w) >= 2:
                out.append(w)
            buf = []
            have_letter = False
    if buf:
        w = "".join(buf).strip().lower()
        if len(w) >= 2:
            out.append(w)
    return out


def _compose_doc(lang: str, domain: str, register: str, style: str, topic: str, *, rnd: random.Random) -> str:
    openers = LANG_OPENERS[lang]
    connectors = LANG_CONNECTORS[lang]
    a = rnd.choice(openers)
    b = rnd.choice(openers)
    c = rnd.choice(connectors)
    d = rnd.choice(connectors)
    # Force lexical overlap with structured metadata cues and repeated topic mentions.
    return (
        f"[{lang}] [{domain}] [{register}] [{style}] {a} "
        f"{c}, the discussion centers on {topic}. "
        f"{b} {d}, stakeholders compare baseline, intervention, and long-horizon outcomes for {topic}. "
        f"Constraints include budget, staffing, regulation, and data quality. "
        f"Recommended actions: validate assumptions, monitor drift, and document edge cases."
    ).strip()


def _generate_records(lang: str, docs_target: int, *, seed: int) -> list[Record]:
    rnd = random.Random(seed)
    records: list[Record] = []
    topics = LANG_TOPICS[lang]
    n = 0
    while n < docs_target:
        domain = DOMAINS[n % len(DOMAINS)]
        register = REGISTERS[(n // len(DOMAINS)) % len(REGISTERS)]
        style = STYLES[(n // (len(DOMAINS) * len(REGISTERS))) % len(STYLES)]
        topic = rnd.choice(topics)
        text = _compose_doc(lang, domain, register, style, topic, rnd=rnd)
        records.append(Record(text=text, domain=domain, register=register, style=style, lang=lang))
        n += 1
    return records


def _tfidf_keywords(docs: list[str], *, k_per_doc: int) -> list[list[str]]:
    tokenized = [tokenize_words(d) for d in docs]
    df: dict[str, int] = {}
    for ws in tokenized:
        for w in set(ws):
            df[w] = df.get(w, 0) + 1

    n_docs = max(1, len(docs))
    all_kw: list[list[str]] = []
    for ws in tokenized:
        tf: dict[str, int] = {}
        for w in ws:
            tf[w] = tf.get(w, 0) + 1
        scored = []
        for w, c in tf.items():
            d = max(1, df.get(w, 1))
            score = float(c) * (1.0 + n_docs / float(d))
            scored.append((score, w))
        scored.sort(reverse=True)
        all_kw.append([w for _, w in scored[:k_per_doc]])
    return all_kw


def _build_hard_dataset(records: list[Record], *, queries_target: int, keywords_per_query: int, seed: int) -> dict[str, Any]:
    rnd = random.Random(seed)
    docs = [r.text for r in records]
    dkw = _tfidf_keywords(docs, k_per_doc=max(24, keywords_per_query * 2))

    ids = list(range(len(docs)))
    rnd.shuffle(ids)

    queries: list[str] = []
    relevant: list[list[int]] = []
    for di in ids:
        if len(queries) >= queries_target:
            break
        kw = dkw[di]
        if len(kw) < max(4, keywords_per_query // 2):
            continue
        rnd.shuffle(kw)
        # Underspecified keyword query with high lexical ambiguity.
        q = " ".join(kw[:keywords_per_query]).strip()
        if len(q) < 14:
            continue
        qi = len(queries)
        queries.append(q)
        relevant.append([qi, di])

    lang = records[0].lang if records else "unknown"
    return {
        "meta": {
            "lang": lang,
            "difficulty": "hard",
            "generator": "make_synthetic_hard_datasets.py",
            "keywords_per_query": int(keywords_per_query),
            "records": len(records),
        },
        "queries": queries,
        "docs": docs,
        "relevant": relevant,
    }


def _write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def _write_lines(path: Path, lines: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


DEFAULT_RAW_DIR_NEW = "gamma/projects/distillation/shared/data/raw"
DEFAULT_RAW_DIR_LEGACY = "gamma/projects/embeddinggemma_subsets/data/raw"
DEFAULT_SEED_DIR_NEW = "gamma/projects/distillation/shared/data"
DEFAULT_SEED_DIR_LEGACY = "gamma/projects/embeddinggemma_subsets/data"
DEFAULT_CORPORA_DIR_NEW = "gamma/projects/distillation/shared/data/corpora"
DEFAULT_CORPORA_DIR_LEGACY = "gamma/projects/embeddinggemma_subsets/data/corpora"
DEFAULT_DATASETS_DIR_NEW = "gamma/projects/distillation/shared/datasets"
DEFAULT_DATASETS_DIR_LEGACY = "gamma/projects/embeddinggemma_subsets/datasets"


def _resolve_default_dir(arg_value: str, *, new_default: str, legacy_default: str, label: str) -> str:
    if str(arg_value) != new_default:
        return str(arg_value)
    new_p = Path(new_default)
    legacy_p = Path(legacy_default)
    if new_p.exists():
        print(f"[paths] {label}: using new default {new_p}")
        return str(new_p)
    if legacy_p.exists():
        print(f"[paths] {label}: using legacy fallback {legacy_p}")
        return str(legacy_p)
    print(f"[paths] {label}: defaulting to new path {new_p} (not found yet)")
    return str(new_p)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--langs", default="en,es,zh,ja,ar,fr,pt,hi")
    ap.add_argument("--raw-dir", default=DEFAULT_RAW_DIR_NEW)
    ap.add_argument("--seed-dir", default=DEFAULT_SEED_DIR_NEW)
    ap.add_argument("--corpora-dir", default=DEFAULT_CORPORA_DIR_NEW)
    ap.add_argument("--datasets-dir", default=DEFAULT_DATASETS_DIR_NEW)
    ap.add_argument("--docs-target", type=int, default=2200)
    ap.add_argument("--queries-target", type=int, default=1500)
    ap.add_argument("--keywords-per-query", type=int, default=12)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()
    args.raw_dir = _resolve_default_dir(
        str(args.raw_dir),
        new_default=DEFAULT_RAW_DIR_NEW,
        legacy_default=DEFAULT_RAW_DIR_LEGACY,
        label="raw-dir",
    )
    args.seed_dir = _resolve_default_dir(
        str(args.seed_dir),
        new_default=DEFAULT_SEED_DIR_NEW,
        legacy_default=DEFAULT_SEED_DIR_LEGACY,
        label="seed-dir",
    )
    args.corpora_dir = _resolve_default_dir(
        str(args.corpora_dir),
        new_default=DEFAULT_CORPORA_DIR_NEW,
        legacy_default=DEFAULT_CORPORA_DIR_LEGACY,
        label="corpora-dir",
    )
    args.datasets_dir = _resolve_default_dir(
        str(args.datasets_dir),
        new_default=DEFAULT_DATASETS_DIR_NEW,
        legacy_default=DEFAULT_DATASETS_DIR_LEGACY,
        label="datasets-dir",
    )

    langs = [x.strip() for x in str(args.langs).split(",") if x.strip()]
    for lang in langs:
        if lang not in LANGS:
            print(f"skip {lang}: unsupported")
            continue
        stable = sum(ord(c) for c in lang) % 1_000_000
        records = _generate_records(lang, int(args.docs_target), seed=int(args.seed) + stable)
        raw_rows = [
            {"lang": r.lang, "domain": r.domain, "register": r.register, "style": r.style, "text": r.text}
            for r in records
        ]
        ds = _build_hard_dataset(
            records,
            queries_target=int(args.queries_target),
            keywords_per_query=int(args.keywords_per_query),
            seed=int(args.seed) + 7,
        )

        _write_jsonl(Path(args.raw_dir) / f"{lang}.jsonl", raw_rows)
        _write_lines(Path(args.seed_dir) / f"{lang}.txt", [r.text for r in records])
        _write_lines(Path(args.corpora_dir) / f"{lang}.txt", [r.text for r in records])
        _write_json(Path(args.datasets_dir) / lang / "dataset.json", ds)
        print(f"{lang}: docs={len(ds['docs'])} queries={len(ds['queries'])} raw={Path(args.raw_dir)/f'{lang}.jsonl'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
