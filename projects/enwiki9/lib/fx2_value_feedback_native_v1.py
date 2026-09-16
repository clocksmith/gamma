"""One source-bound native realization of the value-feedback prototype.

This materializes source only. It does not select settings or launch a codec.
P remains byte-identical to the delivered trimmed source. K executes feedback
bookkeeping but retains the original quantizer's values. D uses aligned state;
S uses previous-token state shifted one coordinate within each 64-value head.
"""
import hashlib

MODEL = 'cpp_infer/src/opt/model_opt.cpp'
MODEL_SHA = 'b49493ece5a3a135baa24eeef00d6aaf56335324d0c6355b7283e46736c9df8e'
HEADER_SHA = 'bb0f5410aa7d317f9cd0e576b78acdc64ebca0a5f1bfc557f4a1def0bd8ac718'
HEADER = 'cpp_infer/src/opt/gamma_value_feedback_v1.h'

INCLUDE = r'''
#include "gamma_value_feedback_v1.h"
#include <cstdlib>
#ifdef GAMMA_VALUE_FEEDBACK_PROBE
extern "C" void gamma_value_feedback_observe(
    int layer, int coordinate, int32_t input, int32_t previous,
    int32_t value, int32_t residual);
extern "C" void gamma_value_feedback_reset();
#endif
'''

BODY = r'''
      // Read all previous-token residuals before writing any current state.
      // K keeps original vv; D and S change the cached value trajectory.
      int32_t previous_value_residual[D];
      std::memcpy(previous_value_residual, value_residual[vi],
                  sizeof(previous_value_residual));
      for (int h = 0; h < NH; ++h) {
        if (!(L.sv[h] > 0.0f) || !std::isfinite(L.sv[h])) std::abort();
        for (int d = 0; d < DH; ++d) {
          const int coordinate = h * DH + d;
          const int donor = h * DH +
              (GAMMA_VALUE_FEEDBACK_ARM == 3 ? (d + 1) % DH : d);
          const float normalized = vf[coordinate] / L.sv[h];
          int32_t input = 0;
          if (!gamma_value_feedback_v1::normalized_q16(normalized, input))
            std::abort();
          const auto feedback = gamma_value_feedback_v1::step(
              input, previous_value_residual[donor]);
          if (!feedback.valid) std::abort();
          value_residual[vi][coordinate] = feedback.residual;
          if (GAMMA_VALUE_FEEDBACK_ARM != 1)
            vv[coordinate] = static_cast<int8_t>(feedback.value);
#ifdef GAMMA_VALUE_FEEDBACK_PROBE
          gamma_value_feedback_observe(vi, coordinate, input,
              previous_value_residual[donor], feedback.value, feedback.residual);
#endif
        }
      }
'''


def replace_once(text, old, new):
    if text.count(old) != 1:
        raise ValueError('native source anchor missing or ambiguous')
    return text.replace(old, new, 1)


def materialize(sources, arm, header):
    if arm not in ('P', 'K', 'D', 'S'):
        raise ValueError('unknown value-feedback arm')
    if hashlib.sha256(sources[MODEL]).hexdigest() != MODEL_SHA:
        raise ValueError('native model source identity differs')
    if hashlib.sha256(header).hexdigest() != HEADER_SHA:
        raise ValueError('kernel identity differs')
    if HEADER in sources:
        raise ValueError('kernel already present')
    result = dict(sources)
    if arm == 'P':
        return result
    text = sources[MODEL].decode('utf-8')
    define = '#define GAMMA_VALUE_FEEDBACK_ARM ' + str({'K': 1, 'D': 2, 'S': 3}[arm])
    text = replace_once(text, '#include "model_opt.h"',
                        '#include "model_opt.h"\n' + define + INCLUDE)
    text = replace_once(text, '  int64_t rope_off = 0;',
                        '  int64_t rope_off = 0;\n  int32_t value_residual[3][D] = {};')
    text = replace_once(text, '  void begin(int64_t rope_position_offset) {',
                        '  void begin(int64_t rope_position_offset) {\n'
                        '    std::memset(value_residual, 0, sizeof(value_residual));\n'
                        '#ifdef GAMMA_VALUE_FEEDBACK_PROBE\n'
                        '    gamma_value_feedback_reset();\n#endif')
    anchor = '        quant64_i8(vf + h * DH, L.sv[h], vv + h * DH);\n      }'
    text = replace_once(text, anchor, anchor + BODY)
    result[MODEL] = text.encode('utf-8')
    result[HEADER] = header
    return result
