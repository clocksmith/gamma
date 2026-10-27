"""Source-free recognition inventory and conservative incremental vector planning.

The operator authenticates metadata inputs before calling these pure functions.
Metadata availability is never statement authority, publication or qualification.
Unknown historical execution provenance cannot be repaired by a matching dimension.
"""
from collections import Counter, defaultdict
import hashlib
import json
import re

ID = re.compile(r'leetcode:[1-9][0-9]*\Z', re.ASCII)
HASH = re.compile(r'[0-9a-f]{64}\Z', re.ASCII)
# Complete execution identity; a reranker intentionally is not a document encoder.
EXECUTION_FIELDS = frozenset({
    'model_manifest_sha256', 'tokenizer_manifest_sha256', 'adapter_sha256',
    'runtime_manifest_sha256', 'python_sha256', 'device', 'dtype', 'threads',
    'interop_threads', 'batch_size', 'padding_side', 'pooling', 'normalization',
    'max_tokens', 'truncation', 'document_instruction', 'query_instruction',
    'dimension',
})


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                    separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def text_hash(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def execution_identity(value):
    if not isinstance(value, dict) or set(value) != EXECUTION_FIELDS:
        raise ValueError('complete exact encoder execution identity required')
    for key in EXECUTION_FIELDS:
        item = value[key]
        if key.endswith('_sha256'):
            if not isinstance(item, str) or not HASH.fullmatch(item):
                raise ValueError('missing original execution provenance: ' + key)
        elif key in ('threads', 'interop_threads', 'batch_size', 'max_tokens', 'dimension'):
            if type(item) is not int or item < 1:
                raise ValueError('positive integer execution field required: ' + key)
        elif not isinstance(item, str) or (not item and key != 'document_instruction'):
            raise ValueError('explicit execution field required: ' + key)
    return digest(value)


def inventory(metadata, boundary, aliases, *, metadata_sha256, description_records=(), vector_records=()):
    """Recount all metadata rows without opening any description/source/case.

    Description records are metadata projections, never inferred from a source
    locator. Frozen protected title vectors may be recorded, never newly enriched.
    Duplicate or ambiguous identities remain visible and block subsequent builds.
    """
    if not isinstance(metadata_sha256, str) or not HASH.fullmatch(metadata_sha256):
        raise ValueError('independently pinned metadata provenance required')
    rows = metadata.get('rows')
    if not isinstance(rows, list) or not rows:
        raise ValueError('complete metadata rows required')
    ids = [r.get('global_problem_id') for r in rows]
    if any(not isinstance(pid, str) or not ID.fullmatch(pid) for pid in ids):
        raise ValueError('invalid canonical numeric identity')
    authorized, protected, unknown = boundary.authorized, boundary.protected, boundary.unknown
    if set(ids) != authorized | protected | unknown:
        raise ValueError('current metadata universe differs from pinned policy')
    if authorized & protected or authorized & unknown or protected & unknown:
        raise ValueError('policy partition overlaps')
    counts = Counter(ids)
    duplicate_ids = sorted(pid for pid, n in counts.items() if n > 1)
    alias_to_ids = defaultdict(set)
    for key, destinations in aliases.items():
        if not isinstance(key, str) or not key or not isinstance(destinations, list) or not destinations:
            raise ValueError('explicit alias identity sequences required')
        for pid in destinations:
            if pid not in counts:
                raise ValueError('alias destination absent from complete metadata')
            alias_to_ids[key].add(pid)
    ambiguous_aliases = {key: sorted(values) for key, values in alias_to_ids.items() if len(values) != 1}
    ambiguous_ids = {pid for values in ambiguous_aliases.values() for pid in values}
    by_id = defaultdict(list)
    for key, destinations in alias_to_ids.items():
        for pid in destinations:
            by_id[pid].append(key)
    descriptions = {}
    for row in description_records:
        pid = row['problem_id']
        if pid not in counts or pid in descriptions:
            raise ValueError('description metadata identity missing or duplicated')
        if row.get('document_sha256') is not None and (not isinstance(row['document_sha256'], str) or not HASH.fullmatch(row['document_sha256'])):
            raise ValueError('invalid description hash')
        if row.get('knowledge_class') != 'title-only' and pid not in authorized:
            raise PermissionError('protected/exterior descriptions remain closed')
        descriptions[pid] = dict(row)
    vectors = {}
    for row in vector_records:
        pid = row['problem_id']
        if pid not in counts or pid in vectors:
            raise ValueError('vector identity missing or duplicated')
        vectors[pid] = dict(row)
    output = []
    for row in rows:
        pid = row['global_problem_id']
        access = 'authorized' if pid in authorized else 'reserved' if pid in protected else 'unresolved'
        identity = 'duplicate' if counts[pid] > 1 else 'ambiguous' if pid in ambiguous_ids else 'unique'
        description = descriptions.get(pid, {'problem_id': pid, 'document_sha256': None,
            'knowledge_class': 'unverified', 'provenance': None})
        output.append({'problem_id': pid, 'aliases': sorted(by_id[pid]),
            'classification': identity if identity != 'unique' else access,
            'access_status': access, 'identity_status': identity,
            'title_metadata_sha256': metadata_sha256,
            'statement_acquisition_authorized': pid in authorized,
            'source_availability': row.get('source_availability', 'unverified'),
            'source_availability_confers_statement_permission': False,
            'publication_permission': row.get('source_publication_permission', 'unverified'),
            'description': description, 'existing_vector': vectors.get(pid)})
    rich = len({r['problem_id'] for r in output if r['access_status'] == 'authorized'
                and r['description'].get('document_sha256') is not None
                and r['description']['knowledge_class'] not in ('title-only', 'unverified')})
    return {'schema': 'gamma.recognition-inventory.v1', 'population': len(set(ids)),
        'metadata_rows': len(ids), 'rows': output,
        'counts': {'authorized': len(authorized), 'reserved': len(protected), 'unresolved': len(unknown),
                   'duplicate_identities': len(duplicate_ids), 'ambiguous_identities': len(ambiguous_ids),
                   'ambiguous_aliases': len(ambiguous_aliases), 'authorized_descriptions': rich,
                   'authorized_missing_descriptions': len(authorized) - rich},
        'duplicate_ids': duplicate_ids, 'ambiguous_aliases': ambiguous_aliases,
        'metadata_sha256': metadata_sha256, 'policy_sha256': boundary.policy_sha256,
        'universe_sha256': boundary.universe_sha256, 'proof_sha256': boundary.proof_sha256,
        'payload_reads': 0, 'source_availability_filter': False, 'qualification_created': False,
        'publication_authorized': False}


def incremental_plan(current, baseline, *, execution, baseline_execution, baseline_id):
    """Plan by stable identity+document+execution proof; never by row/dimension alone.

    Inputs are inventories, so blocked rows may retain byte-identical frozen
    vectors but cannot request new embeddings. Changes in aliases bind a new
    release, not a new document vector. Rerankers are outside execution identity.
    """
    if not isinstance(baseline_id, str) or not baseline_id.strip():
        raise ValueError('separately identified original baseline required')
    current_execution = execution_identity(execution)
    baseline_fingerprint = None
    if baseline_execution is not None:
        baseline_fingerprint = execution_identity(baseline_execution)
    for data in (current, baseline):
        if data['counts']['duplicate_identities'] or data['counts']['ambiguous_identities']:
            raise ValueError('duplicate/ambiguous identities require resolution before build')
    old = {r['problem_id']: r for r in baseline['rows']}
    seen = set(); rows = []
    counts = Counter()
    for row in current['rows']:
        pid = row['problem_id']; seen.add(pid); prior = old.get(pid)
        doc = row['description'].get('document_sha256')
        previous_doc = prior['description'].get('document_sha256') if prior else None
        state = 'added' if prior is None else 'unchanged' if doc is not None and doc == previous_doc else 'changed'
        candidate = prior.get('existing_vector') if prior else None
        compatible = bool(candidate and doc and doc == previous_doc and
            candidate.get('document_sha256') == doc and
            candidate.get('execution_sha256') == current_execution == baseline_fingerprint and
            candidate.get('validated') is True and candidate.get('binding_verified') is True and
            isinstance(candidate.get('vector_file_sha256'), str) and HASH.fullmatch(candidate['vector_file_sha256']) and
            type(candidate.get('row')) is int and candidate['row'] >= 0)
        if compatible:
            action = 'reuse'; reason = 'exact_document_and_execution_binding'
        elif row['access_status'] != 'authorized':
            action = 'blocked'; reason = 'frozen_competitor_cannot_be_reembedded_without_authority'
        elif doc is None:
            action = 'blocked'; reason = 'description_provenance_missing'
        else:
            action = 'embed'; reason = 'new_changed_or_unproven_vector'
        counts[state] += 1; counts[action + '_vectors'] += 1
        rows.append({'problem_id': pid, 'delta': state, 'action': action, 'reason': reason,
            'document_sha256': doc, 'prior_document_sha256': previous_doc,
            'vector_source': candidate if compatible else None})
    removed = sorted(set(old) - seen)
    counts['removed'] = len(removed)
    return {'schema': 'gamma.recognition-incremental-plan.v1',
        'baseline_id': baseline_id, 'baseline_execution_sha256': baseline_fingerprint,
        'execution_sha256': current_execution, 'execution': execution,
        'inventory_sha256': digest(current), 'baseline_inventory_sha256': digest(baseline),
        'rows': rows, 'removed_problem_ids': removed,
        'counts': {name: counts[name] for name in ('added', 'changed', 'unchanged', 'removed',
                   'reuse_vectors', 'embed_vectors', 'blocked_vectors')},
        'requires_full_population_recalibration': current_execution != baseline_fingerprint or
            digest([(r['problem_id'], r['description'].get('document_sha256')) for r in current['rows']]) !=
            digest([(r['problem_id'], r['description'].get('document_sha256')) for r in baseline['rows']]),
        'historical_provenance_invented': False, 'source_availability_filter': False,
        'recognition_qualified': False}
