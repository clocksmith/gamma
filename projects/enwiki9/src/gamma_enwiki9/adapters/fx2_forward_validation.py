"""Fixed P/E native-forward validation. Backward checks never update parameters."""
from __future__ import annotations
import argparse
import gc
import hashlib
import importlib
import json
from pathlib import Path

from .fx2_native_forward import NativeForward, build, digest
from .fx2_training_reference import materialize, load_package, load_model
from .fx2_numeric_reference import loss_bits


def write(path, value):
    with path.open('x') as stream:
        json.dump(value, stream, indent=2)
        stream.write('\n')


def state_identity(model):
    return {name: hashlib.sha256(value.detach().numpy().tobytes()).hexdigest()
            for name, value in model.state_dict().items()}


def run(root, output, plan):
    import numpy as np
    import torch
    torch.set_num_threads(1)
    torch.use_deterministic_algorithms(True)
    output.mkdir(parents=True, exist_ok=False)
    binary, build_record = build(root/plan['native_source_zip'], root/plan['harness'],
                                 output/'build', Path(plan['compiler']))
    materialize(root/plan['upstream'], output/'reference')
    package = load_package(output/'reference')
    packer = importlib.import_module(package+'.weights_compress')
    forward = NativeForward(binary, build_record['binary_sha256'], output/'calls')
    result = {'schema': 'gamma.enwiki9.fx2-native-forward-validation.v1',
              'build': build_record, 'plan': plan, 'fixtures': {},
              'training_performed': False, 'optimizer_updates': 0,
              'gradient_semantics': 'whole CPU-reference Jacobian plus Torch softmax at native logits; surrogate, not native differentiation',
              'internal_torch_state_parity_established': False,
              'full_corpus_score_bytes': None, 'objective_credit_bytes': 0}
    for fixture in plan['fixtures']:
        original = root/plan['baseline']/fixture
        tm = np.fromfile(original/'tokens-markers.bin', dtype='u1').reshape(-1, 2)
        tokens, markers = tm[:,0].copy(), tm[:,1].copy()
        priors = np.fromfile(original/'priors.f16', dtype='<f2').reshape(-1,205)
        item = {'rows': len(tokens), 'arms': {}, 'repeat_P_bitwise_equal': False}
        for arm in ('P', 'E', 'P-repeat'):
            selected = 'P' if arm == 'P-repeat' else arm
            paths = plan['checkpoints'][selected]
            model = load_model(package, root/paths['checkpoint'])
            template = packer.read_tensor_file_v2(str(root/paths['packed']))
            before = state_identity(model)
            gradient_check = fixture == 'synthetic' and arm != 'P-repeat'
            call = forward(model, template, package, tokens, markers, priors,
                           label=fixture+'-'+arm, surrogate_backward=gradient_check)
            # Expected predictions enter the validator only after forward execution.
            native = np.fromfile(original/selected/'base.f32', dtype='<f4').reshape(-1,410)
            values = np.concatenate((call.logits.detach().numpy(), call.probabilities.detach().numpy()),axis=1)
            if values.tobytes() != native.tobytes():
                raise ValueError('forward differs from pinned native baseline: '+fixture+'/'+arm)
            expected_tensors = json.loads((original/selected/'decoded-tensors.json').read_bytes())
            expected_tensors = sorted(expected_tensors,key=lambda x:x['name'])
            if sorted(call.receipt['exported_tensors'],key=lambda x:x['name']) != expected_tensors:
                raise ValueError('fresh checkpoint export differs from decoded native tensors')
            actual_loss = call.loss_bits(tokens, markers)
            native_loss, truth = loss_bits(native[:,205:],tokens,markers)
            if abs(actual_loss.item()-native_loss['bits']) > 1e-10:
                raise ValueError('loss reduction differs from native truth probabilities')
            gradients = {'performed': False}
            if gradient_check:
                actual_loss.backward()
                values_grad = [p.grad for p in model.parameters() if p.grad is not None]
                if not values_grad or not all(torch.isfinite(g).all() for g in values_grad):
                    raise ValueError('missing or nonfinite surrogate gradient')
                nonzero = sum(bool(torch.count_nonzero(g)) for g in values_grad)
                if not nonzero:
                    raise ValueError('all surrogate gradients are zero')
                gradients = {'performed': True, 'participating_parameter_tensors': len(values_grad),
                             'nonzero_parameter_tensors': nonzero, 'all_finite': True,
                             'optimizer_updates': 0}
            if state_identity(model) != before:
                raise ValueError('model state changed during fixed-checkpoint validation')
            item['arms'][arm] = {'native_loss': native_loss, 'corrected_loss_bits': actual_loss.item(),
                'max_logit_difference': 0, 'max_probability_difference': 0,
                'all_forward_values_bitwise_equal': True, 'exported_tensors_equal': len(expected_tensors),
                'parameters_unchanged': True, 'gradients': gradients,
                'forward_receipt': str((output/'calls'/(fixture+'-'+arm)/'forward.json').relative_to(output))}
            del actual_loss, call, model, template
            gc.collect()
        p,e,repeat = (item['arms'][a] for a in ('P','E','P-repeat'))
        assert p['native_loss'] == repeat['native_loss']
        item['repeat_P_bitwise_equal'] = True
        item['delta_reference_bits'] = e['corrected_loss_bits']-p['corrected_loss_bits']
        item['delta_native_bits'] = e['native_loss']['bits']-p['native_loss']['bits']
        item['delta_mismatch_bits'] = item['delta_native_bits']-item['delta_reference_bits']
        # Probability arrays agree bitwise; scalar reduction can differ by FP64 summation order.
        item['loss_reduction_absolute_bound_bits'] = 1e-10
        result['fixtures'][fixture] = item
        print(json.dumps({'fixture':fixture,'forward_bitwise_equal':True,
                          'delta_mismatch_bits':item['delta_mismatch_bits']}),flush=True)
    result['comparison_complete'] = True
    result['forward_parity_pass'] = True
    result['promotion_authorized'] = False
    write(output/'comparison.json', result)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    for field in ('root','output','plan'):
        parser.add_argument('--'+field,type=Path,required=True)
    args = parser.parse_args()
    run(args.root.resolve(),args.output.resolve(),json.loads(args.plan.read_bytes()))
