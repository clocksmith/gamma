// Exact greedy normalized open gain with:
//   (1) Independent implementation of the single-entry pruning bound:
//         Delta_T(w) / (s - 1)  <=  min_{1 <= i <= s-1} Delta_T(t_i t_{i+1})  +  U(w)
//       where U(w) counts occurrences of w whose start OR end byte is strictly inside
//       a token of the fixed old optimal V-parse P_0, maintained incrementally on every
//       boundary flip and verifiable from scratch via --verify-u-every N.
//   (2) Active-run dirty-document caching for closed pairs (Phase 1) and lazily for any
//       non-pair candidate surviving Phase 2 pruning bounds, guaranteeing exact rational
//       comparisons (64-bit integer cross-multiplication), incumbent eligibility, and
//       exact candidate-id tie order matching unpruned engine_norm.c / exact-norm-s1-whole.txt.
//
// Mathematical dominance audit:
//   For every candidate w with s_V(w) >= 3, any maximum non-overlapping set S of
//   occurrences (|S| = used(w)) splits into aligned S_A (|S_A| <= min_i Delta_T(t_i t_{i+1}))
//   and unaligned S_U (|S_U| <= U(w)), so min_i Delta_T(t_i t_{i+1}) + U(w) >= used(w) always.
//   This engine tracks BOTH:
//     - pruned_u_vs_used: candidates pruned by the U-bound after surviving static used(w)
//     - pruned_u_vs_nocc: candidates where the U-bound beats naive nocc (even though >= used(w))
//     - pruned_dirty_nonpair: candidates pruned by exact incremental dirty-document caching
//     - u_dominance_violations: count of any candidate violating min_i Delta_T + U(w) >= used(w)
//
// Usage:
//   engine_norm_pruned POLICY L KMAX LIMIT_SECONDS LIST OUT [--verify-u-every N] [--no-dirty-nonpair]
#define ENGINE_NO_MAIN
#include "../fixed-source-v3/engine.c"

static unsigned char *in_dict;
static unsigned char *closed_in_pool;
static unsigned char *active_in_dirty;
static int *members, nmembers;

static int *fwd, *bwd;
static unsigned char *is_bdry;
static int *cand_at;
static int *unaligned;
static int L_glob;

static long nruns;
static long *c_run_start;
static int *c_run_cnt;
static int *r_cand, *r_doc, *r_used, *r_gain;
static long *r_occ_off;
static int *r_occ_cnt;
static unsigned char *r_dirty;

// Per-document active linked list of runs for closed pairs + lazily evaluated non-pairs.
static long *d_active_head;
static long *r_next_active;

static long *clean_gain, *dirty_used;

// Indexed max-heap for closed-pool candidates (key = exact upper bound on Delta_T(c)).
static long *h_key;
static int *h_cand;
static int *h_pos;
static int h_n;

static long closed_run_evals = 0;
static long nonpair_run_evals = 0;
static long nonpair_full_evals = 0;
static long pruned_static = 0;
static long pruned_u_fast = 0;
static long pruned_u_cleaned = 0;
static long pruned_u_vs_nocc = 0;
static long pruned_dirty_nonpair = 0;
static long u_dominance_violations = 0;
static long u_flips = 0;
static double u_maint_seconds = 0.0;
static double phase1_seconds = 0.0;
static double phase2_seconds = 0.0;

static inline int h_above_idx(long ka, int ca, long kb, int cb) {
  return ka > kb || (ka == kb && ca < cb);
}

