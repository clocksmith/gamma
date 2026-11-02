#!/usr/bin/env python3
"""Canonical metadata-only problem index and lookup CLI for Gamma.

Builds and queries a flat, greppable index (PROBLEM_INDEX.tsv and
PROBLEM_INDEX.jsonl) across all 4,096 official LeetCode problems and 1,048
Hack2Hire question-bank entries/variants without opening candidate source
payloads or protected test cases.

Organization and indexing confer no qualification, execution, or publication
authority. Qualification and boundary classifications are preserved verbatim
from their owning metadata artifacts.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path
import re
import sys

HERE = Path(__file__).resolve().parent
ALG_ROOT = HERE.parent
REPO_ROOT = ALG_ROOT.parent.parent

TSV_PATH = HERE / "PROBLEM_INDEX.tsv"
JSONL_PATH = HERE / "PROBLEM_INDEX.jsonl"

TSV_COLUMNS = (
    "key",
    "source",
    "id",
    "category",
    "slug",
    "title",
    "method",
    "status",
    "tier",
    "py_path",
    "js_path",
    "semantics_path",
    "study_path",
    "companies",
    "topics",
    "complexity",
    "design",
)

# Within catalogue/authored/, specialized repair or official-interface batches
# supersede the earlier base batch for the same problem ID.
AUTHORED_BATCH_PRIORITY = {
    "repair-python695-iterative-20261028-v1": 0,
    "continuation-q126-output-sensitive-20261028-v1": 0,
    "continuation-q140-output-sensitive-20261028-v1": 0,
    "continuation-p-js-official-20261028-v1": 0,
    "packed-path1743-v1": 1,
    "hack2hire-chunk05-blocked-20261029-v1": 1,
    "leetcode-eight-v1": 2,
    "leetcode-easy96-v7": 2,
    "leetcode-medium-32-v1": 2,
    "leetcode-hard32-v1": 2,
}

TIER_ORDER = (
    "authored",
    "qualified-archive",
    "staged",
    "candidates",
    "literals",
    "quarantined-archival",
    "run-snapshot",
)


def _clean_tsv_field(value: object) -> str:
    if value is None:
        return "-"
    if isinstance(value, (list, tuple)):
        text = ",".join(str(x).strip() for x in value if str(x).strip())
    else:
        text = str(value)
    text = re.sub(r"[\t\r\n]+", " ", text).strip()
    return text if text else "-"


def _norm_key(raw: object) -> str:
    s = str(raw).strip()
    if ":" in s:
        ns, val = s.split(":", 1)
        if ns == "leetcode" and val.isdigit():
            return f"leetcode:{int(val)}"
        if ns == "hack2hire":
            return f"hack2hire:{val}"
    if re.fullmatch(r"[0-9a-f]{24}", s):
        return f"hack2hire:{s}"
    if s.isdigit():
        return f"leetcode:{int(s)}"
    return s


def _classify_source_path(rel_alg_path: Path) -> tuple[str, int, str]:
    """Return (tier_name, priority_rank, repo_relative_path) for a source path."""
    parts = rel_alg_path.parts
    repo_rel = f"projects/algorithm_solver/{rel_alg_path.as_posix()}"
    if len(parts) >= 3 and parts[0] == "catalogue" and parts[1] == "authored":
        batch = parts[2]
        batch_rank = AUTHORED_BATCH_PRIORITY.get(batch, 10)
        return ("authored", batch_rank, repo_rel)
    if (
        len(parts) >= 5
        and parts[0] == "catalogue"
        and parts[1] == "private-recovery-20261026"
        and parts[2] == "qualified-sources"
    ):
        return ("qualified-archive", 20, repo_rel)
    if parts[0] == "staged":
        return ("staged", 30, repo_rel)
    if len(parts) >= 2 and parts[0] == "catalogue" and parts[1] == "candidates":
        return ("candidates", 40, repo_rel)
    if parts[0] == "literals" and (
        "paired-authoring-v1" in parts or "guides-qualified-v1" in parts or "python-devval-v1" in parts
    ):
        return ("literals", 50, repo_rel)
    if len(parts) >= 2 and parts[0] == "catalogue" and parts[1] == "quarantined":
        return ("quarantined-archival", 80, repo_rel)
    if parts[0] in ("runs", "data", "findings") or (parts[0] == "catalogue" and "easy16" in parts[1]):
        return ("run-snapshot", 90, repo_rel)
    return ("run-snapshot", 95, repo_rel)


def _collect_source_paths() -> tuple[dict[str, list[tuple[str, int, str]]], dict[str, list[tuple[str, int, str]]]]:
    """Enumerate .py and .js solution paths by problem key without reading file bytes."""
    py_by_key: dict[str, list[tuple[str, int, str]]] = defaultdict(list)
    js_by_key: dict[str, list[tuple[str, int, str]]] = defaultdict(list)

    for ext, bucket in ((".py", py_by_key), (".js", js_by_key)):
        for p in sorted(ALG_ROOT.rglob(f"*{ext}")):
            if "__pycache__" in p.parts:
                continue
            stem = p.stem
            if stem.isdigit():
                key = f"leetcode:{int(stem)}"
            elif re.fullmatch(r"[0-9a-f]{24}", stem):
                key = f"hack2hire:{stem}"
            else:
                continue
            rel = p.relative_to(ALG_ROOT)
            tier, rank, repo_rel = _classify_source_path(rel)
            bucket[key].append((tier, rank, repo_rel))

    for bucket in (py_by_key, js_by_key):
        for key, items in bucket.items():
            items.sort(key=lambda x: (x[1], x[2]))
    return py_by_key, js_by_key


def _extract_method_from_interface(oi: object) -> str | None:
    if not isinstance(oi, dict):
        return None
    for k in ("name", "leetcode_method", "javascript_entry", "method"):
        val = oi.get(k)
        if isinstance(val, str) and val.strip() and val.strip() != "solve":
            return val.strip()
    cls_name = oi.get("classname") or oi.get("class")
    if isinstance(cls_name, str) and cls_name.strip():
        if cls_name.strip() != "Solution":
            return cls_name.strip()
        methods = oi.get("methods")
        if isinstance(methods, list) and methods and isinstance(methods[0], dict) and methods[0].get("name"):
            return str(methods[0]["name"]).strip()
    meta = oi.get("metadata")
    if isinstance(meta, dict):
        res = _extract_method_from_interface(meta)
        if res:
            return res
    act = oi.get("actual_interface")
    if isinstance(act, dict):
        exports = act.get("exports")
        if isinstance(exports, dict):
            js_exp = exports.get("javascript")
            if isinstance(js_exp, list) and js_exp and str(js_exp[0]).strip() != "solve":
                return str(js_exp[0]).strip()
    ep = oi.get("entrypoint")
    if isinstance(ep, str) and ep.strip() and ep.strip() != "solve":
        return ep.strip()
    return None


def _extract_method_from_declaration(decl: str) -> str | None:
    for fn in re.findall(r"\bdef\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(", decl):
        if fn not in ("solve", "__init__"):
            return fn
    for cls_name in re.findall(r"\bclass\s+([A-Za-z_][A-Za-z0-9_]*)\s*[:(]", decl):
        if cls_name != "Solution":
            return cls_name
    for fn in re.findall(r"\bfunction\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(", decl):
        if fn != "solve":
            return fn
    for fn in re.findall(r"module\.exports\.([A-Za-z_][A-Za-z0-9_]*)\s*\(", decl):
        if fn != "solve":
            return fn
    return None


def _infer_cohort_difficulty(repo_rel_path: str | None) -> str | None:
    if not repo_rel_path:
        return None
    low = repo_rel_path.lower()
    if "/leetcode-easy" in low or "/easy" in low:
        return "Easy"
    if "/leetcode-medium" in low or "/medium" in low:
        return "Medium"
    if "/leetcode-hard" in low or "/hard" in low:
        return "Hard"
    return None


def _collect_authored_metadata() -> dict[str, dict[str, object]]:
    """Read JSON metadata files under catalogue/authored/ without opening candidate code."""
    authored = HERE / "authored"
    meta: dict[str, dict[str, object]] = defaultdict(dict)

    # 1. assignment.public-safe.json
    for p in sorted(authored.glob("*/assignment.public-safe.json")):
        d = json.loads(p.read_text())
        probs = d.get("problems", [])
        items = probs.values() if isinstance(probs, dict) else probs if isinstance(probs, list) else []
        for item in items:
            if not isinstance(item, dict):
                continue
            raw_id = item.get("id") or item.get("problem_id") or item.get("variant_id")
            if not raw_id:
                continue
            key = _norm_key(raw_id)
            m = meta[key]
            if item.get("difficulty"):
                m.setdefault("difficulty", str(item["difficulty"]))
            if item.get("method"):
                m.setdefault("method", str(item["method"]))
            for iface_key in ("official_interface", "official_api", "external_interface"):
                fn = _extract_method_from_interface(item.get(iface_key))
                if fn:
                    m.setdefault("method", fn)
            nc = item.get("numeric_complexity_contract") or {}
            if isinstance(nc, dict):
                if nc.get("complexity_target"):
                    m.setdefault("complexity", str(nc["complexity_target"]))
                elif nc.get("time"):
                    t_val = nc["time"]
                    sp = nc.get("auxiliary_memory") or nc.get("auxiliary_space") or nc.get("space")
                    m.setdefault("complexity", f"{t_val} time" + (f", {sp} space" if sp else ""))
                if nc.get("candidate_design"):
                    m.setdefault("design", str(nc["candidate_design"]))
            for dk in ("objective_summary", "candidate_design", "summary", "algorithm"):
                if isinstance(item.get(dk), str) and item[dk].strip():
                    m.setdefault("design", item[dk].strip())

    # 2. contracts.json
    for p in sorted(authored.glob("*/contracts.json")):
        d = json.loads(p.read_text())
        probs = d.get("problems", d) if isinstance(d, dict) else {}
        rows: list[tuple[object, dict[str, object]]] = []
        if isinstance(probs, dict):
            rows = [(k, v) for k, v in probs.items() if isinstance(v, dict)]
        elif isinstance(probs, list):
            rows = [
                (v.get("variant_id") or v.get("problem_id") or v.get("id"), v)
                for v in probs
                if isinstance(v, dict) and (v.get("variant_id") or v.get("problem_id") or v.get("id"))
            ]
        for raw_k, v in rows:
            key = _norm_key(raw_k)
            m = meta[key]
            for iface_key in (
                "official_interface",
                "official_api",
                "inferred_interface",
                "external_interface",
                "interface",
            ):
                fn = _extract_method_from_interface(v.get(iface_key))
                if fn:
                    m["method"] = fn
                    break
            if v.get("complexity_target"):
                m["complexity"] = str(v["complexity_target"])
            if v.get("candidate_design"):
                m["design"] = str(v["candidate_design"])

    # 3. design.json
    for p in sorted(authored.glob("*/design.json")):
        d = json.loads(p.read_text())
        probs = d.get("problems", d) if isinstance(d, dict) else {}
        if isinstance(probs, dict):
            for k, v in probs.items():
                if not isinstance(v, dict):
                    continue
                key = _norm_key(k)
                m = meta[key]
                if v.get("complexity_target"):
                    m["complexity"] = str(v["complexity_target"])
                if v.get("candidate_design"):
                    m["design"] = str(v["candidate_design"])
        elif isinstance(probs, list):
            for v in probs:
                if not isinstance(v, dict):
                    continue
                raw_k = v.get("problem_id") or v.get("id")
                if not raw_k:
                    continue
                key = _norm_key(raw_k)
                m = meta[key]
                nc = v.get("numeric_complexity_contract") or v
                if isinstance(nc, dict):
                    if nc.get("complexity_target"):
                        m["complexity"] = str(nc["complexity_target"])
                    if nc.get("candidate_design"):
                        m["design"] = str(nc["candidate_design"])

    # 4. native-bindings.json, source-interfaces.json, source-completion*/manifest.json, delivery.original.json, batch*/manifest.json
    for p in sorted(authored.glob("*/native-bindings.json")):
        d = json.loads(p.read_text())
        for route in d.get("routes", []):
            if not isinstance(route, dict) or not route.get("id"):
                continue
            key = _norm_key(route["id"])
            fn = _extract_method_from_interface(route.get("native_api"))
            if fn:
                meta[key].setdefault("method", fn)

    for p in sorted(authored.glob("*/source-interfaces.json")):
        d = json.loads(p.read_text())
        ifaces = d.get("interfaces") or {}
        if isinstance(ifaces, dict):
            for raw_k, v in ifaces.items():
                key = _norm_key(raw_k)
                fn = _extract_method_from_interface(v)
                if fn:
                    meta[key].setdefault("method", fn)

    for p in sorted(authored.glob("source-completion*/manifest.json")):
        d = json.loads(p.read_text())
        for v in d.get("problems", []):
            if not isinstance(v, dict) or not v.get("problem_id"):
                continue
            key = _norm_key(v["problem_id"])
            if v.get("entrypoint"):
                meta[key].setdefault("method", str(v["entrypoint"]))

    for p in sorted(authored.glob("request-*/batch*/manifest.json")):
        d = json.loads(p.read_text())
        entries = d if isinstance(d, list) else (d.get("entries") or d.get("problems") or []) if isinstance(d, dict) else []
        for row in entries:
            if not isinstance(row, dict):
                continue
            raw_k = row.get("problem_id") or row.get("id")
            if not raw_k:
                continue
            key = _norm_key(raw_k)
            m = meta[key]
            if row.get("complexity"):
                m.setdefault("complexity", str(row["complexity"]))
            for dk in ("algorithm", "correctness_argument", "notes", "contract"):
                if isinstance(row.get(dk), str) and row[dk].strip():
                    m.setdefault("design", row[dk].strip())
                    break

    # 4b. study-content.json & study-notes.json
    for p in sorted(authored.glob("*/study-content.json")):
        d = json.loads(p.read_text())
        variants = d.get("variants") or d.get("problems") or {}
        if isinstance(variants, dict):
            for raw_k, v in variants.items():
                if not isinstance(v, dict):
                    continue
                key = _norm_key(raw_k)
                m = meta[key]
                if isinstance(v.get("complexity"), str) and v["complexity"].strip():
                    m.setdefault("complexity", v["complexity"].strip())
                elif isinstance(v.get("complexity"), dict):
                    c_dict = v["complexity"]
                    t_v = c_dict.get("time") or c_dict.get("target")
                    s_v = c_dict.get("space") or c_dict.get("auxiliary_space")
                    if t_v:
                        m.setdefault("complexity", f"{t_v} time" + (f", {s_v} space" if s_v else ""))
                for dk in ("approach", "candidate_design", "summary", "variantLabel"):
                    val = v.get(dk)
                    if isinstance(val, str) and val.strip():
                        m.setdefault("design", val.strip())
                        break
                    if isinstance(val, dict) and isinstance(val.get("title"), str) and val["title"].strip():
                        m.setdefault("design", val["title"].strip())
                        break
                ifaces = v.get("interfaces")
                if isinstance(ifaces, list):
                    for iface in ifaces:
                        decl = iface.get("declaration") if isinstance(iface, dict) else iface
                        if isinstance(decl, str):
                            fn = _extract_method_from_declaration(decl)
                            if fn:
                                m.setdefault("method", fn)
                                break

    for p in sorted(authored.glob("*/study-notes.json")):
        d = json.loads(p.read_text())
        probs = d.get("problems") or {}
        if isinstance(probs, dict):
            for raw_k, v in probs.items():
                if not isinstance(v, dict):
                    continue
                key = _norm_key(raw_k)
                m = meta[key]
                if v.get("complexity_target"):
                    m.setdefault("complexity", str(v["complexity_target"]))
                if v.get("candidate_design"):
                    m.setdefault("design", str(v["candidate_design"]))

    # 5. semantics/*.json (per-language or per-problem metadata)
    for p in sorted(authored.glob("*/semantics/*.json")):
        d = json.loads(p.read_text())
        pid = d.get("problem_id") or d.get("id") or d.get("official_question_frontend_id")
        lang = d.get("language", "")
        if not pid:
            match = re.match(r"^([0-9a-f]+)(?:-(python|javascript))?\.json$", p.name)
            if match:
                pid, lang = match.group(1), match.group(2) or ""
        elif not lang:
            match = re.match(r"^.+-(python|javascript)\.json$", p.name)
            if match:
                lang = match.group(1)
        if not pid:
            continue
        key = _norm_key(pid)
        m = meta[key]
        repo_rel = f"projects/algorithm_solver/{p.relative_to(ALG_ROOT).as_posix()}"
        if lang == "python":
            m["semantics_py_path"] = repo_rel
        elif lang == "javascript":
            m["semantics_js_path"] = repo_rel
        else:
            m.setdefault("semantics_shared_path", repo_rel)
        p_contract = d.get("problem_contract") if isinstance(d.get("problem_contract"), dict) else {}
        for iface_obj in (
            d.get("official_interface"),
            d.get("official_api"),
            d.get("inferred_interface"),
            d.get("external_interface"),
            d.get("interface"),
            p_contract.get("external_interface"),
            d,
        ):
            fn = _extract_method_from_interface(iface_obj)
            if fn:
                m["method"] = fn
                break
        if d.get("complexity_target"):
            m["complexity"] = str(d["complexity_target"])
        if d.get("candidate_design"):
            m["design"] = str(d["candidate_design"])
        for nc_obj in (d.get("numeric_complexity_contract"), p_contract.get("numeric_complexity_contract")):
            if isinstance(nc_obj, dict):
                if nc_obj.get("complexity_target"):
                    m.setdefault("complexity", str(nc_obj["complexity_target"]))
                elif nc_obj.get("time"):
                    t_val = nc_obj["time"]
                    sp = nc_obj.get("auxiliary_memory") or nc_obj.get("auxiliary_space") or nc_obj.get("space")
                    m.setdefault("complexity", f"{t_val} time" + (f", {sp} space" if sp else ""))
                if nc_obj.get("candidate_design"):
                    m.setdefault("design", str(nc_obj["candidate_design"]))

    # 6. study-records/*.json (resolve highest version per record ID across approach, contract, artifact)
    latest_study: dict[tuple[str, str], tuple[int, str, dict[str, object]]] = {}
    for p in sorted(authored.glob("*/study-records/*.json")):
        d = json.loads(p.read_text())
        kind = d.get("kind")
        rid = d.get("id")
        ver = int(d.get("version", 1))
        if not kind or not rid:
            continue
        k = (str(kind), str(rid))
        repo_rel = f"projects/algorithm_solver/{p.relative_to(ALG_ROOT).as_posix()}"
        if k not in latest_study or ver > latest_study[k][0]:
            latest_study[k] = (ver, repo_rel, d)

    def _study_record_key(rid: str, d: dict[str, object]) -> str:
        vid = d.get("variantId")
        if isinstance(vid, str) and vid.strip():
            return _norm_key(vid.strip())
        if isinstance(vid, dict) and vid.get("status") == "present" and vid.get("value"):
            return _norm_key(vid["value"])
        parts = rid.split(":")
        if len(parts) >= 4 and parts[1] == "hack2hire" and re.fullmatch(r"[0-9a-f]{24}", parts[3]):
            return f"hack2hire:{parts[3]}"
        return _norm_key(d.get("problemId", ""))

    for (kind, rid), (ver, repo_rel, d) in sorted(latest_study.items()):
        key = _study_record_key(rid, d)
        if not key:
            continue
        m = meta[key]
        if kind == "approach":
            m["study_path"] = repo_rel
            m["study_version"] = ver
            title_field = d.get("title")
            if isinstance(title_field, dict) and title_field.get("status") == "present" and title_field.get("value"):
                m.setdefault("design", str(title_field["value"]))
            expl_field = d.get("explanation")
            if isinstance(expl_field, dict) and expl_field.get("status") == "present" and expl_field.get("value"):
                m_comp = re.search(r"Complexity target:\s*([^\n.]+(?:\.[^\n.]*)?)", str(expl_field["value"]))
                if m_comp:
                    m.setdefault("complexity", m_comp.group(1).strip().rstrip("."))
        elif kind == "contract":
            m["contract_path"] = repo_rel
            ifaces = d.get("interfaces")
            if isinstance(ifaces, list):
                for iface in ifaces:
                    if not isinstance(iface, dict):
                        continue
                    nm_obj = iface.get("nativeMetadata")
                    nm_val = nm_obj.get("value") if isinstance(nm_obj, dict) else None
                    fn = _extract_method_from_interface(nm_val)
                    if not fn:
                        decl_obj = iface.get("declaration")
                        decl_val = decl_obj.get("value") if isinstance(decl_obj, dict) else decl_obj
                        fn = (
                            _extract_method_from_interface(decl_val)
                            if isinstance(decl_val, dict)
                            else _extract_method_from_declaration(str(decl_val or ""))
                        )
                    if fn:
                        m.setdefault("method", fn)
                        break
        elif kind == "artifact":
            cc = d.get("complexityClaims")
            if isinstance(cc, dict) and cc.get("status") == "present":
                cc_val = cc.get("value")
                if isinstance(cc_val, list) and cc_val:
                    m.setdefault("complexity", str(cc_val[0]))
                elif isinstance(cc_val, str) and cc_val.strip():
                    m.setdefault("complexity", cc_val.strip())
            nm = d.get("nativeMetadata")
            if isinstance(nm, dict) and nm.get("status") == "present" and isinstance(nm.get("value"), dict):
                nm_val = nm["value"]
                if nm_val.get("complexity_target"):
                    m.setdefault("complexity", str(nm_val["complexity_target"]))
                if nm_val.get("candidate_design"):
                    m.setdefault("design", str(nm_val["candidate_design"]))

    return meta


def _collect_corpus_metadata(slug_to_key: dict[str, str]) -> dict[str, dict[str, object]]:
    """Read metadata-only difficulty, topic tags, and reviewed objectives from findings/recovery."""
    extra: dict[str, dict[str, object]] = defaultdict(dict)

    inv_path = ALG_ROOT / "findings/library-answer-audit-v2/inventory.jsonl"
    if inv_path.exists():
        for line in inv_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            key: str | None = None
            for mem in row.get("members") or []:
                if isinstance(mem, str) and (mem.startswith("lcd:") or mem.startswith("doocs:")):
                    num = mem.split(":", 1)[1]
                    if num.isdigit():
                        key = f"leetcode:{int(num)}"
                        break
            if not key and row.get("family"):
                key = slug_to_key.get(str(row["family"]))
            if not key:
                continue
            if row.get("difficulty"):
                extra[key]["difficulty"] = str(row["difficulty"])
            if row.get("tags"):
                extra[key]["topics"] = [str(t) for t in row["tags"] if str(t).strip()]

    docs_path = (
        HERE
        / "private-recovery-20261026/qualified-sources/owner-artifacts/originals/workspace/shared/gamma-recognition-documents-102-v1-20261025-2146/documents.json"
    )
    if docs_path.exists():
        docs_data = json.loads(docs_path.read_text(encoding="utf-8"))
        for doc in docs_data.get("documents") or []:
            if not isinstance(doc, dict) or not doc.get("text_changed"):
                continue
            pkey = _norm_key(doc.get("problem_id", ""))
            txt = str(doc.get("text", ""))
            m_obj = re.search(r'Objective:\s*"([^"]+)"', txt)
            if m_obj:
                extra[pkey].setdefault("design", m_obj.group(1).strip())

    return extra


def build_records() -> list[dict[str, object]]:
    """Build deterministic problem index records across LeetCode and Hack2Hire."""
    py_by_key, js_by_key = _collect_source_paths()
    authored_meta = _collect_authored_metadata()

    # Load qualification and boundary metadata
    v25_path = (
        HERE
        / "private-recovery-20261026/qualified-sources/owner-artifacts/originals/workspace/shared/gamma-known-spec-service-v25-20261025-2217/catalogue.json"
    )
    qualified_by_key: dict[str, dict[str, str]] = {}
    if v25_path.exists():
        v25 = json.loads(v25_path.read_text())
        for row in v25.get("problems", []):
            pkey = _norm_key(row["problem_id"])
            impls = row.get("implementations", {})
            py_impl = impls.get("python", {})
            js_impl = impls.get("javascript", {})
            if py_impl.get("status") == "qualified" and js_impl.get("status") == "qualified":
                qualified_by_key[pkey] = {
                    "status": "qualified",
                    "evidence_class": str(py_impl.get("evidence_class", "")),
                }

    cls_path = (
        HERE
        / "private-recovery-20261026/qualified-sources/owner-artifacts/originals/workspace/shared/gamma-boundary-metadata-v3-20261025-1940/all4081-classification-review-candidate.json"
    )
    boundary_by_key: dict[str, str] = {}
    if cls_path.exists():
        cls_data = json.loads(cls_path.read_text())
        for row in cls_data.get("rows", []):
            boundary_by_key[_norm_key(row["problem_id"])] = str(row.get("status", ""))

    dev66_path = HERE / "development-66-20261029-v1/acceptance.json"
    dev66_keys: set[str] = set()
    if dev66_path.exists():
        dev66 = json.loads(dev66_path.read_text())
        for ext_item in dev66.get("studyExtensions", []):
            cohort_name = ext_item.get("cohort")
            if not cohort_name:
                continue
            c_path = HERE / "authored" / cohort_name / "contracts.json"
            if c_path.exists():
                c_data = json.loads(c_path.read_text())
                probs = c_data.get("problems", {})
                if isinstance(probs, dict):
                    for pid in probs.keys():
                        dev66_keys.add(_norm_key(pid))
                elif isinstance(probs, list):
                    for row in probs:
                        if isinstance(row, dict) and (row.get("problem_id") or row.get("id")):
                            dev66_keys.add(_norm_key(row.get("problem_id") or row.get("id")))

    lc_meta_path = REPO_ROOT / "projects/question_bank/hack2hire/leetcode-metadata.json"
    lc_meta = json.loads(lc_meta_path.read_text())
    slug_to_key = {
        str(item["slug"]): f"leetcode:{int(item['id'])}"
        for item in lc_meta
        if item.get("slug") and item.get("id")
    }
    corpus_meta = _collect_corpus_metadata(slug_to_key)

    # Pre-scan Hack2Hire bank to collect related_hack2hire and company overlaps for LeetCode IDs
    bank_path = REPO_ROOT / "projects/question_bank/hack2hire/bank.json"
    desc_path = REPO_ROOT / "projects/question_bank/hack2hire/descriptions.json"
    bank_data = json.loads(bank_path.read_text())
    desc_by_post: dict[str, dict[str, object]] = {}
    if desc_path.exists():
        for r in json.loads(desc_path.read_text()).get("records", []):
            if r.get("source_post_id"):
                desc_by_post[str(r["source_post_id"])] = r

    lc_to_h2h: dict[str, list[str]] = defaultdict(list)
    lc_to_companies: dict[str, list[str]] = defaultdict(list)
    for group in bank_data.get("records", []):
        post_id = str(group.get("source_post_id", ""))
        group_uid = str(group.get("uid", f"hack2hire:{post_id}"))
        g_companies = [str(c) for c in (group.get("companies") or [])]
        desc_rec = desc_by_post.get(post_id, {})
        for cand in (group.get("leetcode_overlap") or {}).get("candidates", []):
            if isinstance(cand, dict) and cand.get("leetcode_id"):
                lck = f"leetcode:{cand['leetcode_id']}"
                if group_uid not in lc_to_h2h[lck]:
                    lc_to_h2h[lck].append(group_uid)
                if cand.get("match_type") == "exact_title":
                    for c in g_companies:
                        if c not in lc_to_companies[lck]:
                            lc_to_companies[lck].append(c)
        for rel in desc_rec.get("source_leetcode_relationships", []) or []:
            if isinstance(rel, dict) and rel.get("leetcode_id"):
                lck = f"leetcode:{rel['leetcode_id']}"
                if group_uid not in lc_to_h2h[lck]:
                    lc_to_h2h[lck].append(group_uid)
                for c in g_companies:
                    if c not in lc_to_companies[lck]:
                        lc_to_companies[lck].append(c)

    records: list[dict[str, object]] = []

    # 1. Official LeetCode problems (sorted 1..4096)
    for item in sorted(lc_meta, key=lambda x: int(x["id"])):
        pid_int = int(item["id"])
        key = f"leetcode:{pid_int}"
        py_list = py_by_key.get(key, [])
        js_list = js_by_key.get(key, [])
        m = authored_meta.get(key, {})
        cm = corpus_meta.get(key, {})

        py_path = py_list[0][2] if py_list else None
        js_path = js_list[0][2] if js_list else None
        tier = py_list[0][0] if py_list else (js_list[0][0] if js_list else "missing")

        b_status = boundary_by_key.get(key, "outside-4081-freeze")
        q_info = qualified_by_key.get(key)
        if q_info:
            status = "qualified"
            evidence_class = q_info["evidence_class"]
        elif key in dev66_keys:
            status = "development-executed"
            evidence_class = "bounded-development-66"
        elif py_path and js_path:
            if tier == "authored":
                status = "authored-candidate"
            elif tier == "staged":
                status = "staged-candidate"
            elif tier == "candidates":
                status = "candidate-import"
            elif tier == "literals":
                status = "paired-authoring"
            elif tier == "quarantined-archival":
                status = "quarantined-archival"
            else:
                status = "run-snapshot"
            evidence_class = None
        else:
            if b_status in ("historical_reserved382", "final100_exact_id_reserved"):
                status = "missing-reserved"
            elif b_status == "unresolved_global_identity_alias_metadata_only":
                status = "missing-non-dual-or-unmapped"
            else:
                status = "missing"
            evidence_class = None

        sem_py = m.get("semantics_py_path")
        sem_js = m.get("semantics_js_path")
        sem_shared = m.get("semantics_shared_path")
        diff_val = (
            m.get("difficulty")
            or cm.get("difficulty")
            or _infer_cohort_difficulty(py_path or js_path)
        )
        topics_val = list(cm.get("topics") or [])
        records.append(
            {
                "key": key,
                "source": "leetcode",
                "id": str(pid_int),
                "group_id": None,
                "category": "coding",
                "slug": item.get("slug", ""),
                "title": item.get("title", ""),
                "difficulty": diff_val,
                "paid_only": bool(item.get("paid_only", False)),
                "url": item.get("url"),
                "method": m.get("method"),
                "status": status,
                "boundary_status": b_status,
                "evidence_class": evidence_class,
                "tier": tier,
                "py_path": py_path,
                "js_path": js_path,
                "alternate_py_paths": [x[2] for x in py_list[1:] if x[0] != "run-snapshot"],
                "alternate_js_paths": [x[2] for x in js_list[1:] if x[0] != "run-snapshot"],
                "semantics_path": sem_py or sem_js or sem_shared,
                "semantics_py_path": sem_py or sem_shared,
                "semantics_js_path": sem_js or sem_shared,
                "study_path": m.get("study_path"),
                "contract_path": m.get("contract_path"),
                "companies": lc_to_companies.get(key, []),
                "topics": topics_val,
                "related_leetcode": [],
                "related_hack2hire": lc_to_h2h.get(key, []),
                "complexity": m.get("complexity"),
                "design": m.get("design") or cm.get("design"),
            }
        )

    # 2. Hack2Hire question bank entries and variants
    for group in bank_data.get("records", []):
        post_id = str(group.get("source_post_id", ""))
        group_uid = str(group.get("uid", f"hack2hire:{post_id}"))
        category = str(group.get("category", "coding"))
        title = str(group.get("title", ""))
        slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
        companies = [str(c) for c in (group.get("companies") or [])]
        topics = [str(t) for t in (group.get("topics") or group.get("source_algorithm_tags") or [])]
        diff = str(group["source_difficulty"]) if group.get("source_difficulty") is not None else None
        url = group.get("url")

        desc_rec = desc_by_post.get(post_id, {})
        related_lc: list[str] = []
        for cand in (group.get("leetcode_overlap") or {}).get("candidates", []):
            if isinstance(cand, dict) and cand.get("leetcode_id"):
                related_lc.append(f"leetcode:{cand['leetcode_id']}")
            elif isinstance(cand, str):
                related_lc.append(cand)
        for rel in desc_rec.get("source_leetcode_relationships", []) or []:
            if isinstance(rel, dict) and rel.get("leetcode_id"):
                val = f"leetcode:{rel['leetcode_id']}"
                if val not in related_lc:
                    related_lc.append(val)

        variants = group.get("variants") or [{"id": post_id, "ordinal": 1, "group_only": True}]
        for var in variants:
            vid = str(var.get("id", post_id))
            ordinal = int(var.get("ordinal", 1))
            key = f"hack2hire:{vid}"
            py_list = py_by_key.get(key, [])
            js_list = js_by_key.get(key, [])
            m = authored_meta.get(key, {})

            py_path = py_list[0][2] if py_list else None
            js_path = js_list[0][2] if js_list else None
            tier = py_list[0][0] if py_list else (js_list[0][0] if js_list else "metadata-only")

            if py_path and js_path:
                status = "authored-inferred-spec"
            else:
                status = "question-bank-metadata"

            var_title = title if len(variants) == 1 else f"{title} (Variant {ordinal})"
            var_slug = slug if len(variants) == 1 else f"{slug}-v{ordinal}"
            sem_py = m.get("semantics_py_path")
            sem_js = m.get("semantics_js_path")
            sem_shared = m.get("semantics_shared_path")

            desc_obj = desc_rec.get("description") if isinstance(desc_rec.get("description"), dict) else {}
            excerpt = str(desc_obj.get("excerpt") or "").strip()
            design_val = m.get("design") or (f"Public preview: {excerpt}" if excerpt else None)

            records.append(
                {
                    "key": key,
                    "source": "hack2hire",
                    "id": vid,
                    "group_id": group_uid,
                    "category": category,
                    "slug": var_slug,
                    "title": var_title,
                    "difficulty": m.get("difficulty") or diff,
                    "paid_only": False,
                    "url": url,
                    "method": m.get("method"),
                    "status": status,
                    "boundary_status": "hack2hire-public-preview",
                    "evidence_class": None,
                    "tier": tier,
                    "py_path": py_path,
                    "js_path": js_path,
                    "alternate_py_paths": [x[2] for x in py_list[1:]],
                    "alternate_js_paths": [x[2] for x in js_list[1:]],
                    "semantics_path": sem_py or sem_js or sem_shared,
                    "semantics_py_path": sem_py or sem_shared,
                    "semantics_js_path": sem_js or sem_shared,
                    "study_path": m.get("study_path"),
                    "contract_path": m.get("contract_path"),
                    "companies": companies,
                    "topics": topics,
                    "related_leetcode": related_lc,
                    "related_hack2hire": [],
                    "complexity": m.get("complexity"),
                    "design": design_val,
                }
            )

    return records


def render_tsv(records: list[dict[str, object]]) -> str:
    lines = ["\t".join(TSV_COLUMNS)]
    for rec in records:
        row = [_clean_tsv_field(rec.get(col)) for col in TSV_COLUMNS]
        lines.append("\t".join(row))
    return "\n".join(lines) + "\n"


def render_jsonl(records: list[dict[str, object]]) -> str:
    lines = [
        json.dumps(rec, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
        for rec in records
    ]
    return "\n".join(lines) + "\n"


def write_index_files() -> list[dict[str, object]]:
    records = build_records()
    TSV_PATH.write_text(render_tsv(records), encoding="utf-8")
    JSONL_PATH.write_text(render_jsonl(records), encoding="utf-8")
    return records


def load_records() -> list[dict[str, object]]:
    if JSONL_PATH.exists():
        return [
            json.loads(line)
            for line in JSONL_PATH.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
    return build_records()


def search_records(
    records: list[dict[str, object]],
    queries: list[str],
    *,
    source: str | None = None,
    category: str | None = None,
    status: str | None = None,
    company: str | None = None,
    topic: str | None = None,
) -> list[dict[str, object]]:
    filtered = records
    if source:
        filtered = [r for r in filtered if r.get("source") == source]
    if category:
        filtered = [r for r in filtered if r.get("category") == category]
    if status:
        filtered = [r for r in filtered if status.lower() in str(r.get("status", "")).lower()]
    if company:
        c_low = company.lower()
        filtered = [
            r for r in filtered if any(c_low in str(c).lower() for c in (r.get("companies") or []))
        ]
    if topic:
        t_low = topic.lower()
        filtered = [
            r for r in filtered if any(t_low in str(t).lower() for t in (r.get("topics") or []))
        ]

    if not queries:
        return filtered

    scored: list[tuple[int, int, dict[str, object]]] = []
    for idx, rec in enumerate(filtered):
        best_rank: int | None = None
        for q in queries:
            q_str = q.strip()
            q_low = q_str.lower()
            norm_q = _norm_key(q_str).lower()

            key_low = str(rec.get("key", "")).lower()
            id_low = str(rec.get("id", "")).lower()
            group_low = str(rec.get("group_id") or "").lower()
            slug_low = str(rec.get("slug", "")).lower()
            title_low = str(rec.get("title", "")).lower()
            method_low = str(rec.get("method") or "").lower()
            design_low = str(rec.get("design") or "").lower()
            comp_str = " ".join(str(c) for c in (rec.get("companies") or [])).lower()
            topic_str = " ".join(str(t) for t in (rec.get("topics") or [])).lower()
            rel_str = " ".join(str(x) for x in (rec.get("related_leetcode") or [])).lower()

            rank: int | None = None
            if q_low in (key_low, id_low, group_low) or norm_q in (key_low, group_low):
                rank = 0
            elif q_low == slug_low or (method_low and q_low == method_low):
                rank = 1
            elif q_low == title_low:
                rank = 2
            elif q_low in title_low or q_low in slug_low or (method_low and q_low in method_low):
                rank = 3
            elif norm_q in rel_str.split():
                rank = 4
            elif q_low in design_low or q_low in comp_str or q_low in topic_str:
                rank = 5

            if rank is not None and (best_rank is None or rank < best_rank):
                best_rank = rank

        if best_rank is not None:
            scored.append((best_rank, idx, rec))

    scored.sort(key=lambda x: (x[0], x[1]))
    return [x[2] for x in scored]


def compute_stats(records: list[dict[str, object]]) -> dict[str, object]:
    lc = [r for r in records if r["source"] == "leetcode"]
    h2h = [r for r in records if r["source"] == "hack2hire"]
    h2h_coding = [r for r in h2h if r["category"] == "coding"]
    return {
        "total_records": len(records),
        "leetcode": {
            "total": len(lc),
            "with_both_py_and_js": sum(1 for r in lc if r["py_path"] and r["js_path"]),
            "with_difficulty": sum(1 for r in lc if r["difficulty"]),
            "with_topics": sum(1 for r in lc if r["topics"]),
            "with_method": sum(1 for r in lc if r["method"]),
            "with_semantics": sum(1 for r in lc if r["semantics_path"]),
            "with_study_record": sum(1 for r in lc if r["study_path"]),
            "with_complexity": sum(1 for r in lc if r["complexity"]),
            "with_design_summary": sum(1 for r in lc if r["design"]),
            "by_status": dict(Counter(str(r["status"]) for r in lc)),
            "by_tier": dict(Counter(str(r["tier"]) for r in lc)),
        },
        "hack2hire": {
            "total": len(h2h),
            "coding_variants": len(h2h_coding),
            "coding_with_both_py_and_js": sum(
                1 for r in h2h_coding if r["py_path"] and r["js_path"]
            ),
            "coding_with_method": sum(1 for r in h2h_coding if r["method"]),
            "coding_with_complexity": sum(1 for r in h2h_coding if r["complexity"]),
            "coding_with_design_summary": sum(1 for r in h2h_coding if r["design"]),
            "coding_with_study_record": sum(1 for r in h2h_coding if r["study_path"]),
            "coding_with_contract_record": sum(1 for r in h2h_coding if r.get("contract_path")),
            "by_category": dict(Counter(str(r["category"]) for r in h2h)),
            "by_status": dict(Counter(str(r["status"]) for r in h2h)),
        },
    }


def _format_human_row(rec: dict[str, object]) -> str:
    lines = [
        f"[{rec['key']}] {rec['title']}  (category={rec['category']}, status={rec['status']}, tier={rec['tier']})"
    ]
    meta_parts = [f"slug={rec['slug']}"]
    if rec.get("method"):
        meta_parts.append(f"method={rec['method']}")
    if rec.get("difficulty"):
        meta_parts.append(f"difficulty={rec['difficulty']}")
    if rec.get("complexity"):
        meta_parts.append(f"complexity={rec['complexity']}")
    lines.append("  " + " | ".join(meta_parts))
    if rec.get("py_path"):
        lines.append(f"  py:        {rec['py_path']}")
    if rec.get("js_path"):
        lines.append(f"  js:        {rec['js_path']}")
    if rec.get("semantics_path"):
        lines.append(f"  semantics: {rec['semantics_path']}")
    if rec.get("study_path"):
        lines.append(f"  study:     {rec['study_path']}")
    if rec.get("companies"):
        lines.append(f"  companies: {', '.join(str(x) for x in rec['companies'])}")
    if rec.get("topics"):
        lines.append(f"  topics:    {', '.join(str(x) for x in rec['topics'])}")
    if rec.get("design"):
        lines.append(f"  design:    {rec['design']}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Search or rebuild the canonical Gamma LeetCode & Hack2Hire problem index."
    )
    parser.add_argument(
        "queries",
        nargs="*",
        help="Problem ID (e.g. 286, leetcode:286, 24-hex), slug, method name, or title/design keyword.",
    )
    parser.add_argument("--source", choices=("leetcode", "hack2hire"), help="Filter by source.")
    parser.add_argument(
        "--category",
        choices=("coding", "sql", "system-design", "ml-system-design", "object-oriented-design"),
        help="Filter by problem category.",
    )
    parser.add_argument("--status", help="Substring filter on status (e.g. qualified, authored).")
    parser.add_argument("--company", help="Substring filter on reported company.")
    parser.add_argument("--topic", help="Substring filter on topic tag.")
    parser.add_argument("--limit", type=int, default=20, help="Maximum matches to print (default: 20).")
    parser.add_argument("--json", action="store_true", help="Emit JSON output.")
    parser.add_argument("--stats", action="store_true", help="Print index coverage statistics.")
    parser.add_argument(
        "--write",
        action="store_true",
        help="Rebuild PROBLEM_INDEX.tsv and PROBLEM_INDEX.jsonl from repository metadata.",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Verify PROBLEM_INDEX.tsv and PROBLEM_INDEX.jsonl match current repository metadata.",
    )
    args = parser.parse_args(argv)

    if args.write:
        records = write_index_files()
        if args.json:
            print(json.dumps(compute_stats(records), indent=2, sort_keys=True))
        else:
            print(f"Wrote {len(records)} records to {TSV_PATH.name} and {JSONL_PATH.name}.")
        return 0

    if args.check:
        records = build_records()
        expected_tsv = render_tsv(records)
        expected_jsonl = render_jsonl(records)
        if not TSV_PATH.exists() or not JSONL_PATH.exists():
            print("Index files missing; run with --write.", file=sys.stderr)
            return 1
        if (
            TSV_PATH.read_text(encoding="utf-8") != expected_tsv
            or JSONL_PATH.read_text(encoding="utf-8") != expected_jsonl
        ):
            print("Index files out of date; run with --write.", file=sys.stderr)
            return 1
        print(f"OK: {len(records)} index records verified up to date.")
        return 0

    records = load_records()
    if args.stats:
        stats = compute_stats(records)
        print(json.dumps(stats, indent=2, sort_keys=True))
        return 0

    matches = search_records(
        records,
        args.queries,
        source=args.source,
        category=args.category,
        status=args.status,
        company=args.company,
        topic=args.topic,
    )
    shown = matches[: args.limit] if args.limit and args.limit > 0 else matches
    if args.json:
        print(
            json.dumps(
                {"total_matches": len(matches), "shown": len(shown), "results": shown},
                indent=2,
                ensure_ascii=False,
            )
        )
    else:
        print(f"Matches: {len(matches)} (showing {len(shown)})")
        for rec in shown:
            print(_format_human_row(rec))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
