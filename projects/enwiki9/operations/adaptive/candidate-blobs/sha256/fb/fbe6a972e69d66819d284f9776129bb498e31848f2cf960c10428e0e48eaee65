"""Frozen 2x2 coverage/preservation comparison; native forward, surrogate backward."""
from __future__ import annotations
import argparse
import importlib
import json
from pathlib import Path
import time

from .fx2_native_forward import NativeForward, build, digest
from .fx2_training_reference import materialize, load_package, load_model
from .fx2_training_capture import validate_rows
from .fx2_weight_training import export_entries
from .fx2_matched_training import windows, loss

ARMS = {'N': (False, False), 'B': (True, False), 'R': (False, True), 'BR': (True, True)}


def distribution_kl(child, teacher):
    """Mean KL(P||child), in bits, over all205 vocabulary entries per row.

Native FP32 softmax rows are explicitly renormalized in FP64. The teacher is
training-only and detached; normalization and KL use the surrogate Jacobian for
the child. This is not an exact derivative of the deployed rounded computation.
"""
    import torch
    if child.ndim != 2 or child.shape != teacher.shape or child.shape[1] != 205:
        raise ValueError('full native vocabulary required')
    if teacher.requires_grad:
        raise ValueError('teacher must be frozen')
    for value in (child, teacher):
        if not torch.isfinite(value).all() or (value <= 0).any() or (value > 1).any():
            raise ValueError('invalid native distribution')
        if (value.double().sum(-1)-1).abs().max() > 1e-5:
            raise ValueError('native softmax normalization differs')
    q = child.double(); p = teacher.double()
    q = q / q.sum(-1, keepdim=True); p = p / p.sum(-1, keepdim=True)
    return (p*(p.log2()-q.log2())).sum(-1).mean()


def target_sets(plan):
    t = plan['training']; count=t['loss_tokens']; warmup=t['warmup_tokens']
    return {name: {row for start in t[name+'_starts'] for row in range(start+warmup+1, start+warmup+count+1)}
            for name in ('narrow', 'broad', 'preservation')}


def partition_name(target, eligible, masks):
    if not eligible:
        if any(target in mask for mask in masks.values()):
            raise ValueError('mask includes an unavailable neural target')
        return 'no_neural'
    return ''.join('1' if target in masks[name] else '0' for name in ('narrow','broad','preservation'))


