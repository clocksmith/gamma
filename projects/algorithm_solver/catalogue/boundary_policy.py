"""Hash-bound pre-open acquisition gate. Reads metadata, never source payloads.

Artifact paths and trusted SHA256 anchors MUST come from the authorized operator,
never the source request. Hash equality binds bytes, not approval authority. This
module checks a reviewed boundary proof; it is not a substitute for that review.
A caller must additionally bind its exact source locator/record to the authorized
identity BEFORE decoding it. Acquisition permission is not qualification, serving
approval, publication permission, or permission to open cases.
"""
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re

ARTIFACTS = frozenset({'policy', 'universe', 'proof', 'closure', 'classification', 'identity_aliases'})
LANGUAGES = frozenset({'javascript', 'python'})
_ID = re.compile(r'leetcode:[1-9][0-9]*\Z', re.ASCII)
_KEY = re.compile(r'lc:[a-z0-9]+(?:-[a-z0-9]+)*\Z', re.ASCII)
_HASH = re.compile(r'[0-9a-f]{64}\Z', re.ASCII)
MAX_METADATA_BYTES = 8 * 1024 * 1024


def _fields(value, names):
    if not isinstance(value, dict) or set(value) != set(names):
        raise ValueError('unexpected or missing boundary metadata fields')


def _ids(value):
    if (not isinstance(value, list) or any(not isinstance(x, str) or not _ID.fullmatch(x) for x in value)
            or len(value) != len(set(value))):
        raise ValueError('invalid or duplicate canonical numeric identity')
    return frozenset(value)


def _strings(value, pattern=None):
    if (not isinstance(value, list) or any(not isinstance(x, str) or not x or
            (pattern is not None and not pattern.fullmatch(x)) for x in value)
            or len(value) != len(set(value))):
        raise ValueError('invalid or duplicate metadata strings')
    return frozenset(value)


def _unique(pairs):
    out = {}
    for key, value in pairs:
        if key in out:
            raise ValueError('duplicate JSON metadata field')
        out[key] = value
    return out


def _decode(raw):
    if not isinstance(raw, bytes) or len(raw) > MAX_METADATA_BYTES:
        raise ValueError('metadata must be bounded raw bytes')
    return json.loads(raw, object_pairs_hook=_unique,
                      parse_constant=lambda _: (_ for _ in ()).throw(ValueError('nonfinite JSON')))


@dataclass(frozen=True)
class ValidatedBoundaryPolicy:
    """Immutable verified snapshot. Use authorize_before_open for live file pins."""
    authorized: frozenset
    existing: frozenset
    protected: frozenset
    unknown: frozenset
    policy_sha256: str
    universe_sha256: str
    proof_sha256: str

    def authorize(self, problem_id, *, language, payload_kind='source'):
        if not isinstance(problem_id, str) or not _ID.fullmatch(problem_id):
            raise PermissionError('invalid canonical problem identity')
        if not isinstance(language, str) or language not in LANGUAGES:
            raise PermissionError('unsupported source language')
        if not isinstance(payload_kind, str) or payload_kind not in ('source', 'statement'):
            raise PermissionError('payload kind is not authorized')
        if problem_id in self.protected:
            raise PermissionError('reserved identity remains closed')
        if problem_id not in self.authorized:
            raise PermissionError('unknown or unauthorized identity remains metadata-only')
        return {'schema': 'gamma.source-acquisition-authorization.v1',
                'problem_id': problem_id, 'language': language, 'payload_kind': payload_kind,
                'policy_sha256': self.policy_sha256, 'universe_sha256': self.universe_sha256,
                'proof_sha256': self.proof_sha256, 'authorized': True,
                'requires_identity_bound_locator': True, 'semantic_qualification_created': False,
                'source_publication_authorized': False, 'case_access_authorized': False,
                'current_serving_runtime_verified': False}


