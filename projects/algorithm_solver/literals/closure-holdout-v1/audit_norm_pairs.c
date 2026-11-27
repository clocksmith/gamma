// Audit of NORMALIZED-PAIRS.md along a real chain.
//
// Replays a chain (closed or normalized; on CodeNet `primary` they are identical). At every EVERY-th step it finds
// the strongest candidate that needs three or more tokens to spell (the strongest non-pair challenger) under
// normalized gain N(w) = Delta(w) / (s_V(w) - 1), exactly, and the best closed candidate (s_V = 2) by Delta.
// For the challenger it records Delta, s, the uses m of w in an optimal parse after adding w (fewest uses among
// optimal parses, so the premise is tested as favourably as possible), and the alignment penalty
// c_{V+w} + m (s - 1) - c_V. The proposition certifies the step when the challenger's penalty is 0 (then some
// adjacent pair scores at least N(w)); it is silent when the penalty is positive. Exactness: N(w) <= used(w), the
// engine's maximum non-overlapping count, a bound that never rises, so candidates are scanned in decreasing
// used(w) until the bound falls below the best challenger found.
//
//   audit_norm_pairs L EVERY LIST CHAIN OUT_TSV
#define ENGINE_NO_MAIN
#include "../fixed-source-v3/engine.c"

static int *fwd, *bwd;

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
    while (m) { int k = __builtin_ctzll(m); m &= m - 1; int j = i + k + 1; if (j <= n && here + 1 < fwd[base + j]) fwd[base + j] = here + 1; }
  }
  bwd[base + n] = 0;
  for (int i = n - 1; i >= 0; i--) {
    int b = INF;
    u64 m = mask[s + i];
    while (m) { int k = __builtin_ctzll(m); m &= m - 1; int j = i + k + 1; if (j <= n && 1 + bwd[base + j] < b) b = 1 + bwd[base + j]; }
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

// Fewest uses of candidate c among optimal parses of document d with c added (lexicographic: tokens, then uses).
static unsigned char *is_occ;
static int min_uses_doc(const Cand *c, int d, int lo, int hi) {
  int s = dstart[d], n = dlen[d];
  static int *bt = NULL, *bu = NULL;
  static int cap = 0;
  if (n + 1 > cap) { cap = n + 1; bt = realloc(bt, cap * sizeof(int)); bu = realloc(bu, cap * sizeof(int)); }
  for (int k = lo; k < hi; k++) is_occ[occ[c->off + k]] = 1;
  bt[0] = 0; bu[0] = 0;
  for (int i = 1; i <= n; i++) { bt[i] = INF; bu[i] = INF; }
  for (int i = 0; i < n; i++) {
    if (bt[i] >= INF) continue;
    u64 m = mask[s + i];
    while (m) {
      int k = __builtin_ctzll(m); m &= m - 1;
      int j = i + k + 1;
      if (j > n) continue;
      if (bt[i] + 1 < bt[j] || (bt[i] + 1 == bt[j] && bu[i] < bu[j])) { bt[j] = bt[i] + 1; bu[j] = bu[i]; }
    }
    if (is_occ[s + i] && i + c->len <= n) {
      int j = i + c->len;
      if (bt[i] + 1 < bt[j] || (bt[i] + 1 == bt[j] && bu[i] + 1 < bu[j])) { bt[j] = bt[i] + 1; bu[j] = bu[i] + 1; }
    }
  }
  for (int k = lo; k < hi; k++) is_occ[occ[c->off + k]] = 0;
  return bu[n];
}

static int *order_by_used;
static int used_cmp(const void *a, const void *b) {
  int x = *(const int *)a, y = *(const int *)b;
  long ux = cands[x].ub / (cands[x].len - 1), uy = cands[y].ub / (cands[y].len - 1);
  if (ux != uy) return ux > uy ? -1 : 1;
  return x - y;
}

int main(int argc, char **argv) {
  if (argc != 6) { fprintf(stderr, "usage: audit_norm_pairs L EVERY LIST CHAIN OUT_TSV\n"); return 2; }
  int L = atoi(argv[1]), every = atoi(argv[2]);
  set_policy("s1-whole");
  load(argv[3]);
  load_side_files();
  enumerate(L);
  FILE *devnull = fopen("/dev/null", "w");
  int k = 0;
  long bytes = 0;
  add_alphabet(devnull, &k, &bytes);
  fwd = xmalloc((total + ndocs) * sizeof(int));
  bwd = xmalloc((total + ndocs) * sizeof(int));
  for (int d = 0; d < ndocs; d++) doc_distances(d);
  is_occ = calloc(total + 1, 1);
  unsigned char *in_dict = calloc(ncand, 1);
  order_by_used = xmalloc(ncand * sizeof(int));
  for (int c = 0; c < ncand; c++) order_by_used[c] = c;
  qsort(order_by_used, ncand, sizeof(int), used_cmp);
  FILE *f = fopen(argv[4], "r"), *out = fopen(argv[5], "w");
  fprintf(out, "step\tchain_entry_gain\tbest_pair_gain\tchallenger_score_num\tchallenger_score_den\tchallenger_gain\tchallenger_s\tchallenger_len\tchallenger_uses\talignment_penalty\tverdict\tchecked\n");
  char line[1 << 12];
  unsigned char e[128];
  int step = 0, certified = 0, silent = 0, beats = 0, audited = 0;
  while (fgets(line, sizeof line, f)) {
    if (line[0] != 'E') continue;
    char hex[512]; int kk, s0; long b0, t0;
    if (sscanf(line, "E %d %ld %ld %d %511s", &kk, &b0, &t0, &s0, hex) != 5) continue;
    int l = (int)strlen(hex) / 2;
    if (l == 1) continue;
    for (int i = 0; i < l; i++) sscanf(hex + 2 * i, "%2hhx", &e[i]);
    int c = find_candidate(e, l);
    if (c < 0) { fprintf(stderr, "chain entry is not a candidate\n"); return 1; }
    if (every > 0 && step % every == 0) {
      int chain_gain = gain_fast(&cands[c]);
      // Best closed candidate by Delta, and the strongest challenger by Delta / (s - 1), both exactly.
      int best_pair = 0;
      long cn = 0, cd = 1; int cg = 0, cs = 0, cl = 0, cx = -1, checked = 0;
      for (int r = 0; r < ncand; r++) {
        int x = order_by_used[r];
        long used = cands[x].ub / (cands[x].len - 1);
        // stop when neither the pair nor the challenger search can improve
        if (used <= best_pair && used * cd <= cn) break;
        if (in_dict[x]) continue;
        int s = span_cost(occ[cands[x].off], cands[x].len);
        if (s < 2) continue;
        if (s == 2) {
          if (used <= best_pair) continue;
          int g = gain_fast(&cands[x]); checked++;
          if (g > best_pair) best_pair = g;
        } else {
          if (used * cd <= cn) continue;
          int g = gain_fast(&cands[x]); checked++;
          if (g > 0 && (long)g * cd > cn * (s - 1)) { cn = g; cd = s - 1; cg = g; cs = s; cl = cands[x].len; cx = x; }
        }
      }
      int uses = 0; long penalty = -1;
      if (cx >= 0) {
        const Cand *w = &cands[cx];
        long with_w = 0, base_cost = 0;
        for (int d = 0; d < ndocs; d++) base_cost += cost[d];
        for (int i = 0; i < w->nocc;) {
          int d = docof[occ[w->off + i]], j = i;
          while (j < w->nocc && docof[occ[w->off + j]] == d) j++;
          uses += min_uses_doc(w, d, i, j);
          i = j;
        }
        with_w = base_cost - cg;
        penalty = with_w + (long)uses * (cs - 1) - base_cost;
      }
      const char *verdict = cx < 0 ? "no-challenger" : (cn * 1 > (long)best_pair * cd ? "challenger-beats-pairs" : (penalty == 0 ? "certified" : "silent"));
      if (cx < 0 || penalty == 0) certified += (cx < 0 || !strcmp(verdict, "certified")); else silent++;
      if (!strcmp(verdict, "challenger-beats-pairs")) beats++;
      audited++;
      fprintf(out, "%d\t%d\t%d\t%ld\t%ld\t%d\t%d\t%d\t%d\t%ld\t%s\t%d\n", step, chain_gain, best_pair, cn, cd, cg, cs, cl, uses, penalty, verdict, checked);
      fflush(out);
    }
    accept(&cands[c]);
    in_dict[c] = 1;
    int last = -1;
    for (int i = 0; i < cands[c].nocc; i++) { int d = docof[occ[cands[c].off + i]]; if (d != last) { doc_distances(d); last = d; } }
    step++;
  }
  fprintf(stderr, "audited %d steps: certified %d, silent %d, challenger beats pairs %d\n", audited, certified, silent, beats);
  return 0;
}
