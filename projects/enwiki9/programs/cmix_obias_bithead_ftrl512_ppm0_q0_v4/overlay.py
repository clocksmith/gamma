#!/usr/bin/env python3
"""Apply sealed Delta-MIDAS instrumentation, then realize online FTRL v4."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[2]
PARENT_OVERLAY = (
    ROOT
    / "programs"
    / "cmix_obias_bithead_delta_midas512_q0_v2"
    / "overlay.py"
)
TARGET = Path("src/models/bitlstm32-head.cpp")
PARENT_SHA256 = "a69776b93cde5b0d53d74746fd71098ca2add1db12bef89853461806c5c8c50e"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        while chunk := source.read(1 << 20):
            digest.update(chunk)
    return digest.hexdigest()


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected one source match, found {count}")
    return text.replace(old, new, 1)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    args = parser.parse_args()

    subprocess.run(
        [sys.executable, str(PARENT_OVERLAY), "--source", str(args.source)],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    target = args.source / TARGET
    parent_hash = sha256(target)
    if parent_hash != PARENT_SHA256:
        raise RuntimeError(
            f"parent overlay output mismatch: expected {PARENT_SHA256}, got {parent_hash}"
        )
    text = target.read_text()
    occurrences = text.count("KH_DELTA_MIDAS_ARM")
    if occurrences < 8:
        raise RuntimeError(f"unexpected parent macro population: {occurrences}")
    text = text.replace("KH_DELTA_MIDAS_ARM", "KH_BITHEAD_FTRL_ARM")
    text = text.replace("KH_DELTA_MIDAS_RECEIPT", "KH_BITHEAD_FTRL_RECEIPT")

    text = replace_once(
        text,
        '''// Gamma DELTA-MIDAS compile-time arms. P is an observationally instrumented
// parent; K computes the complete sidecar with zero injection; O changes only
// the terminal logit; R reconstructs the measured gradient through an
// orthogonal Walsh subspace; D uses the tied transpose; S uses the preceding
// segment's tied gradient. The segment is 512 coded bits, not 64 raw bytes.
''',
        '''// Gamma online FTRL compile-time arms. The adapter used for coded bit t is
// derived only from events preceding t in the current 512-bit segment. K runs
// complete D bookkeeping with zero injection; R uses an orthogonal Walsh
// reconstruction; S pairs the previous residual with the current Jacobian.
''',
        "algorithm comment",
    )
    text = replace_once(
        text,
        '''constexpr int kDmSegmentBits = 512;
constexpr int kDmCollectBits = 256;
constexpr int kDmRank = 8;
constexpr int kDmGateCoordinates = 64;
constexpr int kDmQ = 20;
constexpr int kDmOne = 1 << kDmQ;
constexpr int kDmClip = 1 << (kDmQ - 2);  // 0.25 in Q20.
''',
        '''constexpr int kDmSegmentBits = 512;
constexpr int kDmRank = 8;
constexpr int kDmGateCoordinates = 64;
constexpr int kDmQ = 20;
constexpr int kDmOne = 1 << kDmQ;
constexpr int kDmClip = 1 << (kDmQ - 2);  // 0.25 in Q20.
constexpr int kDmJacClip = 8 << kDmQ;
constexpr int kDmLambda = 1 << kDmQ;
''',
        "constants",
    )
    text = replace_once(
        text,
        '''inline int32_t DmClipQ20(int64_t x) {
  if (x > kDmClip) return kDmClip;
  if (x < -kDmClip) return -kDmClip;
  return (int32_t)x;
}
''',
        '''inline int32_t DmClipQ20(int64_t x) {
  if (x > kDmClip) return kDmClip;
  if (x < -kDmClip) return -kDmClip;
  return (int32_t)x;
}

inline int32_t DmClipJacQ20(int64_t x) {
  if (x > kDmJacClip) return kDmJacClip;
  if (x < -kDmJacClip) return -kDmJacClip;
  return (int32_t)x;
}
''',
        "jacobian clip",
    )
    text = replace_once(
        text,
        '''  // Gamma-owned episodic sidecar. It is never serialized and is derived only
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
        '''  // Gamma-owned episodic sidecar. It is never serialized and is derived only
  // from coder probabilities and truths already available to the decoder.
  int64_t dm_gate_grad[kDmRank] = {0};
  int64_t dm_gate_curvature[kDmRank] = {0};
  int64_t dm_logit_grad = 0;
  int64_t dm_logit_curvature = 0;
  int32_t dm_gate_inject[kDmGateCoordinates] = {0};
  int32_t dm_logit_active = 0;
  int32_t dm_previous_residual_num = 0;
  float dm_gi[kHid] = {0};
  float dm_gg[kHid] = {0};
  float dm_go[kHid] = {0};
  float dm_tanh_c[kHid] = {0};
  unsigned int dm_pending_q = 32768;
  bool dm_pending_override = false;
  bool dm_finite = true;
  uint64_t dm_q_hash = 1469598103934665603ULL;
  uint64_t dm_state_hash = 1469598103934665603ULL;
  uint64_t dm_adapter_hash = 1469598103934665603ULL;
  uint64_t dm_bits = 0;
  int32_t dm_max_abs_gate_inject = 0;
  int32_t dm_max_abs_logit_inject = 0;

  void DmBeginSegment();
  void DmRefresh();
  void DmObserve(int bit);
  void DmHash(uint64_t* hash, uint32_t value);
  void DmPrintReceipt() const;
''',
        "sidecar state",
    )
    old_methods = '''void KhBitLstm32Head::Impl::DmBeginSegment() {
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
#if KH_BITHEAD_FTRL_ARM == 5
    selected[j] = dm_previous[j];
#else
    selected[j] = current[j];
#endif
  }
  const int32_t current_logit = DmClipQ20(dm_logit_accum / 256);
#if KH_BITHEAD_FTRL_ARM == 5
  const int32_t selected_logit = dm_logit_previous;
#else
  const int32_t selected_logit = current_logit;
#endif

#if KH_BITHEAD_FTRL_ARM == 3 || KH_BITHEAD_FTRL_ARM == 4 || KH_BITHEAD_FTRL_ARM == 5
  for (int c0 = 0; c0 < kDmGateCoordinates; ++c0) {
    int64_t sum = 0;
    for (int j = 0; j < kDmRank; ++j) {
#if KH_BITHEAD_FTRL_ARM == 3
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

#if KH_BITHEAD_FTRL_ARM == 2 || KH_BITHEAD_FTRL_ARM == 3 || KH_BITHEAD_FTRL_ARM == 4 || KH_BITHEAD_FTRL_ARM == 5
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
#if KH_BITHEAD_FTRL_ARM != 0
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
'''
    new_methods = '''void KhBitLstm32Head::Impl::DmBeginSegment() {
  for (int j = 0; j < kDmRank; ++j) {
    dm_gate_grad[j] = 0;
    dm_gate_curvature[j] = 0;
  }
  for (int c0 = 0; c0 < kDmGateCoordinates; ++c0) dm_gate_inject[c0] = 0;
  dm_logit_grad = 0;
  dm_logit_curvature = 0;
  dm_logit_active = 0;
  dm_previous_residual_num = 0;
}

void KhBitLstm32Head::Impl::DmRefresh() {
  int32_t theta[kDmRank];
  for (int j = 0; j < kDmRank; ++j) {
    const int64_t denominator = dm_gate_curvature[j] + kDmLambda;
    theta[j] = DmClipQ20((-dm_gate_grad[j] * kDmOne) / denominator);
  }
#if KH_BITHEAD_FTRL_ARM == 3 || KH_BITHEAD_FTRL_ARM == 4 || KH_BITHEAD_FTRL_ARM == 5
  for (int c0 = 0; c0 < kDmGateCoordinates; ++c0) {
    int64_t sum = 0;
    for (int j = 0; j < kDmRank; ++j) {
#if KH_BITHEAD_FTRL_ARM == 3
      const int row = j + 9;
#else
      const int row = j + 1;
#endif
      sum += (int64_t)DmWalshSign(row, c0) * theta[j];
    }
    dm_gate_inject[c0] = DmClipQ20(sum / 8);
    const int32_t a = dm_gate_inject[c0] < 0
        ? -dm_gate_inject[c0] : dm_gate_inject[c0];
    if (a > dm_max_abs_gate_inject) dm_max_abs_gate_inject = a;
    DmHash(&dm_adapter_hash, (uint32_t)dm_gate_inject[c0]);
  }
#endif
#if KH_BITHEAD_FTRL_ARM == 2 || KH_BITHEAD_FTRL_ARM == 3 || KH_BITHEAD_FTRL_ARM == 4 || KH_BITHEAD_FTRL_ARM == 5
  const int64_t denominator = dm_logit_curvature + kDmLambda;
  dm_logit_active = DmClipQ20((-dm_logit_grad * kDmOne) / denominator);
  const int32_t a = dm_logit_active < 0 ? -dm_logit_active : dm_logit_active;
  if (a > dm_max_abs_logit_inject) dm_max_abs_logit_inject = a;
  DmHash(&dm_adapter_hash, (uint32_t)dm_logit_active);
#endif
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
#if KH_BITHEAD_FTRL_ARM != 0
  const int32_t residual_num = (int32_t)dm_pending_q - (bit ? 65536 : 0);
  if (!dm_pending_override) {
#if KH_BITHEAD_FTRL_ARM == 5
    const int32_t aligned_residual = dm_previous_residual_num;
#else
    const int32_t aligned_residual = residual_num;
#endif
    const int64_t pvar_q20 =
        ((int64_t)dm_pending_q * (65536 - dm_pending_q)) / 4096;
    dm_logit_grad += ((int64_t)aligned_residual * kDmOne) / 65536;
    dm_logit_curvature += pvar_q20;

    int32_t jacobian[kDmGateCoordinates];
    for (int r = 0; r < kHid; ++r) {
      const float dc = wout[r] * dm_go[r] *
          (1.0f - dm_tanh_c[r] * dm_tanh_c[r]);
      const float ji = dc * dm_gg[r] * dm_gi[r] * (1.0f - dm_gi[r]);
      const float jg = dc * dm_gi[r] * (1.0f - dm_gg[r] * dm_gg[r]);
      if (!std::isfinite(ji) || !std::isfinite(jg)) dm_finite = false;
      jacobian[r] = DmQuantizeQ20(ji);
      jacobian[kHid + r] = DmQuantizeQ20(jg);
    }
    for (int j = 0; j < kDmRank; ++j) {
      int64_t projected_sum = 0;
      for (int c0 = 0; c0 < kDmGateCoordinates; ++c0) {
        projected_sum +=
            (int64_t)DmWalshSign(j + 1, c0) * jacobian[c0];
      }
      const int32_t projected = DmClipJacQ20(projected_sum / 8);
      dm_gate_grad[j] +=
          ((int64_t)aligned_residual * projected) / 65536;
      const int64_t projected_square =
          ((int64_t)projected * projected) / kDmOne;
      dm_gate_curvature[j] +=
          (pvar_q20 * projected_square) / kDmOne;
    }
    dm_previous_residual_num = residual_num;
  } else {
    dm_previous_residual_num = 0;
  }
  DmRefresh();
#endif
}
'''
    text = replace_once(text, old_methods, new_methods, "online methods")

    old_injection = '''#if KH_BITHEAD_FTRL_ARM == 3 || KH_BITHEAD_FTRL_ARM == 4 || KH_BITHEAD_FTRL_ARM == 5
  if ((i & (kDmSegmentBits - 1)) >= kDmCollectBits) {
    for (int r = 0; r < kHid; ++r) {
      pre[0 * kHid + r] += (float)dm_gate_inject[r] / (float)kDmOne;
      pre[2 * kHid + r] += (float)dm_gate_inject[kHid + r] / (float)kDmOne;
    }
  }
#endif
'''
    new_injection = '''#if KH_BITHEAD_FTRL_ARM == 3 || KH_BITHEAD_FTRL_ARM == 4 || KH_BITHEAD_FTRL_ARM == 5
  for (int r = 0; r < kHid; ++r) {
    pre[0 * kHid + r] += (float)dm_gate_inject[r] / (float)kDmOne;
    pre[2 * kHid + r] += (float)dm_gate_inject[kHid + r] / (float)kDmOne;
  }
#endif
'''
    if text.count(old_injection) != 2:
        raise RuntimeError("gate injection: expected AVX and scalar source matches")
    text = text.replace(old_injection, new_injection)
    text = replace_once(
        text,
        '''#if KH_BITHEAD_FTRL_ARM == 2 || KH_BITHEAD_FTRL_ARM == 3 || KH_BITHEAD_FTRL_ARM == 4 || KH_BITHEAD_FTRL_ARM == 5
  if ((s.i & (kDmSegmentBits - 1)) >= kDmCollectBits) {
    delta += (float)s.dm_logit_active / (float)kDmOne;
  }
#endif
''',
        '''#if KH_BITHEAD_FTRL_ARM == 2 || KH_BITHEAD_FTRL_ARM == 3 || KH_BITHEAD_FTRL_ARM == 4 || KH_BITHEAD_FTRL_ARM == 5
  delta += (float)s.dm_logit_active / (float)kDmOne;
#endif
''',
        "logit injection",
    )
    text = replace_once(
        text,
        '''      "state_hash=%016llx adapter_hash=%016llx max_gate_q20=%d "
      "max_logit_q20=%d finite=1\\n",
''',
        '''      "state_hash=%016llx adapter_hash=%016llx max_gate_q20=%d "
      "max_logit_q20=%d finite=%d\\n",
''',
        "receipt format",
    )
    text = replace_once(
        text,
        '''      (unsigned long long)dm_adapter_hash, dm_max_abs_gate_inject,
      dm_max_abs_logit_inject);
''',
        '''      (unsigned long long)dm_adapter_hash, dm_max_abs_gate_inject,
      dm_max_abs_logit_inject, dm_finite ? 1 : 0);
''',
        "receipt values",
    )

    target.write_text(text)
    print(
        {
            "path": str(target),
            "parent_sha256": parent_hash,
            "modified_sha256": sha256(target),
        }
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
