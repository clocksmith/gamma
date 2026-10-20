"""Exact, coordinator-reviewed738 policy migration for the868 dispatch addition."""
import copy
from pathlib import Path
from .campaign_exact_integer import need, check, sha, distinct, digest

HISTORICAL_POLICY = '451d80c4080abb39a9ecb2a79713a6b47b58d11f175320cf8ab5fd2df8aeea9b'
OLD_IMPORT = 'from . import campaign_uint1024_dispatch as integer_profile'
NEW_IMPORT = 'from . import campaign_868_dispatch as integer_profile'

def expected_reader(old):
    need(old.count(OLD_IMPORT) == 2, 'Exact historical738 dispatcher imports required')
    return old.replace(OLD_IMPORT, NEW_IMPORT)

def validate(policy, allowed):
    transition_ref = policy.get('compatibility_transition')
    transition = check(transition_ref)
    need(transition.get('schema') == 'algsolve.738-868-module-transition.v1' and
         transition.get('status') == 'approved', 'Explicit738 transition approval required')
    historic_ref = transition.get('historical_policy')
    need(historic_ref.get('sha256') == HISTORICAL_POLICY, 'Wrong historical738 policy')
    historical = check(historic_ref)
    need(transition.get('approved_by') == policy.get('approved_by') and
         distinct(policy.get('approved_by'), allowed.get('source_author')),
         'Independent transition coordinator required')
    need(transition.get('old_modules') == historical['entries']['0738:javascript']['admission_modules'],
         'Historical738 module closure changed')
    need(transition.get('new_modules') == allowed.get('admission_modules'),
         'Transition module closure differs')
    # Only module identities and explicit transition provenance can change.
    restored = copy.deepcopy(policy)
    restored.pop('compatibility_transition')
    target = restored['entries']['0738:javascript']
    prior = historical['entries']['0738:javascript']
    for name in ['admission_modules', 'admission_validator_sha256']:
        target[name] = prior[name]
    need(digest(restored) == digest(historical), '738 migration changed evidence/domain/approval/comparison')
    return [transition_ref, historic_ref]
