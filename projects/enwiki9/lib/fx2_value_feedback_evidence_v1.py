"""Diagnostic source attachment and complete residual-stream validation."""
import hashlib
import json
import struct
import zlib

from lib.fx2_value_feedback_native_v1 import MODEL, replace_once


def coder_observer_adapter(sources):
    """Bind the trimmed coder, whose disabled release hooks differ from upstream."""
    expected = {
        'encoder': '01c43deb487706c80438bbf2187587bdb22ed56974d0c500d1ab5a6eced9a9fb',
        'decoder': '9565ac7a3d73ee04a46e7c802581fab6be1e950f99c9c73536053a354d2c6860'}
    rows = []
    for name in ('encoder', 'decoder'):
        path = 'src/coder/' + name + '.cpp'
        raw = sources[path]
        if hashlib.sha256(raw).hexdigest() != expected[name]:
            raise ValueError('trimmed coder source differs')
        changes = [(f'#include "{name}.h"', f'#include "{name}.h"\n#include "gamma-coder-trace.h"'),
            ('  unsigned int p = Discretize(p_->Predict());',
             '  const float gamma_probability = p_->Predict();\n'
             '  unsigned int p = Discretize(gamma_probability);'),
            ('  const unsigned int xmid =',
             '  gamma_fx2_trace::Record gamma_record(gamma_probability, p, x1_, x2_);\n'
             '  const unsigned int xmid =')]
        if name == 'encoder':
            changes.append(('    x2_ = (x2_ << 8) + 255;\n  }\n}\n\nvoid Encoder::Flush()',
                            '    x2_ = (x2_ << 8) + 255;\n  }\n'
                            '  gamma_record.Finish(bit, x1_, x2_);\n}\n\nvoid Encoder::Flush()'))
        else:
            changes.append(('  return bit;', '  gamma_record.Finish(bit, x1_, x2_);\n  return bit;'))
        text = raw.decode('utf-8')
        for before, after in changes:
            text = replace_once(text, before, after)
        rows.append(dict(source_path=path, source_sha256=expected[name],
            patched_sha256=hashlib.sha256(text.encode()).hexdigest(),
            replacements=[dict(before=a, after=b) for a, b in changes]))
    return dict(schema='gamma.enwiki9.exact-source-adapter-multi.v1',
                adapter_id='fx2_value_feedback_coder_observer_v1', files=rows,
                scope='Observation only. Original Predict/Perceive and quantization order retained.')


def observe_sources(sources, arm, coder_adapter, coder_header, value_header):
    result = dict(sources)
    for row in coder_adapter['files']:
        name = row['source_path']
        if name not in ('src/coder/encoder.cpp', 'src/coder/decoder.cpp'):
            continue
        raw = sources[name]
        if hashlib.sha256(raw).hexdigest() != row['source_sha256']:
            raise ValueError('coder observer preimage differs')
        text = raw.decode('utf-8')
        for change in row['replacements']:
            text = replace_once(text, change['before'], change['after'])
        raw = text.encode('utf-8')
        if hashlib.sha256(raw).hexdigest() != row['patched_sha256']:
            raise ValueError('coder observer postimage differs')
        result[name] = raw
    result['src/coder/gamma-coder-trace.h'] = coder_header
    if arm != 'P':
        text = result[MODEL].decode('utf-8')
        anchor = '#include "gamma_value_feedback_v1.h"'
        text = replace_once(text, anchor, anchor + '\n#define GAMMA_VALUE_FEEDBACK_PROBE\n'
                            '#include "gamma_value_feedback_observer_v1.h"')
        result[MODEL] = text.encode('utf-8')
        result['cpp_infer/src/opt/gamma_value_feedback_observer_v1.h'] = value_header
    return result


def residual_stream(path):
    """Read every residual; reject missing footer, illegal values and reset order."""
    size = path.stat().st_size
    if size < 20 or size % 4:
        raise ValueError('residual stream length invalid')
    count = resets = maximum = nonzero = 0
    with path.open('rb') as f:
        if f.read(4) != b'GVF1':
            raise ValueError('residual stream header invalid')
        remaining = size - 20
        while remaining:
            data = f.read(min(65536, remaining))
            if not data or len(data) % 4:
                raise ValueError('residual stream truncated')
            remaining -= len(data)
            for (v,) in struct.iter_unpack('<i', data):
                if v == -2147483648:
                    if count % 576:
                        raise ValueError('mid-token reset')
                    resets += 1
                elif -32768 <= v <= 32768:
                    if not resets:
                        raise ValueError('residual before reset')
                    count += 1
                    nonzero += v != 0
                    maximum = max(maximum, abs(v))
                else:
                    raise ValueError('residual out of range')
        end, lo, hi, declared_resets = struct.unpack('<IIII', f.read(16))
        if (end != 0x80000001 or count != lo + (hi << 32) or count % 576 or
                resets != declared_resets or not count or not resets or f.read(1)):
            raise ValueError('residual footer or population differs')
    return dict(observations=count, tokens=count // 576, resets=resets,
                maximum_abs_residual=maximum, nonzero_residuals=nonzero,
                stream_bytes=size, complete=True)


def pack_stream(path, directory):
    """Preserve complete diagnostic bytes in individually publishable chunks."""
    directory.mkdir()
    digest = hashlib.sha256()
    restored = hashlib.sha256()
    size = 0
    chunks = []
    with path.open('rb') as source:
        while raw := source.read(8 * 1024 * 1024):
            name = f'{len(chunks):05d}.zlib'
            packed = zlib.compress(raw, 1)
            target = directory / name
            target.write_bytes(packed)
            decoded = zlib.decompress(target.read_bytes())
            if decoded != raw:
                raise ValueError('diagnostic packing inverse differs')
            digest.update(raw); restored.update(decoded); size += len(raw)
            chunks.append(dict(file=name, raw_bytes=len(raw), bytes=len(packed),
                raw_sha256=hashlib.sha256(raw).hexdigest(),
                sha256=hashlib.sha256(packed).hexdigest()))
    if digest.digest() != restored.digest() or size != path.stat().st_size:
        raise ValueError('diagnostic packing completeness differs')
    manifest = directory / 'manifest.json'
    manifest.write_text(json.dumps(dict(schema='gamma.enwiki9.lossless-diagnostic-chunks.v1',
        algorithm='zlib', chunk_raw_limit_bytes=8 * 1024 * 1024,
        original_bytes=size, original_sha256=digest.hexdigest(), chunks=chunks,
        exact_chunk_inverse=True, scope='Evidence storage only; not codec or score.'), indent=2) + '\n')
    return manifest
