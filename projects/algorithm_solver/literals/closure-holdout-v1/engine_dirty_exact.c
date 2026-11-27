// Dirty-document incremental exact greedy trainer built on fixed-source-v3/engine.c.
//
// Partitions each candidate's occurrences by document into runs r = (c, d) and maintains:
//   - r_used[r]: maximum pairwise non-overlapping occurrences of c in document d
//   - r_gain[r]: exact shortest-path token gain of c in document d at last evaluation
//   - r_dirty[r]: 1 if document d was modified since r_gain[r] was computed, else 0
// For modes exact-entry, exact-closed, exact-closed-len, and exact-byte, span_cost_V(c) never
// increases as V grows, so clean_gain[c] + dirty_used[c] * cached_sm1[c] upper-bounds gain(c | V)
// at every step. Requires cuts=none (FSV3_CUTS unset). All chains emitted for scientific claims
// must still be checked independently with verify_greedy or verify_norm.
//
//   engine_dirty_exact MODE POLICY L KMAX LIMIT_SECONDS LIST OUT
#define ENGINE_NO_MAIN
#include "../fixed-source-v3/engine.c"

enum { M_ENTRY = 0, M_CLOSED = 1, M_CLOSED_LEN = 2, M_BYTE = 3, M_NORM = 4 };
static int emode;

static unsigned char *in_dict, *in_heap;
static int *members, nmembers;

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

static long nruns;
static long *c_run_start;
static int *c_run_cnt;
static int *r_cand, *r_doc, *r_used, *r_gain;
static long *r_occ_off;
static int *r_occ_cnt;
static unsigned char *r_dirty;

static long *d_run_start;
static int *d_run_cnt;
static long *d_runs;

static long *clean_gain, *dirty_used;
static int *cached_sm1;

static double *h_key;
static int *h_cand;
static int *h_pos;
static int h_n;

static inline int h_above_idx(double ka, int ca, double kb, int cb) {
  return ka > kb || (ka == kb && ca < cb);
}

static void h_swap(int i, int j) {
  double tk = h_key[i]; h_key[i] = h_key[j]; h_key[j] = tk;
  int tc = h_cand[i]; h_cand[i] = h_cand[j]; h_cand[j] = tc;
  h_pos[h_cand[i]] = i;
  h_pos[h_cand[j]] = j;
}

static void h_up(int i) {
  while (i > 0) {
    int up = (i - 1) >> 1;
    if (!h_above_idx(h_key[i], h_cand[i], h_key[up], h_cand[up])) break;
    h_swap(i, up);
    i = up;
  }
}

static void h_down(int i) {
  for (;;) {
    int a = (i << 1) + 1, b = a + 1, m = i;
    if (a < h_n && h_above_idx(h_key[a], h_cand[a], h_key[m], h_cand[m])) m = a;
    if (b < h_n && h_above_idx(h_key[b], h_cand[b], h_key[m], h_cand[m])) m = b;
    if (m == i) break;
    h_swap(i, m);
    i = m;
  }
}

static void h_set_key(int c, double k) {
  int i = h_pos[c];
  if (i < 0) {
    i = h_n++;
    h_key[i] = k;
    h_cand[i] = c;
    h_pos[c] = i;
    h_up(i);
  } else {
    double old = h_key[i];
    h_key[i] = k;
    if (k > old) h_up(i);
    else if (k < old) h_down(i);
  }
}

static void h_remove(int c) {
  int i = h_pos[c];
  if (i < 0) return;
  h_pos[c] = -1;
  h_n--;
  if (i < h_n) {
    h_key[i] = h_key[h_n];
    h_cand[i] = h_cand[h_n];
    h_pos[h_cand[i]] = i;
    h_up(i);
    h_down(i);
  }
}

