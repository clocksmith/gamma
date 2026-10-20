"""Explicit two-profile dispatch. No changes to the frozen670 validator/policy."""
from . import campaign_exact_integer as old,campaign_633_integer as square
distinct=old.distinct

def requires_square(data,entry):
    reference=data.get('inputs',{}).get('uint64_bool_policy')
    if reference is None:return False
    policy=old.check(reference)
    old.need(policy.get('schema')=='algsolve.uint64-bool-admission-policy.v1' and type(policy.get('entries')) is dict,'Wrong633 coordinator policy')
    old.need(set(policy['entries'])<= {'0633:python','0633:javascript'},'633 policy includes unsupported entry')
    return old.key(entry) in policy['entries']

def select(data,entry):
    key=old.key(entry)
    if key=='0670:javascript':
        old.need(not requires_square(data,entry),'Combined alternate profiles forbidden')
        return old
    if key in ['0633:python','0633:javascript']:
        old.need(not old.requires_profile(data,entry),'Combined alternate profiles forbidden')
        return square
    raise ValueError('Unsupported alternate integer profile entry')

def reject_legacy(data,entry,*documents):
    old.need(not requires_square(data,entry),'Coordinator633 policy requires version3 exact integer admission; downgrade forbidden')
    return old.reject_legacy(data,entry,*documents)

def profile(data,entry,contract):
    return select(data,entry).profile(data,entry,contract)

def execution_profile(data,entry,contract,execution,review):
    return select(data,entry).execution_profile(data,entry,contract,execution,review)
