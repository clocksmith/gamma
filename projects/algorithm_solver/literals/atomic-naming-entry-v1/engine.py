"""Bounded source-only, dictionary-only, alternating and atomic transactions."""
from collections import Counter
from itertools import combinations
import time
import core as c

ARMS=('D','S','A','J')

class Budget:
    def __init__(self,limits):self.cap=limits['trials'];self.seconds=limits['seconds'];self.start=time.monotonic();self.trials=0
    def expired(self):return self.trials>=self.cap or time.monotonic()-self.start>=self.seconds
    def stop(self):return 'trial_limit' if self.trials>=self.cap else 'time_limit'


def removal_sets(state,additions,loss):
    needed=max(0,len(state['vocab'])+len(additions)-256)
    if needed==0:return [()]
    shortlist=sorted(loss,key=lambda w:(loss[w],w))[:12]
    def score(words):return tuple(sum(loss[w][i] for w in words) for i in range(3)),tuple(sorted(words))
    return sorted(combinations(shortlist,needed),key=score)[:12]


def menus(state,records,names,ledger,round_no,budget=None):
    contexts=c.contexts(state,records);groups=[];rendered=[]
    for context in contexts:
        for name in names:
            if budget and budget.expired():return contexts,groups,False,rendered
            group=c.make_group(state['sources'],records,context,name)
            if group is None:continue
            # Every rendered variant is encountered, even if support/length makes
            # its transaction ineligible or the later full-fit trial rejects it.
            rendered.append(group['id'])
            ledger.pending_group=group
            ledger.encounter(group['updates'],f'fit:{round_no}:group:{group["id"]}')
            ledger.assert_incumbent(state)
            if group['eligible']:groups.append(group)
    return contexts,groups,True,rendered


def streams(state,groups,forbidden,arm):
    dictionary=arm in ('D','A','J');source=arm in ('S','A','J')
    ordinary=[{'kind':'dictionary','additions':words,'group':None} for words in c.literal_proposals(state,forbidden)] if dictionary else []
    projected=[];naming=[];joint=[]
    for group in groups:
        if source:naming.append({'kind':'source','additions':[],'group':group})
        for offered in ([group['target']],[group['target'],group['fragment']]):
            additions=c.order(set(offered)-set(state['vocab']))
            if not additions or any(word in forbidden for word in additions):continue
            if dictionary:projected.append({'kind':'context_dictionary','additions':additions,'group':group})
            if arm=='J':joint.append({'kind':'joint','additions':additions,'group':group})
    groups=[ordinary,projected,naming,joint]
    for index in range(max(map(len,groups),default=0)):
        for stream in groups:
            if index<len(stream):yield stream[index]


def optimize(texts,initial,names,arm,limits,checkpoint=None):
    assert arm in ARMS
    budget=Budget(limits);ledger=c.BanLedger();ledger.encounter(texts,'fit:initial')
    state=c.evaluate(texts,initial);budget.trials+=1;ledger.assert_incumbent(state)
    mandatory={word for word in initial if len(word)==1}
    log=[];rounds=[];round_no=0;coverage=0;counts=Counter();stop='bounded_neighborhood_no_improvement'
    def snapshot(complete=False):
        value={'complete':complete,'arm':arm,'state':state,'trace':log,'round_menus':rounds,'ledger':ledger.receipt(),
               'trials':budget.trials,'rounds':round_no,'coverage_failures':coverage,'trial_composition':dict(counts)}
        if checkpoint:checkpoint(value)
        return value
    snapshot()
    try:
        while not budget.expired():
            records=c.rewrite.records(state['sources'])
            contexts,groups,full,rendered=menus(state,records,names,ledger,round_no,budget)
            menu={'round':round_no,'contexts':contexts,'groups':groups,'complete':full,
                  'rendered_group_ids':rendered,'source_state_sha256':c.digest_sources(state['sources']),'banned_sha256':c.sha(c.canonical(sorted(ledger.forbidden)).encode())}
            rounds.append(menu);snapshot()
            if not full:stop=budget.stop();break
            loss={};tested=set();best=None
            def trial(additions,removals,kind,group=None):
                nonlocal best,coverage
                if budget.expired():return None
                actual_sources=({**state['sources'],**group['updates']} if kind in ('source','joint') else state['sources'])
                vocab=c.order((set(state['vocab'])-set(removals))|set(additions))
                assert mandatory<=set(vocab) and len(vocab)<=256 and not set(additions)&set(removals)
                if set(vocab)&ledger.forbidden:return None
                signature=(c.digest_sources(actual_sources),tuple(vocab))
                if signature in tested:return None
                tested.add(signature);budget.trials+=1;started=time.monotonic()
                try:got=c.evaluate(actual_sources,vocab,state)
                except ValueError:got=None;coverage+=1
                counts[kind]+=1
                row={'trial':budget.trials,'round':round_no,'kind':kind,'additions':c.order(additions),'removals':c.order(removals),
                     'group_id':None if group is None else group['id'],'coverage':got is not None,
                     'score':None if got is None else list(c.cost(got)),'trial_seconds':time.monotonic()-started}
                log.append(row)
                if got is not None and c.cost(got)<c.cost(state) and (best is None or c.tie(got)<c.tie(best[0])):best=(got,row)
                return got
            if arm in ('D','A','J'):
                for word in state['vocab']:
                    if word in mandatory:continue
                    if budget.expired():break
                    got=trial([], [word], 'remove')
                    loss[word]=tuple(a-b for a,b in zip(c.cost(got),c.cost(state))) if got else (float('inf'),)*3
            if not budget.expired():
                for offered in streams(state,groups,ledger.forbidden,arm):
                    if budget.expired():break
                    additions=offered['additions']
                    for removals in removal_sets(state,additions,loss):
                        if budget.expired():break
                        trial(additions,removals,offered['kind'],offered['group'])
            if best is None:
                stop=budget.stop() if budget.expired() else 'bounded_neighborhood_no_improvement';break
            got,winner=best
            kind=('N_improvement' if got['N']<state['N'] else 'C_plateau' if got['C']<state['C'] else 'package_plateau')
            log.append({'accepted_round':round_no+1,'accepted_trial':winner['trial'],'kind':winner['kind'],'improvement':kind,
                        'before':c.brief(state),'after':c.brief(got),'source_sha256':c.digest_sources(got['sources']),
                        'dictionary':got['vocab']})
            state=got;round_no+=1;snapshot()
        else:stop=budget.stop()
        final_records=c.rewrite.records(state['sources']);final_contexts=c.contexts(state,final_records)
        result=snapshot(True)
        result.update(stop=stop,seconds=time.monotonic()-budget.start,
                      overrun_seconds=max(0,time.monotonic()-budget.start-budget.seconds),names=names,
                      final_contexts=final_contexts,initial_character_count=len(mandatory))
        return result
    except BaseException as error:
        result=snapshot(False);result.update(error_type=type(error).__name__,error=str(error),stop='failed')
        if checkpoint:checkpoint(result)
        raise