def validate_policy(raw_artifacts, trusted_hashes):
    """Validate exact trusted metadata bytes; no file or payload reads occur here."""
    _fields(raw_artifacts, ARTIFACTS); _fields(trusted_hashes, ARTIFACTS)
    parsed = {}
    for name in ARTIFACTS:
        pin = trusted_hashes[name]
        if not isinstance(pin, str) or not _HASH.fullmatch(pin):
            raise ValueError('invalid external metadata anchor')
        raw = raw_artifacts[name]
        if not isinstance(raw, bytes) or hashlib.sha256(raw).hexdigest() != pin:
            raise ValueError('external boundary metadata anchor mismatch: ' + name)
        parsed[name] = _decode(raw)
    p, u, proof, closure, classification, aliases = (parsed[k] for k in
        ('policy', 'universe', 'proof', 'closure', 'classification', 'identity_aliases'))
    _fields(u, ('schema', 'eligible_problem_ids', 'protected_problem_ids', 'metadata_sha256', 'eligibility_policy'))
    if u['schema'] != 'gamma.catalogue-universe.v1' or not isinstance(u['metadata_sha256'], str) or not _HASH.fullmatch(u['metadata_sha256']) or not isinstance(u['eligibility_policy'], str) or not u['eligibility_policy']:
        raise ValueError('unsupported global universe')
    all_ids, protected = _ids(u['eligible_problem_ids']), _ids(u['protected_problem_ids'])
    if not all_ids or not protected <= all_ids:
        raise ValueError('invalid immutable protection universe')
    _fields(p, ('schema', 'metadata_revision', 'population_size', 'language_slots',
                'universe_sha256', 'evidence_sha256', 'supersedes_policy_sha256',
                'authorized_existing_source_problem_ids', 'authorized_source_acquisition_problem_ids',
                'known_protected_problem_ids', 'unknown_problem_ids', 'outside_authorized_count',
                'authority', 'approval_scope', 'new_source_access_authorized',
                'source_publication_authorized', 'case_access_authorized', 'qualification_changed',
                'current_serving_runtime_checked', 'final100_membership_complete',
                'historical382_key_closure_complete', 'full4081_alias_closure_complete'))
    if p['schema'] != 'gamma.all4081-source-access-policy.v2' or type(p['metadata_revision']) is not int or p['metadata_revision'] != 3:
        raise ValueError('unsupported source-access policy')
    if (p['new_source_access_authorized'] is not True or
            any(p[k] is not False for k in ('source_publication_authorized', 'case_access_authorized',
                'qualification_changed', 'current_serving_runtime_checked', 'full4081_alias_closure_complete')) or
            any(p[k] is not True for k in ('final100_membership_complete', 'historical382_key_closure_complete'))):
        raise ValueError('source access must not confer publication, cases, qualification or global closure')
    if p['approval_scope'] != 'prospective-exact-known-corpus-source-and-statement-acquisition' or not isinstance(p['authority'], str) or not p['authority']:
        raise ValueError('explicit bounded approval scope required')
    if p['universe_sha256'] != trusted_hashes['universe'] or not isinstance(p['supersedes_policy_sha256'], str) or not _HASH.fullmatch(p['supersedes_policy_sha256']):
        raise ValueError('policy universe or predecessor mismatch')
    _fields(p['evidence_sha256'], ARTIFACTS - {'policy', 'universe'})
    if any(p['evidence_sha256'][k] != trusted_hashes[k] for k in p['evidence_sha256']):
        raise ValueError('policy proof binding mismatch')
    authorized = _ids(p['authorized_source_acquisition_problem_ids']); existing = _ids(p['authorized_existing_source_problem_ids'])
    unknown = _ids(p['unknown_problem_ids'])
    if (_ids(p['known_protected_problem_ids']) != protected or not existing <= authorized or
            authorized & protected or authorized & unknown or protected & unknown or
            authorized | protected | unknown != all_ids):
        raise ValueError('policy must exactly partition immutable universe')
    if (any(type(p[k]) is not int for k in ('population_size', 'language_slots', 'outside_authorized_count')) or
            p['population_size'] != len(all_ids) or p['language_slots'] != 2 * len(all_ids) or
            p['outside_authorized_count'] != len(protected | unknown)):
        raise ValueError('policy denominator mismatch')
    _fields(proof, ('schema', 'status', 'owner_published_index_keys', 'historical_metadata_commit',
                   'counts', 'proof', 'premises', 'source_payload_reads', 'statement_payload_reads',
                   'case_payload_reads', 'new_source_access_authorized', 'canonical_f625_recomputed',
                   'raw_a4a_index_entries_recomputed', 'metadata_input_refs', 'private_outputs', 'limits'))
    if proof['schema'] != 'gamma.boundary-metadata-receipt.v3' or proof['new_source_access_authorized'] is not False or any(type(proof[k]) is not int or proof[k] != 0 for k in ('source_payload_reads', 'statement_payload_reads', 'case_payload_reads')):
        raise ValueError('not the reviewed metadata-only reconstruction proof')
    if not isinstance(proof['private_outputs'], list) or not all(isinstance(r, dict) and set(r) == {'path', 'sha256', 'bytes'} and isinstance(r['path'], str) and isinstance(r['sha256'], str) and _HASH.fullmatch(r['sha256']) and type(r['bytes']) is int and r['bytes'] >= 0 for r in proof['private_outputs']):
        raise ValueError('invalid proof output references')
    output_hashes = [r['sha256'] for r in proof['private_outputs']]
    if any(output_hashes.count(trusted_hashes[k]) != 1 for k in ('closure', 'classification')):
        raise ValueError('reviewed proof does not bind exact closure/classification')
    _fields(closure, ('schema', 'status', 'keys', 'families', 'problem_ids', 'known_uids_only',
                     'full815_uid_closure_reconstructed', 'witnesses'))
    if closure['schema'] != 'gamma.historical-key-closure-proof.v1' or closure['full815_uid_closure_reconstructed'] is not False:
        raise ValueError('unsupported closure scope')
    reserved = _ids(closure['problem_ids']); keys = _strings(closure['keys'], _KEY)
    families = _strings(closure['families']); _strings(closure['known_uids_only'])
    if not reserved <= protected or len(reserved) != len(keys):
        raise ValueError('closure identities differ from protection')
    _fields(aliases, ('schema', 'metadata_revision', 'to_universe_sha256', 'proof_sha256',
                     'closure_sha256', 'corpus_metadata_sha256', 'by_key', 'known_corpus_keys',
                     'outside_corpus_reserved_keys', 'source_payload_reads', 'case_payload_reads'))
    if (aliases['schema'] != 'gamma.corpus-key-numeric-alias-map.v1' or type(aliases['metadata_revision']) is not int or aliases['metadata_revision'] != 3 or
            aliases['to_universe_sha256'] != trusted_hashes['universe'] or
            aliases['proof_sha256'] != trusted_hashes['proof'] or aliases['closure_sha256'] != trusted_hashes['closure'] or
            any(type(aliases[k]) is not int or aliases[k] != 0 for k in ('source_payload_reads', 'case_payload_reads'))):
        raise ValueError('alias proof/universe scope mismatch')
    if not isinstance(aliases['corpus_metadata_sha256'], str) or not _HASH.fullmatch(aliases['corpus_metadata_sha256']):
        raise ValueError('missing immutable source-free corpus metadata anchor')
    mapping = aliases['by_key']; known_keys = _strings(aliases['known_corpus_keys'], _KEY)
    outside_keys = _strings(aliases['outside_corpus_reserved_keys'], _KEY)
    if (not isinstance(mapping, dict) or any(not isinstance(k, str) or not _KEY.fullmatch(k) or
            not isinstance(v, str) or not _ID.fullmatch(v) for k, v in mapping.items()) or
            len(set(mapping.values())) != len(mapping) or set(mapping) != known_keys | outside_keys or
            known_keys & outside_keys or not outside_keys <= keys or not set(mapping.values()) <= all_ids):
        raise ValueError('invalid exact key/numeric alias mapping')
    if {mapping[k] for k in keys if k in mapping} != reserved or not keys <= set(mapping):
        raise ValueError('reserved numeric identities not bound to exact keys')
    if not authorized <= {mapping[k] for k in known_keys}:
        raise ValueError('authorization cannot expand beyond reviewed known corpus')
    if not isinstance(closure['witnesses'], list) or len(closure['witnesses']) != len(keys):
        raise ValueError('incomplete closure witnesses')
    witnessed = set()
    witness_kinds = {'narrow_exclusion_key', 'exact_corpus_minus_research_key',
                     'family_seed:narrow', 'family_seed:development_audit',
                     'family_seed:recognition', 'family_seed:nonresearch'}
    for w in closure['witnesses']:
        _fields(w, ('key', 'family', 'problem_id', 'membership_witnesses'))
        if w['key'] in witnessed or w['key'] not in keys or w['problem_id'] != mapping[w['key']] or w['family'] not in families or not _strings(w['membership_witnesses']):
            raise ValueError('invalid closure inclusion witness')
        expected_family = re.sub(r'-(?:i|ii|iii|iv|v)$', '', w['key'][3:])
        if w['family'] != expected_family or not set(w['membership_witnesses']) <= witness_kinds:
            raise ValueError('closure witness rule differs from reviewed producer')
        witnessed.add(w['key'])
    _fields(classification, ('schema', 'new_source_access_authorized', 'current_allowlist_unchanged', 'rows', 'counts', 'full_current4081_alias_closure_complete'))
    if (classification['schema'] != 'gamma.all4081-boundary-classification-review.v1' or
            classification['new_source_access_authorized'] is not False or
            classification['current_allowlist_unchanged'] is not True or
            classification['full_current4081_alias_closure_complete'] is not False or
            not isinstance(classification['rows'], list)):
        raise ValueError('classification is not the reviewed pre-activation snapshot')
    groups = {k: set() for k in ('previously_authorized_400', 'historical_reserved382', 'final100_exact_id_reserved',
                  'known_corpus_nonreserved_pending_independent_review', 'unresolved_global_identity_alias_metadata_only')}
    seen = set()
    for row in classification['rows']:
        _fields(row, ('problem_id', 'status', 'source_access_currently_authorized'))
        pid, status = row['problem_id'], row['status']
        if pid not in all_ids or pid in seen or status not in groups or row['source_access_currently_authorized'] is not (status == 'previously_authorized_400'):
            raise ValueError('invalid or duplicate classification row')
        seen.add(pid); groups[status].add(pid)
    expected_counts = {k: len(v) for k, v in groups.items() if v}
    if not isinstance(classification['counts'], dict) or any(type(v) is not int for v in classification['counts'].values()):
        raise ValueError('classification counts must be exact integers')
    if (seen != all_ids or classification['counts'] != expected_counts or
            groups['previously_authorized_400'] != existing or groups['historical_reserved382'] != reserved or
            groups['historical_reserved382'] | groups['final100_exact_id_reserved'] != protected or
            groups['previously_authorized_400'] | groups['known_corpus_nonreserved_pending_independent_review'] != authorized or
            groups['unresolved_global_identity_alias_metadata_only'] != unknown):
        raise ValueError('activation differs from exact reviewed classification')
    counts = proof['counts']
    if not isinstance(counts, dict) or any(type(v) is not int for v in counts.values()):
        raise ValueError('invalid proof counts')
    expected = {'all4081': len(all_ids), 'historical_reserved_keys': len(keys),
                'historical_reserved_families': len(families), 'historical_reserved_numeric_ids': len(reserved),
                'known_exact_id_nonreserved': len(authorized), 'currently_source_authorized': len(existing),
                'additional_exact_id_candidates': len(authorized - existing), 'unresolved_exterior_ids': len(unknown),
                'corpus_keys': len(known_keys), 'final100': len(protected - reserved)}
    if any(counts.get(k) != v for k, v in expected.items()):
        raise ValueError('activation counts differ from reviewed proof')
    return ValidatedBoundaryPolicy(authorized, existing, protected, unknown, trusted_hashes['policy'],
                                   trusted_hashes['universe'], trusted_hashes['proof'])


def authorize_before_open(problem_id, artifact_paths, trusted_hashes, *, language, payload_kind='source'):
    """Re-read/hash-check all metadata now, before caller opens any source record.

    No paths in metadata are followed. Only the six explicit operator paths are
    read; no corpus scanning or payload loader is used. A successful receipt does
    not identify a source file; caller's reviewed scoped reader must do that.
    """
    _fields(artifact_paths, ARTIFACTS)
    raw = {}
    for name, path in artifact_paths.items():
        with Path(path).open('rb') as stream:
            raw[name] = stream.read(MAX_METADATA_BYTES + 1)
    return validate_policy(raw, trusted_hashes).authorize(problem_id, language=language, payload_kind=payload_kind)
