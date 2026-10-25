"""Validate a complete metadata-only dual-language catalogue, never execute sources.

A consistent manifest is not qualification. Receipt attestations must be produced
by a separately trusted judge verifier; this module only checks their bindings.
"""
import hashlib
import json

LANGUAGES = ('javascript', 'python')
STATUSES = {'missing', 'authored', 'blocked', 'protected', 'qualified'}
BINDINGS = ('source_sha256', 'problem_contract_sha256', 'interface_sha256',
            'runtime_sha256', 'tests_sha256', 'effects_sha256')


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
                                     allow_nan=False).encode()).hexdigest()


def hash_value(value):
    return isinstance(value, str) and len(value) == 64 and all(c in '0123456789abcdef' for c in value)


def fields(value, allowed):
    if not isinstance(value, dict) or set(value) - set(allowed):
        raise ValueError('unknown metadata fields')


def validate(universe, catalogue, verified_receipts):
    """Require every frozen eligible ID, including missing/protected languages.

    Inputs contain metadata/hashes, not cases, source text or stored answers.
    verified_receipts is an explicit external trust input, not an approval flag
    accepted from catalogue rows. Completion is conditional on that verifier.
    """
    fields(universe, ('schema', 'eligible_problem_ids', 'metadata_sha256', 'eligibility_policy', 'protected_problem_ids'))
    fields(catalogue, ('schema', 'universe_sha256', 'problems'))
    if universe.get('schema') != 'gamma.catalogue-universe.v1':
        raise ValueError('unknown universe schema')
    ids = universe.get('eligible_problem_ids', [])
    if not isinstance(ids, list) or not ids or any(not isinstance(x, str) or not x for x in ids) or len(ids) != len(set(ids)):
        raise ValueError('invalid frozen eligible universe')
    protected = universe.get('protected_problem_ids')
    if not isinstance(protected, list) or any(not isinstance(x, str) for x in protected) or len(protected) != len(set(protected)) or not set(protected) <= set(ids):
        raise ValueError('explicit immutable protection subset required')
    if not hash_value(universe.get('metadata_sha256')) or not universe.get('eligibility_policy'):
        raise ValueError('missing independent universe provenance')
    if catalogue.get('schema') != 'gamma.dual-language-catalogue.v1' or catalogue.get('universe_sha256') != digest(universe):
        raise ValueError('catalogue universe mismatch')
    rows = catalogue.get('problems', [])
    if not isinstance(rows, list):
        raise ValueError('problem rows must be a list')
    for row in rows:
        fields(row, ('problem_id', 'implementations'))
    keyed = {row['problem_id']: row for row in rows}
    if len(keyed) != len(rows) or set(keyed) != set(ids):
        raise ValueError('missing, duplicate or extra problem: denominator cannot change')
    counts = {language: {status: 0 for status in sorted(STATUSES)} for language in LANGUAGES}
    for pid in ids:
        row = keyed[pid]
        if set(row.get('implementations', {})) != set(LANGUAGES):
            raise ValueError('both language slots required: ' + pid)
        for language in LANGUAGES:
            impl = row['implementations'][language]
            fields(impl, (*BINDINGS, 'status', 'reason', 'canonical_variant_id', 'provenance', 'interface', 'receipt_sha256'))
            status = impl.get('status')
            if status not in STATUSES:
                raise ValueError('unknown status')
            counts[language][status] += 1
            if status != 'qualified':
                if not impl.get('reason'):
                    raise ValueError('unqualified slot requires explicit reason')
                continue
            if pid in protected:
                raise ValueError('protected universe identity cannot be promoted by a row')
            if not impl.get('canonical_variant_id') or not impl.get('provenance'):
                raise ValueError('canonical identity/provenance required')
            if any(not hash_value(impl.get(key)) for key in BINDINGS):
                raise ValueError('missing source/contract/interface/runtime/test/effect binding')
            interface = impl.get('interface', {})
            fields(interface, ('schema', 'entrypoint', 'arguments', 'typed_contract'))
            if interface.get('schema') != 'gamma.call-interface.v1' or interface.get('entrypoint') != 'solve' or interface.get('arguments') != 'ordered-positional' or interface.get('typed_contract') != impl['problem_contract_sha256']:
                raise ValueError('noncanonical call interface')
            if digest(interface) != impl['interface_sha256']:
                raise ValueError('interface content mismatch')
            receipt_id = impl.get('receipt_sha256')
            if not hash_value(receipt_id):
                raise ValueError('invalid receipt identity')
            receipt = verified_receipts.get(receipt_id)
            if not receipt or digest(receipt) != receipt_id:
                raise ValueError('no independently verified receipt binding')
            if receipt.get('problem_id') != pid or receipt.get('language') != language or receipt.get('verdict') != 'qualified' or receipt.get('evidence_class') != 'normative-typed-effects' or receipt.get('independent_verifier') is not True:
                raise ValueError('wrong identity or compatibility-only receipt')
            if receipt.get('canonical_variant_id') != impl['canonical_variant_id'] or receipt.get('provenance_sha256') != digest(impl['provenance']):
                raise ValueError('canonical variant/provenance not receipt-bound')
            if any(receipt.get(key) != impl[key] for key in BINDINGS):
                raise ValueError('stale qualification binding')
    complete = all(counts[language]['qualified'] == len(ids) for language in LANGUAGES)
    return {'schema': 'gamma.catalogue-validation.v1', 'eligible_problems': len(ids),
            'language_counts': counts, 'complete_dual_language_catalogue': complete,
            'qualification_conditional_on_external_receipt_verifier': True,
            'current_runtime_and_serving_policy_verified': False,
            'recognition_1a_1b_1c_qualified': False, 'historical_m1_qualified': False}