static inline double compute_ub_key(int c) {
  const Cand *x = &cands[c];
  if (emode == M_NORM) {
    return (double)clean_gain[c] / (double)cached_sm1[c] + (double)dirty_used[c] + 1e-12;
  }
  long ubg = clean_gain[c] + dirty_used[c] * (long)cached_sm1[c];
  if (emode == M_ENTRY || emode == M_CLOSED) return (double)ubg;
  if (emode == M_CLOSED_LEN) return (double)(ubg * (x->len - 1));
  if (emode == M_BYTE) return (double)ubg / (double)(1 + x->len) + 1e-12;
  return (double)ubg;
}

static inline int exact_better(long ga, int sm1_a, int la, int ca,
                               long gb, int sm1_b, int lb, int cb) {
  long long lhs = 0, rhs = 0;
  if (emode == M_ENTRY || emode == M_CLOSED) {
    lhs = ga; rhs = gb;
  } else if (emode == M_CLOSED_LEN) {
    lhs = (long long)ga * (la - 1); rhs = (long long)gb * (lb - 1);
  } else if (emode == M_BYTE) {
    lhs = (long long)ga * (1 + lb); rhs = (long long)gb * (1 + la);
  } else if (emode == M_NORM) {
    lhs = (long long)ga * sm1_b; rhs = (long long)gb * sm1_a;
  }
  if (lhs != rhs) return lhs > rhs;
  return ca < cb;
}

static long evaluations;

static void eval_dirty_runs(int c) {
  const Cand *x = &cands[c];
  if (emode != M_CLOSED && emode != M_CLOSED_LEN) {
    int sm1 = span_cost(occ[x->off], x->len) - 1;
    if (sm1 < 1) sm1 = 1;
    cached_sm1[c] = sm1;
  }
  if (dirty_used[c] == 0) return;
  u64 bit = 1ULL << (x->len - 1);
  long rs = c_run_start[c];
  int rc = c_run_cnt[c];
  for (int idx = 0; idx < rc; idx++) {
    long r = rs + idx;
    if (!r_dirty[r]) continue;
    int d = r_doc[r];
    int cnt = r_occ_cnt[r];
    long off = r_occ_off[r];
    int g = 0;
    if (cnt == 1) {
      int p = occ[off], base = dstart[d] + d, poff = p - dstart[d];
      int alt = fwd[base + poff] + 1 + bwd[base + poff + x->len];
      if (alt < cost[d]) g = cost[d] - alt;
    } else {
      for (int k = 0; k < cnt; k++) mask[occ[off + k]] |= bit;
      g = cost[d] - doc_cost(d);
      for (int k = 0; k < cnt; k++) mask[occ[off + k]] &= ~bit;
    }
    r_dirty[r] = 0;
    r_gain[r] = g;
    clean_gain[c] += g;
    dirty_used[c] -= r_used[r];
    evaluations++;
  }
}

static void mark_doc_dirty(int d) {
  long ds = d_run_start[d];
  int dc = d_run_cnt[d];
  for (int i = 0; i < dc; i++) {
    long r = d_runs[ds + i];
    if (r_dirty[r]) continue;
    int c = r_cand[r];
    if (in_dict[c]) continue;
    r_dirty[r] = 1;
    clean_gain[c] -= r_gain[r];
    dirty_used[c] += r_used[r];
    if (in_heap[c]) h_set_key(c, compute_ub_key(c));
  }
}

