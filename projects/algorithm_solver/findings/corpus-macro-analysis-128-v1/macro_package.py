from pathlib import Path
import json,hashlib,shutil,subprocess
R=Path('/home/x/deco/gamma/projects/algorithm_solver');T=Path('/home/x/Documents/Codex/2026-10-19/task');O=R/'runs/corpus-macro-analysis-128-v1';F=R/'findings/corpus-macro-analysis-128-v1';F.mkdir()
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
c=json.loads((O/'contract.json').read_text());a=json.loads((O/'analysis-summary.json').read_text());v=json.loads((O/'validation.json').read_text());account=json.loads((O/'accounting.json').read_text());mined=json.loads((O/'mined-candidates.json').read_text())
assert v['problem_pairs']==5 and v['independent_cases_per_language']==409 and v['public_cases_per_language']==11 and v['malformed_controls_passed']==24
assert sha(T/'macro_codec.py')==a['codec_sha256']==v['codec_sha256']
scripts=['macro_freeze.py','macro_ast_scan.cjs','macro_mine.py','macro_codec.py','macro_analyze.py','macro_validate.py','macro_accounting.py','macro_package.py'];(O/'executed-tooling').mkdir()
for name in scripts:shutil.copyfile(T/name,F/name);shutil.copyfile(T/name,O/'executed-tooling'/name)
source_manifest=[{k:r[k] for k in ['id','key','language','original_source','source_sha256','independent_cases']} for r in c['source_rows']]
(F/'source-manifest.json').write_text(json.dumps(dict(catalog_sha256=c['catalog_sha256'],scope=c['scope'],rows=source_manifest),indent=2)+'\n')
excluded=c['unadmitted'];excluded[-1]['reason']='All12 quarantined Scramble String cases have unequal input-string lengths.'
(F/'exclusions.json').write_text(json.dumps(dict(wave=100,foundation=5,foundation_ids=c['foundation_ids'],overlap=0,union=105,admitted=94,unadmitted=11,rows=excluded),indent=2)+'\n')
rank=[]
for position,(name,ids,why) in enumerate([('bfs_collect_one_level',[102,103,107],'One level collector is reused by ordinary, zigzag and bottom-up traversal; outer output ordering remains outside the fragment.'),('skip_adjacent_equal_values',[15,18],'After emitting a tuple, advance the selected pointer over equal neighbor values. Direction and pointer bindings are explicit operands.')],1):
 fs=[f for f in a['fragments'] if f['name']==name];cost=[r for r in account['comparisons'] if r.get('fragment')==name];rank.append(dict(rank=position,name=name,problem_ids=ids,languages=['javascript','python'],tested=True,why=why,fragments=fs,measured_complete_program_costs=cost,full_program_without_lexical_remainder=0))
for position,name,selector,why in [(3,'whole_breadth_first_level_loop',lambda g:g['kind'] in ['While','WhileStatement'] and set(g['ids'])=={102,107},'Larger overlapping parent of the tested level collector; two problems only. Do not add its coverage or savings to the contained fragment.'),(4,'bounded_integer_list_domain_guard',lambda g:g['kind'] in ['If','IfStatement'] and set(g['ids'])=={1512,1748} and 'declared input domain' in g['representative'],'Guard reuse is real but specific to these two identical numeric domains. Error type and caller-visible behavior differ by language; not a general algorithm macro.'),(5,'advance_linked_node_cursor',lambda g:g['language']=='javascript' and g['kind']=='ExpressionStatement' and set(g['ids'])=={19,21,25,61,82,83,92},'Small pointer step is frequent, but mutation, aliasing and nullability depend on context. No general reusable-fragment qualification or Python parity inferred.')]:
 groups=[g for g in mined if selector(g)];assert groups,name
 rank.append(dict(rank=position,name=name,tested=False,why=why,language_candidates=[dict(language=g['language'],kind=g['kind'],shape_sha256=g['shape_sha256'],ids=g['ids'],occurrences=g['occurrences'],raw_bytes=g['raw_bytes']) for g in groups],qualification='Syntactic candidate only; no decoder entry, complete stream cost or behavioral promotion.'))
