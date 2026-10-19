from pathlib import Path
from collections import Counter
import hashlib,json,shutil,sys
R=Path('/home/x/deco/gamma/projects/algorithm_solver');T=Path('/home/x/Documents/Codex/2026-10-19/task');sys.path.insert(0,str(T));import selection_codec as c
P=R/'runs/corpus-macro-analysis-128-v1';O=R/'runs/corpus-macro-selection-128-v1';F=R/'findings/corpus-macro-selection-128-v1';F.mkdir();sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
s=json.loads((O/'selection-summary.json').read_text());v=json.loads((O/'validation.json').read_text());contract=json.loads((O/'contract.json').read_text());assert v['independent_cases_per_language']==610 and v['public_cases_per_language']==17
scripts=['select_macro_prepare.py','selection_codec.py','select_macro_run.py','select_macro_validate.py','select_macro_package.py'];(O/'executed-tooling').mkdir()
for name in scripts:shutil.copyfile(T/name,F/name);shutil.copyfile(T/name,O/'executed-tooling'/name)
def breakdown(data,b):
 counts=Counter(header=38);n,p=c.readvar(data,38);counts['binding_count']=p-38
 for _ in range(n):start=p;length,p=c.readvar(data,p);counts['binding_lengths']+=p-start;counts['binding_names']+=length;p+=length
 entries={e['id']:e for e in b['entries']}
 while p<len(data):
  code=data[p];p+=1;e=entries[code];kind=e['kind']
  if kind=='end':counts['end_control']+=1
  elif kind=='text':counts['ascii_ids' if code<130 else 'lexical_shortcut_ids']+=1
  elif kind=='literal_run':counts['raw_control']+=1;start=p;length,p=c.readvar(data,p);counts['raw_lengths']+=p-start;counts['raw_payload']+=length;p+=length
  elif kind=='fragment':
   counts['macro_ids']+=1;variant=data[p];p+=1;counts['variant_operands']+=1;start=p;_,p=c.readvar(data,p);counts['indent_operands']+=p-start
   for _ in range(e['variants'][variant]['arity']):start=p;_,p=c.readvar(data,p);counts['binding_reference_operands']+=p-start
  else:raise ValueError(kind)
 assert sum(counts.values())==len(data);return counts
profiles=[];attribution=[];frontier=[];examples=[];totals=[]
for langdata in s['languages']:
 lang=langdata['language'];best=langdata['best'];d=O/lang/f"subset-{langdata['best_mask']:02d}";b=json.loads((d/'codebook.json').read_text());rows=json.loads((d/'summary.json').read_text())['rows'];count=Counter()
 for row in rows:
  stream=(d/f"{row['id']:04d}.bin").read_bytes();count.update(breakdown(stream,b));source=c.decode(stream,b);assert sha(next(x['source'] for x in contract['source_rows'] if x['id']==row['id'] and x['language']==lang))==hashlib.sha256(source).hexdigest()
  if row['used']:examples.append(dict(language=lang,id=row['id'],complete_stream_bytes=row['encoded_bytes'],binding_table=row['bindings'],calls=row['used'],remainder_source_bytes=row['lexical_remainder_source_bytes']))
 assert sum(count.values())==best['input_bytes'];totals.append(dict(language=lang,bytes=dict(count)))
 for kind in ['lexical','semantic','whole']:
  old=json.loads((P/lang/f'{kind}-summary.json').read_text());profiles.append(dict(language=lang,profile={'semantic':'frozen_two_fragment'}.get(kind,kind),macro_count=0 if kind=='lexical' else 2 if kind=='semantic' else 94,slots=old['slots'],input_bytes=old['total_stream_bytes'],input_bits=old['total_stream_bits'],codebook_bytes=old['codebook_bytes']))
 profiles.append(dict(language=lang,profile='selected',macro_count=best['macro_count'],slots=256,input_bytes=best['input_bytes'],input_bits=best['input_bytes']*8,codebook_bytes=best['codebook_bytes'],fragment_calls=best['fragment_calls'],problem_ids=best['fragment_problem_ids'],lexical_remainder_source_bytes=best['lexical_remainder_source_bytes'],fragment_source_bytes=best['fragment_source_bytes']))
 attribution.extend(dict(language=lang,**x) for x in langdata['attribution'])
 for n in range(1+max(r['macro_count'] for r in langdata['subsets'])):
  x=min((x for x in langdata['subsets'] if x['macro_count']==n),key=lambda x:(x['input_bytes'],x['mask']));frontier.append(dict(language=lang,macros=n,input_bytes=x['input_bytes'],selected=x['selected']))
