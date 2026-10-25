"""Bounded global indexed-fold impact, exact qualified bytes as inert data only."""
import hashlib,itertools,json,math,re,resource,sys,time
from pathlib import Path
import frontier as f
from run_synthetic import serial
from run_qualified_pair import CONFIG,CONFIG_SHA,KnownSpecService
from projects.algorithm_solver.catalogue import boundary_policy

BASE='/workspace/shared/gamma-character-basis-freeze-20261025-1820/contract.json'
BASE_SHA='fdc0ba6f1c35a4231d9981fd2353ca3b51a394f61fa4021c8971f1cf060305ff'
FOLD='/workspace/shared/gamma-fold19-freeze-20261025-1728/contract.json'
FOLD_SHA='2cb3ed045b00535a7f37f68f0895905d71e75af304962052ef7249492444f3d5'
RUN='/workspace/shared/gamma-dot-diagnostics/fold19-20261025-1729/contract.json'
RUN_SHA='b7a9e1ec43f5a0cac9b18e2152e23e253980db511883a94f55e1ae5efa28c542'
REPORT='/workspace/shared/gamma-dot-diagnostics/fold19-20261025-1729/report.json'
REPORT_SHA='b17f0f7cab276c68d97cc8be17213d83ff801766f8ee6bcf29664964292cf321'
VERIFIED='/workspace/shared/gamma-dot-diagnostics/fold19-verified.json'
VERIFIED_SHA='784a9799ac93c1c70617daca5d4b53caed72ef02ffbc5e4570946f5f92276ff4'
LEDGER='/workspace/shared/gamma-character-basis256-run-20261025-1821/ledger.jsonl'
HEAD='b41d1271e3f97e2da260a325b324d45dc046ed4d0fe5dbb32c7e799b6127be17'


def digest(x):return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def pinned(path,sha):
    raw=Path(path).read_bytes()
    if hashlib.sha256(raw).hexdigest()!=sha:raise ValueError('metadata hash mismatch')
    return json.loads(raw)