static void build_runs(void) {
  c_run_start = xmalloc(ncand * sizeof(long));
  c_run_cnt = xmalloc(ncand * sizeof(int));
  d_run_cnt = calloc(ndocs, sizeof(int));
  nruns = 0;
  for (int c = 0; c < ncand; c++) {
    const Cand *x = &cands[c];
    int cnt = 0;
    for (int i = 0; i < x->nocc;) {
      int d = docof[occ[x->off + i]], j = i + 1;
      while (j < x->nocc && docof[occ[x->off + j]] == d) j++;
      cnt++;
      d_run_cnt[d]++;
      i = j;
    }
    c_run_start[c] = nruns;
    c_run_cnt[c] = cnt;
    nruns += cnt;
  }
  r_cand = xmalloc(nruns * sizeof(int));
  r_doc = xmalloc(nruns * sizeof(int));
  r_used = xmalloc(nruns * sizeof(int));
  r_gain = calloc(nruns, sizeof(int));
  r_occ_off = xmalloc(nruns * sizeof(long));
  r_occ_cnt = xmalloc(nruns * sizeof(int));
  r_dirty = xmalloc(nruns);
  memset(r_dirty, 1, nruns);

  d_run_start = xmalloc((ndocs + 1) * sizeof(long));
  long acc = 0;
  for (int d = 0; d < ndocs; d++) { d_run_start[d] = acc; acc += d_run_cnt[d]; d_run_cnt[d] = 0; }
  d_run_start[ndocs] = acc;
  d_runs = xmalloc(nruns * sizeof(long));

  clean_gain = calloc(ncand, sizeof(long));
  dirty_used = calloc(ncand, sizeof(long));
  cached_sm1 = xmalloc(ncand * sizeof(int));

  int is_closed = (emode == M_CLOSED || emode == M_CLOSED_LEN);
  for (int c = 0; c < ncand; c++) {
    const Cand *x = &cands[c];
    cached_sm1[c] = is_closed ? 1 : (x->len - 1);
    long r = c_run_start[c];
    for (int i = 0; i < x->nocc;) {
      int d = docof[occ[x->off + i]], j = i + 1;
      while (j < x->nocc && docof[occ[x->off + j]] == d) j++;
      int u = 0, last_end = -1;
      for (int k = i; k < j; k++) {
        int p = occ[x->off + k];
        if (p >= last_end) { u++; last_end = p + x->len; }
      }
      r_cand[r] = c;
      r_doc[r] = d;
      r_used[r] = u;
      r_occ_off[r] = x->off + i;
      r_occ_cnt[r] = j - i;
      dirty_used[c] += u;
      d_runs[d_run_start[d] + d_run_cnt[d]++] = r;
      r++;
      i = j;
    }
  }
}

static void offer_closed(const unsigned char *a, int la, const unsigned char *b, int lb, int L, unsigned char *buf) {
  if (la + lb > L) return;
  memcpy(buf, a, la);
  memcpy(buf + la, b, lb);
  int c = find_candidate(buf, la + lb);
  if (c < 0 || in_dict[c] || in_heap[c]) return;
  in_heap[c] = 1;
  cached_sm1[c] = 1;
  h_set_key(c, compute_ub_key(c));
}

