// pipe_probe: Zen 2 FP/SIMD pipe-assignment probes for the attention-kernel
// design decisions MACHINE.md does not cover: does vpmaddwd share a pipe with
// FMA? where do vcvtdq2ps / vpmovsxbd / vsubps issue? All loops are pure
// register ALU (no memory), independent chains, asm bodies; results are
// instructions/cycle at steady state.
#include "../../bench/bench_common.h"

// Each test: asm loop, BODY repeated per iteration; returns ticks for ITERS
// iterations. FMA accumulators ymm2-11 (10 chains, latency 5, tput 2 -> ok);
// pure-dest ops write ymm0/ymm1; sources ymm12-15 are constants.

#define PRE                                                        \
  "vpcmpeqd %%ymm12,%%ymm12,%%ymm12\n\t"                           \
  "vpsrld $25,%%ymm12,%%ymm12\n\t" /* small positive ints */       \
  "vmovdqa %%ymm12,%%ymm13\n\t"                                    \
  "vcvtdq2ps %%ymm12,%%ymm14\n\t"                                  \
  "vmovaps %%ymm14,%%ymm15\n\t"                                    \
  "vxorps %%xmm2,%%xmm2,%%xmm2\n\t" "vxorps %%xmm3,%%xmm3,%%xmm3\n\t" \
  "vxorps %%xmm4,%%xmm4,%%xmm4\n\t" "vxorps %%xmm5,%%xmm5,%%xmm5\n\t" \
  "vxorps %%xmm6,%%xmm6,%%xmm6\n\t" "vxorps %%xmm7,%%xmm7,%%xmm7\n\t" \
  "vxorps %%xmm8,%%xmm8,%%xmm8\n\t" "vxorps %%xmm9,%%xmm9,%%xmm9\n\t" \
  "vxorps %%xmm10,%%xmm10,%%xmm10\n\t" "vxorps %%xmm11,%%xmm11,%%xmm11\n\t"

#define CLOBBER                                                            \
  "xmm0", "xmm1", "xmm2", "xmm3", "xmm4", "xmm5", "xmm6", "xmm7", "xmm8", \
      "xmm9", "xmm10", "xmm11", "xmm12", "xmm13", "xmm14", "xmm15", "cc",  \
      "memory"

#define MADD(d) "vpmaddwd %%ymm13,%%ymm12,%%ymm" #d "\n\t"
#define FMA(a) "vfmadd231ps %%ymm14,%%ymm15,%%ymm" #a "\n\t"
#define CVT(d) "vcvtdq2ps %%ymm12,%%ymm" #d "\n\t"
#define SX(d) "vpmovsxbd %%xmm12,%%ymm" #d "\n\t"
#define SXW(d) "vpmovsxbw %%xmm12,%%ymm" #d "\n\t"
#define SUB(d) "vsubps %%ymm14,%%ymm15,%%ymm" #d "\n\t"
#define POR(d) "vpor %%ymm13,%%ymm12,%%ymm" #d "\n\t"

#define DEF_TEST(name, ninstr, BODY)                             \
  __attribute__((noinline)) static uint64_t name(uint64_t it) {  \
    uint64_t n = it;                                             \
    uint64_t t0 = rdtsc_ser();                                   \
    asm volatile(PRE "1:\n\t" BODY "dec %0\n\tjnz 1b\n\t"        \
                 : "+r"(n)::CLOBBER);                            \
    return rdtsc_ser() - t0;                                     \
  }                                                              \
  static const int name##_n = ninstr;

// --- pure throughputs
DEF_TEST(t_madd, 10,
         MADD(0) MADD(1) MADD(0) MADD(1) MADD(0) MADD(1) MADD(0) MADD(1)
         MADD(0) MADD(1))
DEF_TEST(t_fma, 10,
         FMA(2) FMA(3) FMA(4) FMA(5) FMA(6) FMA(7) FMA(8) FMA(9) FMA(10)
         FMA(11))
DEF_TEST(t_cvt, 10,
         CVT(0) CVT(1) CVT(0) CVT(1) CVT(0) CVT(1) CVT(0) CVT(1) CVT(0) CVT(1))
DEF_TEST(t_sx, 10,
         SX(0) SX(1) SX(0) SX(1) SX(0) SX(1) SX(0) SX(1) SX(0) SX(1))
DEF_TEST(t_sub, 10,
         SUB(0) SUB(1) SUB(0) SUB(1) SUB(0) SUB(1) SUB(0) SUB(1) SUB(0) SUB(1))

// --- decisive mixes
// 1 madd : 1 fma (5 groups; 5 fma chains, reuse distance ok at IPC 2)
DEF_TEST(m_1m1f, 10,
         MADD(0) FMA(2) MADD(1) FMA(3) MADD(0) FMA(4) MADD(1) FMA(5) MADD(0)
         FMA(6))
// 1 madd : 2 fma (5 groups, 10 fma chains): 3.0 IPC iff madd pipe is
// disjoint from both FMA pipes; 2.0 IPC if it shares one.
DEF_TEST(m_1m2f, 15,
         MADD(0) FMA(2) FMA(3) MADD(1) FMA(4) FMA(5) MADD(0) FMA(6) FMA(7)
         MADD(1) FMA(8) FMA(9) MADD(0) FMA(10) FMA(11))