static void h_swap(int i, int j) {
  long tk = h_key[i]; h_key[i] = h_key[j]; h_key[j] = tk;
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

static void h_set_key(int c, long k) {
  int i = h_pos[c];
  if (i < 0) {
    i = h_n++;
    h_key[i] = k;
    h_cand[i] = c;
    h_pos[c] = i;
    h_up(i);
  } else {
    long old = h_key[i];
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

static int *tmp_back;
static unsigned char *tmp_bdry;

static void update_doc_distances_and_u(int d, int do_u_update) {
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
      if (j <= n && here + 1 < fwd[base + j]) {
        fwd[base + j] = here + 1;
        tmp_back[j] = i;
      }
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
  if (!do_u_update) return;

  double tu0 = now();
  memset(tmp_bdry, 0, (size_t)(n + 1));
  for (int at = n; at > 0; at = tmp_back[at]) tmp_bdry[at] = 1;
  tmp_bdry[0] = 1;

  int stride = L_glob + 1;
  unsigned char *cur = is_bdry + base;
  for (int off = 1; off < n; off++) {
    unsigned char nv = tmp_bdry[off];
    if (cur[off] == nv) continue;
    int delta = (nv == 0) ? 1 : -1;
    int p = s + off;
    int max_r = n - off;
    if (max_r > L_glob) max_r = L_glob;
    const int *row_start = cand_at + (long)p * stride;
    for (int l = 2; l <= max_r; l++) {
      if (cur[off + l]) {
        int c = row_start[l];
        if (c >= 0) unaligned[c] += delta;
      }
    }
    int max_l = off;
    if (max_l > L_glob) max_l = L_glob;
    for (int l = 2; l <= max_l; l++) {
      if (cur[off - l]) {
        int c = cand_at[(long)(p - l) * stride + l];
        if (c >= 0) unaligned[c] += delta;
      }
    }
    cur[off] = nv;
    u_flips++;
  }
  u_maint_seconds += now() - tu0;
}

static void verify_u_exact(int step) {
  for (int c = 0; c < ncand; c++) {
    const Cand *x = &cands[c];
    int want = 0;
    for (int i = 0; i < x->nocc; i++) {
      int p = occ[x->off + i];
      int d = docof[p];
      int base = dstart[d] + d;
      int off = p - dstart[d];
      if (!is_bdry[base + off] || !is_bdry[base + off + x->len]) want++;
    }
    if (want != unaligned[c]) {
      fprintf(stderr, "U(w) mismatch at step %d cand %d: got %d want %d\n", step, c, unaligned[c], want);
      exit(9);
    }
  }
}

static int spelling_of(int p, int l, int *cum) {
  int b[72], back[72];
  b[0] = 0;
  for (int i = 1; i <= l; i++) b[i] = INF;
  for (int i = 0; i < l; i++) {
    if (b[i] >= INF) continue;
    u64 m = mask[p + i];
    while (m) {
      int k = __builtin_ctzll(m);
      m &= m - 1;
      int j = i + k + 1;
      if (j <= l && b[i] + 1 < b[j]) { b[j] = b[i] + 1; back[j] = i; }
    }
  }
  int s = b[l];
  if (s >= INF) return -1;
  cum[s] = l;
  for (int j = l, n = s; j > 0; j = back[j]) cum[--n] = back[j];
  return s;
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

static void build_runs_and_index(int L) {
  L_glob = L;
  long cells = (long)total * (L + 1);
  cand_at = xmalloc((size_t)cells * sizeof(int));
  memset(cand_at, -1, (size_t)cells * sizeof(int));
  for (int c = 0; c < ncand; c++) {
    const Cand *x = &cands[c];
    for (int i = 0; i < x->nocc; i++)
      cand_at[(long)occ[x->off + i] * (L + 1) + x->len] = c;
  }

  c_run_start = xmalloc((size_t)ncand * sizeof(long));
  c_run_cnt = xmalloc((size_t)ncand * sizeof(int));
  nruns = 0;
  for (int c = 0; c < ncand; c++) {
    const Cand *x = &cands[c];
    int cnt = 0;
    for (int i = 0; i < x->nocc;) {
      int d = docof[occ[x->off + i]], j = i + 1;
      while (j < x->nocc && docof[occ[x->off + j]] == d) j++;
      cnt++;
      i = j;
    }
    c_run_start[c] = nruns;
    c_run_cnt[c] = cnt;
    nruns += cnt;
  }

  r_cand = xmalloc((size_t)nruns * sizeof(int));
  r_doc = xmalloc((size_t)nruns * sizeof(int));
  r_used = xmalloc((size_t)nruns * sizeof(int));
  r_gain = calloc((size_t)nruns, sizeof(int));
  r_occ_off = xmalloc((size_t)nruns * sizeof(long));
  r_occ_cnt = xmalloc((size_t)nruns * sizeof(int));
  r_dirty = xmalloc((size_t)nruns);
  memset(r_dirty, 1, (size_t)nruns);

  r_next_active = xmalloc((size_t)nruns * sizeof(long));
  d_active_head = xmalloc((size_t)ndocs * sizeof(long));
  for (int d = 0; d < ndocs; d++) d_active_head[d] = -1;

  clean_gain = calloc((size_t)ncand, sizeof(long));
  dirty_used = calloc((size_t)ncand, sizeof(long));
  unaligned = calloc((size_t)ncand, sizeof(int));

  for (int c = 0; c < ncand; c++) {
    const Cand *x = &cands[c];
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
      r++;
      i = j;
    }
  }
}

static void activate_dirty_runs(int c) {
  if (active_in_dirty[c]) return;
  active_in_dirty[c] = 1;
  long rs = c_run_start[c];
  int rc = c_run_cnt[c];
  for (int idx = 0; idx < rc; idx++) {
    long r = rs + idx;
    int d = r_doc[r];
    r_next_active[r] = d_active_head[d];
    d_active_head[d] = r;
  }
}

static void eval_dirty_runs(int c, int is_closed) {
  if (!active_in_dirty[c]) activate_dirty_runs(c);
  if (dirty_used[c] == 0) return;
  const Cand *x = &cands[c];
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
    if (is_closed) closed_run_evals++;
    else nonpair_run_evals++;
  }
}

static void mark_doc_dirty_active(int d) {
  for (long r = d_active_head[d]; r >= 0; r = r_next_active[r]) {
    if (r_dirty[r]) continue;
    int c = r_cand[r];
    if (in_dict[c]) continue;
    r_dirty[r] = 1;
    clean_gain[c] -= r_gain[r];
    dirty_used[c] += r_used[r];
    if (h_pos[c] >= 0) h_set_key(c, clean_gain[c] + dirty_used[c]);
  }
}

static void offer_closed(const unsigned char *a, int la, const unsigned char *b, int lb, int L, unsigned char *buf) {
  if (la + lb > L) return;
  memcpy(buf, a, (size_t)la);
  memcpy(buf + la, b, (size_t)lb);
  int c = find_candidate(buf, la + lb);
  if (c < 0 || in_dict[c] || closed_in_pool[c]) return;
  closed_in_pool[c] = 1;
  activate_dirty_runs(c);
  h_set_key(c, clean_gain[c] + dirty_used[c]);
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

static int run_norm_pruned(FILE *out, int L, int kmax, double limit, int verify_u_every, int use_dirty_nonpair) {
  int k = 0;
  long bytes = 0;
  add_alphabet(out, &k, &bytes);
  double start = now();

  fwd = xmalloc((size_t)(total + ndocs) * sizeof(int));
  bwd = xmalloc((size_t)(total + ndocs) * sizeof(int));
  is_bdry = xmalloc((size_t)(total + ndocs));
  memset(is_bdry, 1, (size_t)(total + ndocs));

  int longest = 0;
  for (int d = 0; d < ndocs; d++) if (dlen[d] > longest) longest = dlen[d];
  tmp_back = xmalloc((size_t)(longest + 2) * sizeof(int));
  tmp_bdry = xmalloc((size_t)(longest + 2));

  for (int d = 0; d < ndocs; d++) update_doc_distances_and_u(d, 0);

  build_runs_and_index(L);

  in_dict = calloc((size_t)ncand, 1);
  closed_in_pool = calloc((size_t)ncand, 1);
  active_in_dirty = calloc((size_t)ncand, 1);
  members = xmalloc((size_t)(kmax + 256) * sizeof(int));
  h_key = xmalloc((size_t)(ncand + 1) * sizeof(long));
  h_cand = xmalloc((size_t)(ncand + 1) * sizeof(int));
  h_pos = xmalloc((size_t)ncand * sizeof(int));
  for (int c = 0; c < ncand; c++) h_pos[c] = -1;

  StaticCand *order = xmalloc((size_t)ncand * sizeof(StaticCand));
  for (int c = 0; c < ncand; c++) {
    order[c].used = cands[c].ub / (cands[c].len - 1);
    order[c].c = c;
  }
  qsort(order, (size_t)ncand, sizeof(StaticCand), cmp_static_cand);

  unsigned char *buf = xmalloc((size_t)(2 * L + 2));
  unsigned char alpha[256];
  int nalpha = 0;
  for (int c = 0; c < 256; c++)
    if (present[c]) alpha[nalpha++] = (unsigned char)c;

  for (int i = 0; i < nalpha; i++)
    for (int j = 0; j < nalpha; j++)
      offer_closed(&alpha[i], 1, &alpha[j], 1, L, buf);

  int cum[72];
  int pair_cids[72];
  int step = 0;
  while (k < kmax) {
    if ((step & 15) == 0 && now() - start > limit) return 1;
    if (verify_u_every > 0 && (step % verify_u_every) == 0) verify_u_exact(step);

    // Phase 1: Exact best eligible closed pair (s_V == 2).
    double tp1 = now();
    int best_pair_c = -1;
    long long best_pair_g = 0;
    while (h_n > 0) {
      int top_c = h_cand[0];
      long top_ub = h_key[0];
      if (best_pair_c >= 0) {
        if (top_ub < best_pair_g || (top_ub == best_pair_g && top_c > best_pair_c)) break;
      }
      if (dirty_used[top_c] == 0) {
        long g = clean_gain[top_c];
        if (top_ub > g) { h_set_key(top_c, g); continue; }
        if (g > 0 && (best_pair_c < 0 || g > best_pair_g || (g == best_pair_g && top_c < best_pair_c))) {
          best_pair_c = top_c;
          best_pair_g = g;
        }
        break;
      }
      eval_dirty_runs(top_c, 1);
      long g = clean_gain[top_c];
      h_set_key(top_c, g);
      if (g > 0 && (best_pair_c < 0 || g > best_pair_g || (g == best_pair_g && top_c < best_pair_c))) {
        best_pair_c = top_c;
        best_pair_g = g;
      }
    }
    phase1_seconds += now() - tp1;

    // Phase 2: Exact normalized search over non-pair candidates (s_V >= 3).
    double tp2 = now();
    int best_c = best_pair_c;
    long long best_g = best_pair_g;
    long long best_sm1 = 1;

    for (int i = 0; i < ncand; i++) {
      int w = order[i].c;
      if (in_dict[w]) continue;
      long long u = order[i].used;
      if (best_c >= 0) {
        long long lhs = u * best_sm1;
        if (lhs < best_g) {
          pruned_static += (ncand - i);
          break;
        }
        if (lhs == best_g && w > best_c) {
          pruned_static++;
          continue;
        }
      }
      if (closed_in_pool[w]) continue;

      const Cand *cw = &cands[w];
      int p0 = occ[cw->off];
      int s = spelling_of(p0, cw->len, cum);
      if (s <= 2) {
        if (s < 2) continue;
        int g = gain_fast(cw);
        nonpair_full_evals++;
        if (g > 0 && (best_c < 0 || (long long)g * best_sm1 > best_g ||
                      ((long long)g * best_sm1 == best_g && w < best_c))) {
          best_c = w; best_g = g; best_sm1 = 1;
        }
        continue;
      }
      long long sm1 = s - 1;

      // Check dirty-document upper bound first if w was previously activated (O(1) exact bound!).
      if (use_dirty_nonpair && active_in_dirty[w] && best_c >= 0) {
        // Exact upper bound: (clean_gain[w] + dirty_used[w] * sm1) / sm1.
        long long ubg = clean_gain[w] + dirty_used[w] * sm1;
        long long lhs = ubg * best_sm1;
        long long rhs = best_g * sm1;
        if (lhs < rhs || (lhs == rhs && w > best_c)) {
          pruned_dirty_nonpair++;
          continue;
        }
      }

      // Evaluate the U(w) pruning bound: Delta_T(w)/(s-1) <= min_i Delta_T(t_i t_{i+1}) + U(w).
      long long Uw = unaligned[w];
      long long min_pair_ub = cw->nocc;
      int npairs = 0;
      const unsigned char *wstr = text + p0;
      for (int j = 0; j < s - 1; j++) {
        int e = find_candidate(wstr + cum[j], cum[j + 2] - cum[j]);
        if (e >= 0) {
          pair_cids[npairs++] = e;
          long long eub = clean_gain[e] + dirty_used[e];
          if (best_pair_c >= 0 && best_pair_g < eub) eub = best_pair_g;
          if (eub < min_pair_ub) min_pair_ub = eub;
        }
      }

      if (best_c >= 0 && npairs > 0) {
        long long pb = min_pair_ub + Uw;
        if (pb < cw->nocc) pruned_u_vs_nocc++;
        if (pb < u) u_dominance_violations++;
        long long lhs = pb * best_sm1;
        if (lhs < best_g || (lhs == best_g && w > best_c)) {
          pruned_u_fast++;
          continue;
        }
        if (Uw * best_sm1 < best_g || (Uw * best_sm1 == best_g && w > best_c)) {
          int pruned = 0;
          for (int pidx = 0; pidx < npairs; pidx++) {
            int e = pair_cids[pidx];
            if (dirty_used[e] > 0) {
              eval_dirty_runs(e, 1);
              if (h_pos[e] >= 0) h_set_key(e, clean_gain[e]);
            }
            if (clean_gain[e] < min_pair_ub) min_pair_ub = clean_gain[e];
            pb = min_pair_ub + Uw;
            if (pb < u) u_dominance_violations++;
            lhs = pb * best_sm1;
            if (lhs < best_g || (lhs == best_g && w > best_c)) {
              pruned = 1;
              break;
            }
          }
          if (pruned) {
            pruned_u_cleaned++;
            continue;
          }
        }
      }

      long g;
      if (use_dirty_nonpair) {
        eval_dirty_runs(w, 0);
        g = clean_gain[w];
      } else {
        g = gain_fast(cw);
        nonpair_full_evals++;
      }
      if (g <= 0) continue;
      long long lhs = (long long)g * best_sm1;
      long long rhs = best_g * sm1;
      if (best_c < 0 || lhs > rhs || (lhs == rhs && w < best_c)) {
        best_c = w;
        best_g = g;
        best_sm1 = sm1;
      }
    }
    phase2_seconds += now() - tp2;

    if (best_c < 0 || best_g <= 0) break;

    const Cand *picked = &cands[best_c];
    h_remove(best_c);
    in_dict[best_c] = 1;
    accept(picked);

    long rs = c_run_start[best_c];
    int rc = c_run_cnt[best_c];
    for (int idx = 0; idx < rc; idx++) {
      int d = r_doc[rs + idx];
      update_doc_distances_and_u(d, 1);
      mark_doc_dirty_active(d);
    }

    k++;
    bytes += 1 + picked->len;
    const unsigned char *e = text + occ[picked->off];
    write_entry(out, k, bytes, emissions, ndocs, e, picked->len);
    fflush(out);

    for (int i = 0; i < nalpha; i++) {
      offer_closed(e, picked->len, &alpha[i], 1, L, buf);
      offer_closed(&alpha[i], 1, e, picked->len, L, buf);
    }
    for (int m = 0; m < nmembers; m++) {
      const Cand *x = &cands[members[m]];
      const unsigned char *xs = text + occ[x->off];
      offer_closed(e, picked->len, xs, x->len, L, buf);
      offer_closed(xs, x->len, e, picked->len, L, buf);
    }
    offer_closed(e, picked->len, e, picked->len, L, buf);
    members[nmembers++] = best_c;
    step++;
  }
  free(order);
  return 0;
}

int main(int argc, char **argv) {
  if (argc < 7) {
    fprintf(stderr, "usage: engine_norm_pruned POLICY L KMAX LIMIT_SECONDS LIST OUT [--verify-u-every N] [--no-dirty-nonpair]\n");
    return 2;
  }
  int verify_u_every = 0;
  int use_dirty_nonpair = 1;
  for (int a = 7; a < argc; a++) {
    if (!strcmp(argv[a], "--verify-u-every") && a + 1 < argc) {
      verify_u_every = atoi(argv[++a]);
    } else if (!strcmp(argv[a], "--no-dirty-nonpair")) {
      use_dirty_nonpair = 0;
    } else {
      fprintf(stderr, "unknown option %s\n", argv[a]);
      return 2;
    }
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
  if (L < 1 || L > 64) { fprintf(stderr, "L must be 1..64\n"); return 2; }
  load(argv[5]);
  load_side_files();
  if (cut_before) { fprintf(stderr, "requires cuts=none\n"); return 2; }

  double t0 = now();
  enumerate(L);
  double enumerated = now() - t0;
  FILE *out = fopen(argv[6], "w");
  if (!out) { perror(argv[6]); return 2; }
  fprintf(out, "H policy=%s mode=exact-norm-pruned dirty_nonpair=%d L=%d K=%d limit=%s %s\n",
          argv[1], use_dirty_nonpair, L, kmax, argv[4], receipt);
  int stopped = run_norm_pruned(out, L, kmax, limit, verify_u_every, use_dirty_nonpair);
  struct rusage use;
  getrusage(RUSAGE_SELF, &use);
  fprintf(out,
          "D exact-norm-pruned dirty_nonpair=%d L=%d candidates=%d occurrences=%ld runs=%ld stopped=%d "
          "seconds=%.3f enumerate_seconds=%.3f phase1_seconds=%.3f phase2_seconds=%.3f "
          "u_maint_seconds=%.3f u_flips=%ld closed_run_evals=%ld nonpair_run_evals=%ld "
          "nonpair_full_evals=%ld pruned_dirty_nonpair=%ld pruned_u_fast=%ld pruned_u_cleaned=%ld "
          "pruned_u_vs_nocc=%ld u_dominance_violations=%ld pruned_static=%ld maxrss_bytes=%ld\n",
          use_dirty_nonpair, L, ncand, nocc, nruns, stopped, now() - t0, enumerated,
          phase1_seconds, phase2_seconds, u_maint_seconds, u_flips, closed_run_evals,
          nonpair_run_evals, nonpair_full_evals, pruned_dirty_nonpair, pruned_u_fast,
          pruned_u_cleaned, pruned_u_vs_nocc, u_dominance_violations, pruned_static,
          (long)use.ru_maxrss);
  fclose(out);
  return 0;
}
