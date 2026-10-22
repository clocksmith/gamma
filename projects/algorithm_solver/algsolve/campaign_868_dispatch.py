"""Exact868/1056 outer dispatch. Prior profiles retain their validators."""
from . import campaign_uint1024_dispatch as previous
from . import campaign_exact_integer as common
from . import campaign_868_integer as gap

distinct = common.distinct

def requires_989(data, entry):
    reference = data.get('inputs', {}).get('integer989_policy')
    if reference is None: return False
    policy = common.check(reference)
    common.need(policy.get('schema') == 'algsolve.integer989-admission-policy.v1' and
                type(policy.get('entries')) is dict and set(policy['entries']) == {'0989:javascript'},
                '989 coordinator policy must contain only0989JavaScript')
    return common.key(entry) in policy['entries']


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

def reject_domain(data, entry):
    reference = data.get('inputs', {}).get('domain_successor_policy')
    if reference is None:
        common.need('domain_successor_installation' not in data.get('inputs', {}),
                    'Incomplete domain policy installation')
        return
    policy = common.check(reference)
    ids = (764, 765, 775, 777, 778, 779, 785, 787, 793, 795, 804, 807, 1260, 1275, 1287)
    entries = {f'{number:04d}:{language}' for number in ids
               for language in ('javascript', 'python')}
    common.need(policy.get('schema') == 'gamma.domain-successor-policy.v1' and
                policy.get('profile_id') == 'assigned20-pinned-domain-v2' and
                policy.get('status') == 'approved' and policy.get('approved_by') == '/root' and
                type(policy.get('entries')) is dict and set(policy['entries']) == entries and
                'domain_successor_installation' in data.get('inputs', {}),
                'Explicit15-pair domain policy required')
    common.need(common.key(entry) not in entries,
                'Registered domain successor requires explicit route; legacy downgrade forbidden')

def select(data, entry):
    reject_domain(data, entry)
    required989 = requires_989(data, entry)
    required = requires_profile(data, entry)
    required1056 = requires_1056(data, entry)
    if common.key(entry) == '0989:javascript':
        common.need(not common.requires_profile(data, entry) and
                    not previous.previous.requires_square(data, entry) and
                    not previous.requires_profile(data, entry) and not required and not required1056,
                    'Combined alternate profiles forbidden')
        from . import campaign_989_integer as carry
        return carry
    common.need(not required989, 'Unsupported989 alternate entry')
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
    reject_domain(data, entry)
    common.need(not requires_989(data, entry),
                "Coordinator989 policy requires version3; downgrade forbidden")
    common.need(not requires_1056(data, entry),
                'Coordinator1056 policy requires version3; downgrade forbidden')
    common.need(not requires_profile(data, entry),
                'Coordinator868 policy requires version3; downgrade forbidden')
    return previous.reject_legacy(data, entry, *documents)

def profile(data, entry, contract):
    return select(data, entry).profile(data, entry, contract)

def execution_profile(data, entry, contract, execution, review):
    return select(data, entry).execution_profile(data, entry, contract, execution, review)
