"""Export only approved editor language metadata, authored examples and aggregate evidence."""
import argparse,hashlib,json
from pathlib import Path
from algsolve.records import LANE_ROOT as ROOT
from algsolve.synth import typed_codec
load=lambda p:json.loads(p.read_text())
def build():
 identity=typed_codec.frozen(ROOT/'contracts/typed_codec_v1.json');descriptor=typed_codec.descriptor()
 examples=load(Path(__file__).with_name('examples.json'))
 for row in examples:typed_codec.encode(row['program'],identity)
 paired=ROOT/'findings/typed-literal-balanced-pair-128-v1/summary.json';summary=load(paired)
 catalog_path=ROOT/'findings/pinned-public-1a-128-v1/approved-library.json';catalog=load(catalog_path)
 completion_path=ROOT/'findings/pinned-public-1a-128-v1/serving-completion.json';completion=load(completion_path)
 assert completion['status']=='passed' and completion['frozen_catalog_sha256']==hashlib.sha256(catalog_path.read_bytes()).hexdigest()
 repair=catalog['evidence'];serving=completion['results']
 return dict(schema='algsolve.editor-language.v1',language=descriptor['program_schema'],codec_sha256=identity,
  **{k:descriptor[k] for k in ['pure_operators','effects','statements','types','limits','recipes']},examples=examples,
  evidence=dict(frozen_gpu_guard=dict(correct=8,cases=10,wrong=0,p95_seconds=.2961809851976795,nearest_correct=9,scope='Previously consumed fit cases only; no unfamiliar or nearby-variant qualification',source='gamma/projects/algorithm_solver/findings/typed-gpu-reuse-fit-128-v2/summary.json'),
   paired_training=dict(control=summary['metrics']['control'],balanced=summary['metrics']['balanced'],selected=False,source='gamma/projects/algorithm_solver/findings/typed-literal-balanced-pair-128-v1/summary.json',source_sha256=hashlib.sha256(paired.read_bytes()).hexdigest()),
   stored_answers=dict(approved=catalog['counts']['approved'],scope='Stored-source qualification; existing2501 approvals preserved plus4 newly qualified. Not full-index re-execution or autonomous solving.',source='gamma/projects/algorithm_solver/findings/pinned-public-1a-128-v1/approved-library.json',source_sha256=hashlib.sha256(catalog_path.read_bytes()).hexdigest(),latest_repair=dict(added=catalog['counts']['approved']-repair['prior_approved_records_preserved'],public_cases=repair['new_public_cases_executed'],independent_cases=repair['new_independent_cases_executed'],known_source_requests_passed=serving['exact_known_source_editor_successes'],raw_missing_example_abstentions=serving['raw_user_missing_example_controls_passed'],full_index_serving_verified=serving['full_index_serving_verified'],source='gamma/projects/algorithm_solver/findings/pinned-public-1a-128-v1/serving-completion.json',source_sha256=hashlib.sha256(completion_path.read_bytes()).hexdigest()))))
if __name__=='__main__':
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
 args.output.write_text(json.dumps(build(),indent=2)+'\n')
