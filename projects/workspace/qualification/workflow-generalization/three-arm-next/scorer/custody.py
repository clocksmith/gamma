#!/usr/bin/env python3
"""Custodian sealing, commitment, shape-validation, and leak-audit CLI for Dot (clocksmith/deco#88).

Implements ouroboros/docs/private/gamma/gammatron-holdout-kit-20261124/{custody-on-dot.md,case-template.json,label-rubric.md}:
  - `canary`: writes `canary.txt` with a fresh random UUIDv4 and emits its SHA-256 hash.
  - `validate-submission`: validates `families.json`, `training-examples.json`,
    `blind-recipes-*.json`, and `answer-key.json` for schema compliance, no leaked label hints
    in recipes or routeIds, no training `failureId` leaked into unseen holdout (unless marked
    `coveredFailure: true`), and counts independent `failureId`s (`n >= 99`, `<= 60` per app).
  - `seal`: injects a per-batch canary GUID into top-level `about`, generates 32-byte CSPRNG
    salts for each file and each individual `answer-key.json` route entry, writes `MANIFEST.tsv`
    and `salts.json` into the sealed store, and outputs the public log commitment JSON.
  - `verify`: recomputes every file and route-entry salted SHA-256 commitment after publication.
  - `leak-scan`: scans builder session transcripts, agent-bus logs, and frozen artifacts for
    canary GUIDs, unseen `routeId`s, and `failureReason`s, flagging any hit so the run is
    downgraded to `Development evaluation only`.

Python 3.10+, zero external dependencies.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import secrets
import sys
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ID_RE = re.compile(r'^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$')
LEAKY_ID_RE = re.compile(r'(valid|invalid|hold|draft|mismatch|wrong|stop|reuse|repair|cosmetic|undecidable)', re.IGNORECASE)
FORBIDDEN_PUBLIC_FAMILY_WORDS = (
    'legal-hold',
    'example-quotation-covers-order',
    'template-format-only',
)
VALID_KINDS = {
    'reuse-valid',
    'needs-repair',
    'must-stop',
    'cosmetic-change',
    'fact-unavailable',
    'no-basis',
}


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def salted_commitment(salt_hex: str, payload: bytes) -> str:
    return hashlib.sha256(bytes.fromhex(salt_hex) + payload).hexdigest()


def canonical_bytes(obj: Any) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode('utf-8')


def normalize_reason(text: str) -> str:
    cleaned = re.sub(r'\b\d+(?:\.\d+)?\b', '<num>', text.lower().strip())
    cleaned = re.sub(r'\s+', ' ', cleaned)
    return cleaned.rstrip('.')


def cmd_canary(sealed_dir: Path) -> dict[str, Any]:
    sealed_dir.mkdir(parents=True, exist_ok=True)
    os.chmod(sealed_dir, 0o700)
    guid = f'gammatron-canary-{uuid.uuid4()}'
    canary_file = sealed_dir / 'canary.txt'
    canary_file.write_text(guid + '\n', encoding='utf-8')
    os.chmod(canary_file, 0o600)
    return {
        'canaryPath': str(canary_file),
        'canarySha256': sha256_bytes(canary_file.read_bytes()),
        'createdAt': datetime.now(timezone.utc).isoformat(),
    }


def validate_recipe_minimal(recipe: dict[str, Any], check_opaque_id: bool = True) -> list[str]:
    problems: list[str] = []
    rid = recipe.get('routeId')
    fid = recipe.get('familyId')
    if not isinstance(rid, str) or not ID_RE.match(rid):
        problems.append(f'invalid routeId: {rid!r}')
    elif check_opaque_id and LEAKY_ID_RE.search(rid):
        problems.append(f'routeId {rid!r} hints at label/kind; routeIds must be opaque')
    if not isinstance(fid, str) or not ID_RE.match(fid):
        problems.append(f'{rid}: invalid familyId {fid!r}')
    elif any(tok in fid.lower() for tok in FORBIDDEN_PUBLIC_FAMILY_WORDS):
        problems.append(f'{rid}: familyId {fid!r} reuses a forbidden public/template family')
    for forbidden in ('valid', 'label', 'reason', 'kind', 'failureId', 'failureReason'):
        if forbidden in recipe:
            problems.append(f'{rid}: recipe must not carry label field {forbidden!r}')
    setup = recipe.get('setup')
    if not isinstance(setup, list) or not (1 <= len(setup) <= 24):
        problems.append(f'{rid}: setup must hold 1..24 steps')
    return problems


def validate_submission_dir(
    sub_dir: Path,
    *,
    require_full_floor: bool = False,
    max_per_app: int = 60,
) -> dict[str, Any]:
    problems: list[str] = []
    families_path = sub_dir / 'families.json'
    train_path = sub_dir / 'training-examples.json'
    key_path = sub_dir / 'answer-key.json'
    blind_paths = sorted(sub_dir.glob('blind-recipes-*.json'))

    for req in (families_path, train_path, key_path):
        if not req.exists():
            problems.append(f'missing required file: {req.name}')
    if not blind_paths:
        problems.append('missing blind-recipes-*.json files')
    if problems:
        return {'ok': False, 'problems': problems}

    families_doc = json.loads(families_path.read_text(encoding='utf-8'))
    train_doc = json.loads(train_path.read_text(encoding='utf-8'))
    key_doc = json.loads(key_path.read_text(encoding='utf-8'))
    blind_docs = [(p.name, json.loads(p.read_text(encoding='utf-8'))) for p in blind_paths]

    family_apps: dict[str, str] = {}
    for fam in families_doc.get('families', []):
        fid = fam.get('familyId')
        app = fam.get('application')
        if not fid or app not in ('openproject', 'erpnext'):
            problems.append(f'family {fid!r} must declare application openproject or erpnext')
            continue
        if any(tok in fid.lower() for tok in FORBIDDEN_PUBLIC_FAMILY_WORDS):
            problems.append(f'family {fid!r} reuses forbidden template/public family name')
        family_apps[fid] = app
        problems.extend(validate_recipe_minimal(fam.get('disclosedExample', {}), check_opaque_id=False))

    train_failure_ids: set[str] = set()
    train_by_family: dict[str, list[dict[str, Any]]] = {}
    for entry in train_doc.get('families', []):
        fid = entry.get('familyId')
        examples = entry.get('examples', [])
        train_by_family[fid] = examples
        pos = sum(1 for e in examples if e.get('valid') is True)
        neg = sum(1 for e in examples if e.get('valid') is False)
        if pos < 2 or neg < 2:
            problems.append(f'training family {fid!r} needs >=2 valid and >=2 invalid examples (got {pos}, {neg})')
        for ex in examples:
            problems.extend(validate_recipe_minimal(ex.get('recipe', {}), check_opaque_id=False))
            if ex.get('valid') is False:
                tfid = ex.get('failureId')
                if not tfid:
                    problems.append(f'training invalid example in {fid!r} lacks failureId')
                else:
                    train_failure_ids.add(tfid)

    for fid in family_apps:
        if fid not in train_by_family:
            problems.append(f'family {fid!r} missing from training-examples.json')

    routes_key = key_doc.get('routes', {})
    seen_routes: set[str] = set()
    invalid_fids_by_app: dict[str, set[str]] = {'openproject': set(), 'erpnext': set()}
    reason_to_fid: dict[str, str] = {}
    duplicate_reason_merges: list[tuple[str, str, str]] = []
    valid_sure_count = 0
    covered_training_failures = 0
    undecidable_by_app: dict[str, int] = {'openproject': 0, 'erpnext': 0}

    for fname, bdoc in blind_docs:
        recipes = bdoc.get('recipes', [])
        if len(recipes) > 64:
            problems.append(f'{fname}: exceeds 64 recipes per file')
        for r in recipes:
            rid = r.get('routeId')
            if rid in seen_routes:
                problems.append(f'{fname}: duplicate routeId {rid!r}')
            seen_routes.add(rid)
            problems.extend(validate_recipe_minimal(r, check_opaque_id=True))
            meta = routes_key.get(rid)
            if not isinstance(meta, dict):
                problems.append(f'{fname}: route {rid!r} missing from answer-key.json')
                continue
            app = meta.get('application')
            if app not in ('openproject', 'erpnext'):
                problems.append(f'{rid}: invalid application {app!r}')
                continue
            if meta.get('kind') not in VALID_KINDS:
                problems.append(f'{rid}: invalid kind {meta.get("kind")!r}')
            if meta.get('decidable') is False:
                undecidable_by_app[app] += 1
            if meta.get('confidence', 'sure') != 'sure':
                continue
            if meta.get('valid') is True:
                valid_sure_count += 1
            elif meta.get('valid') is False:
                fid = meta.get('failureId')
                freason = meta.get('failureReason')
                if not fid or not freason:
                    problems.append(f'{rid}: invalid case requires failureId and failureReason')
                    continue
                if fid in train_failure_ids:
                    if meta.get('coveredFailure') is True:
                        covered_training_failures += 1
                    else:
                        problems.append(f'{rid}: failureId {fid!r} appears in training-examples.json without coveredFailure=true')
                norm = normalize_reason(freason)
                if norm in reason_to_fid and reason_to_fid[norm] != fid:
                    duplicate_reason_merges.append((fid, reason_to_fid[norm], norm))
                else:
                    reason_to_fid[norm] = fid
                invalid_fids_by_app[app].add(reason_to_fid.get(norm, fid))

    all_merged_fids = set().union(*invalid_fids_by_app.values())
    for app, fids in invalid_fids_by_app.items():
        if len(fids) > max_per_app:
            problems.append(f'{app}: {len(fids)} independent invalid failureIds exceeds per-app cap {max_per_app}')
    if require_full_floor:
        if len(all_merged_fids) < 99:
            problems.append(f'independent invalid failureIds={len(all_merged_fids)} is below floor 99')
        if valid_sure_count < 99:
            problems.append(f'valid sure count={valid_sure_count} is below floor 99')
        for app, count in undecidable_by_app.items():
            if count < 1:
                problems.append(f'{app}: requires at least one undecidable case')

    return {
        'ok': not problems,
        'problems': problems,
        'counts': {
            'totalUnseenRoutes': len(seen_routes),
            'validSureCount': valid_sure_count,
            'independentInvalidFailureIds': len(all_merged_fids),
            'byApplicationInvalidFailureIds': {k: len(v) for k, v in invalid_fids_by_app.items()},
            'coveredTrainingFailures': covered_training_failures,
            'mergedDuplicateFailureReasons': duplicate_reason_merges,
            'undecidableByApp': undecidable_by_app,
        },
    }


def seal_submission(sub_dir: Path, sealed_dir: Path, author_pseudonym: str = 'A1') -> dict[str, Any]:
    check = validate_submission_dir(sub_dir, require_full_floor=False)
    if not check['ok']:
        raise ValueError(f"refusing to seal invalid submission: {check['problems']}")

    sealed_dir.mkdir(parents=True, exist_ok=True)
    os.chmod(sealed_dir, 0o700)
    batch_canary = f'gammatron-batch-canary-{uuid.uuid4()}'
    now = datetime.now(timezone.utc).isoformat()

    json_files = sorted(sub_dir.glob('*.json'))
    salts: dict[str, Any] = {'files': {}, 'answerKeyRoutes': {}, 'batchCanaryGuid': batch_canary}
    manifest_rows: list[str] = ['path\tsize\tcommitment\tsubmittedAt\tauthor']
    file_commitments: dict[str, str] = {}

    for src in json_files:
        doc = json.loads(src.read_text(encoding='utf-8'))
        existing_about = doc.get('about')
        if isinstance(existing_about, list):
            doc['about'] = [*existing_about, batch_canary]
        else:
            doc['about'] = [batch_canary]
        out_bytes = (json.dumps(doc, indent=2, ensure_ascii=False) + '\n').encode('utf-8')
        dst = sealed_dir / src.name
        dst.write_bytes(out_bytes)
        os.chmod(dst, 0o600)

        salt_hex = secrets.token_hex(32)
        comm = salted_commitment(salt_hex, out_bytes)
        salts['files'][src.name] = salt_hex
        file_commitments[src.name] = comm
        manifest_rows.append(f'{src.name}\t{len(out_bytes)}\t{comm}\t{now}\t{author_pseudonym}')

        if src.name == 'answer-key.json':
            for rid, entry in sorted(doc.get('routes', {}).items()):
                r_salt = secrets.token_hex(32)
                salts['answerKeyRoutes'][rid] = {
                    'salt': r_salt,
                    'commitment': salted_commitment(r_salt, canonical_bytes(entry)),
                }

    manifest_file = sealed_dir / 'MANIFEST.tsv'
    manifest_file.write_text('\n'.join(manifest_rows) + '\n', encoding='utf-8')
    os.chmod(manifest_file, 0o600)

    salts_file = sealed_dir / 'salts.json'
    salts_file.write_text(json.dumps(salts, indent=2) + '\n', encoding='utf-8')
    os.chmod(salts_file, 0o600)

    canary_txt = sealed_dir / 'canary.txt'
    store_canary_sha = sha256_bytes(canary_txt.read_bytes()) if canary_txt.exists() else None

    public_log_entry = {
        'schema': 'gammatron-custody-commitment/v1',
        'committedAt': now,
        'authorPseudonym': author_pseudonym,
        'storeCanarySha256': store_canary_sha,
        'batchCanarySha256': sha256_bytes(batch_canary.encode('utf-8')),
        'counts': check['counts'],
        'fileCommitments': file_commitments,
        'answerKeyRouteCommitments': {
            rid: v['commitment'] for rid, v in salts['answerKeyRoutes'].items()
        },
    }
    (sealed_dir / 'public-commitment.json').write_text(
        json.dumps(public_log_entry, indent=2) + '\n', encoding='utf-8'
    )
    return public_log_entry


def verify_sealed_store(sealed_dir: Path) -> dict[str, Any]:
    salts = json.loads((sealed_dir / 'salts.json').read_text(encoding='utf-8'))
    pub = json.loads((sealed_dir / 'public-commitment.json').read_text(encoding='utf-8'))
    problems: list[str] = []

    for fname, expected in pub['fileCommitments'].items():
        raw = (sealed_dir / fname).read_bytes()
        got = salted_commitment(salts['files'][fname], raw)
        if got != expected:
            problems.append(f'file commitment mismatch on {fname}')

    key_doc = json.loads((sealed_dir / 'answer-key.json').read_text(encoding='utf-8'))
    for rid, expected in pub['answerKeyRouteCommitments'].items():
        entry = key_doc['routes'].get(rid)
        got = salted_commitment(salts['answerKeyRoutes'][rid]['salt'], canonical_bytes(entry))
        if got != expected:
            problems.append(f'answer-key route commitment mismatch on {rid}')

    return {'ok': not problems, 'problems': problems, 'filesVerified': len(pub['fileCommitments'])}


def leak_scan(sealed_dir: Path, scan_paths: list[Path]) -> dict[str, Any]:
    needles: dict[str, str] = {}
    canary_txt = sealed_dir / 'canary.txt'
    if canary_txt.exists():
        val = canary_txt.read_text(encoding='utf-8').strip()
        if val:
            needles[val] = 'store-canary'
    salts_file = sealed_dir / 'salts.json'
    if salts_file.exists():
        salts = json.loads(salts_file.read_text(encoding='utf-8'))
        bc = salts.get('batchCanaryGuid')
        if bc:
            needles[bc] = 'batch-canary'
    key_file = sealed_dir / 'answer-key.json'
    if key_file.exists():
        routes = json.loads(key_file.read_text(encoding='utf-8')).get('routes', {})
        for rid, meta in routes.items():
            needles[rid] = f'unseen-routeId:{rid}'
            fr = meta.get('failureReason')
            if isinstance(fr, str) and len(fr.strip()) >= 16:
                needles[fr.strip()] = f'failureReason:{rid}'

    hits: list[dict[str, str]] = []
    files_scanned = 0
    for target in scan_paths:
        candidates = [target] if target.is_file() else sorted(p for p in target.rglob('*') if p.is_file())
        for fp in candidates:
            files_scanned += 1
            text = fp.read_text(encoding='utf-8', errors='replace')
            for needle, kind in needles.items():
                if needle in text:
                    hits.append({'file': str(fp), 'kind': kind, 'matched': needle[:64]})

    return {
        'clean': len(hits) == 0,
        'filesScanned': files_scanned,
        'needlesChecked': len(needles),
        'hits': hits,
        'classification': 'blind-holdout-eligible' if not hits else 'Development evaluation only: sealed needle found in builder context',
    }


def selftest() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        sub = root / 'submission'
        sealed = root / 'sealed'
        builder = root / 'builder'
        sub.mkdir()
        builder.mkdir()

        canary_info = cmd_canary(sealed)
        assert len(canary_info['canarySha256']) == 64

        op_recipe = lambda rid, hrs: {
            'routeId': rid,
            'familyId': 'fam-alpha',
            'entryBranch': 'direct',
            'setup': [{'as': 'author', 'method': 'POST', 'path': '/api/v3/projects/p/work_packages', 'body': {'subject': 'Item {tag}'}, 'save': {'w': 'id'}}],
            'target': {'workPackage': '{w}', 'project': 'p'},
            'write': {'workHours': hrs},
        }
        (sub / 'families.json').write_text(json.dumps({
            'families': [{'familyId': 'fam-alpha', 'application': 'openproject', 'policy': 'Plain rule.', 'disclosedExample': op_recipe('op-disc-1', 12)}]
        }), encoding='utf-8')
        (sub / 'training-examples.json').write_text(json.dumps({
            'families': [{
                'familyId': 'fam-alpha',
                'examples': [
                    {'valid': True, 'why': 'ok 1', 'recipe': op_recipe('op-tr-1', 10)},
                    {'valid': True, 'why': 'ok 2', 'recipe': op_recipe('op-tr-2', 14)},
                    {'valid': False, 'why': 'no 1', 'failureId': 'tr-f1', 'recipe': op_recipe('op-tr-3', 10)},
                    {'valid': False, 'why': 'no 2', 'failureId': 'tr-f2', 'recipe': op_recipe('op-tr-4', 14)},
                ],
            }]
        }), encoding='utf-8')
        (sub / 'blind-recipes-openproject-a.json').write_text(json.dumps({
            'recipes': [op_recipe('op-k7f2', 16), op_recipe('op-m2x8', 16), op_recipe('op-q9z1', 20)]
        }), encoding='utf-8')
        (sub / 'answer-key.json').write_text(json.dumps({
            'routes': {
                'op-k7f2': {
                    'valid': False, 'why': 'Parent item locked.', 'application': 'openproject',
                    'familyId': 'fam-alpha', 'kind': 'must-stop', 'decidable': True,
                    'failureId': 'hold-f1', 'failureReason': 'The parent item has lock status 12.',
                    'pairOf': 'op-m2x8', 'decidingFact': {'readableBy': 'approver', 'where': 'parent'},
                    'release': '14.0.0', 'confidence': 'sure', 'author': 'A1',
                },
                'op-q9z1': {
                    'valid': False, 'why': 'Parent item locked with 99.', 'application': 'openproject',
                    'familyId': 'fam-alpha', 'kind': 'must-stop', 'decidable': True,
                    'failureId': 'hold-f2-dup', 'failureReason': 'The parent item has lock status 99.',
                    'pairOf': None, 'decidingFact': {'readableBy': 'approver', 'where': 'parent'},
                    'release': '14.0.0', 'confidence': 'sure', 'author': 'A1',
                },
                'op-m2x8': {
                    'valid': True, 'why': 'Parent unlocked.', 'application': 'openproject',
                    'familyId': 'fam-alpha', 'kind': 'reuse-valid', 'decidable': True,
                    'failureId': None, 'failureReason': None, 'pairOf': 'op-k7f2',
                    'decidingFact': {'readableBy': 'approver', 'where': 'parent'},
                    'release': '14.0.0', 'confidence': 'sure', 'author': 'A1',
                },
            }
        }), encoding='utf-8')

        pub = seal_submission(sub, sealed, author_pseudonym='A3')
        # Duplicate normalized failureReason ("the parent item has lock status <num>") merges 2 -> 1!
        assert pub['counts']['independentInvalidFailureIds'] == 1
        assert len(pub['counts']['mergedDuplicateFailureReasons']) == 1
        verified = verify_sealed_store(sealed)
        assert verified['ok'], verified['problems']

        # Clean builder transcript passes leak scan
        t_file = builder / 'transcript.jsonl'
        t_file.write_text('{"step": 1, "text": "only training op-tr-1 seen"}\n', encoding='utf-8')
        clean_res = leak_scan(sealed, [builder])
        assert clean_res['clean'] is True

        # Leaked canary or routeId triggers Development evaluation only
        t_file.write_text('{"step": 2, "text": "saw op-k7f2 in prompt"}\n', encoding='utf-8')
        dirty_res = leak_scan(sealed, [builder])
        assert dirty_res['clean'] is False
        assert dirty_res['classification'].startswith('Development evaluation only')
    print('custody selftest ok')


def main() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest='cmd')
    p_can = sub.add_parser('canary')
    p_can.add_argument('--sealed-dir', required=True)
    p_val = sub.add_parser('validate-submission')
    p_val.add_argument('--submission-dir', required=True)
    p_val.add_argument('--require-full-floor', action='store_true')
    p_seal = sub.add_parser('seal')
    p_seal.add_argument('--submission-dir', required=True)
    p_seal.add_argument('--sealed-dir', required=True)
    p_seal.add_argument('--author', default='A1')
    p_ver = sub.add_parser('verify')
    p_ver.add_argument('--sealed-dir', required=True)
    p_leak = sub.add_parser('leak-scan')
    p_leak.add_argument('--sealed-dir', required=True)
    p_leak.add_argument('--scan', action='append', required=True)
    sub.add_parser('selftest')

    args = parser.parse_args()
    if args.cmd == 'selftest':
        selftest()
        return
    if args.cmd == 'canary':
        print(json.dumps(cmd_canary(Path(args.sealed_dir)), indent=2))
    elif args.cmd == 'validate-submission':
        res = validate_submission_dir(Path(args.submission_dir), require_full_floor=args.require_full_floor)
        print(json.dumps(res, indent=2))
        sys.exit(0 if res['ok'] else 1)
    elif args.cmd == 'seal':
        print(json.dumps(seal_submission(Path(args.submission_dir), Path(args.sealed_dir), args.author), indent=2))
    elif args.cmd == 'verify':
        res = verify_sealed_store(Path(args.sealed_dir))
        print(json.dumps(res, indent=2))
        sys.exit(0 if res['ok'] else 1)
    elif args.cmd == 'leak-scan':
        res = leak_scan(Path(args.sealed_dir), [Path(p) for p in args.scan])
        print(json.dumps(res, indent=2))
        sys.exit(0 if res['clean'] else 1)
    else:
        parser.print_help()
        sys.exit(2)


if __name__ == '__main__':
    main()
