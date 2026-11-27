// Shared-ancestor closure-preserving bundle selector under exact minimum-token DP.
//
// Features:
//   1. Exact single-pair (|B| = 1) search via dirty-document active-run max-heap:
//      - At b_max = 1, mode = slot: reproduces exact-closed entry for entry.
//      - At b_max = 1, mode = byte: reproduces exact-closed-byte (pair-byte) entry for entry.
//      - At b_max = 1, mode = dag: exact incremental A1AD pair-DAG cost (ties = exact-closed).
//   2. At b_max > 1, genuine shared-ancestor bundle search:
//      - Extracts top high-potential non-closed roots from a monotone upper-bound heap.
//      - Computes optimal binary construction trees via CYK interval DP (both min-cost
//        and ancestor-reuse-weighted trees, deduplicating repeated internal pieces).
//      - Groups roots by shared missing closure ancestors (and top closed-pair anchors)
//        to assemble multi-root bundles charging every unique ancestor ONCE.
//      - Scores every candidate bundle by exact joint minimum-token DP reparsing
//        Delta(B) = c_V(D) - c_{V U B}(D) over exact unique-node bundle cost, with exact
//        64-bit integer cross-multiplication and deterministic tie order
//        (higher exact ratio, smaller |B|, lexicographically smaller sorted candidate ids).
//   3. Logs provenance lines (`B ...` and `P ...`) alongside standard `E ...` lines so
//      downstream evaluation can inspect purchased, shared, emitted, and unused ancestors.
//
// Usage:
//   engine_shared_bundle MODE BMAX L KMAX FRAG_BYTE_STOP DAG_HEADER_STOP LIMIT_SECONDS LIST OUT
//   MODE: slot | byte | dag | flat-header
#define ENGINE_NO_MAIN
#include "../fixed-source-v3/engine.c"
#include <math.h>

enum { PR_SLOT = 0, PR_BYTE = 1, PR_DAG = 2, PR_FLAT_HEADER = 3 };
static int pmode;
static int bmax_glob;
static int L_glob;

static unsigned char *in_dict;
static unsigned char *closed_in_pool;
static int *members, nmembers;

static int *fwd, *bwd;

static long nruns;
static long *c_run_start;
static int *c_run_cnt;
static int *r_cand, *r_doc, *r_used, *r_gain;
static long *r_occ_off;
static int *r_occ_cnt;
static unsigned char *r_dirty;

// Per-doc active run list for closed-pool candidates only.
static long *d_active_head;
static long *r_next_active;

static long *clean_gain, *dirty_used;

// Indexed max-heap for closed pairs (|B| = 1).
static double *h_key;
static int *h_cand;
static int *h_pos;
static int h_n;

// Monotone upper-bound heap for open non-closed roots (used when bmax > 1).
typedef struct { double key; int c, stamp; } ONode;
static ONode *oh;
static int oh_n;

static int *dmark, *dlist, dstamp;
static int *doc_occ_cnt, *doc_single_pos, *doc_single_len;

static long closed_run_evals = 0;
static long bundle_dp_evals = 0;
static long multi_bundle_accepts = 0;
static long multi_bundle_entries = 0;
static long multi_root_accepts = 0;
static long shared_ancestor_nodes_purchased = 0;

static const unsigned char *str_of(int c) { return text + occ[cands[c].off]; }

static inline int bitlen_u(int v) {
  if (v <= 1) return 1;
  return 32 - __builtin_clz((unsigned int)v);
}

// Per-node static cost for slot / byte / flat-header modes.
// For PR_DAG, incremental cost depends on current total node count M (see bundle_cost).
static inline long node_cost_static(int c) {
  if (pmode == PR_SLOT) return 1;
  if (pmode == PR_BYTE) return 1 + cands[c].len;
  if (pmode == PR_FLAT_HEADER) return 2 + cands[c].len;
  return 1;
}

static inline long dag_node_bits_at(int node_idx) {
  // Exact A1AD mode=0 node bits + 8-bit Huffman code-table byte.
  int w = bitlen_u(node_idx > 0 ? node_idx - 1 : 0);
  return 2L * w + 8L;
}

static long bundle_cost(const int *B, int nb, int cur_total_nodes) {
  long tot = 0;
  if (pmode == PR_DAG) {
    for (int i = 0; i < nb; i++) tot += dag_node_bits_at(cur_total_nodes + i);
  } else {
    for (int i = 0; i < nb; i++) tot += node_cost_static(B[i]);
  }
  return tot;
}

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

static inline double closed_ub_key(int c) {
  long ubg = clean_gain[c] + dirty_used[c];
  if (pmode == PR_SLOT || pmode == PR_DAG) return (double)ubg;
  return (double)ubg / (double)node_cost_static(c) + 1e-12;
}

static inline int oh_above(const ONode *a, const ONode *b) {
  return a->key > b->key || (a->key == b->key && a->c < b->c);
}

static void oh_push(ONode x) {
  int i = oh_n++;
  while (i > 0) {
    int up = (i - 1) >> 1;
    if (!oh_above(&x, &oh[up])) break;
    oh[i] = oh[up];
    i = up;
  }
  oh[i] = x;
}

