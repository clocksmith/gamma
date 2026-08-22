#include <errno.h>
#include <fenv.h>
#include <float.h>
#include <math.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#if defined(__SSE__)
#include <xmmintrin.h>
#endif

#pragma STDC FENV_ACCESS ON

_Static_assert(sizeof(float) == 4, "reference requires 32-bit float");
_Static_assert(FLT_RADIX == 2, "reference requires radix-2 float");
_Static_assert(FLT_MANT_DIG == 24, "reference requires binary32 precision");

enum {
  kStates = 64,
  kStreams = 32,
  kHeads = 8,
  kKeys = 320,
  kRows = kStates * kStreams * kHeads,
  kElements = kRows * kKeys,
};

typedef enum {
  kNormal = 0,
  kReverseKeys = 1,
  kNegateAdjoint = 2,
} Mode;

static float f32_from_bf16(uint16_t value) {
  const uint32_t bits = ((uint32_t)value) << 16;
  float result;
  memcpy(&result, &bits, sizeof(result));
  return result;
}

static uint16_t bf16_from_f32(float value) {
  uint32_t bits;
  memcpy(&bits, &value, sizeof(bits));
  const uint32_t exponent = bits & 0x7f800000u;
  const uint32_t mantissa = bits & 0x007fffffu;
  if (exponent == 0x7f800000u && mantissa != 0) {
    return (uint16_t)((bits >> 16) | 0x0040u);
  }
  const uint32_t tie = (bits >> 16) & 1u;
  bits += 0x00007fffu + tie;
  return (uint16_t)(bits >> 16);
}

static int read_exact(const char *path, uint16_t *values) {
  FILE *stream = fopen(path, "rb");
  if (stream == NULL) {
    fprintf(stderr, "open input failed: %s: %s\n", path, strerror(errno));
    return 0;
  }
  const size_t count = fread(values, sizeof(uint16_t), kElements, stream);
  const int extra = fgetc(stream);
  const int close_status = fclose(stream);
  if (count != kElements || extra != EOF || close_status != 0) {
    fprintf(stderr, "input size/read differs: %s\n", path);
    return 0;
  }
  return 1;
}

static int write_exact(const char *path, const uint16_t *values) {
  FILE *stream = fopen(path, "wb");
  if (stream == NULL) {
    fprintf(stderr, "open output failed: %s: %s\n", path, strerror(errno));
    return 0;
  }
  const size_t count = fwrite(values, sizeof(uint16_t), kElements, stream);
  const int close_status = fclose(stream);
  if (count != kElements || close_status != 0) {
    fprintf(stderr, "output write differs: %s\n", path);
    return 0;
  }
  return 1;
}

static int parse_mode(const char *text, Mode *mode) {
  if (strcmp(text, "normal") == 0) {
    *mode = kNormal;
  } else if (strcmp(text, "reverse-keys") == 0) {
    *mode = kReverseKeys;
  } else if (strcmp(text, "negate-adjoint") == 0) {
    *mode = kNegateAdjoint;
  } else {
    return 0;
  }
  return 1;
}

int main(int argc, char **argv) {
  if (argc != 5) {
    fprintf(stderr,
            "usage: %s PROBABILITY.bf16 PROBABILITY_ADJOINT.bf16 "
            "OUTPUT.bf16 MODE\n",
            argv[0]);
    return 2;
  }
  Mode mode;
  if (!parse_mode(argv[4], &mode)) {
    fprintf(stderr, "unknown mode: %s\n", argv[4]);
    return 2;
  }
  const uint16_t endian_probe = 1;
  if (*(const uint8_t *)&endian_probe != 1) {
    fprintf(stderr, "reference requires a little-endian host\n");
    return 3;
  }
  if (fesetround(FE_TONEAREST) != 0) {
    fprintf(stderr, "cannot set FE_TONEAREST\n");
    return 3;
  }
#if defined(__SSE__)
  unsigned int csr = _mm_getcsr();
  csr &= ~(1u << 15); /* FTZ off. */
  csr &= ~(1u << 6);  /* DAZ off. */
  _mm_setcsr(csr);
#endif

  uint16_t *probability =
      (uint16_t *)malloc((size_t)kElements * sizeof(uint16_t));
  uint16_t *adjoint =
      (uint16_t *)malloc((size_t)kElements * sizeof(uint16_t));
  uint16_t *output =
      (uint16_t *)malloc((size_t)kElements * sizeof(uint16_t));
  if (probability == NULL || adjoint == NULL || output == NULL) {
    fprintf(stderr, "allocation failed\n");
    free(probability);
    free(adjoint);
    free(output);
    return 3;
  }
  if (!read_exact(argv[1], probability) || !read_exact(argv[2], adjoint)) {
    free(probability);
    free(adjoint);
    free(output);
    return 3;
  }

  for (size_t row = 0; row < (size_t)kRows; ++row) {
    const size_t base = row * (size_t)kKeys;
    volatile float dot = 0.0f;
    for (size_t key = 0; key < (size_t)kKeys; ++key) {
      const size_t adjoint_key =
          mode == kReverseKeys ? (size_t)kKeys - 1u - key : key;
      const float p = f32_from_bf16(probability[base + key]);
      float dp = f32_from_bf16(adjoint[base + adjoint_key]);
      if (mode == kNegateAdjoint) dp = -dp;
      if (!isfinite(p) || !isfinite(dp)) {
        fprintf(stderr, "non-finite input at row=%zu key=%zu\n", row, key);
        free(probability);
        free(adjoint);
        free(output);
        return 4;
      }
      volatile float product = p * dp;
      dot = dot + product;
    }
    if (!isfinite(dot)) {
      fprintf(stderr, "non-finite reduction at row=%zu\n", row);
      free(probability);
      free(adjoint);
      free(output);
      return 4;
    }
    for (size_t key = 0; key < (size_t)kKeys; ++key) {
      const size_t adjoint_key =
          mode == kReverseKeys ? (size_t)kKeys - 1u - key : key;
      const float p = f32_from_bf16(probability[base + key]);
      float dp = f32_from_bf16(adjoint[base + adjoint_key]);
      if (mode == kNegateAdjoint) dp = -dp;
      volatile float centered = dp - dot;
      volatile float ds = p * centered;
      if (!isfinite(ds)) {
        fprintf(stderr, "non-finite output at row=%zu key=%zu\n", row, key);
        free(probability);
        free(adjoint);
        free(output);
        return 4;
      }
      output[base + key] = bf16_from_f32(ds);
    }
  }

  const int ok = write_exact(argv[3], output);
  free(probability);
  free(adjoint);
  free(output);
  return ok ? 0 : 3;
}
