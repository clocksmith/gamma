"""868-only outer dispatch. Existing profiles retain their previous routing."""
from . import campaign_uint1024_dispatch as previous
from . import campaign_exact_integer as common
from . import campaign_868_integer as gap

distinct = common.distinct

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
    if common.key(entry) == '0868:javascript':
        common.need(not common.requires_profile(data, entry) and
                    not previous.previous.requires_square(data, entry) and
                    not previous.requires_profile(data, entry),
                    'Combined alternate profiles forbidden')
        return gap
    common.need(not required, 'Unsupported868 alternate entry')
    return previous.select(data, entry)

def reject_legacy(data, entry, *documents):
    common.need(not requires_profile(data, entry),
                'Coordinator868 policy requires version3; downgrade forbidden')
    return previous.reject_legacy(data, entry, *documents)

def profile(data, entry, contract):
    return select(data, entry).profile(data, entry, contract)

def execution_profile(data, entry, contract, execution, review):
    return select(data, entry).execution_profile(data, entry, contract, execution, review)