(F/'ranked-candidates.json').write_text(json.dumps(rank,indent=2)+'\n')
metrics=dict(base_commit=c['base_commit'],run='runs/corpus-macro-analysis-128-v1',contract_sha256=sha(O/'contract.json'),analysis_sha256=sha(O/'analysis-summary.json'),validation_sha256=sha(O/'validation.json'),accounting_sha256=sha(O/'accounting.json'),mined_groups={'javascript':sum(g['language']=='javascript' for g in mined),'python':sum(g['language']=='python' for g in mined)},profiles=[{k:x for k,x in p.items() if k!='rows'} for p in a['profiles']],comparisons=account['comparisons'],byte_accounting=[{k:x for k,x in p.items() if k!='rows'} for p in account['profiles']],shared_codec_bytes=account['shared_codec_implementation_bytes'],exact_source_roundtrips=564,canonical_stream_roundtrips=564,fragment_calls=14,fragment_problem_pairs=5,full_semantic_programs_without_remainder=0,public_cases_per_language=11,independent_cases_per_language=409,malformed_controls=24,autonomous_solves=0,protected_opened=False,training=False,deployment=False,runner_files={n:sha(T/n) for n in scripts})
(F/'metrics.json').write_text(json.dumps(metrics,indent=2)+'\n')
table='\n'.join(f"| {p['language']} | {p['profile']} | {p['slots']} | {p['total_stream_bytes']:,} | {p['codebook_bytes']:,} | {p['one_corpus_pass_including_codebook_bytes']:,} |" for p in a['profiles'])
extable='\n'.join(f"| {r['id']} | {r['key'].removeprefix('lc:')} | {r['reason']} | {r['valid_existing_cases']}/{r['quarantined_cases']} |" for r in excluded)
(F/'README.md').write_text('''# Corpus macro representation analysis

Two parameterized fragment entries reconstruct shared pieces across five problems
in both languages: one breadth-first level collector and adjacent-duplicate pointer
skipping. The complete streams save327 bytes across the94-problem paired corpus
relative to a syntax-only lexical profile, but the dictionaries cost2,943 extra
bytes. **The two-fragment profile loses2,616 bytes on one complete corpus pass.**
That is a measured representation tradeoff, not autonomous-solving improvement.

## Exact admission accounting

The first wave contains100 unique problems. The five foundation problems are252,
1046,1464,1512 and1748; none overlaps the wave. Therefore the union is105, with94
admitted and11 unadmitted. Do not subtract the foundation five from the wave count.
The table lists retained valid-domain/quarantined existing cases; those domain
regressions do not retroactively pass the frozen full-set gate.

| ID | Problem | Why full-set admission remains withheld | Valid/quarantined |
|---|---|---|---:|
'''+extable+'''

No excluded source was mined. Their originals, test expectations, failed receipts
and separately scoped domain evidence remain unchanged.

## Bounded analysis and candidate ranking

The [source manifest](source-manifest.json) freezes188 admitted implementations.
Existing Babel parses JavaScript; Python uses its standard AST. Matching statement
shapes parameterizes identifiers, preserving properties, operators and literals.
The bounded search accepts20..700-character statements with at least five AST
nodes and occurrences in at least two problems. It found57 recurring JavaScript
groups and25 Python groups. This is structural evidence, not a semantic proof:
wrappers such as forwarding to an implementation are not promoted as algorithmic
reuse, and overlapping parent/child candidates are not counted independently.

[Ranked candidates](ranked-candidates.json):

1. **Collect one BFS level:**102 ordinary level order,103 zigzag level order,
   107 bottom-up level order. The same fragment is instantiated three times in
   each language. JavaScript reads a frontier array and appends values and children
   to separate arrays; Python consumes exactly the initial deque length and
   appends children on that deque. The language-specific effects are explicit.
   Actual complete streams for these three programs fall from883 to725 bytes in
   JavaScript and898 to757 in Python, including bindings and remaining source.
2. **Skip adjacent duplicate values:**15 Three Sum and18 Four Sum. Both leftward
   and rightward variants share one entry, with a paid direction byte and explicit
   array/pointer bindings. Four uses per language. Complete streams fall from1258
   to1186 bytes in JavaScript and795 to707 in Python. This preserves existing
   sorted-input and in-range-pointer preconditions; it does not sort or mutate
   the input array itself.
3. **Whole BFS level loop:** structural reuse in102/107, but overlaps candidate1.
   Not promoted; its coverage and raw sizes must not be added to candidate1.
4. **Bounded integer-list guard:** structural reuse in1512/1748 in both languages.
   Domain bounds and language-specific exceptions need an explicit contract.
5. **Advance linked-node cursor:**11 JavaScript occurrences across seven problems.
   Small and common, but nullability and reference effects are context-dependent;
   no generic or Python-equivalent fragment is claimed.

Only the first two are included in the measured semantic profile. Each has a
closed language-specific template: no arbitrary source-body operand. Identifier
operands and direction select names and a fixed expansion variant. Original
bindings and algorithms are retained. Candidate ranking is a bounded engineering
choice informed by recurrence and measured reuse, not global vocabulary optimality.

## Complete input and codebook cost

All values below are actual serialized bytes. Each byte corresponds to eight
ideal binary presses; [metrics](metrics.json) also report bits. The lexical profile
has128 ASCII entries,126 fitted shortcuts, END and literal-run controls. The hybrid
replaces two shortcuts with two parameterized fragments. The whole-solution
baseline has94 exact solution bodies plus two controls, occupying96 slots. It is
legitimate bounded stored representation, but is not evidence of generalization.

| Language | Profile | Slots | Complete stream bytes | Codebook bytes | One pass, including codebook |
|---|---|---:|---:|---:|---:|
'''+table+'''

Each stream includes38 bytes of magic/version, language/profile and codebook hash;
a binding count; every UTF8 binding name and length; all macro IDs, variant,
indentation and slot-reference operands; all lexical/raw remainder; and END.
Signatures and constants are not supplied through a free side channel. Fixed
step/offset1, tree-field names and control operators are part of the paid codebook.
The two semantic profiles use14 fragment calls total, plus14 variant bytes,
14 indentation operands and54 binding-reference bytes. Identifier table lengths
and bytes are charged too. ASCII identifiers and literals outside fragments remain
in the measured lexical remainder. Python's non-ASCII comments use explicit raw
UTF8 controls and length/payload bytes. A byte-by-byte audit reconciles every total.

Dictionary cost is the exact canonical UTF8 JSON serialization, including bodies,
schemas and semantic contracts. It is not a minimal compressed-description bound.
The shared codec implementation is6,830 bytes, reported separately. The new fitted
profiles are experiment artifacts; no deployed byte256 alphabet was changed.

At the observed mix, paying the dictionary once, the hybrid first strictly beats
lexical after11 complete JavaScript corpus repetitions or8 Python repetitions.
Whole-solution dictionaries first beat lexical after2 JavaScript repetitions or3
Python repetitions. These are repeat-use amortization figures for the same known
corpus, not claims about new problems. Source-aware encoding picks short streams
offline; there is no model choosing the correct solution or fragment sequence.

## Reconstruction and execution evidence

All564 profile/source combinations reconstruct the exact original UTF8 bytes and
re-encode to the identical stream. Exact identity preserves algorithms, public
interfaces, mutation, reference aliases and exceptions; it is stronger than merely
matching a formatted source appearance. The two fragments account for seven
calls per language across five problems. All94 programs still require lexical/raw
remainder in that profile: **zero full programs are represented solely by those
two semantic entries**. Whole-solution one-entry coverage is94 per language and
stores every body in its explicitly charged dictionary.

The five reconstructed program pairs pass409 unchanged independent cases and11
public examples per language in the existing isolated Linux judge. Expected
outputs stay outside candidate sandboxes.24 malformed-stream/operand controls
reject missing/trailing data, profile mismatch, invalid variants, unknown slots,
noncanonical lengths and duplicate fragment handles. These are reconstruction
and software checks on consumed development evidence, not new autonomous solves.
The generic decoder is not a new type/scope verifier: valid tree/list types, fresh
local names and semantic preconditions come from the reviewed occurrences. No
claim of arbitrary safe fragment composition is made.

## Reproduction and preservation

Exact executed scripts are retained here and in the ignored run's `executed-tooling`.
The run contract binds source/catalog/wave hashes; the metrics bind all scripts,
analysis, validation and byte-accounting artifacts. Existing Node/Babel and the
Gamma Python environment were used without downloads. The serial scope was limited
to one CPU and1,536MiB; unrelated model-serving workloads were left running.

Execution order: `macro_freeze.py`, `macro_mine.py`, `macro_analyze.py`,
`macro_validate.py`, `macro_accounting.py`, then `macro_package.py`. Scripts pin the
128 workspace and immutable run name. For a replay, copy the retained tooling to
a new named run, update only its declared output path, and retain the original
script hashes as parents; never overwrite this run or its receipts. Source and
codebook bodies, binary streams, AST examples and complete verdicts remain private
under `runs/corpus-macro-analysis-128-v1`; public Git push is not part of this work.

Production recognition, the original model experiment, protected reservations,
training and the deployed256.one app remain unchanged. This completes the bounded
analysis task; it does not complete autonomous goals2a/2b or select a final256-entry
semantic language. The next useful test is a separately sealed corpus split and
fragment selector after a bounded vocabulary has been specified and frozen.
''')
status=R/'STATUS.md';s=status.read_text();marker='## Reviewed bilingual development corpus:94 unique problems\n';assert marker in s
s=s.replace(marker,'''## Bounded macro analysis on the94-problem corpus

[Representation study](findings/corpus-macro-analysis-128-v1/README.md) compares
syntax-only shortcuts, two parameterized fragments and94 bounded whole-solution
entries per language. BFS level collection reuses one entry across102/103/107;
adjacent-duplicate skipping reuses another across15/18. All564 profile/source
round trips preserve exact bytes. The five reconstructed pairs pass409 existing
independent cases and11 public examples per language;24 decoder controls pass.

Complete hybrid streams save327 bytes across both languages, but dictionaries
cost2,943 extra bytes, so the hybrid loses2,616 bytes on one corpus pass. All94
hybrid programs still require lexical remainder. This is source-aware in-sample
representation evidence, with zero autonomous solves or protected evaluation.
The105-problem union is100 wave plus five disjoint foundation problems; all11
unadmitted problems and their retained domain failures are enumerated in the report.

'''+marker);status.write_text(s)
print('Packaged bounded macro evidence and updated status')
