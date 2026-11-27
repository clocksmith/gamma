// Exact greedy token gain, open or closed, built on the frozen fixed-source-v3 engine.
//
// The frozen greedy-entry mode, and greedy-closed in engine_closed.c, keep each candidate's last
// computed gain as its heap key. Exact token gain under shortest-path parsing can grow as the
// dictionary grows, so a stale key can be too low and the lazy pick is not always the best entry
// (audit_lazy.c measures how often). This engine keys the heap by a bound that is valid at every
// later step:
//
//   gain(w | V) <= sum over occurrences i of w of ( d_V(i, i + |w|) - 1 )
//
// where d_V(i, j) is the fewest tokens that spell text[i:j] with V. Proof: take an optimal parse
// with V + {w}; replace each use of w by an optimal V-parse of the same span; the result is a parse
// with V that costs at most the sum above more. d_V only falls as V grows, so the bound never rises
// and lazy evaluation with it is exact. At each step candidates are popped by bound; a candidate's
// exact gain is computed once its bound is current; the step ends when the best exact gain found is
// at least the largest remaining bound. Ties: larger gain, then lower candidate id (the frozen
// engine's tie rule).
//
//   engine_exact MODE POLICY L KMAX LIMIT_SECONDS LIST OUT
// MODE: exact-entry (open), exact-closed (closed), exact-byte (open, gain per stored byte, 1 + |w|).
#define ENGINE_NO_MAIN
#include "../fixed-source-v3/engine.c"

static unsigned char *in_dict, *in_heap;
static int *members, nmembers;
static int closed_mode, per_byte;

// Fewest tokens for text[p : p + l] with the current dictionary (mask holds entry lengths at p).
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

// Every occurrence of a candidate is the same string, and span_cost only reads entries that end inside
// the span, so the cost is the same at every occurrence. A parse uses non-overlapping occurrences only,
// at most `used` of them (the engine's maximum non-overlapping count, ub / (len - 1)).
static double bound_of(const Cand *c) {
  long used = c->ub / (c->len - 1);
  long s = used * (span_cost(occ[c->off], c->len) - 1);
  return per_byte ? (double)s / (1.0 + c->len) : (double)s;
}

// Shortest-path distances from each document start (fwd) and to each document end (bwd), kept current
// for every document after each accepted entry. Index of position p of document d: p + d.
static int *fwd, *bwd;
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

// Exact gain. A document with one occurrence at p: the new cost is min(cost, fwd[p] + 1 + bwd[p + len]).
// A document with several occurrences falls back to a full shortest-path recomputation.
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
    if (d != last) { doc_distances(d); last = d; }
  }
}

static double score_of(int gain, const Cand *c) { return per_byte ? gain / (1.0 + c->len) : (double)gain; }

typedef struct { double key; int c, stamp; } BNode;
static BNode *bh;
static int bh_n;
static inline int b_above(const BNode *a, const BNode *b) { return a->key > b->key || (a->key == b->key && a->c < b->c); }
static void b_push(BNode x) {
  int i = bh_n++;
  while (i) { int up = (i - 1) / 2; if (!b_above(&x, &bh[up])) break; bh[i] = bh[up]; i = up; }
  bh[i] = x;
}
static BNode b_pop(void) {
  BNode top = bh[0], x = bh[--bh_n];
  int i = 0;
  for (;;) {
    int a = 2 * i + 1, b = a + 1, m = -1;
    if (a < bh_n) m = a;
    if (b < bh_n && b_above(&bh[b], &bh[a])) m = b;
    if (m < 0 || !b_above(&bh[m], &x)) break;
    bh[i] = bh[m];
    i = m;
  }
  if (bh_n) bh[i] = x;
  return top;
}

static void offer(const unsigned char *a, int la, const unsigned char *b, int lb, int L, unsigned char *buf) {
  if (la + lb > L) return;
  memcpy(buf, a, la);
  memcpy(buf + la, b, lb);
  int c = find_candidate(buf, la + lb);
  if (c < 0 || in_dict[c] || in_heap[c]) return;
  in_heap[c] = 1;
  b_push((BNode){(double)cands[c].ub / (per_byte ? 1.0 + cands[c].len : 1.0), c, -1});
}

static long evaluations;

