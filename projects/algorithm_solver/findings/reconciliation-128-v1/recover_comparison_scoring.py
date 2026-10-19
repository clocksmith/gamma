"""One-time evaluator-only recovery of frozen decisions; no prediction or training."""
from pathlib import Path
import copy,json,hashlib
from algsolve.synth import compare_typed as comparison, typed_codec, typed_confirmation, mine, development_tests
from algsolve.synth.typed_scoring import write_bytes_once,write_json_once
from algsolve.records import LANE_ROOT,load_hidden_tests
from algsolve.synth.train_typed import problem_for
old=LANE_ROOT/'runs/typed-composer-recovered-128-v1'
new=LANE_ROOT/'runs/typed-composer-recovered-128-scorefix-v1'
assert not new.exists(), 'Recovery destination must be new'
old_candidate=json.loads((old/'candidate.json').read_text())
seal=json.loads((old/'scoring/seal.json').read_text())
assert not list((old/'scoring').glob('[0-9]*.json')), 'This recovery expects no scored outcomes'
sha=typed_confirmation.sha
for name,h in seal['frozen_files_sha256'].items():assert sha(old/name)==h,(name,'original drift')
assert typed_codec.digest(old_candidate)==seal['candidate_sha256']
config_path=LANE_ROOT/'contracts/typed_composer_development_v1.json'; config=json.loads(config_path.read_text())
identity=typed_codec.frozen(LANE_ROOT/'contracts/typed_codec_v1.json')
current=comparison.manifest(config_path,config,old_candidate['checkpoint_contract'],identity)
changed='algsolve/synth/typed_scoring.py'
expected=copy.deepcopy(old_candidate)
expected['sources_sha256'][changed]=current['sources_sha256'][changed]
assert current==expected, 'Recovery may change only typed_scoring.py; all other inputs/runtime must match'
assert current!=old_candidate, 'Recovery requires the explicitly reviewed evaluator fix'
# Bind the sole allowable source change to the exact known textual repair.
import subprocess
previous=subprocess.check_output(['git','show','36404d2a1:projects/algorithm_solver/'+changed],cwd=LANE_ROOT)
assert hashlib.sha256(previous).hexdigest()==old_candidate['sources_sha256'][changed]
fixed=previous.decode().replace('from . import typed_codec','from . import mine, typed_codec')
fixed=fixed.replace('typed_codec.digest(tests)','mine.digest(tests)').replace('typed_codec.digest(scoring_tests)','mine.digest(scoring_tests)')
fixed=fixed.replace('    rows = []\n    for i,','    # Qualification stores independent-test hashes with mine.digest, not the\n    # compact graph serialization used for candidate and receipt identities.\n    rows = []\n    for i,')
assert (LANE_ROOT/changed).read_text()==fixed, 'Unexpected evaluator change'
pairs=typed_confirmation.verify_development(LANE_ROOT/config['corpus'],LANE_ROOT/config['qualification'],identity)
requests=list({p['uid']:p for p in reversed(pairs)}.values())
# Validate every permitted development suite using its original qualification hash.
checked=[]
for pair in requests:
 tests,_=development_tests.select(pair['uid'],load_hidden_tests(problem_for(pair)))
 h=mine.digest(tests);assert tests and h==pair['provenance']['independent_tests_sha256'],pair['uid']
 checked.append({'uid':pair['uid'],'tests':len(tests),'qualified_sha256':h})
new.mkdir()
write_json_once(new/'candidate.json',current)
for name in ('captures.jsonl','setup.json','decisions.jsonl','sandbox_probe.json'):
 write_bytes_once(new/name,(old/name).read_bytes())
 assert sha(new/name)==sha(old/name)
record={'schema':'algsolve.evaluator-only-recovery.v1','previous_run':old.name,'new_run':new.name,
 'reason':'Independent test provenance uses mine.digest sorted standard JSON; scorer incorrectly used compact graph digest.',
 'previous_candidate_sha256':typed_codec.digest(old_candidate),'candidate_sha256':typed_codec.digest(current),
 'changed_source':changed,'previous_source_sha256':old_candidate['sources_sha256'][changed],
 'corrected_source_sha256':current['sources_sha256'][changed],
 'unchanged_frozen_files_sha256':{n:sha(new/n) for n in ('captures.jsonl','setup.json','decisions.jsonl','sandbox_probe.json')},
 'original_frozen_files_sha256':seal['frozen_files_sha256'],'development_test_bindings':checked,
 'inference_repeated':False,'decisions_changed':False,'configuration_changed':False,'scoring_outcomes_previously_opened':False,
 'protected_opened':False,'training':False}
write_json_once(new/'recovery.json',record)
print(json.dumps(record,indent=2))