def validation_matches(text,record,pattern):
    found=[]
    if record['unsafe'] or not text.isascii():return found
    for variable in record['variables']:
        if not variable['eligible']:continue
        word=''.join(variable['name'] if part is None else part for part in pattern)
        start=text.find(word)
        while start>=0:
            if c.pattern_at(text,variable['spans'],start,start+len(word))==pattern:
                found.append(variable['id']);break
            start=text.find(word,start+1)
    return found


def validation(texts,vocab,names,contexts,fit_ledger,arm,checkpoint=None):
    ledger=c.BanLedger();ledger.variants=dict(fit_ledger['variants']);ledger.forbidden=set(fit_ledger['banned']);ledger.encounters=list(fit_ledger['encounters'])
    selected=dict(texts);trace=[];initial_failures=[]
    try:
        ledger.encounter(texts,'validation:initial')
        # Check source/body legality before source adaptation. Coverage failure in an
        # initial validation source is retained; adaptation may not rescue it.
        if set(vocab)&ledger.forbidden:
            if checkpoint:checkpoint({'selected':selected,'trace':trace,'ledger':ledger.receipt(),'error':'Initial validation bans invalidate dictionary','complete':False})
            raise c.LegalityFailure('Initial validation bans invalidate dictionary')
        for pid,text in texts.items():
            try:state=c.evaluate({pid:text},vocab)
            except ValueError:initial_failures.append(pid);continue
            if arm not in ('S','A','J'):continue
            for pass_no in range(2):
                recs=c.rewrite.records(state['sources']);rec=recs[pid];best=None;trials=[]
                for context in contexts:
                    matches=validation_matches(state['sources'][pid],rec,context['pattern'])
                    local={'pattern':context['pattern'],'matches':[[pid,bid] for bid in matches]}
                    for target in names:
                        group=c.make_group(state['sources'],recs,local,target,min_support=1)
                        if group is None:continue
                        ledger.pending_group=group
                        ledger.encounter(group['updates'],f'validation:{pid}:{pass_no}:{group["id"]}')
                        try:ledger.assert_incumbent(state)
                        except c.LegalityFailure:
                            if checkpoint:checkpoint({'selected':selected,'trace':trace,'ledger':ledger.receipt(),'failed_group':group,'complete':False})
                            raise
                        # Fit support determines the sealed context; source transfer
                        # itself does not require an occurrence in another val ID.
                        try:got=c.evaluate(group['updates'],vocab,state)
                        except ValueError:got=None
                        row={'pid':pid,'pass':pass_no,'group':group,'before_score':list(c.cost(state)),
                             'score':None if got is None else list(c.cost(got)),'coverage':got is not None}
                        trials.append(row)
                        if got is not None and c.cost(got)<c.cost(state) and (best is None or c.tie(got)<c.tie(best[0])):best=(got,len(trials)-1)
                trace.append({'pid':pid,'pass':pass_no,'trials':trials,'accepted':None if best is None else best[1]})
                if best is None:break
                state=best[0];selected[pid]=state['sources'][pid]
                if checkpoint:checkpoint({'selected':selected,'trace':trace,'ledger':ledger.receipt(),'initial_coverage_failures':initial_failures})
        result={'selected':selected,'trace':trace,'ledger':ledger.receipt(),'initial_coverage_failures':initial_failures}
        if checkpoint:checkpoint(result)
        return result
    except BaseException as error:
        if checkpoint:checkpoint({'selected':selected,'trace':trace,'ledger':ledger.receipt(),'initial_coverage_failures':initial_failures,
                                  'complete':False,'error_type':type(error).__name__,'error':str(error)})
        raise
