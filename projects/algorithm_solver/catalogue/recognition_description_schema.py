"""Consistent statement-derived recognition descriptions, not solution labels.

Pure normalization after an operator's boundary-before-open acquisition step.
Hashes bind provenance; neither a source file, public URL, nor this validator
supplies statement access, publication, qualification, or semantic authority.
Unknown fields stay explicit. Originals and encoder settings are not changed.
"""
from __future__ import annotations

import hashlib
import json
import re
from collections import Counter

SCHEMA = 'gamma.recognition-description.v2'
FIELDS = ('intent', 'input', 'output', 'constraints', 'effects', 'distinguishing_details')
LABELS = ('Intent', 'Input', 'Output', 'Constraints', 'Effects', 'Distinguishing details')
EVIDENCE = frozenset({'reviewed-normative-contract', 'development-authored-description-candidate',
                      'authorized-statement-extraction', 'independently-reviewed-statement-extraction'})
ID = re.compile(r'leetcode:[1-9][0-9]*\Z', re.ASCII)
HASH = re.compile(r'[0-9a-f]{64}\Z', re.ASCII)
UNKNOWN = 'Unknown in this description; do not infer a requirement.'
MAX_TEXT_CHARS = 16384


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':'), allow_nan=False)


def strict_json(text):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError('duplicate legacy JSON field')
            result[key] = value
        return result
    return json.loads(text, object_pairs_hook=unique,
        parse_constant=lambda _: (_ for _ in ()).throw(ValueError('nonfinite legacy JSON')))


