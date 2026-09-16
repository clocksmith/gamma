"""Fixed source adapter for article-local attention cache retention."""
import hashlib

SOURCE = 'cpp_infer/src/opt/model_opt.cpp'
HEADER = 'cpp_infer/src/opt/gamma_attention_anchor.h'
PREIMAGE = 'b49493ece5a3a135baa24eeef00d6aaf56335324d0c6355b7283e46736c9df8e'


def materialize(members, header):
    data = members[SOURCE]
    if hashlib.sha256(data).hexdigest() != PREIMAGE or HEADER in members:
        raise ValueError('attention anchor source preimage differs')
    replacements = [
        (b'#include "model_opt.h"', b'#include "model_opt.h"\n#include "gamma_attention_anchor.h"'),
        (b'const int slot = static_cast<int>(t % WIN);',
         b'const int slot = gamma_attention_slot(t);'),
    ]
    for before, after in replacements:
        if data.count(before) != 1:
            raise ValueError('attention anchor replacement is ambiguous')
        data = data.replace(before, after)
    result = dict(members)
    result[SOURCE] = data
    result[HEADER] = header
    return result
