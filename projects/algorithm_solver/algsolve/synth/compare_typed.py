"""Reproduce matched development routes from the frozen checkpoint; no training.

Run on the existing Linux judge host. The output directory must be new. Protected
artifacts are never read. A rejected candidate is still sealed as evaluated, but
cannot open protected scoring.
"""
from __future__ import annotations

import argparse
import importlib.metadata
import json
import platform
from pathlib import Path
import sys
import time

import numpy as np
import torch

from .. import validate
from ..embed import Embedder, EMBEDDING_DIR
from ..judge import sandbox
from ..records import LANE_ROOT, load_hidden_tests
from . import development_tests, typed_codec, typed_confirmation
from .train_typed import INSTRUCTION, problem_for, query_text
from .typed_prediction_codec import PredictionCodec
from .typed_predictor import TypedPredictor, decisions
from .typed_comparison import nearest_graph, run_route, score_fixed, summarize, report


def write(path, value):
    with path.open('x') as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write('\n')


def write_rows(path, rows):
    with path.open('x') as stream:
        for row in rows:
            stream.write(json.dumps(row, allow_nan=False)+'\n')


def source_hashes():
    return {str(p.relative_to(LANE_ROOT)): typed_confirmation.sha(p)
            for p in sorted((LANE_ROOT/'algsolve').rglob('*.py'))}


