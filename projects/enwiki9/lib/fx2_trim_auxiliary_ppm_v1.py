"""New packaging realization: PPM-only auxiliary assets for the trimmed codec.

Materializes source; does not execute a native codec or claim package savings.
The live native trimming and feedback candidates remain immutable.
"""
import hashlib

ID = 'fx2_trim_auxiliary_ppm_v1'
RUNNER = 'src/runner.cpp'
SELF = 'src/readalike_prepr/self_extract.h'
PREIMAGES = {
    RUNNER: 'e8b9bc757902006bf0d2b30e1461276b172c883cece6d3c9eb3df03c804924bf',
    SELF: 'f91619073e4e9aa1d292383c8f62d858ab6ec96a66b78a4acec8cc49ffe44607',
}

DECODE_PERMISSION = '''  // Fixed auxiliary streams have their own PPM-only probability model.
  // Permit that exact decode request; retain all other option restrictions.
  if (mode == 'd' && options.ppmd_only && !options.transformer_only &&
      !options.bytes_only && options.transformer.empty() &&
      options.save_ppmd_bytes.empty() && options.save_article_boundaries.empty() &&
      options.save_ppmd_probs.empty() && options.load_transformer_probs.empty() &&
      options.save_transformer_probs.empty()) return;
'''

HELPERS = (
    './cmix -d .new_article_order.comp .new_article_order',
    './cmix -d .dict.comp .dict',
    './archive9 -d .dict.comp_decomp .dict',
)


def replace_once(text, old, new):
    if text.count(old) != 1:
        raise ValueError('auxiliary source anchor absent or ambiguous')
    return text.replace(old, new, 1)


def materialize(source, packager):
    result = dict(source)
    for name, expected in PREIMAGES.items():
        if hashlib.sha256(source[name]).hexdigest() != expected:
            raise ValueError('auxiliary source preimage differs: ' + name)
    if 'gamma_pack_auxiliary.py' in source:
        raise ValueError('packager already present')
    text = source[RUNNER].decode()
    text = replace_once(text, '  if (!options.AnySet()) return;',
                        DECODE_PERMISSION + '  if (!options.AnySet()) return;')
    result[RUNNER] = text.encode()
    text = source[SELF].decode()
    for command in HELPERS:
        text = replace_once(text, 'RunSubprocess("' + command + '")',
                            'RunSubprocess("' + command + ' --ppmd-only")')
    result[SELF] = text.encode()
    result['gamma_pack_auxiliary.py'] = packager
    return result
