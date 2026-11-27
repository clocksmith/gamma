// Closure-preserving bundle selection for DEV-BUNDLE.md. Lazy greedy: a heuristic trainer, not exact.
//
// For a fragment w with one minimum V-spelling t_1 ... t_s (the first found by shortest-path search), its bundle
// B(w) is the set of prefixes t_1t_2, t_1t_2t_3, ..., w that are not in V. Each is the concatenation of the previous
// prefix and a member of V, so adding B(w) in prefix order keeps every entry closed. s = 2 gives B = {w}, a pair.
// Score: Delta(B) / |B| (MODE slot) or Delta(B) / sum over B of (1 + |e|) (MODE byte), with Delta(B) the exact drop
// in training tokens from adding all of B at once. Bundles larger than BMAX are not eligible (BMAX = 1 is lazy pair
// selection, the calibration arm).
//
// Heap keys: a never-evaluated candidate is keyed by the bound sum over B of used(e) * (s_V(e) - 1) divided by its
// cost (valid when computed: replace each use of e in an optimal parse by its V-spelling); an evaluated one by its
// last exact score. When an accepted entry e occurs inside a candidate w, w's spelling and bundle may
// have changed, so w is re-keyed (bound if never evaluated, else its last gain over its new cost) if that raises its key. Other stale keys
// are not refreshed, which is why the trainer is lazy and inexact.
//
//   engine_bundle MODE BMAX L KMAX FRAG_BYTE_STOP LIMIT_SECONDS LIST OUT
// Stops at KMAX entries (alphabet included) or when fragment bytes sum(1 + |e|) reach FRAG_BYTE_STOP (0 = no stop).
#define ENGINE_NO_MAIN
#include "../fixed-source-v3/engine.c"

static unsigned char *in_dict;
static int per_byte, bmax;
static int *last_gain, *last_cost, *ver;
static int *dmark, *dlist, dstamp;
static long evaluations, rekeys;

static const unsigned char *str_of(int c) { return text + occ[cands[c].off]; }

// One minimum spelling of text[p : p + l] with the current V: returns s and the prefix lengths cum[0..s-1].
static int spelling(int p, int l, int *cum) {
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
  for (int j = l, n = s; j > 0; j = back[j]) cum[--n] = j;
  return s;
}

// Bundle of candidate c: fills B (prefix order) and returns its size, or -1 if not buildable; *bound gets the
// gain bound and *costp the cost (slots or bytes).
static int bundle_of(int c, int *B, long *bound, int *costp) {
  int cum[72];
  int p = occ[cands[c].off], s = spelling(p, cands[c].len, cum);
  if (s < 2) return -1;
  int nb = 0;
  long bd = 0;
  int cost = 0;
  for (int j = 1; j < s; j++) {  // prefix of j + 1 tokens, length cum[j]
    int e = find_candidate(text + p, cum[j]);
    if (e < 0) return -1;
    if (in_dict[e]) continue;
    B[nb++] = e;
    bd += (long)(cands[e].ub / (cands[e].len - 1)) * j;  // used(e) * (s_V(e) - 1), s_V(e) = j + 1
    cost += per_byte ? 1 + cands[e].len : 1;
  }
  *bound = bd;
  *costp = cost;
  return nb;
}

static int bundle_gain(const int *B, int nb) {
  dstamp++;
  int nd = 0;
  for (int t = 0; t < nb; t++) {
    const Cand *e = &cands[B[t]];
    u64 bit = 1ULL << (e->len - 1);
    for (int i = 0; i < e->nocc; i++) {
      int pos = occ[e->off + i], d = docof[pos];
      mask[pos] |= bit;
      if (dmark[d] != dstamp) { dmark[d] = dstamp; dlist[nd++] = d; }
    }
  }
  int g = 0;
  for (int k = 0; k < nd; k++) g += cost[dlist[k]] - doc_cost(dlist[k]);
  for (int t = 0; t < nb; t++) {
    const Cand *e = &cands[B[t]];
    u64 bit = 1ULL << (e->len - 1);
    for (int i = 0; i < e->nocc; i++) mask[occ[e->off + i]] &= ~bit;
  }
  return g;
}

typedef struct { double key; int c, stamp, ver; } BNode;
static BNode *bh;
static long bh_n, bh_cap;
static inline int b_above(const BNode *a, const BNode *b) { return a->key > b->key || (a->key == b->key && a->c < b->c); }
static void b_push(BNode x) {
  if (bh_n == bh_cap) { bh_cap *= 2; bh = realloc(bh, bh_cap * sizeof(BNode)); }
  long i = bh_n++;
  while (i) { long up = (i - 1) / 2; if (!b_above(&x, &bh[up])) break; bh[i] = bh[up]; i = up; }
  bh[i] = x;
}
static BNode b_pop(void) {
  BNode top = bh[0], x = bh[--bh_n];
  long i = 0;
  for (;;) {
    long a = 2 * i + 1, b = a + 1, m = -1;
    if (a < bh_n) m = a;
    if (b < bh_n && b_above(&bh[b], &bh[a])) m = b;
    if (m < 0 || !b_above(&bh[m], &x)) break;
    bh[i] = bh[m];
    i = m;
  }
  if (bh_n) bh[i] = x;
  return top;
}

static double *cur_key;
static void rekey(int c, double key, int stamp) {
  if (key <= cur_key[c]) return;
  cur_key[c] = key;
  ver[c]++;
  b_push((BNode){key, c, stamp, ver[c]});
  rekeys++;
}

