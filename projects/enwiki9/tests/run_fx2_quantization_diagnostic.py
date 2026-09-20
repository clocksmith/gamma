"""Localize FX2 CPU/native rounding on eight synthetic tokens; no corpus input."""
from pathlib import Path
import argparse
import json
import subprocess
import tempfile

from run_fx2_reference_diagnostic import ROOT, identity
from gamma_enwiki9.adapters.fx2_title_native import adapt
from gamma_enwiki9.adapters.fx2_training_reference import materialize, load_package, load_model


def run(output):
    import numpy as np
    import torch
    output = output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    torch.set_num_threads(1)
    upstream = ROOT / 'external/fx2-cmix-transformer-v1'
    checkpoint = upstream / 'models/6m-q4-fp32.tch'
    packed = upstream / 'models/6m-q4-fp32.tfwc2'
    source = ROOT / 'results/fx2_expert_release250k_v3/P-source.zip'
    fixture = ROOT / 'tests/fx2_title_model_fixture.cpp'
    report = {'schema': 'gamma.enwiki9.fx2-synthetic-quantization-diagnostic.v1',
              'tokens': list(range(8)), 'prior_binary16_bits': '0x1cff',
              'scope': 'parent P, block index3, first vanilla attention and its MLP',
              'inputs': [identity(p) for p in (Path(__file__), fixture, checkpoint, packed, source)],
              'observations': {}, 'objective_credit_bytes': 0,
              'limitation': 'Localizes this synthetic mismatch only; does not attribute corpus archive losses.'}
    with tempfile.TemporaryDirectory(prefix='gamma-fx2-quant-') as temporary:
        work = Path(temporary)
        native = work / 'native'
        members, report['native_adaptation'] = adapt(source, ROOT / 'lib')
        for name, data in members.items():
            path = native / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
        infer = native / 'cpp_infer/src'
        path = infer / 'opt/model_opt.cpp'
        original = path.read_text()
        helper = '''
#include <string>
static void gamma_dump(const char* name, const void* p, size_t n) {
  std::string path = std::string(%s) + name + ".bin";
  FILE* f = std::fopen(path.c_str(), "ab");
  if (!f || std::fwrite(p, 1, n, f) != n) std::abort();
  std::fclose(f);
}
''' % json.dumps(str(work) + '/')
        original = original.replace('namespace fx2 {', helper + '\nnamespace fx2 {', 1)
        patches = {
            'rms_norm_quant192_x3(x, xn, s3, q5, q5 + D, q5 + 2 * D);':
                'if (vi==0) gamma_dump("qkv", q5, 576);',
            'const int slot = static_cast<int>(t % WIN);':
                'if (vi==0) { gamma_dump("q",qq,192); gamma_dump("k",kk,192); gamma_dump("v",vv,192); }',
            'quant192_u8(pre, L.op.s_act, q5);':
                'if (vi==0) gamma_dump("op",q5,192);',
            'rms_norm_quant192(x, xn, mm.up.s_act, q5);': '''if (l==3) {
                gamma_dump("up",q5,192);
                alignas(64) float gamma_y[768];
                qgemv_f32(mm.up.m, q5, gamma_y);
                for (int i=0; i<768; ++i) {
                  const float y = std::max(gamma_y[i], 0.0f);
                  gamma_y[i] = (y*y)/mm.down_s_act;
                }
                gamma_dump("down_scaled",gamma_y,sizeof(gamma_y));
            }''',
            'nnz = qgemv_relu2q(mm.up.m, q5, mm.down_s_act, q768, idx768);':
                'if (l==3) gamma_dump("down",q768,768);',
        }
        for anchor, extra in patches.items():
            if original.count(anchor) != 1:
                raise ValueError('ambiguous quantization capture anchor: ' + anchor)
            original = original.replace(anchor, anchor + '\n' + extra)
        path.write_text(original)
        (output / 'instrumented-model.cpp').write_text(original)
        sources = [infer / 'weights_io.cpp', infer / 'weights_io_compressed.cpp',
                   *[infer / 'opt' / (n + '.cpp') for n in
                     ('qmat_dense', 'qmat_sparse', 'attn', 'kda', 'glue', 'arena_build', 'model_opt')]]
        binary = work / 'fixture'
        command = ['/usr/bin/g++', '-std=c++17', '-O3', '-march=x86-64-v3', '-mrecip=none',
                   '-fno-math-errno', '-I', str(native), str(fixture), *map(str, sources), '-o', str(binary)]
        report['compile_command_template'] = [s.replace(str(work), '${WORKSPACE}') for s in command]
        subprocess.run(command, check=True, timeout=120)
        subprocess.run([str(binary), str(packed)], check=True, stdout=subprocess.DEVNULL, timeout=30)
        reference = work / 'reference'
        report['reference_adaptation'] = materialize(upstream, reference)
        model = load_model(load_package(reference), checkpoint)
        recorded, inputs = {}, {}
        for name, module in model.blocks[3].named_modules():
            if name.endswith('quantize_activation') or name in (
                    'attention.quantize_queries', 'attention.quantize_keys', 'attention.quantize_values'):
                def hook(m, args, out, name=name):
                    scale = m.scale.detach().to(torch.bfloat16).float().reshape(1, -1, 1)
                    recorded[name] = (m.reshape_input(out) / scale).round().numpy().reshape(8, -1)
                    inputs[name] = (m.reshape_input(args[0]) / scale).detach().numpy().reshape(8, -1)
                module.register_forward_hook(hook)
        prior = np.array([0x1cff], dtype=np.uint16).view(np.float16).astype(np.float32).item()
        with torch.no_grad():
            model.compute_logits(torch.arange(8).reshape(1, 8), torch.full((1, 8, 205), prior),
                                 torch.tensor([[0, 8]], dtype=torch.int32))
        qkv = np.fromfile(work / 'qkv.bin', dtype=np.uint8).reshape(8, 576).astype(int) - 128
        for name, key, column in (
            ('attention.query_projection.quantize_activation', 'qkv', 0),
            ('attention.key_projection.quantize_activation', 'qkv', 192),
            ('attention.value_projection.quantize_activation', 'qkv', 384),
            ('attention.quantize_queries', 'q', 0), ('attention.quantize_keys', 'k', 0),
            ('attention.quantize_values', 'v', 0), ('attention.output_projection.quantize_activation', 'op', 0),
            ('mlp.up.quantize_activation', 'up', 0), ('mlp.down.quantize_activation', 'down', 0)):
            if key == 'qkv':
                other = qkv[:, column:column+192]
            elif key in ('q', 'k', 'v'):
                other = np.fromfile(work / (key + '.bin'), dtype=np.int8).reshape(8, 192)
            else:
                other = np.fromfile(work / (key + '.bin'), dtype=np.uint8).reshape(8, -1).astype(int)
                if key != 'down':
                    other -= 128
            indices = np.argwhere(other != recorded[name])
            rows = []
            for coordinate in indices:
                index = tuple(coordinate)
                row = {'coordinate': coordinate.tolist(), 'native_bin': int(other[index]),
                       'cpu_bin': int(recorded[name][index]), 'cpu_scaled': float(inputs[name][index])}
                if key == 'down':
                    row['native_scaled'] = float(np.fromfile(work / 'down_scaled.bin', dtype='<f4').reshape(8, 768)[index])
                rows.append(row)
            report['observations'][name] = {'mismatches': len(rows), 'rows': rows}
        for name in ('qkv', 'q', 'k', 'v', 'op', 'up', 'down', 'down_scaled'):
            (output / (name + '.bin')).write_bytes((work / (name + '.bin')).read_bytes())
    import hashlib
    report['outputs'] = {p.name: {'bytes': p.stat().st_size, 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()}
                         for p in sorted(output.iterdir())}
    (output / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report['observations']['mlp.down.quantize_activation']))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path)
    run(parser.parse_args().output)