static int run_exact(FILE *out, int L, int kmax, double limit) {
  int k = 0;
  long bytes = 0;
  add_alphabet(out, &k, &bytes);
  double start = now();
  fwd = xmalloc((total + ndocs) * sizeof(int));
  bwd = xmalloc((total + ndocs) * sizeof(int));
  for (int d = 0; d < ndocs; d++) doc_distances(d);
  in_dict = calloc(ncand, 1);
  in_heap = calloc(ncand, 1);
  members = xmalloc((kmax + 256) * sizeof(int));
  bh = xmalloc((ncand + 1) * sizeof(BNode));
  unsigned char *buf = xmalloc(2 * L + 2);
  unsigned char alpha[256];
  int nalpha = 0;
  for (int c = 0; c < 256; c++)
    if (present[c]) alpha[nalpha++] = (unsigned char)c;
  if (closed_mode) {
    for (int i = 0; i < nalpha; i++)
      for (int j = 0; j < nalpha; j++) offer(&alpha[i], 1, &alpha[j], 1, L, buf);
  } else {
    for (int c = 0; c < ncand; c++) { in_heap[c] = 1; b_push((BNode){(double)cands[c].ub / (per_byte ? 1.0 + cands[c].len : 1.0), c, -1}); }
  }
  // Popped this step but not chosen: returned to the heap with a current bound once the step ends.
  int *held = xmalloc(sizeof(int) * (ncand + 1));
  double *held_key = xmalloc(sizeof(double) * (ncand + 1));
  int step = 0;
  while (k < kmax) {
    if ((step & 15) == 0 && now() - start > limit) return 1;
    int nheld = 0, best_c = -1, best_gain = 0;
    double best_score = 0.0;
    while (bh_n) {
      if (best_c >= 0 && !b_above(&bh[0], &(BNode){best_score, best_c, 0})) break;  // no remaining bound can beat it
      BNode top = b_pop();
      if (top.stamp != step) {
        top.key = bound_of(&cands[top.c]);
        top.stamp = step;
        if (bh_n && b_above(&bh[0], &top)) { b_push(top); continue; }
      }
      int g = gain_fast(&cands[top.c]);
      evaluations++;
      double sc = score_of(g, &cands[top.c]);
      held[nheld] = top.c;
      held_key[nheld++] = top.key;
      if (g > 0 && (best_c < 0 || sc > best_score || (sc == best_score && top.c < best_c))) {
        best_c = top.c; best_gain = g; best_score = sc;
      }
    }
    for (int i = 0; i < nheld; i++)
      if (held[i] != best_c) b_push((BNode){held_key[i], held[i], step});
    if (best_c < 0) break;
    const Cand *c = &cands[best_c];
    accept_fast(c);
    in_heap[best_c] = 0;
    in_dict[best_c] = 1;
    k++;
    bytes += 1 + c->len;
    const unsigned char *e = text + occ[c->off];
    write_entry(out, k, bytes, emissions, ndocs, e, c->len);
    fflush(out);
    (void)best_gain;
    if (closed_mode) {
      for (int i = 0; i < nalpha; i++) { offer(e, c->len, &alpha[i], 1, L, buf); offer(&alpha[i], 1, e, c->len, L, buf); }
      for (int m = 0; m < nmembers; m++) {
        const Cand *x = &cands[members[m]];
        const unsigned char *xs = text + occ[x->off];
        offer(e, c->len, xs, x->len, L, buf);
        offer(xs, x->len, e, c->len, L, buf);
      }
      offer(e, c->len, e, c->len, L, buf);
      members[nmembers++] = best_c;
    }
    step++;
  }
  return 0;
}

int main(int argc, char **argv) {
  if (argc != 8) {
    fprintf(stderr, "usage: engine_exact MODE POLICY L KMAX LIMIT_SECONDS LIST OUT\n");
    return 2;
  }
  const char *mode = argv[1], *receipt = getenv("FSV3_RECEIPT");
  if (!receipt || !strstr(receipt, "manifest=") || !strstr(receipt, "pool=") ||
      !strstr(receipt, "cuts=") || !strstr(receipt, "impl=") || !strstr(receipt, "run=")) {
    fprintf(stderr, "FSV3_RECEIPT must bind manifest, pool, cuts, impl and run\n");
    return 2;
  }
  if (!strcmp(mode, "exact-entry")) { closed_mode = 0; per_byte = 0; }
  else if (!strcmp(mode, "exact-closed")) { closed_mode = 1; per_byte = 0; }
  else if (!strcmp(mode, "exact-byte")) { closed_mode = 0; per_byte = 1; }
  else { fprintf(stderr, "unknown mode\n"); return 2; }
  set_policy(argv[2]);
  int L = atoi(argv[3]), kmax = atoi(argv[4]);
  double limit = atof(argv[5]);
  if (L < 1 || L > 64) { fprintf(stderr, "L must be 1..64\n"); return 2; }
  load(argv[6]);
  load_side_files();
  double t0 = now();
  enumerate(L);
  double enumerated = now() - t0;
  FILE *out = fopen(argv[7], "w");
  if (!out) { perror(argv[7]); return 2; }
  fprintf(out, "H policy=%s mode=%s L=%d K=%d limit=%s %s\n", argv[2], mode, L, kmax, argv[5], receipt);
  int stopped = run_exact(out, L, kmax, limit);
  struct rusage use;
  getrusage(RUSAGE_SELF, &use);
  fprintf(out, "D %s L=%d candidates=%d occurrences=%ld stopped=%d seconds=%.1f enumerate_seconds=%.1f evaluations=%ld maxrss_kb=%ld\n",
          mode, L, ncand, nocc, stopped, now() - t0, enumerated, evaluations, (long)use.ru_maxrss);
  fclose(out);
  return 0;
}