def manifest(config_path, config, checkpoint_contract, identity):
    files = [config_path, LANE_ROOT/config['comparison_authority'],
             LANE_ROOT/config['checkpoint'], LANE_ROOT/config['corpus'],
             LANE_ROOT/config['qualification'], LANE_ROOT/'contracts/typed_codec_v1.json',
             LANE_ROOT/'findings/typed-student-v2/summary.json']
    embedding_files = {p.name: typed_confirmation.sha(p) for p in sorted(EMBEDDING_DIR.iterdir())
                       if p.is_file()}
    return {'schema': 'algsolve.typed-composer-candidate.v1', 'config': config,
            'codec_sha256': identity, 'checkpoint_contract': checkpoint_contract,
            'files_sha256': {str(p.relative_to(LANE_ROOT)): typed_confirmation.sha(p) for p in files},
            'sources_sha256': source_hashes(), 'embedding_files_sha256': embedding_files,
            'runtime': {'python': sys.version, 'executable_sha256': typed_confirmation.sha(Path(sys.executable).resolve()),
                        'platform': platform.platform(), 'machine': platform.machine(),
                        'dependencies': sorted(f'{d.metadata["Name"]}=={d.version}' for d in importlib.metadata.distributions()),
                        'sandbox_tools_sha256': {p: typed_confirmation.sha(p) for p in (sandbox.BWRAP,sandbox.PRLIMIT,sandbox.PYTHON)}},
            'protected_opened': False, 'protected_campaign_seal': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--name', required=True)
    args = parser.parse_args()
    if not args.name.replace('-', '').isalnum():
        raise ValueError('Invalid run name')
    config_path = LANE_ROOT/'contracts/typed_composer_development_v1.json'
    config = json.loads(config_path.read_text())
    authority = json.loads((LANE_ROOT/config['comparison_authority']).read_text())
    identity = typed_codec.frozen(LANE_ROOT/'contracts/typed_codec_v1.json')
    if identity != authority['schema_binding']['codec_sha256']:
        raise ValueError('Comparison schema drift')
    checkpoint_path = LANE_ROOT/config['checkpoint']
    # Fail before allocating output or loading a model if the original assets
    # or tested Linux sandbox are unavailable. No replacement training run.
    missing = [str(p) for p in (checkpoint_path, LANE_ROOT/config['corpus']) if not p.is_file()]
    if missing:
        parser.error('Original frozen assets unavailable: '+', '.join(missing))
    if typed_confirmation.sha(checkpoint_path) != config['checkpoint_sha256']:
        raise ValueError('Checkpoint differs')
    sandbox.check_available()
    torch.set_num_threads(config['threads']); torch.manual_seed(config['seed'])
    assert torch.equal(torch.ones(2,2)@torch.ones(2,2), torch.full((2,2),2.))
    import transformers
    print(f'[compute] python={sys.executable} torch={torch.__version__} transformers={transformers.__version__} '
          f'cuda_available={torch.cuda.is_available()} cuda_count={torch.cuda.device_count()} target=cpu matmul=passed', flush=True)
    pairs = typed_confirmation.verify_development(LANE_ROOT/config['corpus'], LANE_ROOT/config['qualification'], identity)
    fit = [p for p in pairs if p['learning_split']=='development_fit']
    unique = {}
    for p in pairs:
        if p['uid'] in unique and p['input'] != unique[p['uid']]['input']:
            raise ValueError('Alternatives disagree about the request')
        unique.setdefault(p['uid'], p)
    requests = list(unique.values())
    started = time.perf_counter()
    checkpoint = torch.load(checkpoint_path, map_location='cpu', weights_only=True)
    training = checkpoint['contract']
    if training['dataset_sha256'] != typed_confirmation.sha(LANE_ROOT/config['corpus']):
        raise ValueError('Checkpoint corpus mismatch')
    descriptor = training['prediction_encoding']
    if typed_codec.digest(descriptor) != authority['schema_binding']['prediction_descriptor_sha256']:
        raise ValueError('Prediction descriptor mismatch')
    encoding = PredictionCodec(descriptor['slots'], descriptor['types'])
    if encoding.descriptor() != descriptor:
        raise ValueError('Prediction implementation differs')
    model = TypedPredictor(checkpoint['state_dict']['project.weight'].shape[1],
                           encoding.slots, len(encoding.types), width=training['width'])
    model.load_state_dict(checkpoint['state_dict'], strict=True); model.eval()
    checkpoint_load = time.perf_counter()-started
    output = LANE_ROOT/'runs'/args.name; output.mkdir(exist_ok=False)
    candidate = manifest(config_path, config, training, identity)
    candidate_id = typed_codec.digest(candidate)
    write(output/'candidate.json', candidate)
    print(f'[run-contract] run_name={args.name} pairs_input_spec={config["corpus"]} '
          f'resume_from={config["checkpoint"]} resume_stage=evaluation decode=raw-and-bounded-schema-correction '
          'eval_dataset_paths=qualified-development-only device=cpu schedule=no-training runtime_mode=cpu sweep_mode=none', flush=True)
    # Prove sandbox execution before the model pass, using a constant fixture.
    probe = validate.judge_problem(problem_for(requests[0]),
        'class Solution:\n    def '+problem_for(requests[0]).entry['method']+'(self, *args):\n        return 7\n',
        [{'args': [0 for _ in requests[0]['input']['params']], 'expected': 7}])
    write(output/'sandbox_probe.json', probe.to_dict())
    if not probe.passed:
        raise RuntimeError('Sandbox probe failed; no development scoring attempted')
    started = time.perf_counter(); embedder = Embedder(device='cpu'); embedding_load = time.perf_counter()-started
    descriptions = [typed_codec.digest(p['target'])+' '+json.dumps(p['target']['program'], sort_keys=True) for p in fit]
    started = time.perf_counter(); contracts = embedder.encode(descriptions,batch_size=4)
    library_setup = time.perf_counter()-started
    started = time.perf_counter()
    warmup_vector = embedder.encode(['Return an integer input unchanged.'], query=True, instruction=INSTRUCTION)[0]
    with torch.inference_mode():
        model(torch.from_numpy(warmup_vector[None]), torch.from_numpy(contracts[:4][None]))
    warmup_seconds = time.perf_counter()-started
    # No test outputs are consulted in model capture. Retain logits because the
    # correction consumes their rankings. No recomputation on later verdicts.
    captures = []
    for i,pair in enumerate(requests):
        phase = time.perf_counter()
        vector = embedder.encode([query_text(pair)], query=True, instruction=INSTRUCTION)[0]
        embedding = time.perf_counter()-phase
        phase = time.perf_counter(); similarities = contracts@vector
        neighbors = np.argsort(-similarities, kind='stable')[:4]
        retrieval = time.perf_counter()-phase
        phase = time.perf_counter()
        with torch.inference_mode():
            logits = model(torch.from_numpy(vector[None]), torch.from_numpy(contracts[neighbors][None]))
            raw = decisions(logits)
            scores = {k:v[0].tolist() for k,v in logits.items() if k!='bits'}
        prediction = time.perf_counter()-phase
        capture = {'uid': pair['uid'], 'split':pair['learning_split'], 'codes':raw,
                   'logits': scores, 'similarities': similarities.tolist(),
                   'embedding_seconds':embedding, 'retrieval_seconds':retrieval, 'prediction_seconds':prediction}
        captures.append(capture)
        print(json.dumps({'captured':i+1,'total':len(requests)}),flush=True)
    write_rows(output/'captures.jsonl', captures)
    cold = {'checkpoint_load_seconds': checkpoint_load, 'embedding_load_seconds': embedding_load,
            'fit_library_embedding_seconds': library_setup, 'warmup_seconds': warmup_seconds,
            'scope': 'in-process phases; imports, file verification and OS cache effects not claimed as full cold opening'}
    write(output/'setup.json', cold)
    rows = []
    for pair,capture in zip(requests,captures):
        # Only the public input is passed to route-specific selection.
        request = {'input':pair['input']}
        problem = problem_for(pair)
        shared = sum(capture[k] for k in ('embedding_seconds','retrieval_seconds','prediction_seconds'))
        common = (problem,capture['codes'],capture['logits'],encoding,identity,shared,
                  config['correction'],config['decision_wall_seconds'])
        routes = {name:run_route(name,*common) for name in ('raw','constrained')}
        phase = time.perf_counter()
        graph, graph_hash, reason = nearest_graph(request,fit,capture['similarities'],encoding)
        baseline_construction = time.perf_counter()-phase
        baseline_seconds = capture['embedding_seconds']+capture['retrieval_seconds']
        routes['nearest_training_graph'] = run_route('nearest_training_graph',*common,
            baseline_graph=graph,baseline_hash=graph_hash,baseline_reason=reason,baseline_seconds=baseline_seconds,
            baseline_construction_seconds=baseline_construction)
        for name,result in routes.items():
            result['timing'].update(embedding_seconds=capture['embedding_seconds'],
                retrieval_seconds=capture['retrieval_seconds'],
                prediction_seconds=capture['prediction_seconds'] if name!='nearest_training_graph' else 0.)
        rows.append({'uid':pair['uid'],'split':pair['learning_split'],'routes':routes})
    write_rows(output/'decisions.jsonl',rows)
    decisions_hash = typed_confirmation.sha(output/'decisions.jsonl')
    # This is the first independent-test read. Freeze every response beforehand.
    scored = []
    for pair,row in zip(requests,rows):
        problem = problem_for(pair)
        tests,_ = development_tests.select(pair['uid'],load_hidden_tests(problem))
        if typed_codec.digest(tests) != pair['provenance']['independent_tests_sha256']:
            raise ValueError('Independent development scoring authority changed')
        scored.append({**row,'independent_tests_sha256':typed_codec.digest(tests),
                       'routes':{k:score_fixed(v,problem,tests) for k,v in row['routes'].items()}})
        print(json.dumps({'scored':len(scored),'total':len(requests)}),flush=True)
    write_rows(output/'scores.jsonl',scored)
    # Detect drift before any promotion, including code, dependencies and inputs.
    if candidate != manifest(config_path,config,training,identity):
        raise ValueError('Candidate environment or files changed during execution')
    if typed_confirmation.sha(output/'decisions.jsonl') != decisions_hash:
        raise ValueError('Frozen decisions changed during scoring')
    summary = summarize(scored,config['selection'])
    summary.update(schema='algsolve.typed-composer-development-report.v1',candidate_sha256=candidate_id,
                   protected_scored=False,autonomous_loop_started=False,setup=cold,
                   artifacts_sha256={p.name:typed_confirmation.sha(p) for p in sorted(output.iterdir()) if p.is_file()},
                   limitations=['Development selection only; no fresh generalization result.',
                                'One fixed checkpoint and one bounded correction configuration; no model training.',
                                'Historical search baselines remain required before protected scoring.',
                                'Finite tests establish tested agreement, not universal program correctness.'])
    write(output/'summary.json',summary)
    with (output/'report.md').open('x') as stream:
        stream.write(report(summary))
    print(json.dumps(summary,indent=2),flush=True)


if __name__=='__main__': main()
