"""Observer insertion into the exact retained native codec; no changed predictions."""
import hashlib
from .fx2_training_capture import source_members, SOURCE_PREIMAGES


def adapt(source_zip, header):
    members = source_members(source_zip)
    changes = {
        'src/runner.cpp': [
            ('#include "predictor.h"', '#include "predictor.h"\n#include "gamma-trajectory.h"'),
            ('  Compress(temp_bytes, &temp_in, &data_out, output_bytes, &p);',
             '  gamma_trajectory::begin();\n  Compress(temp_bytes, &temp_in, &data_out, output_bytes, &p);\n  gamma_trajectory::end();'),
            ('  Decompress(*output_bytes, &data_in, &temp_out, &p);',
             '  gamma_trajectory::begin();\n  Decompress(*output_bytes, &data_in, &temp_out, &p);\n  gamma_trajectory::end();'),
        ],
        'src/predictor.cpp': [
            ('#include "predictor.h"', '#include "predictor.h"\n#include "gamma-trajectory.h"'),
            ('  if (last_of_piece) {\n    // The next token starts a fresh context;',
             '  gamma_trajectory::row(token, last_of_piece ? 2 : article_tokens_ == 1 ? 1 : 0, half_scratch_.data());\n  if (last_of_piece) {\n    gamma_trajectory::publish(nullptr);\n    // The next token starts a fresh context;'),
            ('        transformer_probs_.data());\n    FloatsToHalves(transformer_probs_.data(),',
             '        transformer_probs_.data());\n    gamma_trajectory::publish(transformer_probs_.data());\n    FloatsToHalves(transformer_probs_.data(),'),
        ],
    }
    for name in ('encoder', 'decoder'):
        changes[f'src/coder/{name}.cpp'] = [
            (f'#include "{name}.h"', f'#include "{name}.h"\n#include "../gamma-trajectory.h"'),
            ('  p_->Perceive(bit);', '  gamma_trajectory::bit(p, bit);\n  p_->Perceive(bit);'),
        ]
    receipts = []
    for name, replacements in changes.items():
        before = members[name]
        if name in SOURCE_PREIMAGES and hashlib.sha256(before).hexdigest() != SOURCE_PREIMAGES[name]:
            raise ValueError('native preimage mismatch: ' + name)
        text = before.decode()
        for old, new in replacements:
            if text.count(old) != 1:
                raise ValueError('ambiguous observer anchor: ' + name)
            text = text.replace(old, new)
        members[name] = text.encode()
        receipts.append({'path': name, 'preimage_sha256': hashlib.sha256(before).hexdigest(),
                         'postimage_sha256': hashlib.sha256(members[name]).hexdigest()})
    members['src/gamma-trajectory.h'] = header.read_bytes()
    receipts.append({'path': 'src/gamma-trajectory.h', 'postimage_sha256': hashlib.sha256(header.read_bytes()).hexdigest()})
    return members, receipts
