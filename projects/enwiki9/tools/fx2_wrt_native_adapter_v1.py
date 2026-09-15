"""Add a causal WRT bit-elision layer while preserving every parent update."""
import hashlib
import io
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]
ZIP = 'results/fx2_expert_release250k_v3/P-source.zip'
ZIP_SHA = 'c44d941f95bd8504d63ed6ea5112af3ce15aeffb6874ebddb66596ce083c3cf6'
HEADER = 'lib/fx2_wrt_native_v1.hpp'
CHANGED = ('src/runner.cpp', 'src/coder/encoder.cpp', 'src/coder/decoder.cpp')


def mutate(data, header):
    if hashlib.sha256(data).hexdigest() != ZIP_SHA:
        raise ValueError('parent ZIP identity differs')
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        if len(z.namelist()) != 127 or len(set(z.namelist())) != 127:
            raise ValueError('duplicate source names')
        members = {name: z.read(name) for name in z.namelist()}
    result = dict(members)
    def replace(name, old, new):
        text = result[name].decode()
        if text.count(old) != 1:
            raise ValueError('source anchor differs: '+name+' '+old)
        result[name] = text.replace(old, new).encode()
    for kind in ('encoder', 'decoder'):
        name = 'src/coder/'+kind+'.cpp'
        replace(name, '#include "'+kind+'.h"', '#include "'+kind+'.h"\n#include "../gamma-wrt.h"')
        forced = '  const int forced = gamma_wrt::forced();\n  if (forced >= 0) {\n'
        if kind == 'encoder':
            forced += '    if (bit != forced) gamma_wrt::fail();\n'
        else:
            forced += '    const int bit = forced;\n'
        forced += '    gamma_wrt::observe(bit,p,forced);\n    p_->Perceive(bit);\n    return'+(';' if kind == 'encoder' else ' bit;')+'\n  }\n'
        replace(name, '  const unsigned int xmid =', forced+'  const unsigned int xmid =')
        replace(name, '  p_->Perceive(bit);\n\n  while', '  gamma_wrt::observe(bit,p,forced);\n  p_->Perceive(bit);\n\n  while')
    name = 'src/runner.cpp'
    replace(name, '#include "preprocess/dictionary.h"', '#include "preprocess/dictionary.h"\n#include "gamma-wrt.h"')
    replace(name, '    data_out.write("GFV1", 4);', '#ifndef GAMMA_WRT_BOOKKEEPING\n    data_out.put(1); data_out.put(1);\n#endif\n    data_out.write("GFV1", 4);')
    replace(name, '    char magic[4] = {0};', '#ifndef GAMMA_WRT_BOOKKEEPING\n    if (data_in.get() != 1 || data_in.get() != 1) gamma_wrt::fail();\n#endif\n    char magic[4] = {0};')
    replace(name, '  Compress(temp_bytes, &temp_in, &data_out, output_bytes, &p);',
            '  if (!gamma_static_frontend || !dictionary) gamma_wrt::fail();\n  gamma_wrt::init(dictionary,vocab);\n  Compress(temp_bytes, &temp_in, &data_out, output_bytes, &p);\n  gamma_wrt::grammar.finish();')
    replace(name, '  Decompress(*output_bytes, &data_in, &temp_out, &p);',
            '  if (!gamma_static_frontend || !dictionary) gamma_wrt::fail();\n  gamma_wrt::init(dictionary,vocab);\n  Decompress(*output_bytes, &data_in, &temp_out, &p);\n  gamma_wrt::grammar.finish();')
    result['src/gamma-wrt.h'] = header
    if {k for k in members if members[k] != result[k]} != set(CHANGED):
        raise ValueError('unexpected changed source set')
    return members, result