// 1 cvt : 2 fma
DEF_TEST(m_1c2f, 15,
         CVT(0) FMA(2) FMA(3) CVT(1) FMA(4) FMA(5) CVT(0) FMA(6) FMA(7)
         CVT(1) FMA(8) FMA(9) CVT(0) FMA(10) FMA(11))
// 2 cvt : 2 fma
DEF_TEST(m_2c2f, 20,
         CVT(0) CVT(1) FMA(2) FMA(3) CVT(0) CVT(1) FMA(4) FMA(5) CVT(0) CVT(1)
         FMA(6) FMA(7) CVT(0) CVT(1) FMA(8) FMA(9) CVT(0) CVT(1) FMA(10)
         FMA(11))
// 1 madd : 1 cvt (QK score conversion pressure)
DEF_TEST(m_1m1c, 10,
         MADD(0) CVT(1) MADD(0) CVT(1) MADD(0) CVT(1) MADD(0) CVT(1) MADD(0)
         CVT(1))
// PV inner mix: 1 pmovsxbd : 1 cvt : 1 fma (5 groups)
DEF_TEST(m_sxcf, 15,
         SX(0) CVT(1) FMA(2) SX(0) CVT(1) FMA(3) SX(0) CVT(1) FMA(4) SX(0)
         CVT(1) FMA(5) SX(0) CVT(1) FMA(6))
// bias-trick PV mix: 1 pmovsx : 1 por : 1 sub : 1 fma (4 groups... 3 groups x4)
DEF_TEST(m_sxpsf, 12,
         SX(0) POR(1) SUB(0) FMA(2) SX(1) POR(0) SUB(1) FMA(3) SX(0) POR(1)
         SUB(0) FMA(4))
// 2 sub : 2 fma  (are the FADD pipes disjoint from FMA?)
DEF_TEST(m_2s2f, 20,
         SUB(0) SUB(1) FMA(2) FMA(3) SUB(0) SUB(1) FMA(4) FMA(5) SUB(0) SUB(1)
         FMA(6) FMA(7) SUB(0) SUB(1) FMA(8) FMA(9) SUB(0) SUB(1) FMA(10)
         FMA(11))
// 1 madd : 1 pmovsxbw (QK unpack mix; MACHINE says shufb+madd = 2 IPC)
DEF_TEST(m_1m1x, 10,
         MADD(0) SXW(1) MADD(0) SXW(1) MADD(0) SXW(1) MADD(0) SXW(1) MADD(0)
         SXW(1))
// full QK-ish: 1 madd : 1 pmovsxbw : 1 paddd-substitute (por) : (bcast skipped)
DEF_TEST(m_qk, 15,
         MADD(0) SXW(1) POR(0) MADD(1) SXW(0) POR(1) MADD(0) SXW(1) POR(0)
         MADD(1) SXW(0) POR(1) MADD(0) SXW(1) POR(0))
// exp-ish + PV fused pressure: 1 madd : 2 fma : 1 cvt : 1 sx (5 ops x 3)
DEF_TEST(m_fuse, 15,
         MADD(0) FMA(2) FMA(3) CVT(1) SX(0) MADD(1) FMA(4) FMA(5) CVT(0) SX(1)
         MADD(0) FMA(6) FMA(7) CVT(1) SX(0))

struct T {
  const char* name;
  uint64_t (*fn)(uint64_t);
  int ninstr;
};

int main() {
  if (!getenv("BENCH_CPU")) setenv("BENCH_CPU", "104", 1);
  pin_from_env();
  Calib c = calibrate();
  print_calib("pipe_probe", c);

  const T tests[] = {
      {"madd_only        ", t_madd, t_madd_n},
      {"fma_only         ", t_fma, t_fma_n},
      {"cvtdq2ps_only    ", t_cvt, t_cvt_n},
      {"pmovsxbd_only    ", t_sx, t_sx_n},
      {"subps_only       ", t_sub, t_sub_n},
      {"1madd:1fma       ", m_1m1f, m_1m1f_n},
      {"1madd:2fma       ", m_1m2f, m_1m2f_n},
      {"1cvt:2fma        ", m_1c2f, m_1c2f_n},
      {"2cvt:2fma        ", m_2c2f, m_2c2f_n},
      {"1madd:1cvt       ", m_1m1c, m_1m1c_n},
      {"1sx:1cvt:1fma(PV)", m_sxcf, m_sxcf_n},
      {"sx:por:sub:fma   ", m_sxpsf, m_sxpsf_n},
      {"2sub:2fma        ", m_2s2f, m_2s2f_n},
      {"1madd:1pmovsxbw  ", m_1m1x, m_1m1x_n},
      {"madd:sxw:por(QK) ", m_qk, m_qk_n},
      {"fuse m:2f:c:sx   ", m_fuse, m_fuse_n},
  };
  const uint64_t iters = 20 * 1000 * 1000;
  for (const T& t : tests) {
    Stats s = repeat_stat([&] {
      double cyc = ticks_to_cycles((double)t.fn(iters));
      return (double)t.ninstr * (double)iters / cyc;  // IPC
    });
    printf("RESULT %s  %6.3f instr/cyc (best %.3f worst %.3f)\n", t.name,
           s.med, s.mx, s.mn);
    fflush(stdout);
  }
  return 0;
}
