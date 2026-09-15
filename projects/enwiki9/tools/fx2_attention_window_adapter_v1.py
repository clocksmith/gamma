"""Exact two-constant runtime mutation; trained weight metadata is unchanged."""
import hashlib

CHANGES = {
    'cpp_infer/src/opt/model_opt.cpp': (
        'b49493ece5a3a135baa24eeef00d6aaf56335324d0c6355b7283e46736c9df8e',
        b'constexpr int WIN = 1024, ROPE_LEN = 131072;',
        b'constexpr int WIN = 2048, ROPE_LEN = 131072;'),
    'cpp_infer/src/opt/attn.h': (
        'b8c728e30fb0ef5781e46970ee59e157bdfb53cb557383dc0677fe8c20e40048',
        b'constexpr int ATTN_WIN = 1024;',
        b'constexpr int ATTN_WIN = 2048;'),
}


def mutate(members):
    result = dict(members)
    for name, (digest, before, after) in CHANGES.items():
        data = members[name]
        if hashlib.sha256(data).hexdigest() != digest or data.count(before) != 1:
            raise ValueError('runtime window preimage differs: '+name)
        result[name] = data.replace(before, after)
    return result