def main(output_name='JS-GLOBAL-RESULT-v2.json',predecessor=None,long_mode=False):
    resource.setrlimit(resource.RLIMIT_AS,(512*1024**2,512*1024**2))
    resource.setrlimit(resource.RLIMIT_CPU,(60,60))
    started=time.monotonic();deadline=started+55
    out=f.HERE/output_name
    if out.exists():raise ValueError('preserve old run; use a newly versioned runner/output')
    report=dict(schema='gamma.exact-component-frontier.js-global.v1',status='running',
        fit_denominator=300,m1_denominator=500,catalogue_denominator=4081,
        candidate_execution=False,protected_access=False,source_publication=False,m1_qualified=False,
        metadata_pins={BASE:BASE_SHA,FOLD:FOLD_SHA,RUN:RUN_SHA,REPORT:REPORT_SHA,VERIFIED:VERIFIED_SHA},
        source_opens=0,evaluations=0,nondominated_ledger=[])
    def checkpoint():
        report['wall_seconds']=time.monotonic()-started
        report['cpu_seconds']=time.process_time()
        report['peak_rss_kib']=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        out.write_text(json.dumps(report,sort_keys=True,indent=2,default=serial)+'\n')
    def check():
        if time.monotonic()>=deadline:raise TimeoutError('bounded global diagnostic deadline')
    try:
        base=pinned(BASE,BASE_SHA);fold=pinned(FOLD,FOLD_SHA);run=pinned(RUN,RUN_SHA)
        qualified=pinned(REPORT,REPORT_SHA);verified=pinned(VERIFIED,VERIFIED_SHA)
        if run['sources']!=fold['sources'] or qualified['contract_sha256']!=RUN_SHA or verified['report_sha256']!=REPORT_SHA or verified['qualified']!=19 or not verified['verified']:
            raise ValueError('fold source/qualification binding mismatch')
        # Canonical serialized source-freeze hash differs from on-disk pretty JSON.
        if run['source_freeze_sha256']!=hashlib.sha256((json.dumps(fold,sort_keys=True,separators=(',',':'))+'\n').encode()).hexdigest():raise ValueError('source freeze digest mismatch')
        chain='0'*64
        for line in Path(LEDGER).read_text().splitlines():
            event=json.loads(line);head=event.pop('sha256')
            if event['previous_sha256']!=chain or digest(event)!=head:raise ValueError('ledger chain mismatch')
            chain=head
        if chain!=HEAD:raise ValueError('accepted terminal ledger changed')
        report['baseline_ledger_head']=chain
        owners=base['owners'];references=base['references'];groups={pid:[] for pid in references}
        for key in base['source_rows']:groups[owners[key]].append(key)
        if len(groups)!=300 or len(base['source_rows'])!=875:raise ValueError('full fit denominator drift')
        hashes={row['sha256']:key for key,row in base['source_rows'].items()}
        foldkeys={pid:hashes[row['sha256']] for pid,row in fold['sources'].items()}
        if any(owners[key]!=pid for pid,key in foldkeys.items()):raise ValueError('fold owner mismatch')
        report['fold_alternatives']=19;report['already_present_exact_fold_alternatives']=len(foldkeys)
        report['new_unique_source_variants']=0
        config=pinned(CONFIG,CONFIG_SHA)
        gate_spec=config['source_access']['boundary_gate'];gate=pinned(gate_spec['path'],gate_spec['sha256'])
        # This initialization validates the complete service catalogue and boundary.
        KnownSpecService.from_config(CONFIG,CONFIG_SHA)
        # Gate all19 cohort owners before any source bytes; each individual open
        # below then revalidates the live boundary, including all other875 owners.
        for pid in foldkeys:
            boundary_policy.authorize_before_open('leetcode:'+pid,gate['artifact_paths'],gate['trusted_hashes'],language='javascript')
        texts={}
        for key,row in sorted(base['source_rows'].items()):
            check()
            boundary_policy.authorize_before_open('leetcode:'+owners[key],gate['artifact_paths'],gate['trusted_hashes'],language='javascript')
            path=Path(row['path'])
            if not path.is_absolute() or any(part.is_symlink() for part in (path,*path.parents)):
                raise ValueError('source locator symlink/relative path rejected')
            raw=path.read_bytes()
            if hashlib.sha256(raw).hexdigest()!=row['sha256']:raise ValueError('qualified source hash drift')
            texts[key]=raw.decode('utf8');report['source_opens']+=1
            if report['source_opens']%100==0:checkpoint()
        accelerator=f.load('exact_global_trie',f.LIT/'explicit-basis-v2/accelerator.py')
        accelerator.configure(base['kernel_sha256'],Path(base['kernel_path']))
        graph=accelerator.Graph(texts)
        def score(vocab,retire=False):
            check();vocab=tuple(vocab)
            if not 1<=len(vocab)<=256:return None
            rows=graph.score(vocab,materialize=True);report['evaluations']+=1
            choices={}
            for pid,keys in groups.items():
                reachable=[k for k in keys if rows[k] is not None]
                if not reachable:return None
                choices[pid]=min(reachable,key=lambda k:(rows[k]['selections'],rows[k]['characters'],k!=references[pid],k))
            if retire:
                used=set().union(*(set(rows[k]['used']) for k in choices.values()))
                clean=tuple(x for x in vocab if x in used)
                if clean!=vocab:return score(clean)
            counts=sorted(rows[k]['selections'] for k in choices.values());n=sum(counts);c=sum(rows[k]['characters'] for k in choices.values())
            m=dict(programs=300,selections=n,characters=c,median=f.median(counts),p95=counts[284],
                above32=sum(x>32 for x in counts),above96=sum(x>96 for x in counts),
                entries=len(vocab),literal_utf8_bytes=sum(len(x.encode()) for x in vocab),
                character_fraction=f.Fraction(c,n),unreachable_variants=sum(x is None for x in rows.values()))
            m['dictionary_bytes']=8+4*len(vocab)+m['literal_utf8_bytes']
            m['packet_bytes']=41*300+n
            m['decoder_bytes']=(f.LIT/'readable-v1/literal_codec.py').stat().st_size
            m['package_bytes']=m['dictionary_bytes']+m['packet_bytes']+m['decoder_bytes']
            return dict(vocabulary=vocab,rows=rows,choices=choices,metrics=m)
        initial=score(event['vocabulary'])
        if initial['choices']!=event['source_choices'] or any(initial['metrics'][k]!=event['metrics'][k] for k in ['selections','characters','entries','median','p95']):
            raise ValueError('independent full875 baseline mismatch')
        report['baseline']=initial['metrics'];report['same_vocabulary_plus19']=initial['metrics']
        report['same_vocabulary_comparison']='All19 exact owner/hash variants already present; deduplicated arm is identical.'
        checkpoint()
        helper=next(h for h in base['audited_helpers'] if h['name']=='indexedFold')
        helpertext=helper['text']
        if hashlib.sha256(helpertext.encode()).hexdigest()!=helper['sha256'] or sum(helpertext in texts[k] for k in foldkeys.values())!=19:
            raise ValueError('reviewed helper witness mismatch')
        compact=lambda s:''.join(s.split())
        # Hard containment exclusions cover all supplied complete sources and
        # complete solve bodies. The audited generic helper alone is an exception.
        banned={compact(s) for s in texts.values()}
        for s in texts.values():
            match=re.search(r'function\s+solve\s*\([^)]*\)\s*\{',s)
            if match and s.rfind('}')>=match.end():banned.add(compact(s[match.end():s.rfind('}')]))
        banned.discard('')
        def legal(s):
            if s==helpertext:return True
            return bool(s) and not any(b in compact(s) for b in banned)
        # Freeze a complete finite worklist of every adjacent2/3 existing exact
        # path-literal composite on19fold sources, <=48 codepoints, no full
        # function/braced body declarations; require2 distinct owner witnesses.
        witnesses={}
        for pid,key in sorted(foldkeys.items(),key=lambda x:int(x[0])):
            row=initial['rows'][key]
            if row is None:continue
            used=row['used']
            for width in (2,3):
                for at in range(len(used)-width+1):
                    piece=''.join(used[at:at+width])
                    if 2<=len(piece)<=48 and not any(x in piece for x in ('{','}','function')):
                        witnesses.setdefault(piece,set()).add(pid)
        pieces=sorted(p for p,w in witnesses.items() if len(w)>=2 and p not in initial['vocabulary'] and legal(p))
        # Every bundle is charged flat: reviewed helper plus one or two adjacent
        # deterministic candidates. No references between dictionary definitions.
        bundles=[(helpertext,)]+[(helpertext,p) for p in pieces]+[(helpertext,*pieces[i:i+2]) for i in range(0,len(pieces),2)]
        report['candidate_freeze']=dict(shared_composites=len(pieces),bundles=len(bundles),
            bundle_sha256=digest(bundles),rule='audited helper plus each legal2/3-trace composite, then consecutive pairs; full finite worklist, no top-K',
            scope='Exact fixed-basis insertion/unused retirement per bundle; not full dictionary optimum',helper_sha256=helper['sha256'])
        if predecessor is not None:
            prior_raw=(f.HERE/predecessor).read_bytes()
            prior=json.loads(prior_raw,object_hook=lambda x:f.Fraction(x['numerator'],x['denominator']) if set(x)=={'numerator','denominator'} else x)
            if prior['candidate_freeze']!=report['candidate_freeze'] or prior['baseline_ledger_head']!=HEAD:
                raise ValueError('resume universe/anchor drift')
            report['predecessor_result_sha256']=hashlib.sha256(prior_raw).hexdigest()
            report['nondominated_ledger']=prior['nondominated_ledger']
            report['starting_bundle_index']=prior['completed_bundles']
            # Recover the privately unpersisted incumbent from its aggregate hash.
            # In v2 there were no source switches and the helper retired; the one
            # extra literal can be reconstructed from the frozen finite universe.
            target=next(x['dictionary_sha256'] for x in prior['nondominated_ledger'] if x['metrics']==prior['best_metrics'])
            recovered=None
            for piece in pieces:
                proposed=tuple(initial['vocabulary'])+(piece,)
                if digest(proposed)==target:
                    recovered=score(proposed);break
            if recovered is None or any(recovered['metrics'].get(k)!=v for k,v in prior['best_metrics'].items()):
                raise ValueError('cannot recover exact prior incumbent without changing search')
            best=recovered;completed=prior['completed_bundles']
            report['best_metrics']=best['metrics']
            report['best_bundle_index']=pieces.index(piece)+1
        else:
            best=initial;completed=0
        if long_mode:
            from long_spans import complementary_worklist,pair_frontier_repairs,clean_union
            short_bundles=bundles
            report['legacy_baseline']=report['baseline']
            report['prior_candidate_freeze']=report['candidate_freeze']
            report['predecessor_best_bundle_index']=report.get('best_bundle_index')
            initial=best
            report['baseline']=initial['metrics']
            target_texts={pid:texts[key] for pid,key in foldkeys.items()}
            target_costs={pid:(initial['rows'][initial['choices'][pid]]['selections'],initial['rows'][initial['choices'][pid]]['characters']) for pid in foldkeys}
            bundles,long_summary,target_bindings=complementary_worklist(target_texts,initial['vocabulary'],helpertext,legal,target_costs,deadline-12)
            if long_mode=='paired':
                # Recover only exact prior frontier identities that were already
                # stored as aggregate hashes; never assume independent deltas add.
                targets={x['dictionary_sha256'] for x in prior['nondominated_ledger'] if x['metrics']['characters']<initial['metrics']['characters']}
                repairs={}
                for old_bundle in short_bundles:
                    candidate=tuple(event['vocabulary'])+tuple(p for p in old_bundle if p!=helpertext and p not in event['vocabulary'])
                    identity=digest(candidate)
                    if identity in targets:repairs[identity]=candidate
                unlocking_count=len(bundles)
                bundles,capacity_rejections=pair_frontier_repairs(initial['vocabulary'],list(repairs.values()),bundles)
                report['complementary_cross_product']=dict(prior_character_saving_frontier_states=len(targets),
                    exactly_hash_recovered_repair_states=len(repairs),unrecovered_states=len(targets)-len(repairs),
                    repair_dictionary_hashes=sorted(repairs),source_unlocking_bundles=unlocking_count,
                    exact_union_proposals=len(bundles),unions_requiring_explicit_retirement=capacity_rejections,
                    ordering='already capacity-legal unions first, then explicit retirement unions; every proposal retained',
                    caveat='Union costs are globally rescored, never added; unrecovered retirement-dependent repair states remain explicitly outside this bounded cross-product')
            report['long_span_freeze']=long_summary
            report['long_span_target_bindings_sha256']=digest(target_bindings)
            report['candidate_freeze']=dict(bundles=len(bundles),bundle_sha256=digest(bundles),
                rule=('Exact cross-product of hash-recovered character-saving prior frontier dictionaries and source-unlocking long-span bundles' if long_mode=='paired' else long_summary['declared_scope']),helper_sha256=helper['sha256'],min_long_span_codepoints=16)
            completed=0;report['starting_bundle_index']=0;report['completed_bundles']=0
            report['best_bundle_index']=None
            checkpoint()
        for old_state in report['nondominated_ledger']:
            old=old_state['metrics']
            old.setdefault('dictionary_bytes',8+4*old['entries']+old['literal_utf8_bytes'])
            old.setdefault('packet_bytes',41*300+old['selections'])
            old.setdefault('decoder_bytes',(f.LIT/'readable-v1/literal_codec.py').stat().st_size)
            old.setdefault('package_bytes',old['dictionary_bytes']+old['packet_bytes']+old['decoder_bytes'])
        report['absolute_character_cap']=initial['metrics']['characters']
        def record(state):
            m=state['metrics'];row=dict(metrics=m,dictionary_sha256=digest(state['vocabulary']),source_choices_sha256=digest(state['choices']))
            names=('selections','characters','median','p95','entries','literal_utf8_bytes')
            def dominates(a,b):return all(a['metrics'][k]<=b['metrics'][k] for k in names) and any(a['metrics'][k]<b['metrics'][k] for k in names)
            if not any(dominates(x,row) or x==row for x in report['nondominated_ledger']):
                report['nondominated_ledger']=[x for x in report['nondominated_ledger'] if not dominates(row,x)]+[row]
        record(initial)
        search_complete=True
        report['retirement_plans']=[]
        for bundle_index,bundle in enumerate(bundles[completed:],start=completed):
            if time.monotonic()>=deadline-12:
                search_complete=False;break
            check()
            vocab=tuple(initial['vocabulary'])+tuple(p for p in bundle if p not in initial['vocabulary'])
            dictionaries=[vocab]
            if len(vocab)>256:
                try:cleaned=clean_union(vocab,texts,owners,references,deadline-12)
                except TimeoutError:
                    report['retirement_plans'].append(dict(bundle_index=bundle_index,status='incomplete_unused_retirement',union_entries=len(vocab)))
                    search_complete=False;break
                if cleaned is None:
                    report['retirement_plans'].append(dict(bundle_index=bundle_index,status='unreachable_union',union_entries=len(vocab)))
                    completed+=1;continue
                excess=max(0,len(cleaned)-256)
                plan=dict(bundle_index=bundle_index,union_entries=len(vocab),unused_retired=len(vocab)-len(cleaned),
                          active_entries_to_retire=excess,planned_deletion_subsets=math.comb(len(cleaned),excess),evaluated_deletion_subsets=0,status='running')
                report['retirement_plans'].append(plan)
                dictionaries=(tuple(p for p in cleaned if p not in removed) for removed in itertools.combinations(cleaned,excess))
            else:plan=None
            for dictionary in dictionaries:
                if time.monotonic()>=deadline-12:
                    search_complete=False
                    if plan is not None:plan['status']='incomplete_active_retirement'
                    break
                candidate=score(dictionary,retire=True)
                if plan is not None:plan['evaluated_deletion_subsets']+=1
                if candidate is None:continue
                record(candidate)
                objective=lambda state:(state['metrics']['selections'],state['metrics']['characters'],state['metrics']['literal_utf8_bytes'])
                if candidate['metrics']['characters']<=report['absolute_character_cap'] and objective(candidate)<objective(best):
                    best=candidate;report['best_bundle_index']=bundle_index
                report['best_metrics']=best['metrics']
            if not search_complete:break
            if plan is not None:plan['status']='complete'
            completed+=1;report['completed_bundles']=completed
            if completed%20==0:checkpoint()
        # Selected final state receives independent codepoint+byte DP and actual
        # packet checks, not merely trusted C scores. This proves complete costs.
        selected={};chosen_variants={}
        for pid,key in sorted(best['choices'].items()):
            check();path=f.exact_path(texts[key],best['vocabulary'])
            if path[:2]!=(best['rows'][key]['selections'],best['rows'][key]['characters']):raise ValueError('independent DP mismatch')
            selected[pid]=(key,path);chosen_variants[pid]={key:texts[key]}
        report['final_full_costs']=f.metrics(best['vocabulary'],selected,chosen_variants,8)
        if any(report['final_full_costs'][k]!=best['metrics'][k] for k in ('dictionary_bytes','packet_bytes','decoder_bytes','package_bytes')):raise ValueError('actual vs analytic package cost mismatch')
        report['source_switch_rows']=[dict(problem_id=pid,
            before_source_sha256=base['source_rows'][initial['choices'][pid]]['sha256'],
            after_source_sha256=base['source_rows'][key]['sha256'],
            before_selections=initial['rows'][initial['choices'][pid]]['selections'],
            after_selections=best['rows'][key]['selections'],
            before_characters=initial['rows'][initial['choices'][pid]]['characters'],
            after_characters=best['rows'][key]['characters'])
            for pid,key in sorted(best['choices'].items()) if key!=initial['choices'][pid]]
        report['reviewed_helper_retained']=helpertext in best['vocabulary']
        report['absolute_character_nonregression']=best['metrics']['characters']<=initial['metrics']['characters']
        report['character_fraction_change']=best['metrics']['character_fraction']-initial['metrics']['character_fraction']
        report['changed_problem_costs']=dict(better=sum(best['rows'][best['choices'][p]]['selections']<initial['rows'][initial['choices'][p]]['selections'] for p in groups),
            worse=sum(best['rows'][best['choices'][p]]['selections']>initial['rows'][initial['choices'][p]]['selections'] for p in groups),
            source_switches=sum(best['choices'][p]!=initial['choices'][p] for p in groups),
            indexed_fold_selected=sum(best['choices'][p]==k for p,k in foldkeys.items()))
        report['status']='complete_frozen_global_bundle_diagnostic' if search_complete else 'incomplete_search_budget_verified_incumbent'
    except TimeoutError as exc:
        report['status']='incomplete_budget';report['reason']=str(exc)
    except Exception as exc:
        report['status']='blocked';report['reason']=type(exc).__name__+': '+str(exc)
    report['code_sha256']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    checkpoint()
    print(json.dumps({k:v for k,v in report.items() if k not in ['nondominated_ledger','final_full_costs','metadata_pins']},default=serial,sort_keys=True))

if __name__=='__main__':main()
