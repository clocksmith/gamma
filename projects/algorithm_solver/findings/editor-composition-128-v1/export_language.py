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
 catalog=load(ROOT/'findings/known-sortedcontainers-1a-128-v1/serving-summary.json')
 return dict(schema='algsolve.editor-language.v1',language=descriptor['program_schema'],codec_sha256=identity,
  **{k:descriptor[k] for k in ['pure_operators','effects','statements','types','limits','recipes']},examples=examples,
  evidence=dict(frozen_gpu_guard=dict(correct=8,cases=10,wrong=0,p95_seconds=.2961809851976795,nearest_correct=9,scope='Previously consumed fit cases only; no unfamiliar or nearby-variant qualification',source='gamma/projects/algorithm_solver/findings/typed-gpu-reuse-fit-128-v2/summary.json'),
   paired_training=dict(control=summary['metrics']['control'],balanced=summary['metrics']['balanced'],selected=False,source='gamma/projects/algorithm_solver/findings/typed-literal-balanced-pair-128-v1/summary.json',source_sha256=hashlib.sha256(paired.read_bytes()).hexdigest()),
   stored_answers=dict(approved=catalog['approved_answered'],eligible=catalog['eligible'],failures=len(catalog['failures']),source='gamma/projects/algorithm_solver/findings/known-sortedcontainers-1a-128-v1/serving-summary.json')))
if __name__=='__main__':
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
 args.output.write_text(json.dumps(build(),indent=2)+'\n')
