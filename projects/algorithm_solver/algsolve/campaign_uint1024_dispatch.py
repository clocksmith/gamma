"""Outer 738-only dispatch; existing633/670 dispatcher remains policy-identical."""
from . import campaign_integer_dispatch as previous,campaign_exact_integer as common,campaign_738_integer as monotone
distinct=common.distinct
def requires_profile(data,entry):
    reference=data.get('inputs',{}).get('uint1024_policy')
    if reference is None:return False
    policy=common.check(reference)
    common.need(policy.get('schema')=='algsolve.uint1024-admission-policy.v1' and type(policy.get('entries')) is dict and set(policy['entries'])=={'0738:javascript'},'Invalid738 coordinator policy scope')
    return common.key(entry) in policy['entries']
def select(data,entry):
    required=requires_profile(data,entry)
    if common.key(entry)=='0738:javascript':
        common.need(not common.requires_profile(data,entry) and not previous.requires_square(data,entry),'Combined alternate profiles forbidden')
        return monotone
    common.need(not required,'Unsupported uint1024 entry')
    return previous.select(data,entry)
def reject_legacy(data,entry,*documents):
    common.need(not requires_profile(data,entry),'Coordinator738 policy requires version3 exact integer admission; downgrade forbidden')
    return previous.reject_legacy(data,entry,*documents)
def profile(data,entry,contract):return select(data,entry).profile(data,entry,contract)
def execution_profile(data,entry,contract,execution,review):return select(data,entry).execution_profile(data,entry,contract,execution,review)