static ONode oh_pop(void) {
  ONode top = oh[0], x = oh[--oh_n];
  int i = 0;
  for (;;) {
    int a = (i << 1) + 1, b = a + 1, m = -1;
    if (a < oh_n) m = a;
    if (b < oh_n && oh_above(&oh[b], &oh[a])) m = b;
    if (m < 0 || !oh_above(&oh[m], &x)) break;
    oh[i] = oh[m];
    i = m;
  }
  if (oh_n) oh[i] = x;
  return top;
}

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

static double open_ub_key(int c) {
  const Cand *x = &cands[c];
  int sm1 = span_cost(occ[x->off], x->len) - 1;
  if (sm1 <= 0) return 0.0;
  long used = x->ub / (x->len - 1);
  // True bundle-cost-normalized upper bound so high-ratio s=3,4 straddled roots
  // and compact shared-ancestor families surface ahead of bloated s=14 strings.
  if (pmode == PR_SLOT || pmode == PR_DAG) {
    // At least sm1 unique merges (or log2 if repeated; use max(1, sm1) for normalized ratio).
    return (double)used;
  }
  // In flat-byte / flat-header mode, building w needs w itself plus at least (sm1 - 1)
  // intermediate ancestors (each >= 3 bytes in flat-byte, >= 4 bytes in flat-header).
  long anc_lb = (pmode == PR_FLAT_HEADER ? 4L : 3L) * (long)(sm1 - 1);
  long cost_lb = node_cost_static(c) + anc_lb;
  return (double)(used * (long)sm1) / (double)cost_lb;
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

static void build_runs(void) {
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

static void eval_dirty_runs(int c) {
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
    closed_run_evals++;
  }
}

static void mark_doc_dirty_closed(int d) {
  for (long r = d_active_head[d]; r >= 0; r = r_next_active[r]) {
    if (r_dirty[r]) continue;
    int c = r_cand[r];
    if (in_dict[c]) continue;
    r_dirty[r] = 1;
    clean_gain[c] -= r_gain[r];
    dirty_used[c] += r_used[r];
    if (h_pos[c] >= 0) h_set_key(c, closed_ub_key(c));
  }
}

static void offer_closed(const unsigned char *a, int la, const unsigned char *b, int lb, int L, unsigned char *buf) {
  if (la + lb > L) return;
  memcpy(buf, a, (size_t)la);
  memcpy(buf + la, b, (size_t)lb);
  int c = find_candidate(buf, la + lb);
  if (c < 0 || in_dict[c] || closed_in_pool[c]) return;
  closed_in_pool[c] = 1;
  long rs = c_run_start[c];
  int rc = c_run_cnt[c];
  for (int idx = 0; idx < rc; idx++) {
    long r = rs + idx;
    int d = r_doc[r];
    r_next_active[r] = d_active_head[d];
    d_active_head[d] = r;
  }
  h_set_key(c, closed_ub_key(c));
}

// Exact joint minimum-token DP token reduction from adding all unique nodes B[0..nb-1] to V.
static long bundle_gain_exact(const int *B, int nb) {
  bundle_dp_evals++;
  dstamp++;
  int nd = 0;
  for (int t = 0; t < nb; t++) {
    const Cand *e = &cands[B[t]];
    u64 bit = 1ULL << (e->len - 1);
    for (int i = 0; i < e->nocc; i++) {
      int pos = occ[e->off + i];
      int d = docof[pos];
      mask[pos] |= bit;
      if (dmark[d] != dstamp) {
        dmark[d] = dstamp;
        dlist[nd++] = d;
        doc_occ_cnt[d] = 1;
        doc_single_pos[d] = pos;
        doc_single_len[d] = e->len;
      } else {
        doc_occ_cnt[d]++;
      }
    }
  }
  long g = 0;
  for (int k = 0; k < nd; k++) {
    int d = dlist[k];
    if (doc_occ_cnt[d] == 1) {
      int p = doc_single_pos[d], base = dstart[d] + d, off = p - dstart[d];
      int alt = fwd[base + off] + 1 + bwd[base + off + doc_single_len[d]];
      if (alt < cost[d]) g += cost[d] - alt;
    } else {
      g += cost[d] - doc_cost(d);
    }
  }
  for (int t = 0; t < nb; t++) {
    const Cand *e = &cands[B[t]];
    u64 bit = 1ULL << (e->len - 1);
    for (int i = 0; i < e->nocc; i++) mask[occ[e->off + i]] &= ~bit;
  }
  return g;
}

// Exact deterministic bundle comparison:
// 1) higher exact rational gain/cost (64-bit integer cross-multiplication)
// 2) smaller bundle size |B| (so single pairs win exact ties)
// 3) lexicographically smaller sorted candidate-id sequence
typedef struct {
  int nb;
  int nroots;
  long gain;
  long cost;
  int nodes[64];       // topological order (children before parent)
  int sorted_ids[64];  // sorted ascending for deterministic tie order
  int roots[64];       // root candidate ids
  unsigned char is_root[64];
} Bundle;

static int cmp_int_asc(const void *a, const void *b) {
  int x = *(const int *)a, y = *(const int *)b;
  return (x > y) - (x < y);
}

static void finalize_bundle_order(Bundle *b) {
  // Topological sort by increasing string length (guarantees every shorter constituent precedes parent).
  for (int i = 1; i < b->nb; i++) {
    int key = b->nodes[i];
    unsigned char kr = b->is_root[i];
    int kl = cands[key].len;
    int j = i - 1;
    while (j >= 0 && (cands[b->nodes[j]].len > kl || (cands[b->nodes[j]].len == kl && b->nodes[j] > key))) {
      b->nodes[j + 1] = b->nodes[j];
      b->is_root[j + 1] = b->is_root[j];
      j--;
    }
    b->nodes[j + 1] = key;
    b->is_root[j + 1] = kr;
  }
  memcpy(b->sorted_ids, b->nodes, (size_t)b->nb * sizeof(int));
  qsort(b->sorted_ids, (size_t)b->nb, sizeof(int), cmp_int_asc);
}

static int bundle_better(const Bundle *a, const Bundle *b) {
  if (a->gain <= 0) return 0;
  if (b->nb == 0 || b->gain <= 0) return 1;
  __int128 lhs = (__int128)a->gain * (__int128)b->cost;
  __int128 rhs = (__int128)b->gain * (__int128)a->cost;
  if (lhs != rhs) return lhs > rhs;
  if (a->nb != b->nb) return a->nb < b->nb;
  for (int i = 0; i < a->nb; i++) {
    if (a->sorted_ids[i] != b->sorted_ids[i]) return a->sorted_ids[i] < b->sorted_ids[i];
  }
  return 0;
}

static int bundle_contains(const int *arr, int n, int c) {
  for (int i = 0; i < n; i++) if (arr[i] == c) return 1;
  return 0;
}

// CYK optimal binary merge tree for candidate w (length l <= 16).
// mode_weight = 0: pure min-cost binary tree (tie-break by higher internal ancestor reuse).
// mode_weight = 1: ancestor-reuse-weighted binary tree (prefers frequent shared substrings).
static void collect_cyk(int i, int j, int split[17][17], int sub_cid[17][17], int *out, int *nout, int max_n) {
  int c = sub_cid[i][j];
  if (c < 0) return;  // leaf or already in V
  int m = split[i][j];
  if (m > i && m < j) {
    collect_cyk(i, m, split, sub_cid, out, nout, max_n);
    collect_cyk(m, j, split, sub_cid, out, nout, max_n);
  }
  if (!bundle_contains(out, *nout, c) && *nout < max_n) out[(*nout)++] = c;
}

static int cyk_tree_for(int w, int mode_weight, int *out_nodes, int max_n) {
  const Cand *cw = &cands[w];
  const unsigned char *s = text + occ[cw->off];
  int l = cw->len;
  int sub_cid[17][17];
  double dp[17][17];
  int split[17][17];

  for (int i = 0; i < l; i++) {
    for (int j = i + 1; j <= l; j++) {
      int sl = j - i;
      split[i][j] = -1;
      if (sl == 1) {
        sub_cid[i][j] = -2;  // single-byte leaf in V
        dp[i][j] = 0.0;
      } else {
        int c = find_candidate(s + i, sl);
        if (c < 0) {
          sub_cid[i][j] = -1;  // ineligible
          dp[i][j] = 1e18;
        } else if (in_dict[c]) {
          sub_cid[i][j] = -2;  // already in V
          dp[i][j] = 0.0;
        } else {
          sub_cid[i][j] = c;
          dp[i][j] = 1e18;
        }
      }
    }
  }

  for (int sl = 2; sl <= l; sl++) {
    for (int i = 0; i + sl <= l; i++) {
      int j = i + sl;
      int c = sub_cid[i][j];
      if (c < 0) continue;  // -2 already 0, -1 ineligible
      double base_c = (pmode == PR_BYTE || pmode == PR_FLAT_HEADER) ? (double)node_cost_static(c) : 1.0;
      double used = (double)(cands[c].ub / (cands[c].len - 1));
      double wcost;
      if (mode_weight == 0) {
        wcost = base_c - 1e-6 * log2(1.0 + used);
      } else {
        wcost = base_c / (1.0 + 0.5 * log2(1.0 + used));
      }
      double best_v = 1e18;
      int best_m = -1;
      for (int m = i + 1; m < j; m++) {
        if (dp[i][m] >= 1e17 || dp[m][j] >= 1e17) continue;
        double v = wcost + dp[i][m] + dp[m][j];
        if (v < best_v) { best_v = v; best_m = m; }
      }
      dp[i][j] = best_v;
      split[i][j] = best_m;
    }
  }

  if (dp[0][l] >= 1e17) return -1;
  int nb = 0;
  collect_cyk(0, l, split, sub_cid, out_nodes, &nb, max_n);
  if (nb < 1 || nb > max_n) return -1;
  // Verify closure: every node must be a pair of earlier/in_dict/single-byte pieces.
  for (int t = 0; t < nb; t++) {
    int c = out_nodes[t];
    const unsigned char *cs = str_of(c);
    int cl = cands[c].len;
    int ok = 0;
    for (int sp = 1; sp < cl; sp++) {
      int lok = (sp == 1);
      if (!lok) {
        int lc = find_candidate(cs, sp);
        lok = (lc >= 0 && (in_dict[lc] || bundle_contains(out_nodes, t, lc)));
      }
      if (!lok) continue;
      int rok = (cl - sp == 1);
      if (!rok) {
        int rc = find_candidate(cs + sp, cl - sp);
        rok = (rc >= 0 && (in_dict[rc] || bundle_contains(out_nodes, t, rc)));
      }
      if (rok) { ok = 1; break; }
    }
    if (!ok) return -1;
  }
  return nb;
}

static int find_split_in_dict(int c, unsigned char *left_hex, unsigned char *right_hex) {
  const unsigned char *s = str_of(c);
  int l = cands[c].len;
  for (int sp = 1; sp < l; sp++) {
    int lok = (sp == 1);
    if (!lok) {
      int lc = find_candidate(s, sp);
      lok = (lc >= 0 && in_dict[lc]);
    }
    if (!lok) continue;
    int rok = (l - sp == 1);
    if (!rok) {
      int rc = find_candidate(s + sp, l - sp);
      rok = (rc >= 0 && in_dict[rc]);
    }
    if (rok) {
      for (int i = 0; i < sp; i++) sprintf((char *)left_hex + 2 * i, "%02x", s[i]);
      left_hex[2 * sp] = 0;
      for (int i = 0; i < l - sp; i++) sprintf((char *)right_hex + 2 * i, "%02x", s[sp + i]);
      right_hex[2 * (l - sp)] = 0;
      return 1;
    }
  }
  return 0;
}

static long estimate_dag_header_bytes(int total_nodes, int alpha_n) {
  // Exact A1AD mode=0 header bytes: 4 magic + 1 flags + varint(M) + varint(A) + A leaves
  // + ceil(sum_{i=A}^{M-1} 2*bitlen(i-1) / 8) + (M + 2) table bytes.
  long vm = total_nodes < 128 ? 1 : (total_nodes < 16384 ? 2 : 3);
  long va = alpha_n < 128 ? 1 : 2;
  long dag_bits = 0;
  for (int i = alpha_n; i < total_nodes; i++) {
    dag_bits += 2L * bitlen_u(i > 0 ? i - 1 : 0);
  }
  return 4 + 1 + vm + va + alpha_n + ((dag_bits + 7) >> 3) + (total_nodes + 2);
}

typedef struct {
  int root_c;
  double ub_score;
  int nb;
  int nodes[32];
} RootTree;

typedef struct {
  int anc_c;
  int nroots;
  double score_sum;
  int root_idxs[64];
} AnchorGroup;

static int cmp_anchor_desc(const void *a, const void *b) {
  const AnchorGroup *x = (const AnchorGroup *)a, *y = (const AnchorGroup *)b;
  if (x->score_sum != y->score_sum) return x->score_sum > y->score_sum ? -1 : 1;
  if (x->nroots != y->nroots) return x->nroots > y->nroots ? -1 : 1;
  return x->anc_c - y->anc_c;
}

static int run_shared_bundle(FILE *out, int L, int kmax, long frag_byte_stop, long dag_header_stop, double limit) {
  int k = 0;
  long bytes = 0;
  add_alphabet(out, &k, &bytes);
  int alpha_n = k;
  long alpha_bytes = bytes;
  double start = now();

  fwd = xmalloc((size_t)(total + ndocs) * sizeof(int));
  bwd = xmalloc((size_t)(total + ndocs) * sizeof(int));
  for (int d = 0; d < ndocs; d++) doc_distances(d);

  build_runs();

  in_dict = calloc((size_t)ncand, 1);
  closed_in_pool = calloc((size_t)ncand, 1);
  members = xmalloc((size_t)(kmax + 512) * sizeof(int));
  h_key = xmalloc((size_t)(ncand + 1) * sizeof(double));
  h_cand = xmalloc((size_t)(ncand + 1) * sizeof(int));
  h_pos = xmalloc((size_t)ncand * sizeof(int));
  for (int c = 0; c < ncand; c++) h_pos[c] = -1;

  dmark = calloc((size_t)ndocs, sizeof(int));
  dlist = xmalloc((size_t)ndocs * sizeof(int));
  doc_occ_cnt = calloc((size_t)ndocs, sizeof(int));
  doc_single_pos = xmalloc((size_t)ndocs * sizeof(int));
  doc_single_len = xmalloc((size_t)ndocs * sizeof(int));

  unsigned char *buf = xmalloc((size_t)(2 * L + 2));
  unsigned char alpha[256];
  int nalpha = 0;
  for (int c = 0; c < 256; c++)
    if (present[c]) alpha[nalpha++] = (unsigned char)c;

  for (int i = 0; i < nalpha; i++)
    for (int j = 0; j < nalpha; j++)
      offer_closed(&alpha[i], 1, &alpha[j], 1, L, buf);

  if (bmax_glob > 1) {
    oh = xmalloc((size_t)(ncand + 1) * sizeof(ONode));
    oh_n = 0;
    for (int c = 0; c < ncand; c++) {
      double k0 = open_ub_key(c);
      if (k0 > 0.0) oh_push((ONode){k0, c, -1});
    }
  }

  int *tie_buf = xmalloc((size_t)(ncand + 1) * sizeof(int));
  double *tie_key = xmalloc((size_t)(ncand + 1) * sizeof(double));
  ONode *oh_held = bmax_glob > 1 ? xmalloc(256 * sizeof(ONode)) : NULL;

  int step = 0;
  int stopped = 0;
  while (k < kmax) {
    if (frag_byte_stop > 0 && bytes - alpha_bytes >= frag_byte_stop) break;
    if (dag_header_stop > 0 && estimate_dag_header_bytes(k, alpha_n) >= dag_header_stop) break;
    if ((step & 7) == 0 && now() - start > limit) { stopped = 1; break; }

    // ------------------------------------------------------------------
    // Phase 1: Exact best single closed pair (|B| = 1).
    // ------------------------------------------------------------------
    int best_pair_c = -1;
    long best_pair_g = 0;
    long best_pair_cost = 1;
    double best_pair_dbl = 0.0;

    while (h_n > 0) {
      int top_c = h_cand[0];
      double top_ub = h_key[0];
      if (best_pair_c >= 0) {
        if (top_ub < best_pair_dbl - 1e-13) break;
        if (pmode == PR_SLOT || pmode == PR_DAG) {
          long iub = (long)top_ub;
          if (iub < best_pair_g || (iub == best_pair_g && top_c > best_pair_c)) break;
        }
      }
      if (dirty_used[top_c] == 0) {
        long g = clean_gain[top_c];
        long cst = node_cost_static(top_c);
        double ex = (pmode == PR_SLOT || pmode == PR_DAG) ? (double)g : (double)g / (double)cst;
        if (top_ub > ex) { h_set_key(top_c, ex); continue; }
        if (g > 0) {
          int better = (best_pair_c < 0);
          if (!better) {
            long long lhs = (long long)g * best_pair_cost;
            long long rhs = (long long)best_pair_g * cst;
            if (lhs != rhs) better = (lhs > rhs);
            else better = (top_c < best_pair_c);
          }
          if (better) {
            best_pair_c = top_c; best_pair_g = g; best_pair_cost = cst; best_pair_dbl = ex;
          }
        }
        if (pmode == PR_SLOT || pmode == PR_DAG) break;
      }
      if (dirty_used[top_c] > 0) {
        eval_dirty_runs(top_c);
        long g = clean_gain[top_c];
        long cst = node_cost_static(top_c);
        double ex = (pmode == PR_SLOT || pmode == PR_DAG) ? (double)g : (double)g / (double)cst;
        h_set_key(top_c, ex);
        if (g > 0) {
          int better = (best_pair_c < 0);
          if (!better) {
            long long lhs = (long long)g * best_pair_cost;
            long long rhs = (long long)best_pair_g * cst;
            if (lhs != rhs) better = (lhs > rhs);
            else better = (top_c < best_pair_c);
          }
          if (better) {
            best_pair_c = top_c; best_pair_g = g; best_pair_cost = cst; best_pair_dbl = ex;
          }
        }
        continue;
      }
      break;
    }

    if ((pmode == PR_BYTE || pmode == PR_FLAT_HEADER) && h_n > 0) {
      int ntie = 0;
      while (h_n > 0 && (best_pair_c < 0 || h_key[0] >= best_pair_dbl - 1e-11)) {
        int c = h_cand[0];
        if (dirty_used[c] > 0) eval_dirty_runs(c);
        long g = clean_gain[c];
        long cst = node_cost_static(c);
        double ex = (double)g / (double)cst;
        h_remove(c);
        tie_buf[ntie] = c;
        tie_key[ntie++] = ex;
        if (g > 0) {
          int better = (best_pair_c < 0);
          if (!better) {
            long long lhs = (long long)g * best_pair_cost;
            long long rhs = (long long)best_pair_g * cst;
            if (lhs != rhs) better = (lhs > rhs);
            else better = (c < best_pair_c);
          }
          if (better) {
            best_pair_c = c; best_pair_g = g; best_pair_cost = cst; best_pair_dbl = ex;
          }
        }
      }
      for (int i = 0; i < ntie; i++) h_set_key(tie_buf[i], tie_key[i]);
    }

    Bundle best_b;
    memset(&best_b, 0, sizeof(best_b));
    if (best_pair_c >= 0 && best_pair_g > 0) {
      best_b.nb = 1;
      best_b.nroots = 1;
      best_b.nodes[0] = best_pair_c;
      best_b.roots[0] = best_pair_c;
      best_b.is_root[0] = 1;
      best_b.gain = best_pair_g;
      best_b.cost = bundle_cost(best_b.nodes, 1, k);
      finalize_bundle_order(&best_b);
    }

    // ------------------------------------------------------------------
    // Phase 2: Shared-Ancestor Multi-Node Bundles (when bmax > 1).
    // ------------------------------------------------------------------
    int max_b = bmax_glob;
    if (kmax - k < max_b) max_b = kmax - k;
    if (max_b > 32) max_b = 32;

    if (bmax_glob > 1 && max_b >= 2 && best_b.nb > 0) {
      const int TOP_ROOTS = 32;
      RootTree rtrees[72];
      int nrt = 0;
      int nheld = 0;

      // Extract top non-closed roots from monotone bundle-ratio open heap.
      double pair_ratio = (double)best_b.gain / (double)best_b.cost;
      int rekey_budget = 512;
      while (oh_n > 0 && nrt < TOP_ROOTS && rekey_budget > 0) {
        ONode top = oh_pop();
        if (in_dict[top.c]) continue;
        if (closed_in_pool[top.c]) {
          // Already evaluated in Phase 1; drop from open root heap.
          continue;
        }
        if (top.stamp != step) {
          rekey_budget--;
          top.key = open_ub_key(top.c);
          top.stamp = step;
          if (top.key <= 0.0) continue;
          if (oh_n > 0 && oh_above(&oh[0], &top)) {
            oh_push(top);
            continue;
          }
        }
        oh_held[nheld++] = top;
        if (top.key < 0.35 * pair_ratio && nrt >= 8) break;

        // Build optimal CYK trees (min-cost and reuse-weighted) for this root.
        int tnodes[32];
        int nb0 = cyk_tree_for(top.c, 0, tnodes, max_b);
        if (nb0 >= 2 && nb0 <= max_b && nrt < 70) {
          rtrees[nrt].root_c = top.c;
          rtrees[nrt].ub_score = top.key;
          rtrees[nrt].nb = nb0;
          memcpy(rtrees[nrt].nodes, tnodes, (size_t)nb0 * sizeof(int));
          nrt++;

          // Score single-root CYK bundle exactly.
          Bundle cand_b;
          memset(&cand_b, 0, sizeof(cand_b));
          cand_b.nb = nb0;
          cand_b.nroots = 1;
          cand_b.roots[0] = top.c;
          for (int i = 0; i < nb0; i++) {
            cand_b.nodes[i] = tnodes[i];
            cand_b.is_root[i] = (tnodes[i] == top.c) ? 1 : 0;
          }
          cand_b.cost = bundle_cost(cand_b.nodes, cand_b.nb, k);
          cand_b.gain = bundle_gain_exact(cand_b.nodes, cand_b.nb);
          finalize_bundle_order(&cand_b);
          if (bundle_better(&cand_b, &best_b)) best_b = cand_b;
        }

        int tnodes1[32];
        int nb1 = cyk_tree_for(top.c, 1, tnodes1, max_b);
        if (nb1 >= 2 && nb1 <= max_b) {
          int same = (nb1 == nb0);
          if (same) {
            for (int i = 0; i < nb1; i++) if (!bundle_contains(tnodes, nb0, tnodes1[i])) { same = 0; break; }
          }
          if (!same && nrt < 70) {
            rtrees[nrt].root_c = top.c;
            rtrees[nrt].ub_score = top.key;
            rtrees[nrt].nb = nb1;
            memcpy(rtrees[nrt].nodes, tnodes1, (size_t)nb1 * sizeof(int));
            nrt++;

            Bundle cand_b;
            memset(&cand_b, 0, sizeof(cand_b));
            cand_b.nb = nb1;
            cand_b.nroots = 1;
            cand_b.roots[0] = top.c;
            for (int i = 0; i < nb1; i++) {
              cand_b.nodes[i] = tnodes1[i];
              cand_b.is_root[i] = (tnodes1[i] == top.c) ? 1 : 0;
            }
            cand_b.cost = bundle_cost(cand_b.nodes, cand_b.nb, k);
            cand_b.gain = bundle_gain_exact(cand_b.nodes, cand_b.nb);
            finalize_bundle_order(&cand_b);
            if (bundle_better(&cand_b, &best_b)) best_b = cand_b;
          }
        }
      }
      for (int i = 0; i < nheld; i++) oh_push(oh_held[i]);

      // Group roots by shared missing ancestors (charged ONCE across co-purchased roots).
      AnchorGroup groups[256];
      int ngroups = 0;
      for (int r = 0; r < nrt; r++) {
        for (int t = 0; t < rtrees[r].nb; t++) {
          int a = rtrees[r].nodes[t];
          if (a == rtrees[r].root_c) continue;  // strictly an ancestor of root r
          int gidx = -1;
          for (int g = 0; g < ngroups; g++) if (groups[g].anc_c == a) { gidx = g; break; }
          if (gidx < 0) {
            if (ngroups >= 256) continue;
            gidx = ngroups++;
            groups[gidx].anc_c = a;
            groups[gidx].nroots = 0;
            groups[gidx].score_sum = 0.0;
          }
          // Avoid adding the same root_c twice to one anchor group.
          int dup = 0;
          for (int q = 0; q < groups[gidx].nroots; q++) {
            if (rtrees[groups[gidx].root_idxs[q]].root_c == rtrees[r].root_c) { dup = 1; break; }
          }
          if (!dup && groups[gidx].nroots < 64) {
            groups[gidx].root_idxs[groups[gidx].nroots++] = r;
            groups[gidx].score_sum += rtrees[r].ub_score;
          }
        }
      }

      // Filter to true shared ancestors (>= 2 distinct roots sharing missing ancestor a).
      int nshared = 0;
      for (int g = 0; g < ngroups; g++) {
        if (groups[g].nroots >= 2) groups[nshared++] = groups[g];
      }
      qsort(groups, (size_t)nshared, sizeof(AnchorGroup), cmp_anchor_desc);

      const int MAX_ANCHORS = 12;
      int try_anchors = nshared < MAX_ANCHORS ? nshared : MAX_ANCHORS;
      for (int g = 0; g < try_anchors; g++) {
        int anc = groups[g].anc_c;
        // Initialize bundle with anchor's own closure (or {anc} if already closed).
        Bundle cur;
        memset(&cur, 0, sizeof(cur));
        if (closed_in_pool[anc]) {
          cur.nodes[0] = anc;
          cur.nb = 1;
        } else {
          int an = cyk_tree_for(anc, 0, cur.nodes, max_b);
          if (an < 1 || an >= max_b) continue;
          cur.nb = an;
        }
        cur.cost = bundle_cost(cur.nodes, cur.nb, k);
        cur.gain = bundle_gain_exact(cur.nodes, cur.nb);

        unsigned char used_root[64];
        memset(used_root, 0, sizeof(used_root));
        int added_roots = 0;

        // Greedily co-purchase roots sharing this anchor, pricing shared nodes ONCE.
        while (cur.nb < max_b && added_roots < 6) {
          int pick_r = -1;
          Bundle pick_b;
          memset(&pick_b, 0, sizeof(pick_b));
          double best_joint = -1.0;

          int checked_here = 0;
          for (int q = 0; q < groups[g].nroots && checked_here < 6; q++) {
            if (used_root[q]) continue;
            int ridx = groups[g].root_idxs[q];
            const RootTree *rt = &rtrees[ridx];
            Bundle trial = cur;
            int fits = 1;
            for (int t = 0; t < rt->nb; t++) {
              int u = rt->nodes[t];
              if (!bundle_contains(trial.nodes, trial.nb, u)) {
                if (trial.nb >= max_b) { fits = 0; break; }
                trial.nodes[trial.nb] = u;
                trial.is_root[trial.nb] = (u == rt->root_c) ? 1 : 0;
                trial.nb++;
              } else if (u == rt->root_c) {
                for (int z = 0; z < trial.nb; z++) if (trial.nodes[z] == u) trial.is_root[z] = 1;
              }
            }
            if (!fits || trial.nb == cur.nb) continue;
            checked_here++;
            trial.roots[trial.nroots++] = rt->root_c;
            trial.cost = bundle_cost(trial.nodes, trial.nb, k);
            trial.gain = bundle_gain_exact(trial.nodes, trial.nb);
            finalize_bundle_order(&trial);
            if (bundle_better(&trial, &best_b)) best_b = trial;

            double jr = (double)trial.gain / (double)trial.cost;
            if (jr > best_joint) {
              best_joint = jr;
              pick_r = q;
              pick_b = trial;
            }
          }
          if (pick_r < 0) break;
          // Keep growing if joint score improved over cur or stays competitive with pair_ratio.
          double cur_r = (double)cur.gain / (double)cur.cost;
          if (added_roots >= 1 && best_joint <= cur_r && best_joint < 0.90 * pair_ratio) break;
          used_root[pick_r] = 1;
          cur = pick_b;
          added_roots++;
        }
      }
    }

    if (best_b.nb == 0 || best_b.gain <= 0) break;

    // Emit provenance line for multi-node bundles (and track stats).
    if (best_b.nb > 1) {
      multi_bundle_accepts++;
      multi_bundle_entries += best_b.nb;
      if (best_b.nroots > 1) multi_root_accepts++;
      int nanc = 0;
      for (int t = 0; t < best_b.nb; t++) if (!best_b.is_root[t]) nanc++;
      if (best_b.nroots > 1) shared_ancestor_nodes_purchased += nanc;
      fprintf(out, "B step=%d size=%d roots=%d ancestors=%d gain=%ld cost=%ld nodes=",
              step, best_b.nb, best_b.nroots, nanc, best_b.gain, best_b.cost);
      for (int t = 0; t < best_b.nb; t++) {
        if (t) fputc(',', out);
        const Cand *ce = &cands[best_b.nodes[t]];
        const unsigned char *cs = str_of(best_b.nodes[t]);
        fprintf(out, "%c:", best_b.is_root[t] ? 'R' : 'A');
        for (int j = 0; j < ce->len; j++) fprintf(out, "%02x", cs[j]);
      }
      fputc('\n', out);
    }

    // Accept all nodes of best_b in topological order (guaranteed closed at every prefix).
    unsigned char lhex[64], rhex[64];
    for (int t = 0; t < best_b.nb; t++) {
      int cid = best_b.nodes[t];
      const Cand *c = &cands[cid];
      if (!find_split_in_dict(cid, lhex, rhex)) {
        fprintf(stderr, "CLOSURE VIOLATION at step %d cand %d\n", step, cid);
        return 3;
      }
      h_remove(cid);
      in_dict[cid] = 1;
      accept(c);

      long rs = c_run_start[cid];
      int rc = c_run_cnt[cid];
      for (int idx = 0; idx < rc; idx++) {
        int d = r_doc[rs + idx];
        doc_distances(d);
        mark_doc_dirty_closed(d);
      }

      k++;
      bytes += 1 + c->len;
      const unsigned char *e = str_of(cid);
      fprintf(out, "P %s %s ", lhex, rhex);
      for (int j = 0; j < c->len; j++) fprintf(out, "%02x", e[j]);
      fputc('\n', out);
      write_entry(out, k, bytes, emissions, ndocs, e, c->len);

      for (int i = 0; i < nalpha; i++) {
        offer_closed(e, c->len, &alpha[i], 1, L, buf);
        offer_closed(&alpha[i], 1, e, c->len, L, buf);
      }
      for (int m = 0; m < nmembers; m++) {
        const Cand *x = &cands[members[m]];
        const unsigned char *xs = str_of(members[m]);
        offer_closed(e, c->len, xs, x->len, L, buf);
        offer_closed(xs, x->len, e, c->len, L, buf);
      }
      offer_closed(e, c->len, e, c->len, L, buf);
      members[nmembers++] = cid;
    }
    fflush(out);
    step++;
  }

  free(tie_buf);
  free(tie_key);
  if (oh_held) free(oh_held);
  return stopped;
}

int main(int argc, char **argv) {
  if (argc != 10) {
    fprintf(stderr,
            "usage: engine_shared_bundle MODE BMAX L KMAX FRAG_BYTE_STOP DAG_HEADER_STOP LIMIT_SECONDS LIST OUT\n");
    return 2;
  }
  const char *mode = argv[1];
  if (!strcmp(mode, "slot")) pmode = PR_SLOT;
  else if (!strcmp(mode, "byte")) pmode = PR_BYTE;
  else if (!strcmp(mode, "dag")) pmode = PR_DAG;
  else if (!strcmp(mode, "flat-header")) pmode = PR_FLAT_HEADER;
  else { fprintf(stderr, "unknown mode %s (slot|byte|dag|flat-header)\n", mode); return 2; }

  const char *receipt = getenv("FSV3_RECEIPT");
  if (!receipt || !strstr(receipt, "manifest=") || !strstr(receipt, "pool=") ||
      !strstr(receipt, "cuts=") || !strstr(receipt, "impl=") || !strstr(receipt, "run=")) {
    fprintf(stderr, "FSV3_RECEIPT must bind manifest, pool, cuts, impl and run\n");
    return 2;
  }
  bmax_glob = atoi(argv[2]);
  int L = atoi(argv[3]);
  int kmax = atoi(argv[4]);
  long frag_byte_stop = atol(argv[5]);
  long dag_header_stop = atol(argv[6]);
  double limit = atof(argv[7]);
  if (bmax_glob < 1 || L < 1 || L > 64) { fprintf(stderr, "bad BMAX or L\n"); return 2; }
  L_glob = L;

  set_policy("s1-whole");
  load(argv[8]);
  load_side_files();
  if (cut_before) { fprintf(stderr, "requires cuts=none\n"); return 2; }

  double t0 = now();
  enumerate(L);
  double enumerated = now() - t0;
  FILE *out = fopen(argv[9], "w");
  if (!out) { perror(argv[9]); return 2; }
  fprintf(out, "H policy=s1-whole mode=shared-bundle-%s bmax=%d L=%d K=%d frag_byte_stop=%ld dag_header_stop=%ld limit=%s %s\n",
          mode, bmax_glob, L, kmax, frag_byte_stop, dag_header_stop, argv[7], receipt);
  int stopped = run_shared_bundle(out, L, kmax, frag_byte_stop, dag_header_stop, limit);
  struct rusage use;
  getrusage(RUSAGE_SELF, &use);
  fprintf(out,
          "D shared-bundle-%s bmax=%d L=%d candidates=%d occurrences=%ld runs=%ld stopped=%d "
          "seconds=%.3f enumerate_seconds=%.3f closed_run_evals=%ld bundle_dp_evals=%ld "
          "multi_bundle_accepts=%ld multi_bundle_entries=%ld multi_root_accepts=%ld "
          "shared_ancestor_nodes=%ld maxrss_bytes=%ld\n",
          mode, bmax_glob, L, ncand, nocc, nruns, stopped, now() - t0, enumerated,
          closed_run_evals, bundle_dp_evals, multi_bundle_accepts, multi_bundle_entries,
          multi_root_accepts, shared_ancestor_nodes_purchased, (long)use.ru_maxrss);
  fclose(out);
  return stopped == 3 ? 3 : 0;
}
