"""Deterministic full-population recognition documents; no encoder or source loader.

Operator-pinned metadata/authority inputs are not request parameters. Hash pins
bind bytes, not approval authority. Public-contract enrichment never removes a
competitor, creates qualification, or turns absent knowledge into a negative fact.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import stat

from . import boundary_policy
from .catalogue import digest, validate

ID = re.compile(r'leetcode:[1-9][0-9]*\Z', re.ASCII)
HASH = re.compile(r'[0-9a-f]{64}\Z', re.ASCII)
MAX_BYTES = 32 * 1024 * 1024


def encoded(value):
    return (json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':'), allow_nan=False)+'\n').encode('utf-8')


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def fields(value, required, optional=()):
    if not isinstance(value, dict) or not set(required) <= set(value) or set(value)-set(required)-set(optional):
        raise ValueError('missing or unknown document-builder fields')


def decode(raw):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError('duplicate JSON key')
            result[key] = value
        return result
    return json.loads(raw, object_pairs_hook=unique,
        parse_constant=lambda _: (_ for _ in ()).throw(ValueError('nonfinite JSON')))


def descriptor(spec):
    fields(spec, ('path', 'sha256'))
    if (not isinstance(spec['path'], str) or not Path(spec['path']).is_absolute() or
            not isinstance(spec['sha256'], str) or not HASH.fullmatch(spec['sha256'])):
        raise ValueError('operator-pinned absolute artifact descriptor required')


def pinned_metadata(spec):
    """Only explicit metadata files; never follows paths found in their contents."""
    descriptor(spec)
    with Path(spec['path']).open('rb') as stream:
        raw = stream.read(MAX_BYTES+1)
    if len(raw)>MAX_BYTES or sha(raw)!=spec['sha256']:
        raise ValueError('metadata size/hash mismatch')
    return decode(raw)


def authority_bytes(spec, roots):
    """Bounded exact regular-file read under operator-approved roots, no symlinks."""
    descriptor(spec)
    choices = [root for root in roots if spec['path'].startswith(root+'/')]
    if not choices:
        raise ValueError('authority artifact outside pinned roots')
    root = max(choices, key=len);parts=spec['path'][len(root)+1:].split('/')
    if any(p in ('','.','..') for p in parts) or '\\' in spec['path']:
        raise ValueError('noncanonical authority path')
    directory=os.open(root,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
    try:
        for part in parts[:-1]:
            child=os.open(part,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW,dir_fd=directory)
            os.close(directory);directory=child
        fd=os.open(parts[-1],os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK,dir_fd=directory)
        try:
            if not stat.S_ISREG(os.fstat(fd).st_mode):
                raise ValueError('authority must be a regular file')
            with os.fdopen(fd,'rb',closefd=False) as stream:raw=stream.read(MAX_BYTES+1)
        finally:os.close(fd)
    finally:os.close(directory)
    if len(raw)>MAX_BYTES or sha(raw)!=spec['sha256']:
        raise ValueError('authority size/hash mismatch')
    return raw


def semantic_fields(contract, kind, pid):
    """Only named semantic fields become text; no cases/source/provenance extraction."""
    if kind=='foundation':
        if (contract.get('schema') not in ('gamma.reviewed-official-foundation-contract.v1','gamma.reviewed-official-foundation-contract.v2') or
                contract.get('official_problem_id')!=int(pid.split(':')[1]) or contract.get('problem_id')!=pid):
            raise ValueError('unsupported exact foundation identity')
        result=contract['official_result'];domain=contract['official_preconditions'];parameters=contract['canonical_parameters']
        objective=result.get('semantics') if isinstance(result,dict) else result
    else:
        if contract.get('problem_id')!=pid or contract.get('numeric_problem_id')!=int(pid.split(':')[1]):
            raise ValueError('reviewed statement identity mismatch')
        result=contract['result'];domain=contract['domain'];interface=contract['interface']
        if interface.get('entrypoint')!='solve' or interface.get('arguments')!='ordered-positional':
            raise ValueError('noncanonical reviewed interface')
        parameters=interface['parameters']
        objective=result.get('semantics',result.get('objective')) if isinstance(result,dict) else result
        if objective is None:objective=result
    values={'objective':objective,'result':result,'input_domain':domain,
            'ordered_interface':{'entrypoint':'solve','arguments':'ordered-positional','parameters':parameters}}
    for key,value in values.items():
        if not isinstance(value,(str,list,dict)) or not value or len(encoded(value))>65536:
            raise ValueError('missing or excessive whitelisted semantic field: '+key)
    return values


def enrich(row, gate, roots):
    pid=row['problem_id'];kind=row['kind']
    def read(spec):
        # Revalidate all six independent metadata pins immediately before EACH
        # authority payload read, even repeated opens of one combined artifact.
        boundary_policy.authorize_before_open(pid,gate['artifact_paths'],gate['trusted_hashes'],
            language='python',payload_kind='statement')
        return decode(authority_bytes(spec,roots))
    if kind=='normative-catalogue':
        fields(row,('problem_id','kind','catalogue','universe','verified_receipts','language','problem_contract_sha256'))
        if row['language'] not in ('javascript','python') or not HASH.fullmatch(row['problem_contract_sha256']):
            raise ValueError('explicit normative contract selector required')
        universe=read(row['universe']);catalogue=read(row['catalogue']);receipts=read(row['verified_receipts'])
        validate(universe,catalogue,receipts)
        selected=[r for r in catalogue['problems'] if r['problem_id']==pid]
        if len(selected)!=1:raise ValueError('exact catalogue identity missing')
        impl=selected[0]['implementations'][row['language']]
        if impl.get('status')!='qualified' or impl.get('evidence_class')!='normative-typed-effects':
            raise ValueError('admitted/probe/missing source is not normative statement authority')
        provenance=impl['provenance']
        if 'public_foundation' in provenance:
            contract=provenance['public_foundation']['problem_contract'];kind='foundation';semantic=contract
        elif 'public_batch' in provenance:
            contract=provenance['public_batch']['problem_contract']
            if contract.get('schema')!='gamma.reviewed-public-batch-contract.v1':raise ValueError('unsupported public batch contract')
            kind='batch';semantic=contract['reviewed_statement_contract']
        else:raise ValueError('unsupported normative authority provenance')
        if digest(contract)!=row['problem_contract_sha256'] or digest(contract)!=impl['problem_contract_sha256']:
            raise ValueError('exact normative contract hash mismatch')
        values=semantic_fields(semantic,kind,pid)
        evidence={'knowledge_class':'reviewed-normative-contract','authority_sha256':digest(contract),
            'catalogue_sha256':row['catalogue']['sha256'],'receipt_sha256':impl['receipt_sha256'],
            'verified_receipts_sha256':row['verified_receipts']['sha256'],
            'selected_fields_schema':kind,'scope':impl['contract_scope'],'caveats':impl['caveats']}
    elif kind=='reviewed-public-batch':
        fields(row,('problem_id','kind','authority','review','freeze','statement_sha256'))
        authority=read(row['authority']);review=read(row['review']);freeze=read(row['freeze'])
        if (authority.get('schema')!='gamma.public-batch-authority-review.v1' or
                authority.get('freeze_sha256')!=row['freeze']['sha256'] or
                authority.get('review_sha256')!=row['review']['sha256'] or
                authority.get('review_scope')!='independent-statement-identity-domain-interface-effects-complexity' or
                not authority.get('reviewer') or authority.get('source_publication_authorized') is not False or
                review.get('independent_review') is not True or review.get('freeze_sha256')!=row['freeze']['sha256'] or
                int(pid.split(':')[1]) not in freeze.get('ids',[])):
            raise ValueError('independent public authority/review/freeze binding missing')
        evidence_rows=authority.get('evidence_artifacts')
        if not isinstance(evidence_rows,list) or not evidence_rows or any(not isinstance(e,dict) or not isinstance(e.get('sha256'),str) or not HASH.fullmatch(e['sha256']) or e.get('role') not in ('official-statement','reviewed-statement-snapshot','identity-clause-override') for e in evidence_rows):
            raise ValueError('independent authority evidence anchors required')
        contract=authority.get('contracts',{}).get(pid)
        if not isinstance(contract,dict) or contract.get('statement_sha256')!=row['statement_sha256'] or not HASH.fullmatch(row['statement_sha256']):
            raise ValueError('exact statement authority binding missing')
        values=semantic_fields(contract,'batch',pid)
        evidence={'knowledge_class':'independently-reviewed-public-contract','authority_sha256':row['authority']['sha256'],
            'review_sha256':row['review']['sha256'],'freeze_sha256':row['freeze']['sha256'],
            'statement_sha256':row['statement_sha256'],'selected_fields_schema':'batch',
            'scope':'Reviewed public contract only; this path creates no source qualification.',
            'caveats':['Finite source verification and artifact eligibility remain separate.']}
    else:raise ValueError('unsupported authority adapter')
    return values,evidence


def build(config):
    fields(config,('schema','title_metadata','boundary_gate','authority_roots','authorities','expected_population'),('baseline_documents',))
    if config['schema']!='gamma.recognition-document-plan.v1' or type(config['expected_population'])is not int or config['expected_population']<1:
        raise ValueError('explicit document-plan population required')
    gate=pinned_metadata(config['boundary_gate'])
    fields(gate,('schema','artifact_paths','trusted_hashes'))
    if gate['schema']!='gamma.boundary-gate-config.v1':raise ValueError('unsupported boundary gate')
    titles=pinned_metadata(config['title_metadata']);rows=titles.get('rows')
    if not isinstance(rows,list) or len(rows)!=config['expected_population']:raise ValueError('complete metadata population required')
    ids=[r.get('global_problem_id')for r in rows]
    if any(not isinstance(pid,str)or not ID.fullmatch(pid)for pid in ids)or len(set(ids))!=len(ids):raise ValueError('duplicate or invalid stable identities')
    universe=pinned_metadata({'path':gate['artifact_paths']['universe'],'sha256':gate['trusted_hashes']['universe']})
    if set(ids)!=set(universe['eligible_problem_ids']):raise ValueError('competitors cannot be filtered by access or qualification')
    baseline={};baseline_sha=None
    if 'baseline_documents' in config:
        old=pinned_metadata(config['baseline_documents']);old_docs=old.get('documents')
        if not isinstance(old_docs,list) or [d.get('problem_id')for d in old_docs]!=ids:
            raise ValueError('baseline competitor identity/order mismatch')
        for metadata,doc in zip(rows,old_docs):
            if set(doc)!={'problem_id','text'} or doc['text']!=metadata.get('title'):
                raise ValueError('baseline must contain exact title-only document bytes')
            baseline[doc['problem_id']]=doc['text']
        baseline_sha=config['baseline_documents']['sha256']
    roots=config['authority_roots']
    if (not isinstance(roots,list)or not roots or any(not isinstance(r,str)or not r.startswith('/')or r=='/'or any(x in ('','.','..')for x in r[1:].split('/'))for r in roots)or len(set(roots))!=len(roots)):
        raise ValueError('unique canonical operator authority roots required')
    authorities=config['authorities']
    if not isinstance(authorities,list):raise ValueError('authority rows required')
    keyed={}
    for row in authorities:
        if not isinstance(row,dict)or row.get('problem_id')not in ids or row['problem_id']in keyed:raise ValueError('extra/duplicate authority identity')
        keyed[row['problem_id']]=row
    docs=[];enriched=0
    for row in rows:
        pid=row['global_problem_id'];title=row.get('title')
        if not isinstance(title,str)or not title.strip() or '\n'in title or '\r'in title:raise ValueError('nonempty single-line metadata title required')
        base_text=baseline.get(pid,title)
        text=base_text
        evidence={'knowledge_class':'title-only','authority_sha256':None,
            'scope':'Title metadata only; missing contract authority is unknown, not false or inapplicable.',
            'caveats':['A title match does not establish semantic scope or source eligibility.']}
        provenance={'problem_id':{'artifact_sha256':config['title_metadata']['sha256'],'field':'rows[].global_problem_id'},
            'title':{'artifact_sha256':config['title_metadata']['sha256'],'field':'rows[].title'}}
        if pid in keyed:
            values,evidence=enrich(keyed[pid],gate,roots);enriched+=1
            text+='\n'
            for key,label in (('objective','Objective'),('result','Result'),('input_domain','Input domain'),('ordered_interface','Ordered interface')):
                text+=label+': '+encoded(values[key]).decode().rstrip('\n')+'\n'
                provenance[key]={'authority_sha256':evidence['authority_sha256'],'whitelisted_semantic_field':key}
        data=text.encode('utf-8')
        docs.append({'problem_id':pid,'text':text,'document_sha256':sha(data),'bytes':len(data),
            'authority':evidence,'field_provenance':provenance,
            'baseline_document_sha256':sha(base_text.encode('utf-8')),
            'text_changed':text!=base_text})
    return {'schema':'gamma.recognition-documents.v1','population':len(docs),'stable_ids':ids,
        'documents':docs,'documents_sha256':sha(encoded(docs)),'plan_sha256':sha(encoded(config)),
        'title_metadata_sha256':config['title_metadata']['sha256'],'boundary_gate_sha256':config['boundary_gate']['sha256'],
        'baseline_documents_sha256':baseline_sha,
        'changed_problem_ids':[d['problem_id']for d in docs if d['text_changed']],
        'unchanged_problem_ids':[d['problem_id']for d in docs if not d['text_changed']],
        'cache_reuse_condition':'Text-stable IDs may reuse vectors only with identical independently pinned encoder/tokenizer/pooling/instruction/truncation/normalization identities; this builder loads no vectors.',
        'builder_sha256':sha(Path(__file__).read_bytes()),'enriched':enriched,'title_only':len(docs)-enriched,
        'knowledge_asymmetry':'Enriched identities have reviewed domain text; all other identities remain competitors with title-only knowledge. No negative semantic inference is licensed.',
        'ranking_input':'Only documents[].text; authority class, hashes, receipts, qualification and availability are not ranking features.',
        'source_availability_filter':False,'qualification_created':False,'candidate_source_reads':0,'case_reads':0,
        'encoder_executed':False,'confirmation_read':False,'recognition_qualified':False}


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plan',type=Path,required=True);parser.add_argument('--plan-sha256',required=True)
    parser.add_argument('--output',type=Path,required=True);args=parser.parse_args(argv)
    config=pinned_metadata({'path':str(args.plan),'sha256':args.plan_sha256});result=build(config)
    with args.output.open('xb')as stream:stream.write(encoded(result))
    print(json.dumps({k:result[k]for k in ('population','enriched','title_only','documents_sha256')}))


if __name__=='__main__':main()