static int run_dirty_exact(FILE *out, int L, int kmax, double limit) {
  int k = 0;
  long bytes = 0;
  add_alphabet(out, &k, &bytes);
  double start = now();
  fwd = xmalloc((total + ndocs) * sizeof(int));
  bwd = xmalloc((total + ndocs) * sizeof(int));
  for (int d = 0; d < ndocs; d++) doc_distances(d);

  build_runs();

  in_dict = calloc(ncand, 1);
  in_heap = calloc(ncand, 1);
  members = xmalloc((kmax + 256) * sizeof(int));
  h_key = xmalloc((ncand + 1) * sizeof(double));
  h_cand = xmalloc((ncand + 1) * sizeof(int));
  h_pos = xmalloc(ncand * sizeof(int));
  for (int c = 0; c < ncand; c++) h_pos[c] = -1;

  unsigned char *buf = xmalloc(2 * L + 2);
  unsigned char alpha[256];
  int nalpha = 0;
  for (int c = 0; c < 256; c++)
    if (present[c]) alpha[nalpha++] = (unsigned char)c;

  int is_closed = (emode == M_CLOSED || emode == M_CLOSED_LEN);
  if (is_closed) {
    for (int i = 0; i < nalpha; i++)
      for (int j = 0; j < nalpha; j++)
        offer_closed(&alpha[i], 1, &alpha[j], 1, L, buf);
  } else {
    for (int c = 0; c < ncand; c++) {
      in_heap[c] = 1;
      h_set_key(c, compute_ub_key(c));
    }
  }

  int step = 0;
  while (k < kmax) {
    if ((step & 15) == 0 && now() - start > limit) return 1;
    int best_c = -1;
    long best_g = 0;
    int best_sm1 = 1, best_len = 2;
    double best_exact_dbl = 0.0;

    while (h_n > 0) {
      int top_c = h_cand[0];
      double top_ub = h_key[0];
      if (best_c >= 0) {
        if (top_ub < best_exact_dbl - 1e-13) break;
        if (emode == M_ENTRY || emode == M_CLOSED) {
          long iub = (long)top_ub;
          if (iub < best_g || (iub == best_g && top_c > best_c)) break;
        } else if (emode == M_CLOSED_LEN) {
          long iub = (long)top_ub;
          long cur = best_g * (best_len - 1);
          if (iub < cur || (iub == cur && top_c > best_c)) break;
        }
      }
      if (dirty_used[top_c] == 0 && (is_closed || cached_sm1[top_c] == span_cost(occ[cands[top_c].off], cands[top_c].len) - 1)) {
        long g = clean_gain[top_c];
        int sm1 = cached_sm1[top_c];
        int len = cands[top_c].len;
        double ex = (emode == M_NORM) ? (double)g / (double)sm1 :
                    (emode == M_BYTE) ? (double)g / (double)(1 + len) :
                    (emode == M_CLOSED_LEN) ? (double)(g * (len - 1)) : (double)g;
        if (top_ub > ex) {
          h_set_key(top_c, ex);
          continue;
        }
        if (g > 0 && (best_c < 0 || exact_better(g, sm1, len, top_c, best_g, best_sm1, best_len, best_c))) {
          best_c = top_c; best_g = g; best_sm1 = sm1; best_len = len; best_exact_dbl = ex;
        }
        if (emode == M_ENTRY || emode == M_CLOSED || emode == M_CLOSED_LEN) break;
      }
      if (dirty_used[top_c] > 0 || (!is_closed && cached_sm1[top_c] != span_cost(occ[cands[top_c].off], cands[top_c].len) - 1)) {
        eval_dirty_runs(top_c);
        long g = clean_gain[top_c];
        int sm1 = cached_sm1[top_c];
        int len = cands[top_c].len;
        double ex = (emode == M_NORM) ? (double)g / (double)sm1 :
                    (emode == M_BYTE) ? (double)g / (double)(1 + len) :
                    (emode == M_CLOSED_LEN) ? (double)(g * (len - 1)) : (double)g;
        h_set_key(top_c, ex);
        if (g > 0 && (best_c < 0 || exact_better(g, sm1, len, top_c, best_g, best_sm1, best_len, best_c))) {
          best_c = top_c; best_g = g; best_sm1 = sm1; best_len = len; best_exact_dbl = ex;
        }
        continue;
      }
      break;
    }

    if ((emode == M_NORM || emode == M_BYTE) && h_n > 0) {
      static int *tie_buf = NULL;
      static double *tie_key = NULL;
      if (!tie_buf) {
        tie_buf = xmalloc((ncand + 1) * sizeof(int));
        tie_key = xmalloc((ncand + 1) * sizeof(double));
      }
      int ntie = 0;
      while (h_n > 0 && (best_c < 0 || h_key[0] >= best_exact_dbl - 1e-11)) {
        int c = h_cand[0];
        if (dirty_used[c] > 0 || cached_sm1[c] != span_cost(occ[cands[c].off], cands[c].len) - 1) {
          eval_dirty_runs(c);
        }
        long g = clean_gain[c];
        int sm1 = cached_sm1[c];
        int len = cands[c].len;
        double ex = (emode == M_NORM) ? (double)g / (double)sm1 : (double)g / (double)(1 + len);
        h_remove(c);
        tie_buf[ntie] = c;
        tie_key[ntie++] = ex;
        if (g > 0 && (best_c < 0 || exact_better(g, sm1, len, c, best_g, best_sm1, best_len, best_c))) {
          best_c = c; best_g = g; best_sm1 = sm1; best_len = len; best_exact_dbl = ex;
        }
      }
      for (int i = 0; i < ntie; i++) h_set_key(tie_buf[i], tie_key[i]);
    }

    if (best_c < 0 || best_g <= 0) break;

    const Cand *c = &cands[best_c];
    h_remove(best_c);
    in_heap[best_c] = 0;
    in_dict[best_c] = 1;
    accept(c);

    long rs = c_run_start[best_c];
    int rc = c_run_cnt[best_c];
    for (int idx = 0; idx < rc; idx++) {
      int d = r_doc[rs + idx];
      doc_distances(d);
      mark_doc_dirty(d);
    }

    k++;
    bytes += 1 + c->len;
    const unsigned char *e = text + occ[c->off];
    write_entry(out, k, bytes, emissions, ndocs, e, c->len);
    fflush(out);

    if (is_closed) {
      for (int i = 0; i < nalpha; i++) {
        offer_closed(e, c->len, &alpha[i], 1, L, buf);
        offer_closed(&alpha[i], 1, e, c->len, L, buf);
      }
      for (int m = 0; m < nmembers; m++) {
        const Cand *x = &cands[members[m]];
        const unsigned char *xs = text + occ[x->off];
        offer_closed(e, c->len, xs, x->len, L, buf);
        offer_closed(xs, x->len, e, c->len, L, buf);
      }
      offer_closed(e, c->len, e, c->len, L, buf);
      members[nmembers++] = best_c;
    }
    step++;
  }
  return 0;
}

