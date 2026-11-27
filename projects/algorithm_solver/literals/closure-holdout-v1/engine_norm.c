// Exact greedy normalized open gain, built on the frozen fixed-source-v3 engine.
//
// At dictionary V (containing all single bytes of the training corpus), candidate w not in V has
// current optimal V-parse length s_V(w) = d_V(p, p + |w|) >= 2 and exact corpus token savings
// gain(w | V) = Tok(T; V) - Tok(T; V + {w}). Normalized open gain scores w by:
//
//   score_norm(w | V) = gain(w | V) / ( s_V(w) - 1 ).
//
// Static upper bound (never rises as V grows):
// In any optimal (V + {w})-parse, the chosen occurrences of w are pairwise non-overlapping, so at
// most `used(w) = ub(w) / (|w| - 1)` occurrences are used across the corpus. Without boundary cuts
// (cut_before == NULL), every occurrence of w has the same span cost s_V(w) >= 2; replacing each
// chosen occurrence of w by an optimal V-parse of that span yields a valid V-parse costing at most
// used(w) * (s_V(w) - 1) additional tokens. Therefore:
//
//   gain(w | V) <= used(w) * ( s_V(w) - 1 )   ==>   score_norm(w | V) <= used(w).
//
// Because `used(w)` depends only on the text and never increases as V grows, sorting candidates
// once by decreasing `(used(w), -cand_id)` and scanning until `used(w) * best_sm1 < best_gain`
// (with exact 64-bit integer cross-multiplication for rational comparisons and ties broken by lower
// candidate id, matching engine_exact.c) is 100% exact and free of floating-point rounding.
//
//   engine_norm POLICY L KMAX LIMIT_SECONDS LIST OUT
#define ENGINE_NO_MAIN
#include "../fixed-source-v3/engine.c"

static unsigned char *in_dict;
static int *fwd, *bwd;
static long evaluations;

static int span_cost(int p, int l) {
  int b[72];
  b[0] = 0;
  for (int i = 1; i <= l; i++) b[i] = INF;
  for (int i = 0; i < l; i++) {
    if (b[i] >= INF) continue;
    u64 m = mask[p + i];
    while (m) {
      int k = __builtin_ctzll(m);
      m &= m - 1;
      int j = i + k + 1;
      if (j <= l && b[i] + 1 < b[j]) b[j] = b[i] + 1;
    }
  }
  return b[l];
}

static void doc_distances(int d) {
  int s = dstart[d], n = dlen[d], base = s + d;
  for (int i = 0; i <= n; i++) fwd[base + i] = INF;
  fwd[base] = 0;
  for (int i = 0; i < n; i++) {
    int here = fwd[base + i];
    if (here >= INF) continue;
    u64 m = mask[s + i];
    while (m) {
      int k = __builtin_ctzll(m);
      m &= m - 1;
      int j = i + k + 1;
      if (j <= n && here + 1 < fwd[base + j]) fwd[base + j] = here + 1;
    }
  }
  bwd[base + n] = 0;
  for (int i = n - 1; i >= 0; i--) {
    int b = INF;
    u64 m = mask[s + i];
    while (m) {
      int k = __builtin_ctzll(m);
      m &= m - 1;
      int j = i + k + 1;
      if (j <= n && 1 + bwd[base + j] < b) b = 1 + bwd[base + j];
    }
    bwd[base + i] = b;
  }
}

static int gain_fast(const Cand *c) {
  u64 bit = 1ULL << (c->len - 1);
  int gain = 0;
  for (int i = 0; i < c->nocc;) {
    int d = docof[occ[c->off + i]], j = i;
    while (j < c->nocc && docof[occ[c->off + j]] == d) j++;
    if (j - i == 1) {
      int p = occ[c->off + i], base = dstart[d] + d, off = p - dstart[d];
      int alt = fwd[base + off] + 1 + bwd[base + off + c->len];
      if (alt < cost[d]) gain += cost[d] - alt;
    } else {
      for (int k = i; k < j; k++) mask[occ[c->off + k]] |= bit;
      gain += cost[d] - doc_cost(d);
      for (int k = i; k < j; k++) mask[occ[c->off + k]] &= ~bit;
    }
    i = j;
  }
  return gain;
}

static void accept_fast(const Cand *c) {
  accept(c);
  int last = -1;
  for (int i = 0; i < c->nocc; i++) {
    int d = docof[occ[c->off + i]];
    if (d != last) {
      doc_distances(d);
      last = d;
    }
  }
}

typedef struct {
  long used;
  int c;
} StaticCand;

