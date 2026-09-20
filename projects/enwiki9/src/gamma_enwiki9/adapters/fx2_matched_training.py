"""Matched objectives from P; native forward and an explicit surrogate adjoint."""
from __future__ import annotations
import argparse
import importlib
import json
from pathlib import Path

from .fx2_native_forward import NativeForward, build, digest, reference_logits
from .fx2_training_reference import materialize, load_package, load_model
from .fx2_training_capture import validate_rows
from .fx2_weight_training import export_entries, quantized_weight_rate_bits, combined_objective


def windows(tokens, markers, priors, starts, warmup, count):
    """Actual native piece starts; no invented reset or cross-piece targets."""
    if warmup < 0 or count <= 0 or len(set(starts)) != len(starts):
        raise ValueError('invalid window budget')
    result = []
    for start in starts:
        end = start + warmup + count + 1
        if start < 0 or end > len(tokens) or markers[start] != 1:
            raise ValueError('window must start at a retained native reset')
        if any(markers[start+1:end] != 0):
            raise ValueError('window crosses a native boundary')
        result.append((tokens[start:end].copy(), markers[start:end].copy(), priors[start:end].copy()))
    if not result:
        raise ValueError('empty training population')
    return result


def loss(probabilities, tokens, warmup, count):
    import torch
    rows = torch.arange(warmup, warmup + count)
    truth = probabilities[rows, torch.tensor(tokens[warmup+1:warmup+count+1].astype('int64'))]
    if not torch.isfinite(truth).all() or (truth <= 0).any() or (truth > 1).any():
        raise ValueError('invalid truth probability')
    return -truth.double().log2().mean()