int main(int argc, char **argv) {
  if (argc != 8) {
    fprintf(stderr, "usage: engine_dirty_exact MODE POLICY L KMAX LIMIT_SECONDS LIST OUT\n");
    return 2;
  }
  const char *mode = argv[1], *receipt = getenv("FSV3_RECEIPT");
  if (!receipt || !strstr(receipt, "manifest=") || !strstr(receipt, "pool=") ||
      !strstr(receipt, "cuts=") || !strstr(receipt, "impl=") || !strstr(receipt, "run=")) {
    fprintf(stderr, "FSV3_RECEIPT must bind manifest, pool, cuts, impl and run\n");
    return 2;
  }
  if (!strcmp(mode, "exact-entry")) emode = M_ENTRY;
  else if (!strcmp(mode, "exact-closed")) emode = M_CLOSED;
  else if (!strcmp(mode, "exact-closed-len")) emode = M_CLOSED_LEN;
  else if (!strcmp(mode, "exact-byte")) emode = M_BYTE;
  else if (!strcmp(mode, "exact-norm")) emode = M_NORM;
  else { fprintf(stderr, "unknown mode %s\n", mode); return 2; }

  set_policy(argv[2]);
  int L = atoi(argv[3]), kmax = atoi(argv[4]);
  double limit = atof(argv[5]);
  if (L < 1 || L > 64) { fprintf(stderr, "L must be 1..64\n"); return 2; }
  load(argv[6]);
  load_side_files();
  if (cut_before) {
    fprintf(stderr, "engine_dirty_exact requires cuts=none (FSV3_CUTS unset)\n");
    return 2;
  }
  double t0 = now();
  enumerate(L);
  double enumerated = now() - t0;
  FILE *out = fopen(argv[7], "w");
  if (!out) { perror(argv[7]); return 2; }
  fprintf(out, "H policy=%s mode=%s L=%d K=%d limit=%s %s\n", argv[2], mode, L, kmax, argv[5], receipt);
  int stopped = run_dirty_exact(out, L, kmax, limit);
  struct rusage use;
  getrusage(RUSAGE_SELF, &use);
  fprintf(out, "D %s L=%d candidates=%d occurrences=%ld runs=%ld stopped=%d seconds=%.2f enumerate_seconds=%.2f run_evals=%ld maxrss_kb=%ld\n",
          mode, L, ncand, nocc, nruns, stopped, now() - t0, enumerated, evaluations, (long)use.ru_maxrss);
  fclose(out);
  return 0;
}
