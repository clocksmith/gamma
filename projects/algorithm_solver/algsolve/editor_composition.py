"""Explicit editor access to the frozen typed language and measured composer.

The graph is data, assembled through the existing interpreter. No autoregressive
source generation, known-answer lookup, independent tests or online learning.
"""
import json
import time
from .records import LANE_ROOT as ROOT
from .editor_execution import query_problem
from .synth import typed_codec

GPU_RECEIPT=ROOT/'findings/typed-gpu-reuse-fit-128-v2/contract.json'


def check_graph(raw, program):
    from . import validate
    problem=query_problem(raw)
    identity=typed_codec.frozen(ROOT/'contracts/typed_codec_v1.json')
    target=typed_codec.encode(program,identity)
    code=typed_codec.render(target,identity,method=problem.entry['method'],params=[p[0] for p in problem.params])
    verdict=validate.judge_problem(problem,code,problem.public_tests,wall_seconds=8)
    return dict(decision='answered' if verdict.passed else 'abstain',reason=verdict.reason,
        example_passed=verdict.passed,independent_tests_passed=None,language='python',
        code=code if verdict.passed else None,program=program,codec_sha256=identity,
        graph_sha256=typed_codec.digest(target),public_example_count=len(problem.public_tests),
        public=verdict.to_dict(),mode='explicit_graph',source_generation=False)


def compose(raw):
    import gc
    import numpy as np
    import torch
    from . import splits
    from .embed import Embedder, EMBEDDING_DIR
    from .rebuild_recognition import sha
    from .synth import typed_confirmation
    from .synth.train_typed import query_text,INSTRUCTION
    from .synth.typed_prediction_codec import PredictionCodec
    from .synth.typed_predictor import TypedPredictor,decisions
    from .synth.typed_comparison import run_route
    from .synth.typed_correction import validate_codes
    from .synth.typed_semantic_repair import run_semantic_route
    from .synth.typed_guard_filter import unreachable_numeric_guard
    problem=query_problem(raw)
    if not problem.public_tests:return dict(decision='abstain',reason='query_has_no_public_examples',example_passed=False,language='python')
    reservation=json.loads((ROOT/'findings/mine-v2-candidates-20261017/split.json').read_text())
    protected={splits.sibling_base(k.removeprefix('lc:')) for k in reservation['confirmation_keys']}
    if problem.slug and splits.sibling_base(problem.slug) in protected:
        return dict(decision='abstain',reason='protected_composition_family',example_passed=False,language='python')
    receipt=json.loads(GPU_RECEIPT.read_text())
    # Load only the original selected assets and immutable composition implementation.
    for name,h in receipt['assets_sha256'].items():
        if name.startswith('runs/typed-composer-recovered'):continue
        if sha(ROOT/name)!=h:raise ValueError('Frozen composition asset changed')
    for name,h in receipt['sources_sha256'].items():
        if name.startswith('algsolve/synth/') or name in ('algsolve/embed.py','algsolve/validate.py','algsolve/values.py'):
            if sha(ROOT/name)!=h:raise ValueError('Frozen composition implementation changed')
    if not torch.cuda.is_available():
        return dict(decision='abstain',reason='qualified_gpu_runtime_unavailable',example_passed=False,language='python')
    torch.set_num_threads(2)
    probe=torch.ones((2,2),device='cuda');assert (probe@probe).cpu().tolist()==[[2.,2.],[2.,2.]]
    torch.cuda.reset_peak_memory_stats()
    identity=typed_codec.frozen(ROOT/'contracts/typed_codec_v1.json')
    pairs=typed_confirmation.verify_development(ROOT/'runs/typed-real-dev-v5/pairs.jsonl',ROOT/'findings/typed-real-dev-v5/summary.json',identity)
    fit=[p for p in pairs if p['learning_split']=='development_fit']
    checkpoint=torch.load(ROOT/'runs/typed-student-v2/model.pt',map_location='cpu',weights_only=True)
    descriptor=checkpoint['contract']['prediction_encoding'];encoding=PredictionCodec(descriptor['slots'],descriptor['types'])
    model=TypedPredictor(1024,encoding.slots,len(encoding.types),width=64);model.load_state_dict(checkpoint['state_dict'],strict=True);model.eval()
    started=time.perf_counter();encoder=Embedder(device='cuda')
    memory=encoder.encode([typed_codec.digest(p['target'])+' '+json.dumps(p['target']['program'],sort_keys=True) for p in fit],batch_size=4)
    # Same signature-only input as the measured route; no source body is embedded.
    pair={'input':dict(statement=problem.statement,starter_code=problem.starter_code)}
    text=query_text(pair)
    encoder.encode(['Return an integer input unchanged.'],query=True,instruction=INSTRUCTION)
    setup=time.perf_counter()-started;started=time.perf_counter()
    vector=encoder.encode([text],query=True,instruction=INSTRUCTION)[0];torch.cuda.synchronize()
    similarities=memory@vector;near=np.argsort(-similarities,kind='stable')[:4]
    with torch.inference_mode():
        logits=model(torch.from_numpy(vector[None]),torch.from_numpy(memory[near][None]));codes=decisions(logits);scores={k:v[0].tolist() for k,v in logits.items()}
    shared=time.perf_counter()-started
    from pathlib import Path
    rss=int(next(line.split()[1] for line in Path('/proc/self/status').read_text().splitlines() if line.startswith('VmRSS:')))*1024
    if rss+torch.cuda.max_memory_reserved()>6*1024**3:raise RuntimeError('Composer process plus GPU reservation exceeds6GiB')
    raw_graph,raw_failure=validate_codes(encoding,codes,[p[0] for p in problem.params])
    # Raw diagnostics do not execute a second public route or spend uncharged budget.
    shared=time.perf_counter()-started
    structural=run_route('constrained',problem,codes,scores,encoding,identity,shared,receipt['structural'],2.)
    result=run_semantic_route(structural,problem,scores,encoding,identity,receipt['literal'],2.,literal_filter=unreachable_numeric_guard)
    del encoder,model;gc.collect();torch.cuda.empty_cache()
    passed=result['decision']=='answered'
    return dict(decision=result['decision'],reason=result['reason'],example_passed=passed,independent_tests_passed=None,
        language='python',code=result['source'] if passed else None,program=result['final_graph'],codec_sha256=identity,
        public_example_count=len(problem.public_tests),public=result['public'],timing=result['timing'],setup_seconds=setup,
        mode='frozen_gpu_guard',source_generation=False,checkpoint_sha256=receipt['assets_sha256']['runs/typed-student-v2/model.pt'],
        raw_decision='not_separately_executed',raw_program=raw_graph,raw_validation_failure=raw_failure,correction=result.get('semantic_repair',result.get('correction')),
        qualification=dict(scope='Ten previously consumed development-fit problems',correct=8,cases=10,wrong=0,p95_seconds=.2961809851976795,release_qualified=False,nearby_variants_qualified=False))