def digest(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def text_hash(text):
    return hashlib.sha256(text.encode()).hexdigest()


def unknown_field(reason='not_assigned_in_this_description; no source-absence inference'):
    return {'status': 'unknown', 'value': None, 'evidence': [], 'unknown_reason': reason}


def known_field(value, *, source_sha256, selector, evidence_class):
    return {'status': 'known', 'value': value,
            'evidence': [{'source_sha256': source_sha256, 'selector': selector,
                          'evidence_class': evidence_class}], 'unknown_reason': None}


def validate(description, *, authorized_ids, exact_aliases, expected_policy_sha256):
    required = {'schema', 'problem_id', 'title', 'aliases', 'fields', 'evidence_class',
                'permission', 'provenance', 'semantic_review_status'}
    if not isinstance(description, dict) or set(description) != required or description['schema'] != SCHEMA:
        raise ValueError('exact normalized description schema required')
    if not isinstance(expected_policy_sha256, str) or not HASH.fullmatch(expected_policy_sha256):
        raise ValueError('external current policy hash required')
    pid = description['problem_id']
    if not isinstance(pid, str) or not ID.fullmatch(pid):
        raise ValueError('canonical numeric identity required')
    if pid not in authorized_ids:
        raise PermissionError('reserved or unresolved identity cannot receive a new description')
    if not isinstance(description['title'], str) or not description['title'].strip() or any(c in description['title'] for c in '\r\n'):
        raise ValueError('exact single-line metadata title required')
    aliases = description['aliases']
    if not isinstance(aliases, list) or len(aliases) != len(set(aliases)) or any(exact_aliases.get(a) != pid for a in aliases):
        raise ValueError('description alias is ambiguous, guessed or belongs to another identity')
    if description['evidence_class'] not in EVIDENCE:
        raise ValueError('solution/guide/test evidence cannot authorize a description')
    permission = description['permission']
    if (not isinstance(permission, dict) or set(permission) != {'policy_sha256', 'payload_kind', 'scope', 'publication'}
            or permission['policy_sha256'] != expected_policy_sha256
            or permission['payload_kind'] != 'statement' or permission['scope'] != 'private-development-description'
            or permission['publication'] != 'not-granted-by-acquisition'):
        raise ValueError('statement-only acquisition and separate publication scope required')
    if description['semantic_review_status'] not in ('source-preserving-projection', 'needs-independent-semantic-review',
                                                       'independently-reviewed', 'independently-reviewed-incomplete'):
        raise ValueError('explicit semantic review scope required')
    provenance = description['provenance']
    if (not isinstance(provenance, dict) or set(provenance) != {'source_sha256', 'source_kind', 'source_locator', 'transformation'}
            or not isinstance(provenance['source_sha256'], str) or not HASH.fullmatch(provenance['source_sha256'])
            or provenance['source_kind'] not in ('authorized-statement', 'approved-derived-description')
            or not isinstance(provenance['source_locator'], str) or not provenance['source_locator']
            or not isinstance(provenance['transformation'], str) or not provenance['transformation']):
        raise ValueError('statement-bound provenance required; implementation is not evidence')
    fields = description['fields']
    if not isinstance(fields, dict) or set(fields) != set(FIELDS):
        raise ValueError('all six semantic fields required, including explicit unknowns')
    for name in FIELDS:
        field = fields[name]
        if not isinstance(field, dict) or set(field) != {'status', 'value', 'evidence', 'unknown_reason'}:
            raise ValueError('typed field with exact evidence required: ' + name)
        if field['status'] == 'unknown':
            if field['value'] is not None or field['evidence'] != [] or not isinstance(field['unknown_reason'], str) or not field['unknown_reason']:
                raise ValueError('unknown is not false, absent, unconstrained or inferred')
            continue
        if field['status'] not in ('known', 'partial') or field['unknown_reason'] is not None:
            raise ValueError('unsupported semantic field state')
        value = field['value']
        if (not isinstance(value, (str, list, dict)) or not value
                or isinstance(value, str) and not value.strip()
                or len(canonical(value)) > MAX_TEXT_CHARS):
            raise ValueError('bounded nonempty semantic value required')
        evidence = field['evidence']
        if not isinstance(evidence, list) or not evidence:
            raise ValueError('known field needs source evidence')
        for item in evidence:
            if (not isinstance(item, dict) or set(item) != {'source_sha256', 'selector', 'evidence_class'}
                    or item['source_sha256'] != provenance['source_sha256']
                    or not isinstance(item['selector'], str) or not item['selector']
                    or item['evidence_class'] != description['evidence_class']):
                raise ValueError('field evidence does not bind the exact statement artifact')
    rendered = render(description)
    if len(rendered) > MAX_TEXT_CHARS:
        raise ValueError('normalized document exceeds unchanged encoder character limit')
    return {'problem_id': pid, 'document_sha256': text_hash(rendered), 'bytes': len(rendered.encode()),
            'characters': len(rendered), 'known_fields': sum(fields[f]['status'] == 'known' for f in FIELDS),
            'unknown_fields': [f for f in FIELDS if fields[f]['status'] == 'unknown'],
            'metadata_sha256': digest(description), 'qualified': False, 'publication_authorized': False}


def render(description):
    """Only problem semantics enter text; IDs/permission/availability do not rank."""
    lines = [description['title']]
    for name, label in zip(FIELDS, LABELS):
        field = description['fields'][name]
        text = UNKNOWN if field['status'] == 'unknown' else (
            field['value'] if isinstance(field['value'], str) else canonical(field['value']))
        lines.append(label + ': ' + text)
    return '\n'.join(lines) + '\n'


def project_legacy(doc, *, title, aliases, source_sha256, policy_sha256):
    """Project exact prior whitelisted JSON fields; do not mine solutions.

    Legacy semantic documents contain title then Objective/Result/Input domain/
    Ordered interface lines. Effects and distinguishing facts are NOT guessed
    from tests, complexity, title suffixes, or implementation availability.
    """
    if (not isinstance(doc.get('text'), str)
            or doc.get('document_sha256') != text_hash(doc['text'])):
        raise ValueError('legacy document UTF-8 hash mismatch')
    lines = doc['text'].splitlines()
    if not lines or lines[0] != title:
        raise ValueError('legacy document title/identity mismatch')
    expected = {'Objective': 'intent', 'Result': 'output', 'Input domain': 'constraints', 'Ordered interface': 'input'}
    selected = {}
    for line in lines[1:]:
        if not line.strip():
            continue
        label, separator, value = line.partition(': ')
        if not separator or label not in expected or label in selected:
            raise ValueError('legacy document has unapproved/duplicate semantic field')
        selected[label] = strict_json(value)
    if set(selected) != set(expected):
        raise ValueError('legacy description missing selected semantic fields')
    evidence_class = doc['authority']['knowledge_class']
    if evidence_class not in EVIDENCE:
        raise ValueError('legacy title-only/unknown authority cannot be upgraded')
    fields = {name: unknown_field() for name in FIELDS}
    for label, name in expected.items():
        fields[name] = known_field(selected[label], source_sha256=source_sha256,
                                  selector=f'documents[{doc["problem_id"]}].{label}', evidence_class=evidence_class)
    return {'schema': SCHEMA, 'problem_id': doc['problem_id'], 'title': title, 'aliases': list(aliases),
        'fields': fields, 'evidence_class': evidence_class,
        'permission': {'policy_sha256': policy_sha256, 'payload_kind': 'statement',
                       'scope': 'private-development-description', 'publication': 'not-granted-by-acquisition'},
        'provenance': {'source_sha256': source_sha256, 'source_kind': 'approved-derived-description',
                       'source_locator': f'documents[{doc["problem_id"]}]',
                       'transformation': 'exact prior whitelisted JSON fields; no solution inference'},
        'semantic_review_status': 'source-preserving-projection'}


def summarize(descriptions):
    ids = [r['problem_id'] for r in descriptions]
    if len(ids) != len(set(ids)):
        raise ValueError('disjoint description batches required')
    return {'schema': 'gamma.recognition-description-summary.v2', 'descriptions': len(ids),
            'evidence_counts': dict(Counter(r['evidence_class'] for r in descriptions)),
            'semantic_review_counts': dict(Counter(r['semantic_review_status'] for r in descriptions)),
            'field_states': {name: dict(Counter(r['fields'][name]['status'] for r in descriptions)) for name in FIELDS},
            'statement_semantics_not_independently_qualified_by_schema': True,
            'solutions_used_as_authority': False, 'encoder_executed': False, 'publication_authorized': False}