static int cmp_static_cand(const void *a, const void *b) {
  const StaticCand *x = (const StaticCand *)a;
  const StaticCand *y = (const StaticCand *)b;
  if (x->used != y->used) return (x->used < y->used) ? 1 : -1;
  return (x->c > y->c) - (x->c < y->c);
}

static int run_exact_norm(FILE *out, int kmax, double limit) {
  int k = 0;
  long bytes = 0;
  add_alphabet(out, &k, &bytes);
  double start = now();
  fwd = xmalloc((total + ndocs) * sizeof(int));
  bwd = xmalloc((total + ndocs) * sizeof(int));
  for (int d = 0; d < ndocs; d++) doc_distances(d);
  in_dict = calloc(ncand, 1);

  StaticCand *order = xmalloc((size_t)ncand * sizeof(StaticCand));
  for (int c = 0; c < ncand; c++) {
    order[c].used = cands[c].ub / (cands[c].len - 1);
    order[c].c = c;
  }
  qsort(order, (size_t)ncand, sizeof(StaticCand), cmp_static_cand);

  int step = 0;
  while (k < kmax) {
    if ((step & 15) == 0 && now() - start > limit) return 1;
    int best_c = -1;
    long long best_g = 0, best_sm1 = 1;
    for (int i = 0; i < ncand; i++) {
      int c = order[i].c;
      if (in_dict[c]) continue;
      long long u = order[i].used;
      if (best_c >= 0) {
        // Since `order` is sorted by `used` descending, if `u * best_sm1 < best_g`, no later
        // candidate can beat or tie `best_g / best_sm1`.
        long long lhs = u * best_sm1;
        if (lhs < best_g) break;
        if (lhs == best_g && c > best_c) continue;
      }
      int g = gain_fast(&cands[c]);
      evaluations++;
      if (g <= 0) continue;
      int sm1 = span_cost(occ[cands[c].off], cands[c].len) - 1;
      if (sm1 < 1) sm1 = 1;
      long long lhs = (long long)g * best_sm1;
      long long rhs = best_g * (long long)sm1;
      if (best_c < 0 || lhs > rhs || (lhs == rhs && c < best_c)) {
        best_c = c;
        best_g = g;
        best_sm1 = sm1;
      }
    }
    if (best_c < 0) break;
    const Cand *picked = &cands[best_c];
    accept_fast(picked);
    in_dict[best_c] = 1;
    k++;
    bytes += 1 + picked->len;
    write_entry(out, k, bytes, emissions, ndocs, text + occ[picked->off], picked->len);
    fflush(out);
    step++;
  }
  free(order);
  return 0;
}

int main(int argc, char **argv) {
  if (argc != 7) {
    fprintf(stderr, "usage: engine_norm POLICY L KMAX LIMIT_SECONDS LIST OUT\n");
    return 2;
  }
  const char *receipt = getenv("FSV3_RECEIPT");
  if (!receipt || !strstr(receipt, "manifest=") || !strstr(receipt, "pool=") ||
      !strstr(receipt, "cuts=") || !strstr(receipt, "impl=") || !strstr(receipt, "run=")) {
    fprintf(stderr, "FSV3_RECEIPT must bind manifest, pool, cuts, impl and run\n");
    return 2;
  }
  set_policy(argv[1]);
  int L = atoi(argv[2]), kmax = atoi(argv[3]);
  double limit = atof(argv[4]);
  if (L < 1 || L > 64) {
    fprintf(stderr, "L must be 1..64\n");
    return 2;
  }
  load(argv[5]);
  load_side_files();
  if (cut_before) {
    fprintf(stderr, "engine_norm requires cuts=none (FSV3_CUTS unset)\n");
    return 2;
  }
  double t0 = now();
  enumerate(L);
  double enumerated = now() - t0;
  FILE *out = fopen(argv[6], "w");
  if (!out) {
    perror(argv[6]);
    return 2;
  }
  fprintf(out, "H policy=%s mode=exact-norm L=%d K=%d limit=%s %s\n", argv[1], L, kmax, argv[4], receipt);
  int stopped = run_exact_norm(out, kmax, limit);
  struct rusage use;
  getrusage(RUSAGE_SELF, &use);
  fprintf(out, "D exact-norm L=%d candidates=%d occurrences=%ld stopped=%d seconds=%.1f enumerate_seconds=%.1f evaluations=%ld maxrss_kb=%ld\n",
          L, ncand, nocc, stopped, now() - t0, enumerated, evaluations, (long)use.ru_maxrss);
  fclose(out);
  return 0;
}
