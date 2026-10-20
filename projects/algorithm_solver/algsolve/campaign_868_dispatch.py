"""Exact868/1056 outer dispatch. Prior profiles retain their validators."""
from . import campaign_uint1024_dispatch as previous
from . import campaign_exact_integer as common
from . import campaign_868_integer as gap

distinct = common.distinct

def requires_1056(data, entry):
    reference = data.get('inputs', {}).get('integer1056_policy')
    if reference is None:
        return False
    policy = common.check(reference)
    common.need(policy.get('schema') == 'algsolve.integer1056-admission-policy.v1' and
                type(policy.get('entries')) is dict and
                set(policy['entries']) == {'1056:javascript'},
                '1056 coordinator policy must contain only1056JavaScript')
    return common.key(entry) in policy['entries']


def requires_profile(data, entry):
    reference = data.get('inputs', {}).get('integer868_policy')
    if reference is None:
        return False
    policy = common.check(reference)
    common.need(policy.get('schema') == gap.POLICY_SCHEMA and
                type(policy.get('entries')) is dict and
                set(policy['entries']) == {'0868:javascript'},
                '868 coordinator policy must contain only0868JavaScript')
    return common.key(entry) in policy['entries']

def select(data, entry):
    required = requires_profile(data, entry)
    required1056 = requires_1056(data, entry)
    if common.key(entry) == '1056:javascript':
        common.need(not common.requires_profile(data, entry) and
                    not previous.previous.requires_square(data, entry) and
                    not previous.requires_profile(data, entry) and not required,
                    'Combined alternate profiles forbidden')
        from . import campaign_1056_integer as confusion
        return confusion
    common.need(not required1056, 'Unsupported1056 alternate entry')
    if common.key(entry) == '0868:javascript':
        common.need(not common.requires_profile(data, entry) and
                    not previous.previous.requires_square(data, entry) and
                    not previous.requires_profile(data, entry),
                    'Combined alternate profiles forbidden')
        return gap
    common.need(not required, 'Unsupported868 alternate entry')
    return previous.select(data, entry)

def reject_legacy(data, entry, *documents):
    common.need(not requires_1056(data, entry),
                'Coordinator1056 policy requires version3; downgrade forbidden')
    common.need(not requires_profile(data, entry),
                'Coordinator868 policy requires version3; downgrade forbidden')
    return previous.reject_legacy(data, entry, *documents)

def profile(data, entry, contract):
    return select(data, entry).profile(data, entry, contract)

def execution_profile(data, entry, contract, execution, review):
    return select(data, entry).execution_profile(data, entry, contract, execution, review)
