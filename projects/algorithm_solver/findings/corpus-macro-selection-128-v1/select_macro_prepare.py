from pathlib import Path
import json,hashlib,subprocess,shutil
R=Path('/home/x/deco/gamma/projects/algorithm_solver');T=Path('/home/x/Documents/Codex/2026-10-19/task');P=R/'runs/corpus-macro-analysis-128-v1';O=R/'runs/corpus-macro-selection-128-v1';F=R/'findings/corpus-macro-analysis-128-v1'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert subprocess.check_output(['hostname'],text=True).strip()=='128' and subprocess.check_output(['whoami'],text=True).strip()=='x'
assert subprocess.check_output(['git','-C',str(R.parent.parent),'rev-parse','HEAD'],text=True).strip()=='1b169f436397806b025e343c4057a4232c3392e1'
O.mkdir();old=json.loads((P/'contract.json').read_text());ranked=json.loads((F/'ranked-candidates.json').read_text());mined=json.loads((P/'mined-candidates.json').read_text())
for row in old['source_rows']:assert sha(row['source'])==sha(R/row['original_source'])==row['source_sha256']
contracts={
'whole_breadth_first_level_loop':dict(precondition='Finite acyclic binary tree; distinct frontier and accumulated-output handles; all emitted temporary names fresh in the original enclosing scope.',effects='Repeatedly collects a level and appends it in top-down order. JS splices the same frontier array to preserve its identity; Python consumes the deque. Final bottom-up reversal stays outside the macro.',constants='Fixed left-before-right traversal and fixed node fields; no arbitrary body or output-order operand.',interpretability='One traversal-loop concept, but7 JS or5 Python identifier operands; overlaps the smaller collector and cannot be counted twice.'),
'bounded_integer_list_domain_guard':dict(precondition='A candidate input value; standard unshadowed Number/Array/TypeError in JS and type/list/int/all/ValueError in Python.',effects='Rejects non-list, length outside0..20000 or noninteger/bool/negative/value>1000000 elements. Does not mutate input. Fixed TypeError in JS, ValueError in Python.',constants='0,20000,1000000 and exception types/messages stay fixed in the charged codebook. Only input name and local predicate-element name are operands.',interpretability='Specific bounded-list validation concept with two identifier operands; learn three fixed bounds and language-specific exception semantics.'),
'advance_linked_node_cursor':dict(precondition='Non-null ordinary list node with a next field; cursor name is assignable in its existing scope.',effects='Rebinds the cursor to its next reference; does not relink nodes, clone objects or mutate the node.',constants='Fixed next property and assignment; no expression/body operand.',interpretability='Simple one-binding step, low conceptual load but much less source compression per call.')}
rows=[]
for language in ['javascript','python']:
 for r in ranked:
  name=r['name'];groups=[]
  if r['tested']:
   fs=next(x for x in r['fragments'] if x['language']==language);desc=fs['contracts']
   kinds=['ForOfStatement' if language=='javascript' else 'For'] if r['rank']==1 else ['WhileStatement' if language=='javascript' else 'While']
   groups=[g for g in mined if g['language']==language and g['kind'] in kinds and set(g['ids'])==set(r['problem_ids'])]
   desc={**desc,'interpretability':'Level collector with6 JS or4 Python bindings.' if r['rank']==1 else 'Sorted-array duplicate skipping with3 bindings and one explicit direction variant.'}
  else:
   desc=contracts[name]
   for c in r['language_candidates']:
    if c['language']==language:groups.append(next(g for g in mined if g['language']==language and g['shape_sha256']==c['shape_sha256']))
  if not groups:continue
  rows.append(dict(language=language,name=name,rank=r['rank'],groups=groups,contract=desc,fixed_global_names=['TypeError','type','all','ValueError'] if r['rank']==4 else []))
record=dict(schema='algsolve.bounded-macro-selection.v1',base_commit='1b169f436397806b025e343c4057a4232c3392e1',baseline_contract_sha256=sha(P/'contract.json'),baseline_metrics_sha256=sha(F/'metrics.json'),baseline_codebooks={f'{lang}/{kind}':sha(P/lang/f'{kind}-codebook.json') for lang in ['javascript','python'] for kind in ['lexical','semantic','whole']},ranked_candidates_sha256=sha(F/'ranked-candidates.json'),candidate_counts={'javascript':5,'python':4},max_authorized_per_language=16,objective='Minimize total serialized program input bytes across the same94 admitted source programs per language. Include framing, identifiers, parameters, constants/variants, controls and lexical remainder. Dictionary storage is reported separately and is NOT the optimization objective.',selection='Manually reviewed finite candidate menu, then exhaustive algorithmic subset search:32 JS and16 Python subsets. Within a subset, exact dynamic programming over registered nonoverlapping occurrences and exhaustive distinct binding-table unions. No model or autonomous problem-to-program choice.',tie_break='Input bytes, then fewer macros, then rank order; no dictionary-byte objective.',human_interpretability='Report distinct concepts, arities, direction variants, fixed bounds, side effects and per-program choices. These are inspectable proxies, not a measured human learnability score.',bound=dict(cpu_threads=1,memory_MiB=1536,source_pairs=94,per_language_macro_limit=16,max_occurrences_per_program=12),scope='Consumed permitted corpus, no new mining beyond ranked candidates, no protected evaluation, training, deployments or autonomous solving claims.',source_rows=old['source_rows'])
(O/'contract.json').write_text(json.dumps(record,indent=2)+'\n');(O/'candidate-menu.json').write_text(json.dumps(rows,indent=2)+'\n');print('Frozen5 JS and4 Python candidates; fixed builtins and exception types are not binding operands')