// Every candidate whose string contains an occurrence of e may have a new spelling and bundle: re-key each once.
static int *cmark, cstamp;
static int L_max;
static void rekey_containing(int e, int *B) {
  const Cand *ce = &cands[e];
  cstamp++;
  for (int i = 0; i < ce->nocc; i++) {
    int pos = occ[ce->off + i], d = docof[pos], ds = dstart[d], de = dstart[d] + dlen[d];
    int lo = pos - (L_max - ce->len);
    if (lo < ds) lo = ds;
    for (int st = lo; st <= pos; st++) {
      for (int en = pos + ce->len; en <= st + L_max && en <= de; en++) {
        if (en - st < 2) continue;
        int c = find_candidate(text + st, en - st);
        if (c < 0 || cmark[c] == cstamp || in_dict[c]) continue;
        cmark[c] = cstamp;
        long bd;
        int cst, nb = bundle_of(c, B, &bd, &cst);
        if (nb < 1 || nb > bmax) continue;
        double key = last_gain[c] >= 0 ? (double)last_gain[c] / cst : (double)bd / cst;
        rekey(c, key, -1);
      }
    }
  }
}

int main(int argc, char **argv) {
  if (argc != 9) { fprintf(stderr, "usage: engine_bundle MODE BMAX L KMAX FRAG_BYTE_STOP LIMIT_SECONDS LIST OUT\n"); return 2; }
  const char *receipt = getenv("FSV3_RECEIPT");
  if (!receipt) { fprintf(stderr, "FSV3_RECEIPT required\n"); return 2; }
  if (!strcmp(argv[1], "slot")) per_byte = 0;
  else if (!strcmp(argv[1], "byte")) per_byte = 1;
  else { fprintf(stderr, "MODE is slot or byte\n"); return 2; }
  bmax = atoi(argv[2]);
  int L = atoi(argv[3]), kmax = atoi(argv[4]);
  long byte_stop = atol(argv[5]);
  double limit = atof(argv[6]);
  set_policy("s1-whole");
  load(argv[7]);
  load_side_files();
  double t0 = now();
  enumerate(L);
  FILE *out = fopen(argv[8], "w");
  fprintf(out, "H policy=s1-whole mode=bundle-%s bmax=%d L=%d K=%d frag_byte_stop=%ld limit=%s %s\n", argv[1], bmax, L, kmax, byte_stop, argv[6], receipt);
  int k = 0;
  long bytes = 0;
  add_alphabet(out, &k, &bytes);
  long alpha_bytes = bytes;
  in_dict = calloc(ncand, 1);
  last_gain = xmalloc(ncand * sizeof(int));
  last_cost = xmalloc(ncand * sizeof(int));
  ver = calloc(ncand, sizeof(int));
  cur_key = xmalloc(ncand * sizeof(double));
  dmark = calloc(ndocs, sizeof(int));
  dlist = xmalloc(ndocs * sizeof(int));
  cmark = calloc(ncand, sizeof(int));
  L_max = L;
  for (int c = 0; c < ncand; c++) { last_gain[c] = -1; cur_key[c] = -1.0; }
  bh_cap = 1 << 20;
  bh = xmalloc(bh_cap * sizeof(BNode));
  int B[72];
  for (int c = 0; c < ncand; c++) {
    long bd;
    int cst, nb = bundle_of(c, B, &bd, &cst);
    if (nb < 1 || nb > bmax) continue;
    rekey(c, (double)bd / cst, -1);
  }
  fprintf(stderr, "initial keys: %ld (%.1f s)\n", bh_n, now() - t0);
  int step = 0, stopped = 0;
  double start = now();
  while (k < kmax && bh_n) {
    if (byte_stop > 0 && bytes - alpha_bytes >= byte_stop) break;
    if ((evaluations & 255) == 0 && now() - start > limit) { stopped = 1; break; }
    BNode top = b_pop();
    if (top.ver != ver[top.c] || in_dict[top.c]) continue;
    long bd;
    int cst, nb = bundle_of(top.c, B, &bd, &cst);
    if (nb < 1 || nb > bmax || nb > kmax - k) { cur_key[top.c] = -1.0; continue; }
    if (top.stamp == step) {
      // Evaluated exactly at this step and still on top: accept.
      for (int t = 0; t < nb; t++) {
        const Cand *e = &cands[B[t]];
        accept(e);
        in_dict[B[t]] = 1;
        k++;
        bytes += 1 + e->len;
        write_entry(out, k, bytes, emissions, ndocs, str_of(B[t]), e->len);
      }
      fflush(out);
      int Bc[72];
      memcpy(Bc, B, nb * sizeof(int));
      for (int t = 0; t < nb; t++) rekey_containing(Bc[t], B);
      step++;
      continue;
    }
    int g = bundle_gain(B, nb);
    evaluations++;
    last_gain[top.c] = g;
    last_cost[top.c] = cst;
    cur_key[top.c] = -1.0;
    if (g <= 0) continue;
    double key = (double)g / cst;
    cur_key[top.c] = key;
    ver[top.c]++;
    b_push((BNode){key, top.c, step, ver[top.c]});
  }
  struct rusage use;
  getrusage(RUSAGE_SELF, &use);
  fprintf(out, "D bundle-%s bmax=%d L=%d candidates=%d steps=%d entries=%d stopped=%d seconds=%.1f evaluations=%ld rekeys=%ld maxrss_kb=%ld\n",
          argv[1], bmax, L, ncand, step, k, stopped, now() - t0, evaluations, rekeys, (long)use.ru_maxrss);
  fclose(out);
  return 0;
}