def run(root, output, plan):
    import numpy as np
    import torch
    torch.set_num_threads(1)
    torch.use_deterministic_algorithms(True)
    t = plan['training']
    if t['device'] != 'cpu' or t['steps'] != 16 or t['model_copies'] != 2:
        raise ValueError('frozen development budget differs')
    output.mkdir(exist_ok=False)
    token_path, prior_path = root / plan['tokens'], root / plan['priors']
    raw = token_path.read_bytes()
    capture = validate_rows(raw, prior_path.stat().st_size)
    tokens = np.frombuffer(raw[::2], dtype='u1')
    markers = np.frombuffer(raw[1::2], dtype='u1')
    priors = np.memmap(prior_path, dtype='<f2', mode='r', shape=(len(tokens), 205))
    population = windows(tokens, markers, priors, t['window_starts'], t['warmup_tokens'], t['loss_tokens'])
    binary, compilation = build(root / plan['native_source_zip'], root / plan['harness'],
                                 output / 'build', Path(plan['build_tools'][0][0]))
    adaptation = materialize(root / plan['upstream'], output / 'reference')
    package = load_package(output / 'reference')
    packer = importlib.import_module(package + '.weights_compress')
    template = packer.read_tensor_file_v2(str(root / plan['parent_packed']))
    forward = NativeForward(binary, digest(binary), output / 'calls')
    summary = {'schema': 'gamma.enwiki9.fx2-matched-training.v1', 'plan': t,
               'capture': capture, 'runtime': {'torch': torch.__version__, 'device': 'cpu'},
               'adaptation': adaptation, 'build': compilation, 'arms': {},
               'gradient': 'Whole-reference surrogate Jacobian; not native differentiation',
               'retention': 'Per-update raw export is disposable after its identity and predictions are retained. Final checkpoints and packed models retained.'}
    def evaluate(model, label):
        values = []
        for wi, (tok, mark, prior) in enumerate(population):
            native = forward(model, template, package, tok, mark, prior, label=f'{label}-w{wi}')
            with torch.no_grad():
                reference = reference_logits(model, tok, mark, prior).softmax(-1)
                values.append({'window': t['window_starts'][wi],
                    'native_bits': loss(native.probabilities, tok, t['warmup_tokens'], t['loss_tokens']).item() * t['loss_tokens'],
                    'reference_bits': loss(reference, tok, t['warmup_tokens'], t['loss_tokens']).item() * t['loss_tokens'],
                    'weight_sha256': native.receipt['weights_sha256']})
            # All windows in an evaluation use identical immutable current parameters.
            if wi:
                (output / 'calls' / f'{label}-w{wi}' / 'current.weights').unlink()
        return {'windows': values, 'native_bits': sum(v['native_bits'] for v in values),
                'reference_bits': sum(v['reference_bits'] for v in values)}
    parent = load_model(package, root / plan['checkpoint']); parent.eval()
    entries = export_entries(parent, template, package)
    if any(k != template[n][0] or not np.array_equal(a, template[n][1]) for n,k,a in entries):
        raise ValueError('initial checkpoint is not native P')
    summary['arms']['P'] = evaluate(parent, 'P')
    del parent
    for arm in ('A', 'J'):
        torch.manual_seed(t['seed'])
        model = load_model(package, root / plan['checkpoint']); model.eval()
        initial = {n: p.detach().clone() for n,p in model.named_parameters()}
        optimizer = torch.optim.AdamW(model.parameters(), lr=t['learning_rate'], betas=(.9,.999), eps=1e-8, weight_decay=0.)
        destination = output / arm; destination.mkdir()
        with (destination / 'metrics.jsonl').open('x') as stream:
            for step in range(t['steps']):
                wi = step % len(population); tok, mark, prior = population[wi]
                label = f'{arm}-step{step+1:02d}'
                optimizer.zero_grad(set_to_none=True)
                native = forward(model, template, package, tok, mark, prior, label=label, surrogate_backward=True)
                data = loss(native.probabilities, tok, t['warmup_tokens'], t['loss_tokens'])
                rate = quantized_weight_rate_bits(model)
                objective = data if arm == 'A' else combined_objective(data, rate, model_copies=2, represented_symbols=t['represented_symbols'])
                if not torch.isfinite(objective): raise ValueError('nonfinite objective')
                objective.backward()
                norm = torch.nn.utils.clip_grad_norm_(model.parameters(), 1., error_if_nonfinite=True)
                optimizer.step()
                if any(not torch.isfinite(p).all() for p in model.parameters()): raise ValueError('nonfinite update')
                row = {'arm': arm, 'step': step+1, 'window': t['window_starts'][wi], 'loss_tokens': t['loss_tokens'],
                       'native_data_bits_per_token': data.item(), 'weight_histogram_surrogate_bits': rate.item(),
                       'objective': objective.item(), 'surrogate_gradient_norm': norm.item(),
                       'input_weight_sha256': native.receipt['weights_sha256'], 'prediction_sha256': native.receipt['prediction_sha256']}
                stream.write(json.dumps(row, sort_keys=True)+'\n'); stream.flush(); print(json.dumps(row), flush=True)
                (output / 'calls' / label / 'current.weights').unlink()
                del native, data, rate, objective
        changed = [n for n,p in model.named_parameters() if not torch.equal(p, initial[n])]
        torch.save(model.state_dict(), destination / 'checkpoint.tch')
        entries = export_entries(model, template, package)
        packed = destination / 'weights.tfwc2'; packer.write_tensor_file_v2(str(packed), entries)
        restored = packer.read_tensor_file_v2(str(packed))
        if any(k != restored[n][0] or not np.array_equal(a, restored[n][1]) for n,k,a in entries):
            raise ValueError('packed model inverse differs')
        evaluation = evaluate(model, arm)
        # The deployed loader must reproduce the raw export on the first frozen window.
        import subprocess
        call = output / 'calls' / f'{arm}-w0'; packed_prediction = destination / 'packed-predictions.f32'
        subprocess.run([str(binary), str(packed), str(call/'tokens-markers.bin'), str(call/'priors.f16'), str(packed_prediction)],
                       check=True, timeout=120, stdout=subprocess.DEVNULL)
        if packed_prediction.read_bytes() != (call/'predictions.f32').read_bytes():
            raise ValueError('packed native inference differs from training export')
        evaluation.update(changed_parameters=changed, optimizer_updates=t['steps'], loss_token_exposures=t['steps']*t['loss_tokens'],
                          packed_bytes=packed.stat().st_size, packed_sha256=digest(packed), packed_forward_exact=True)
        evaluation['delta_native_bits'] = evaluation['native_bits'] - summary['arms']['P']['native_bits']
        evaluation['delta_reference_bits'] = evaluation['reference_bits'] - summary['arms']['P']['reference_bits']
        evaluation['delta_mismatch_bits'] = evaluation['delta_native_bits'] - evaluation['delta_reference_bits']
        summary['arms'][arm] = evaluation
        (destination/'training.json').write_text(json.dumps(evaluation, indent=2)+'\n')
        del model, optimizer, initial
    (output/'comparison.json').write_text(json.dumps(summary, indent=2)+'\n')


def main():
    parser=argparse.ArgumentParser()
    for n in ('root','output','plan'): parser.add_argument('--'+n,type=Path,required=True)
    a=parser.parse_args();run(a.root,a.output,json.loads(a.plan.read_bytes()))

if __name__ == '__main__': main()
