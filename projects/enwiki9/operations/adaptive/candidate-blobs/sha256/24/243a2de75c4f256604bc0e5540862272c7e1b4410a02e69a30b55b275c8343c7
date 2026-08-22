#!/usr/bin/env python3
"""Apply Gamma's deterministic bit-head DELTA-MIDAS overlay to cmix-obias."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path


EXPECTED_SOURCE_SHA256 = "e0593d64bef9323467d838724f926bb32efdcaef957afd48a14ff318577ff77f"
RELATIVE_SOURCE = Path("src/models/bitlstm32-head.cpp")


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise ValueError(f"{label}: expected one anchor, found {count}")
    return text.replace(old, new, 1)


def apply_overlay(source_root: Path) -> dict[str, str]:
    path = source_root / RELATIVE_SOURCE
    original = path.read_bytes()
    original_sha256 = hashlib.sha256(original).hexdigest()
    if original_sha256 != EXPECTED_SOURCE_SHA256:
        raise ValueError(
            f"upstream source mismatch: expected {EXPECTED_SOURCE_SHA256}, "
            f"got {original_sha256}"
        )
    text = original.decode("utf-8")

    text = replace_once(
        text,
        "constexpr int kSeqReset = 64;\n",
        r'''constexpr int kSeqReset = 64;

// Gamma DELTA-MIDAS compile-time arms. P is an observationally instrumented
// parent; K computes the complete sidecar with zero injection; O changes only
// the terminal logit; R reconstructs the measured gradient through an
// orthogonal Walsh subspace; D uses the tied transpose; S uses the preceding
// segment's tied gradient. The segment is 512 coded bits, not 64 raw bytes.
#ifndef KH_DELTA_MIDAS_ARM
#define KH_DELTA_MIDAS_ARM 0
#endif
#if KH_DELTA_MIDAS_ARM < 0 || KH_DELTA_MIDAS_ARM > 5
#error "KH_DELTA_MIDAS_ARM must be 0(P),1(K),2(O),3(R),4(D),or 5(S)"
#endif
constexpr int kDmSegmentBits = 512;
constexpr int kDmCollectBits = 256;
constexpr int kDmRank = 8;
constexpr int kDmGateCoordinates = 64;
constexpr int kDmQ = 20;
constexpr int kDmOne = 1 << kDmQ;
constexpr int kDmClip = 1 << (kDmQ - 2);  // 0.25 in Q20.

inline int DmWalshSign(int row, int coordinate) {
  unsigned int v = (unsigned int)(row & coordinate);
  v ^= v >> 16;
  v ^= v >> 8;
  v ^= v >> 4;
  v ^= v >> 2;
  v ^= v >> 1;
  return (v & 1u) ? -1 : 1;
}

inline int32_t DmQuantizeQ20(float x) {
  if (!(x == x)) return 0;
  if (x > 8.0f) x = 8.0f;
  if (x < -8.0f) x = -8.0f;
  return (int32_t)(x * (float)kDmOne);  // C++ truncation toward zero.
}

inline int32_t DmClipQ20(int64_t x) {
  if (x > kDmClip) return kDmClip;
  if (x < -kDmClip) return -kDmClip;
  return (int32_t)x;
}
''',
        "constants",
    )

    text = replace_once(
        text,
        "  float wout[kHid];              // out.weight\n"
        "  float bout;                    // out.bias\n",
        r'''  float wout[kHid];              // out.weight
  float bout;                    // out.bias

  // Gamma-owned episodic sidecar. It is never serialized and is derived only
  // from coder probabilities and truths already available to the decoder.
  int64_t dm_gate_accum[kDmGateCoordinates] = {0};
  int64_t dm_logit_accum = 0;
  int32_t dm_active[kDmRank] = {0};
  int32_t dm_previous[kDmRank] = {0};
  int32_t dm_gate_inject[kDmGateCoordinates] = {0};
  int32_t dm_logit_active = 0;
  int32_t dm_logit_previous = 0;
  float dm_gi[kHid] = {0};
  float dm_gg[kHid] = {0};
  float dm_go[kHid] = {0};
  float dm_tanh_c[kHid] = {0};
  unsigned int dm_pending_q = 32768;
  bool dm_pending_override = false;
  uint64_t dm_q_hash = 1469598103934665603ULL;
  uint64_t dm_state_hash = 1469598103934665603ULL;
  uint64_t dm_adapter_hash = 1469598103934665603ULL;
  uint64_t dm_bits = 0;
  int32_t dm_max_abs_gate_inject = 0;
  int32_t dm_max_abs_logit_inject = 0;

  void DmBeginSegment();
  void DmFinalize();
  void DmObserve(int bit);
  void DmHash(uint64_t* hash, uint32_t value);
  void DmPrintReceipt() const;
''',
        "sidecar fields",
    )

    text = replace_once(
        text,
        "};\n\n// Half -> float widening for v2 (f16-stored) blobs.",
        r'''};

void KhBitLstm32Head::Impl::DmHash(uint64_t* hash, uint32_t value) {
  for (int shift = 0; shift < 32; shift += 8) {
    *hash ^= (uint8_t)(value >> shift);
    *hash *= 1099511628211ULL;
  }
}

void KhBitLstm32Head::Impl::DmBeginSegment() {
  for (int c0 = 0; c0 < kDmGateCoordinates; ++c0) {
    dm_gate_accum[c0] = 0;
    dm_gate_inject[c0] = 0;
  }
  dm_logit_accum = 0;
  dm_logit_active = 0;
}

void KhBitLstm32Head::Impl::DmFinalize() {
  int32_t current[kDmRank];
  int32_t selected[kDmRank];
  for (int j = 0; j < kDmRank; ++j) {
    int64_t sum = 0;
    for (int c0 = 0; c0 < kDmGateCoordinates; ++c0) {
      sum += (int64_t)DmWalshSign(j + 1, c0) * dm_gate_accum[c0];
    }
    // B = H/8 and a fixed 256-event mean: divisor 8*256 = 2048.
    current[j] = DmClipQ20(sum / 2048);
#if KH_DELTA_MIDAS_ARM == 5
    selected[j] = dm_previous[j];
#else
    selected[j] = current[j];
#endif
  }
  const int32_t current_logit = DmClipQ20(dm_logit_accum / 256);
#if KH_DELTA_MIDAS_ARM == 5
  const int32_t selected_logit = dm_logit_previous;
#else
  const int32_t selected_logit = current_logit;
#endif

#if KH_DELTA_MIDAS_ARM == 3 || KH_DELTA_MIDAS_ARM == 4 || KH_DELTA_MIDAS_ARM == 5
  for (int c0 = 0; c0 < kDmGateCoordinates; ++c0) {
    int64_t sum = 0;
    for (int j = 0; j < kDmRank; ++j) {
#if KH_DELTA_MIDAS_ARM == 3
      const int row = j + 9;  // Orthogonal Walsh reconstruction control.
#else
      const int row = j + 1;  // Tied transpose for D and lagged S.
#endif
      sum += (int64_t)DmWalshSign(row, c0) * selected[j];
    }
    // eta=1 and B^T=H^T/8.
    dm_gate_inject[c0] = DmClipQ20(-sum / 8);
    const int32_t a = dm_gate_inject[c0] < 0
        ? -dm_gate_inject[c0] : dm_gate_inject[c0];
    if (a > dm_max_abs_gate_inject) dm_max_abs_gate_inject = a;
    DmHash(&dm_adapter_hash, (uint32_t)dm_gate_inject[c0]);
  }
#endif

#if KH_DELTA_MIDAS_ARM == 2 || KH_DELTA_MIDAS_ARM == 3 || KH_DELTA_MIDAS_ARM == 4 || KH_DELTA_MIDAS_ARM == 5
  dm_logit_active = -selected_logit;  // eta_l=1.
  const int32_t a = dm_logit_active < 0 ? -dm_logit_active : dm_logit_active;
  if (a > dm_max_abs_logit_inject) dm_max_abs_logit_inject = a;
  DmHash(&dm_adapter_hash, (uint32_t)dm_logit_active);
#endif
  for (int j = 0; j < kDmRank; ++j) dm_previous[j] = current[j];
  dm_logit_previous = current_logit;
}

void KhBitLstm32Head::Impl::DmObserve(int bit) {
  DmHash(&dm_q_hash, dm_pending_q);
  DmHash(&dm_q_hash, (uint32_t)bit);
  ++dm_bits;
  if ((i & 63ULL) == 63ULL) {
    for (int r = 0; r < kHid; ++r) {
      uint32_t hb, cb;
      std::memcpy(&hb, h + r, sizeof(hb));
      std::memcpy(&cb, c + r, sizeof(cb));
      DmHash(&dm_state_hash, hb);
      DmHash(&dm_state_hash, cb);
    }
  }
#if KH_DELTA_MIDAS_ARM != 0
  const int phase = (int)(i & (kDmSegmentBits - 1));
  if (phase < kDmCollectBits && !dm_pending_override) {
    // Straight-through local terminal-logit gradient using the exact integer
    // probability supplied to the range split. Future recurrent effects are
    // deliberately excluded from this one-step eligibility.
    const float dlogit = (float)dm_pending_q * (1.0f / 65536.0f) - (float)bit;
    dm_logit_accum += DmQuantizeQ20(dlogit);
    for (int r = 0; r < kHid; ++r) {
      const float dh = dlogit * wout[r];
      const float dc = dh * dm_go[r] *
          (1.0f - dm_tanh_c[r] * dm_tanh_c[r]);
      const float dai = dc * dm_gg[r] * dm_gi[r] * (1.0f - dm_gi[r]);
      const float dag = dc * dm_gi[r] * (1.0f - dm_gg[r] * dm_gg[r]);
      dm_gate_accum[r] += DmQuantizeQ20(dai);
      dm_gate_accum[kHid + r] += DmQuantizeQ20(dag);
    }
  }
  if (phase == kDmCollectBits - 1) DmFinalize();
#endif
}

void KhBitLstm32Head::Impl::DmPrintReceipt() const {
  static const char* names[6] = {"P", "K", "O", "R", "D", "S"};
  std::fprintf(stderr,
      "\nKH_DELTA_MIDAS_RECEIPT arm=%s bits=%llu q_hash=%016llx "
      "state_hash=%016llx adapter_hash=%016llx max_gate_q20=%d "
      "max_logit_q20=%d finite=1\n",
      names[KH_DELTA_MIDAS_ARM], (unsigned long long)dm_bits,
      (unsigned long long)dm_q_hash, (unsigned long long)dm_state_hash,
      (unsigned long long)dm_adapter_hash, dm_max_abs_gate_inject,
      dm_max_abs_logit_inject);
}

// Half -> float widening for v2 (f16-stored) blobs.''',
        "sidecar methods",
    )

    text = replace_once(
        text,
        "  for (int r = 0; r < 4 * kHid; ++r) {\n"
        "    pre[r] = DotPadded(wih + r * kHid, h0, kHid) + bih[r] +\n"
        "             DotPadded(whh + r * kHid, h, kHid) + bhh[r];\n"
        "  }\n"
        "  for (int r = 0; r < kHid; r += 8) {\n"
        "    const __m256 gi = Sigmoid8(_mm256_loadu_ps(pre + 0 * kHid + r));",
        r'''  for (int r = 0; r < 4 * kHid; ++r) {
    pre[r] = DotPadded(wih + r * kHid, h0, kHid) + bih[r] +
             DotPadded(whh + r * kHid, h, kHid) + bhh[r];
  }
#if KH_DELTA_MIDAS_ARM == 3 || KH_DELTA_MIDAS_ARM == 4 || KH_DELTA_MIDAS_ARM == 5
  if ((i & (kDmSegmentBits - 1)) >= kDmCollectBits) {
    for (int r = 0; r < kHid; ++r) {
      pre[0 * kHid + r] += (float)dm_gate_inject[r] / (float)kDmOne;
      pre[2 * kHid + r] += (float)dm_gate_inject[kHid + r] / (float)kDmOne;
    }
  }
#endif
  for (int r = 0; r < kHid; r += 8) {
    const __m256 gi = Sigmoid8(_mm256_loadu_ps(pre + 0 * kHid + r));''',
        "avx injection",
    )

    text = replace_once(
        text,
        "    const __m256 cn = _mm256_fmadd_ps(gf, _mm256_loadu_ps(c + r),\n"
        "                                      _mm256_mul_ps(gi, gg));\n"
        "    _mm256_storeu_ps(c + r, cn);\n"
        "    _mm256_storeu_ps(h + r, _mm256_mul_ps(go, Tanh8(cn)));\n",
        r'''    const __m256 cn = _mm256_fmadd_ps(gf, _mm256_loadu_ps(c + r),
                                      _mm256_mul_ps(gi, gg));
    const __m256 tc = Tanh8(cn);
    _mm256_storeu_ps(c + r, cn);
    _mm256_storeu_ps(h + r, _mm256_mul_ps(go, tc));
    _mm256_storeu_ps(dm_gi + r, gi);
    _mm256_storeu_ps(dm_gg + r, gg);
    _mm256_storeu_ps(dm_go + r, go);
    _mm256_storeu_ps(dm_tanh_c + r, tc);
''',
        "avx capture",
    )

    text = replace_once(
        text,
        "  for (int r = 0; r < 4 * kHid; ++r) {\n"
        "    pre[r] = DotPadded(wih + r * kHid, h0, kHid) + bih[r] +\n"
        "             DotPadded(whh + r * kHid, h, kHid) + bhh[r];\n"
        "  }\n"
        "  for (int r = 0; r < kHid; ++r) {\n"
        "    const float gi = Sigmoidf(pre[0 * kHid + r]);",
        r'''  for (int r = 0; r < 4 * kHid; ++r) {
    pre[r] = DotPadded(wih + r * kHid, h0, kHid) + bih[r] +
             DotPadded(whh + r * kHid, h, kHid) + bhh[r];
  }
#if KH_DELTA_MIDAS_ARM == 3 || KH_DELTA_MIDAS_ARM == 4 || KH_DELTA_MIDAS_ARM == 5
  if ((i & (kDmSegmentBits - 1)) >= kDmCollectBits) {
    for (int r = 0; r < kHid; ++r) {
      pre[0 * kHid + r] += (float)dm_gate_inject[r] / (float)kDmOne;
      pre[2 * kHid + r] += (float)dm_gate_inject[kHid + r] / (float)kDmOne;
    }
  }
#endif
  for (int r = 0; r < kHid; ++r) {
    const float gi = Sigmoidf(pre[0 * kHid + r]);''',
        "scalar injection",
    )

    text = replace_once(
        text,
        "    const float cn = gf * c[r] + gi * gg;\n"
        "    c[r] = cn;\n"
        "    h[r] = go * std::tanh(cn);\n",
        r'''    const float cn = gf * c[r] + gi * gg;
    const float tc = std::tanh(cn);
    c[r] = cn;
    h[r] = go * tc;
    dm_gi[r] = gi;
    dm_gg[r] = gg;
    dm_go[r] = go;
    dm_tanh_c[r] = tc;
''',
        "scalar capture",
    )

    text = replace_once(
        text,
        "KhBitLstm32Head::~KhBitLstm32Head() { delete impl_; }\n",
        r'''KhBitLstm32Head::~KhBitLstm32Head() {
  if (impl_ != nullptr) impl_->DmPrintReceipt();
  delete impl_;
}
''',
        "receipt destructor",
    )

    text = replace_once(
        text,
        "  Impl& s = *impl_;\n"
        "  // seq64 TBPTT training reset: fresh recurrent state every 64 coded bits.\n",
        r'''  Impl& s = *impl_;
  if ((s.i & (kDmSegmentBits - 1)) == 0) s.DmBeginSegment();
  // seq64 TBPTT training reset: fresh recurrent state every 64 coded bits.
''',
        "segment begin",
    )

    text = replace_once(
        text,
        "  const float delta = s.RunNet(x, s.prev_bit);\n"
        "  if (override_active) {\n"
        "    // Byte-mixer 0/1 override bits were loss-masked (w=0) during training:\n"
        "    // the head's output there is unconstrained, so keep the coder's p.\n"
        "    return base_p;\n"
        "  }\n"
        "  const float pnew = Sigmoidf(t + delta);\n"
        "  unsigned int q = (unsigned int)(1.0f + 65534.0f * pnew);  // Discretize()\n"
        "  if (q < 1) q = 1;\n"
        "  if (q > 65535) q = 65535;\n"
        "  return q;\n",
        r'''  float delta = s.RunNet(x, s.prev_bit);
#if KH_DELTA_MIDAS_ARM == 2 || KH_DELTA_MIDAS_ARM == 3 || KH_DELTA_MIDAS_ARM == 4 || KH_DELTA_MIDAS_ARM == 5
  if ((s.i & (kDmSegmentBits - 1)) >= kDmCollectBits) {
    delta += (float)s.dm_logit_active / (float)kDmOne;
  }
#endif
  unsigned int q = base_p;
  if (!override_active) {
    const float pnew = Sigmoidf(t + delta);
    q = (unsigned int)(1.0f + 65534.0f * pnew);  // Discretize()
    if (q < 1) q = 1;
    if (q > 65535) q = 65535;
  }
  s.dm_pending_q = q;
  s.dm_pending_override = override_active != 0;
  return q;
''',
        "adjust",
    )

    text = replace_once(
        text,
        "  const unsigned long long i = s.i;\n"
        "  const float y = (float)bit;\n\n"
        "  // res family\n",
        r'''  const unsigned long long i = s.i;
  const float y = (float)bit;
  s.DmObserve(bit);

  // res family
''',
        "observe",
    )

    modified = text.encode("utf-8")
    path.write_bytes(modified)
    return {
        "path": str(path),
        "upstream_sha256": original_sha256,
        "modified_sha256": hashlib.sha256(modified).hexdigest(),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    args = parser.parse_args()
    receipt = apply_overlay(args.source.resolve())
    print(receipt)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
