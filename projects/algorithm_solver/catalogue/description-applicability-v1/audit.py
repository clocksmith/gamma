"""Bounded permitted-document coverage audit; never reads a query cohort."""
import json
from pathlib import Path
from collections import Counter
from guard import load_documents, sha, FACETS

ROOT=Path(__file__).parent
PLAN={'path':'/workspace/shared/gamma-recognition-documents-v2-20261025-2025b/plan.json',
      'sha256':'950fcbe6cce0a7c3aad8ae93dcd792c3ac7aa8514688be5f0758bf19ff733ca8'}
DOCUMENTS={'path':'/workspace/shared/gamma-recognition-documents-v2-20261025-2025b/documents.json',
           'sha256':'578dc19ba6b687071a5f1a54765b4537269bcf877aff153166c2b71bfa50cb1e'}

if __name__=='__main__':
    ids,contracts=load_documents(PLAN,DOCUMENTS)
    counts=Counter(k for c in contracts.values() for k in c['facts'])
    report={'schema':'gamma.description-applicability-coverage.v1','population':len(ids),
        'plan':PLAN,'documents':DOCUMENTS,
        'guard_sha256':sha(ROOT.joinpath('guard.py').read_bytes()),
        'facets':{f:{'known':counts[f],'unknown':len(ids)-counts[f]} for f in FACETS},
        'identities_with_facts':sum(bool(c['facts']) for c in contracts.values()),
        'contracts_with_conflicts':sum(bool(c['conflicts']) for c in contracts.values()),
        'all_competitors_retained_before_query':True,'query_cohorts_read':False,
        'source_reads':0,'encoder_invocations':0,'candidate_executions':0,
        'recognition_qualified':False,
        'evidence_scope':'Permitted contract extraction coverage, not recognition accuracy or semantic completeness.'}
    ROOT.joinpath('coverage.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    # Evidence is a derived view of the explicitly permitted contracts, not a new authority.
    ROOT.joinpath('contract-facets.json').write_text(json.dumps({'schema':'gamma.description-contract-facets.v1',
        'documents_sha256':DOCUMENTS['sha256'],'stable_ids':ids,'contracts':contracts},indent=2,sort_keys=True)+'\n')
    print(json.dumps(report,sort_keys=True))