def run(root, output, plan):
    import numpy as np
    import torch
    torch.set_num_threads(1); torch.use_deterministic_algorithms(True)
    t=plan['training']
    if (t['device'],t['steps'],t['loss_tokens'],t['warmup_tokens'],t['preservation_coefficient']) != ('cpu',16,128,512,1.):
        raise ValueError('frozen training profile differs')
    output.mkdir(exist_ok=False)
    raw=(root/plan['tokens']).read_bytes(); prior_path=root/plan['priors']
    capture=validate_rows(raw,prior_path.stat().st_size)
    tokens=np.frombuffer(raw[::2],dtype='u1'); markers=np.frombuffer(raw[1::2],dtype='u1')
    priors=np.memmap(prior_path,dtype='<f2',mode='r',shape=(len(tokens),205))
    starts=t['preservation_starts']
    pop=dict(zip(starts,windows(tokens,markers,priors,starts,512,128)))
    if not set(t['narrow_starts']) <= set(t['broad_starts']) <= set(starts):
        raise ValueError('frozen context inclusion differs')
    binary,compilation=build(root/plan['native_source_zip'],root/plan['harness'],output/'build',Path(plan['build_tools'][0][0]))
    adaptation=materialize(root/plan['upstream'],output/'reference');package=load_package(output/'reference')
    packer=importlib.import_module(package+'.weights_compress');template=packer.read_tensor_file_v2(str(root/plan['parent_packed']))
    forward=NativeForward(binary,digest(binary),output/'calls')
    summary={'schema':'gamma.enwiki9.coverage-preservation-training.v1','plan':t,'capture':capture,
        'runtime':{'torch':torch.__version__,'numpy':np.__version__,'device':'cpu'},'adaptation':adaptation,'build':compilation,
        'arms':{},'teacher':'Detached full native205-token distributions, training-only; no hidden state or predictions enter deployed child.',
        'backward':'Explicit whole-reference surrogate; not exact differentiation of native quantization or finite archives.'}
    teacher={}
    def evaluate(model,label):
        values=[];first=None
        for wi,start in enumerate(starts):
            tok,mark,prior=pop[start];native=forward(model,template,package,tok,mark,prior,label=f'{label}-w{wi}')
            if label=='P':teacher[start]=native.probabilities[512:640].detach().clone()
            values.append({'window':start,'native_bits':128*loss(native.probabilities,tok,512,128).item(),
                'kl_from_P_bits_per_target':distribution_kl(native.probabilities[512:640],teacher[start]).item()})
            if wi: (output/'calls'/f'{label}-w{wi}'/'current.weights').unlink()
            else:first=native.receipt['weights_sha256']
        return {'windows':values,'native_bits':sum(v['native_bits'] for v in values),'evaluation_targets':len(starts)*128,'raw_export_sha256':first}
    parent=load_model(package,root/plan['checkpoint']);parent.eval()
    if any(k!=template[n][0] or not np.array_equal(a,template[n][1]) for n,k,a in export_entries(parent,template,package)):
        raise ValueError('initial checkpoint differs from native P')
    begin=time.monotonic();summary['arms']['P']=evaluate(parent,'P');summary['teacher_generation_wall_seconds']=time.monotonic()-begin
    del parent
    for arm,(broader,preserve) in ARMS.items():
        torch.manual_seed(t['seed']);model=load_model(package,root/plan['checkpoint']);model.eval()
        initial={n:p.detach().clone() for n,p in model.named_parameters()}
        optimizer=torch.optim.AdamW(model.parameters(),lr=t['learning_rate'],betas=(.9,.999),eps=1e-8,weight_decay=0.)
        schedule=t['broad_starts'] if broader else t['narrow_starts']; destination=output/arm;destination.mkdir()
        wall=time.monotonic()
        with (destination/'metrics.jsonl').open('x') as stream:
            for step in range(16):
                tick=time.monotonic();optimizer.zero_grad(set_to_none=True)
                start=schedule[step%len(schedule)];tok,mark,prior=pop[start];label=f'{arm}-step{step+1:02d}-supervised'
                native=forward(model,template,package,tok,mark,prior,label=label,surrogate_backward=True)
                data=loss(native.probabilities,tok,512,128);data_value=data.item();input_sha=native.receipt['weights_sha256']
                data.backward();del data,native
                (output/'calls'/label/'current.weights').unlink()
                replay_start=None;kl_value=0.;replay_sha=None
                if preserve:
                    replay_start=starts[step%len(starts)];tok,mark,prior=pop[replay_start];label=f'{arm}-step{step+1:02d}-preservation'
                    native=forward(model,template,package,tok,mark,prior,label=label,surrogate_backward=True)
                    if native.receipt['weights_sha256']!=input_sha:raise ValueError('parameters changed between loss terms')
                    kl=distribution_kl(native.probabilities[512:640],teacher[replay_start]);kl_value=kl.item()
                    (t['preservation_coefficient']*kl).backward();replay_sha=native.receipt['prediction_sha256'];del kl,native
                    (output/'calls'/label/'current.weights').unlink()
                norm=torch.nn.utils.clip_grad_norm_(model.parameters(),1.,error_if_nonfinite=True);optimizer.step()
                if any(not torch.isfinite(p).all() for p in model.parameters()):raise ValueError('nonfinite update')
                row={'arm':arm,'step':step+1,'supervised_start':start,'supervised_targets':128,
                    'preservation_start':replay_start,'preservation_targets':128 if preserve else 0,'distribution_entries_per_target':205 if preserve else 0,
                    'native_data_bits_per_target':data_value,'preservation_kl_bits_per_target':kl_value,'objective':data_value+kl_value*t['preservation_coefficient'],
                    'surrogate_gradient_norm':norm.item(),'input_weight_sha256':input_sha,'preservation_prediction_sha256':replay_sha,'elapsed_seconds':time.monotonic()-tick}
                stream.write(json.dumps(row,sort_keys=True)+'\n');stream.flush();print(json.dumps(row),flush=True)
        train_seconds=time.monotonic()-wall
        changed=[n for n,p in model.named_parameters() if not torch.equal(p,initial[n])]
        torch.save(model.state_dict(),destination/'checkpoint.tch')
        entries=export_entries(model,template,package);packed=destination/'weights.tfwc2';packer.write_tensor_file_v2(str(packed),entries)
        restored=packer.read_tensor_file_v2(str(packed))
        if any(k!=restored[n][0] or not np.array_equal(a,restored[n][1]) for n,k,a in entries):raise ValueError('packed model inverse differs')
        evaluation=evaluate(model,arm)
        import subprocess
        call=output/'calls'/f'{arm}-w0';pp=destination/'packed-predictions.f32'
        subprocess.run([str(binary),str(packed),str(call/'tokens-markers.bin'),str(call/'priors.f16'),str(pp)],check=True,timeout=120,stdout=subprocess.DEVNULL)
        if pp.read_bytes()!=(call/'predictions.f32').read_bytes():raise ValueError('packed export inference differs')
        evaluation.update(changed_parameters=changed,optimizer_updates=16,supervised_exposures=2048,distinct_supervised_targets=len(schedule)*128,
            preservation_exposures=2048 if preserve else 0,distinct_preservation_targets=len(starts)*128 if preserve else 0,
            training_forward_calls=32 if preserve else 16,training_forward_rows=641*(32 if preserve else 16),surrogate_backward_calls=32 if preserve else 16,
            training_wall_seconds=train_seconds,packed_bytes=packed.stat().st_size,packed_sha256=digest(packed),checkpoint_sha256=digest(destination/'checkpoint.tch'),packed_forward_exact=True)
        summary['arms'][arm]=evaluation;(destination/'training.json').write_text(json.dumps(evaluation,indent=2)+'\n')
        del model,optimizer,initial
    (output/'comparison.json').write_text(json.dumps(summary,indent=2)+'\n')


def main():
    parser=argparse.ArgumentParser()
    for name in ('root','output','plan'):parser.add_argument('--'+name,type=Path,required=True)
    a=parser.parse_args();run(a.root,a.output,json.loads(a.plan.read_bytes()))

if __name__=='__main__':main()
