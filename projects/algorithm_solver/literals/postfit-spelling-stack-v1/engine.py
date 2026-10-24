"""One fit-derived menu; at most two independent per-source spelling passes."""
import time
import common as c
matches=c.prior('engine').validation_matches


def menu(texts,vocab):
    state=c.evaluate(texts,vocab);records=c.rewrite.records(texts)
    return {'names':c.names(vocab,records),'contexts':c.contexts(state,records),
            'source_sha256':c.p.digest_sources(texts),'dictionary_binary_sha256':c.sha(c.analyze.dictionary_bytes(vocab))}


def apply(texts,vocab,sealed,initial_ledger=None,checkpoint=None,proposal_cap=153600,phase='fit',dictionaries=None):
    started=time.monotonic();ledger=c.BanLedger();selected=dict(texts);trace=[];initial_failures=[];count=0
    if initial_ledger:
        ledger.variants=dict(initial_ledger['variants']);ledger.forbidden=set(initial_ledger['banned']);ledger.encounters=list(initial_ledger['encounters'])
    dictionaries=dictionaries or {'self':vocab}
    def check_bans():
        if any(set(words)&ledger.forbidden for words in dictionaries.values()):
            raise c.LegalityFailure('Global fixed dictionary/source-body ban collision')
    def result(complete):
        return {'complete':complete,'original':dict(texts),'selected':dict(selected),'vocab':list(vocab),
            'names':sealed['names'],'contexts':sealed['contexts'],'trace':trace,'ledger':ledger.receipt(),
            'initial_coverage_failures':initial_failures,'proposals':count,
            'accepted':sum(row['accepted'] is not None for row in trace),'seconds':time.monotonic()-started}
    try:
        ledger.encounter(texts,phase+':initial')
        check_bans()
        for pid in sorted(texts,key=int):
            try:state=c.evaluate({pid:texts[pid]},vocab)
            except ValueError:initial_failures.append(pid);continue
            for pass_no in range(2):
                records=c.rewrite.records(state['sources']);record=records[pid];best=None
                row={'pid':pid,'pass':pass_no,'trials':[],'accepted':None};trace.append(row)
                for context in sealed['contexts']:
                    bids=matches(state['sources'][pid],record,context['pattern'])
                    local={'pattern':context['pattern'],'matches':[[pid,bid] for bid in bids]}
                    for target in sealed['names']:
                        if count>=proposal_cap:raise c.HardDeadline('Proposal cap exhausted')
                        group=c.make_group(state['sources'],records,local,target,min_support=1)
                        if group is None:continue
                        count+=1;ledger.pending_group=group
                        ledger.encounter(group['updates'],f'{phase}:{pid}:{pass_no}:{group["id"]}')
                        check_bans()
                        ledger.assert_incumbent(state)
                        try:got=c.evaluate(group['updates'],vocab,state)
                        except ValueError:got=None
                        row['trials'].append({'group':group,'before_score':list(c.cost(state)),
                            'score':None if got is None else list(c.cost(got)),'coverage':got is not None})
                        if got is not None and c.cost(got)<c.cost(state) and (best is None or c.tie(got)<c.tie(best[0])):
                            best=(got,len(row['trials'])-1)
                if best is None:break
                state=best[0];selected[pid]=state['sources'][pid];row['accepted']=best[1]
                if checkpoint:checkpoint(result(False))
        value=result(True)
        if checkpoint:checkpoint(value)
        return value
    except BaseException:
        if checkpoint:checkpoint(result(False))
        raise