for name,value in [('costs.json',profiles),('macro-attribution.json',attribution),('input-complexity-frontier.json',frontier),('binding-examples.json',examples),('byte-accounting.json',totals)]:
 (F/name).write_text(json.dumps(value,indent=2)+'\n')
result=dict(base_commit=contract['base_commit'],candidate_menu='Five ranked JS and four ranked Python candidates, hand-reviewed; no extra candidates invented to fill16 slots.',algorithmic_selection=True,subsets_evaluated=48,source_roundtrips_all_subsets=4512,selected_source_roundtrips=v['selected_source_roundtrips'],selected_canonical_roundtrips=v['selected_canonical_stream_roundtrips'],selected_menus={r['language']:r['best']['selected'] for r in s['languages']},complete_input_bytes=58898,saving_over_frozen_two_fragment_bytes=424,saving_over_lexical_bytes=751,selected_codebooks_bytes=27461,codebook_extra_over_two_fragment_bytes=3242,selected_fragment_calls=17,covered_problem_pairs=7,remaining_lexical_source_bytes=104020,total_source_bytes=106839,full_programs_without_lexical_remainder=0,independent_cases_per_language=610,public_cases_per_language=17,guard_rejection_executions=sum(r['cases'] for r in v['guard_rejection_controls']),malformed_controls=len(v['malformed_controls']),optimizer_exhaustive_controls=v['optimizer_controls'],shared_codec_bytes=(T/'selection_codec.py').stat().st_size,stopping_decision='Retain the measured3-macro JS and4-macro Python winners as bounded research representation candidates. Reject added JS collector and node step under this exact objective. Stop this menu here; no inflation toward16. Python three-concept alternative costs only7 extra bytes and remains a human-interpretability tradeoff, not a measured human preference.',human_testing=False,autonomous_solves=0,training=False,protected_opened=False,deployment=False,baseline_preserved=True,hashes={'contract':sha(O/'contract.json'),'selection':sha(O/'selection-summary.json'),'validation':sha(O/'validation.json'),'baseline_contract':sha(P/'contract.json')},scripts={name:sha(T/name) for name in scripts})
assert sum(p['input_bytes'] for p in profiles if p['profile']=='selected')==result['complete_input_bytes'];assert sum(p['codebook_bytes'] for p in profiles if p['profile']=='selected')==result['selected_codebooks_bytes']
(F/'result.json').write_text(json.dumps(result,indent=2)+'\n')
rows='\n'.join(f"| {p['language']} | {p['profile']} | {p['macro_count']} | {p['input_bytes']:,} | {p['codebook_bytes']:,} |" for p in profiles)
macrotable='\n'.join(f"| {m['language']} | {m['name']} | {'keep' if m['selected'] else 'reject'} | {m['selected_calls']} / {len(m['selected_problem_ids'])} | {str(m['leave_one_out_input_penalty'])+' bytes saved by keeping' if m['selected'] else str(m['add_one_input_change'])+' bytes added if included'} |" for m in attribution)
(F/'README.md').write_text('''# Bounded macro selection: input-cost decision

**Keep three JavaScript macros and four Python macros from this ranked menu.**
The measured winners save424 bytes (3,392 ideal binary presses) beyond the frozen
two-fragment profiles, or751 bytes beyond lexical shortcuts, across the same94
programs per language. This is a0.715% incremental input reduction. Dictionary
storage grows3,242 bytes relative to the two-fragment profiles; that growth was
reported separately and was not penalized by the selection objective.

No attempt was made to fill16 slots. The existing ranked menu supplies five JS
and four Python candidates. Their effects, fixed globals and operand schemas were
reviewed first; then all32 JS and16 Python subsets were evaluated algorithmically.
This menu is hand-designed; the winning subset and shortest source-aware streams
are selected algorithmically. No model chooses a program from a problem statement.

## Complete input comparison

All input totals include the version/language/profile/codebook-hash frame, binding
count, every identifier byte and length, fragment ID, explicit variant, indentation,
slot references, all lexical/raw fallback and END. Fixed constants and control
operators reside in the separately charged dictionary; there is no free binding,
constant, source-body or signature channel. One byte equals eight error-free binary
presses under this protocol, not a measured human action/time result.

| Language | Profile | Semantic/whole entries | Complete input bytes | Codebook bytes |
|---|---|---:|---:|---:|
'''+rows+'''

The lexical and whole-solution baselines are the original frozen artifacts. The
new CMA2 profile is separate; CMA1 was not modified. Every selected profile still
fits256 slots:128 ASCII entries, two controls,123 JS or122 Python lexical shortcuts,
and three JS or four Python fragments. Whole-solution entries remain a valid
bounded representation baseline but explicitly store all94 bodies in their book.
No generalization or autonomous-solving result follows from their short inputs.

The [byte audit](byte-accounting.json) reconciles every stream byte. Exact canonical
UTF8 JSON measures codebook storage, including template text, constants and
contracts. The common codec implementation size is recorded separately in
[result.json](result.json). This experiment optimizes compact program input rather
than one-pass storage compression; including book storage makes the winners2,818
bytes larger than the prior two-fragment profiles for a single corpus pass.

## Per-macro decision and reuse

The marginal number removes one selected macro and reoptimizes the remaining
stream/book allocation, or adds one rejected macro and reoptimizes. These values
are conditional and need not add to the total improvement. Small and whole BFS
loops overlap; their nested occurrences cannot both encode the same source bytes.

| Language | Macro | Decision | Calls / distinct problems | Conditional input effect |
|---|---|---|---:|---|
'''+macrotable+'''

The JavaScript small collector would add2 bytes once the larger traversal loop is
present, despite saving bytes on its own. The cursor step would add48 bytes after
identifier-table and sacrificed lexical-slot costs. Frequency alone therefore
does not justify admission. Python retains the small collector for zigzag103 and
the larger loop for ordinary102/bottom-up107. Duplicate skipping remains shared by
15/18, with paid direction variants. The bounded-list guard is reused by1512/1748.
Its351-byte combined marginal benefit is validation boilerplate compression, not
an algorithmic solving improvement.

[Detailed attribution](macro-attribution.json) includes singleton gains, available
versus selected occurrences, actual instruction bytes, covered source bytes and
binding arities. [Binding examples](binding-examples.json) show real retained names,
ordered macro calls and full-program costs. Source code and dictionary bodies stay
private in `runs/corpus-macro-selection-128-v1`.

## Human interpretability, reported separately

- **Duplicate skipping:** one sorted-array operation, three binding operands and
  two direction variants. Requires understanding the post-emission pointer state.
- **Whole BFS traversal loop:** one traversal concept, but seven JS/five Python
  identifier operands and language-specific frontier mutation. It contains the
  smaller collector, so learning both introduces overlapping granularity.
- **Single-level collector:** six JS/four Python operands. Useful independently
  in zigzag traversal, but its JS use does not earn its slot in this chosen menu.
- **Bounded-list guard:** two identifiers and three fixed numeric bounds
  (0,20,000,1,000,000). TypeError/ValueError and integer-versus-boolean semantics
  remain language-specific and fixed; this is not a general validation macro.
- **Cursor step:** easy one-binding concept but input-inefficient here; rejected.

These are inspectable complexity proxies, not measured learnability scores. The
[input/concept frontier](input-complexity-frontier.json) exposes the tradeoff:
Python's best three-macro menu needs23,873 bytes, only7 more than the four-macro
winner, and omits the larger BFS loop. A human-facing pilot may prefer that simpler
menu, but no human preference is asserted or deployment made. The measured
input-optimal decision remains three JS/four Python; stop this candidate set here.

## Selection algorithm and semantic limits

Each global subset sacrifices exactly one lexical slot per semantic entry, using
the same frozen lexical priority. Within each program, exhaustive enumeration of
binding-name unions charges only candidate tables that could be needed. Dynamic
programming then finds the shortest cover by registered fragment occurrences,
lexical entries and explicit raw escapes, with no overlap. The minimum is exact
within this finite registered-occurrence/lexical model; it is not a global optimum
over possible vocabularies, variable renamings, algorithms or source formatting.
The search is bounded to at most12 candidate occurrences per program.

Exception classes and builtins (`TypeError`, `ValueError`, `type`, `all`) were
explicitly fixed in the guard template, not treated as arbitrary binding holes.
The whole BFS loop preserves JS frontier-array identity via splice and Python
deque consumption. The node step rebinds a cursor; it does not relink nodes.
Original algorithms, public interfaces, mutation and alias behavior are retained
through exact byte reconstruction. This does not qualify arbitrary new parameter
bindings: semantic preconditions and fresh-name requirements still come from the
reviewed source contexts, not a newly invented general type/scope framework.

## Verification and remaining fallback

All4,512 subset/source combinations reconstruct their original bytes. The188
winning source streams also pass canonical encode-decode-encode identity checks.
Three independent exhaustive path-enumeration controls verify shortest costs on
small overlapping-fragment examples with actual used-binding table costs.
26 malformed-stream/operand controls pass, including unknown distinct bindings,
wrong versions, noncanonical lengths, invalid variants, duplicate names, aliased
operand slots and indentation bounds. A metadata-construction failure before
selection was retained as `failed-attempt001`; it changed no source or stream.

Seven reconstructed pairs pass610 existing independent cases and17 public examples
per language.28 additional invalid-input guard executions retain the expected
language-specific exceptions. Expected outputs never enter candidate sandboxes.
The original188 source hashes, all six baseline books and production recognition
catalog remain unchanged. No protected data, training or new dependency was used.

The chosen menus make17 fragment calls across seven problem pairs, covering2,819
of106,839 source bytes. **104,020 source bytes (97.36%) remain lexical/raw fallback,
and zero complete programs use semantic fragments alone.** This is a bounded
representation experiment and a measured stopping decision, not autonomous2a/2b
success or evidence that a complete learnable256-entry language has been found.

## Reproduction

The immutable run contract, candidate menu, all48 books/streams/subset results,
validation receipts and exact executed tooling are retained in the private run.
Tracked scripts reproduce the selection on128 with existing Python/Babel/Node.
Execution order is prepare, run, validate, package. Scripts pin the workspace and
run name; use a new output name for a replay and retain parent hashes rather than
overwriting artifacts. Selection consumed2.36 seconds measured wall time; execution
checks ran serially under one CPU and1,536MiB. Unrelated serving jobs stayed active.
''')
status=R/'STATUS.md';text=status.read_text();marker='## Bounded macro analysis on the94-problem corpus\n';assert marker in text
text=text.replace(marker,'''## Bounded macro selection: three JS and four Python entries

[Selection experiment](findings/corpus-macro-selection-128-v1/README.md) exhaustively
evaluates the existing five-JS/four-Python candidate menu. Input-optimal subsets
save424 complete-stream bytes beyond the frozen two-fragment profiles (751 versus
lexical), with codebook storage reported separately. The cursor step and extra JS
collector are rejected; Python's fourth concept earns only7 bytes over its best
three-concept alternative. No unused slots were filled speculatively.

All4,512 subset/source round trips preserve bytes. Seven reconstructed pairs pass
610 existing independent cases and17 public examples per language;26 malformed
controls, three independent optimizer controls and28 guard rejection executions
pass.17 fragment calls cover seven pairs, but97.36% of source bytes remain lexical
fallback and no complete program is semantic-only. This is a measured stopping
decision on representation, with no training, deployment or autonomous solve.

'''+marker);status.write_text(text)
print(json.dumps(result,indent=2))
