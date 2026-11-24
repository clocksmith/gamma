// Fixed-source vocabulary search v2 (FREEZE.md). Reads a list of source files,
// builds one nested chain of dictionaries, and writes it to a private file.
//   engine MODE POLICY L KMAX LIMIT_SECONDS LIST_FILE OUT_FILE [SEED_CHAIN]
// MODE: greedy-entry greedy-byte freq-occ freq-doc bpe
//       cover-mixed cover-nosingle polish
// POLICY: s1-whole   any observed substring, whole files allowed (primary)
//         s1-nowhole any observed substring, no multibyte whole file (isolation)
//         s2-nowhole in two files, no multibyte whole file (historical control)
// FSV2_RECEIPT must hold the run's manifest, pool, implementation and run id.
// The first line of the chain binds them:
//   H policy=<p> mode=<m> L=<L> K=<K> limit=<s> <FSV2_RECEIPT>
// Chain file, one line per dictionary entry in the order added:
//   E <entries> <stored bytes> <total emissions, or -1 if not all spelled>
//     <files spelled> <hex of the entry>
// BPE chains also carry M <left hex> <right hex> before each merge, so the
// checker can replay the ordinary segmentation.
// The checker (verify.py) shares no code with this file.
#define _GNU_SOURCE
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/resource.h>
#include <time.h>

typedef uint64_t u64;
enum { INF = 1 << 29 };

static unsigned char *text;
static int total, ndocs;
static int *dstart, *dlen, *docof;
static u64 *mask;
static int *best;
static int min_docs = 2, allow_whole = 0;

static int set_policy(const char *name) {
  if (!strcmp(name, "s1-whole")) { min_docs = 1; allow_whole = 1; return 1; }
  if (!strcmp(name, "s1-nowhole")) { min_docs = 1; allow_whole = 0; return 2; }
  if (!strcmp(name, "s2-nowhole")) { min_docs = 2; allow_whole = 0; return 3; }
  fprintf(stderr, "unknown policy\n");
  exit(2);
}

typedef struct { int len, nocc, off, ub, docs; } Cand;
static Cand *cands;
static int ncand, capcand;
static int *occ;
static long nocc, capocc;

static double now(void) {
  struct timespec t;
  clock_gettime(CLOCK_MONOTONIC, &t);
  return t.tv_sec + t.tv_nsec * 1e-9;
}

static void *xmalloc(size_t n) {
  void *p = malloc(n ? n : 1);
  if (!p) { fprintf(stderr, "out of memory\n"); exit(3); }
  return p;
}

static void load(const char *list) {
  FILE *f = fopen(list, "r");
  if (!f) { perror(list); exit(2); }
  char path[4096];
  int cap = 2048;
  dstart = xmalloc(cap * sizeof(int));
  dlen = xmalloc(cap * sizeof(int));
  size_t size = 1 << 20, used = 0;
  text = xmalloc(size);
  while (fgets(path, sizeof path, f)) {
    path[strcspn(path, "\n")] = 0;
    if (!path[0]) continue;
    FILE *g = fopen(path, "rb");
    if (!g) { perror(path); exit(2); }
    if (ndocs == cap) { fprintf(stderr, "too many files\n"); exit(2); }
    dstart[ndocs] = (int)used;
    for (;;) {
      if (used == size) { size *= 2; text = realloc(text, size); }
      size_t got = fread(text + used, 1, size - used, g);
      if (!got) break;
      used += got;
    }
    fclose(g);
    dlen[ndocs] = (int)used - dstart[ndocs];
    ndocs++;
  }
  fclose(f);
  total = (int)used;
  docof = xmalloc(total * sizeof(int));
  for (int d = 0; d < ndocs; d++)
    for (int i = 0; i < dlen[d]; i++) docof[dstart[d] + i] = d;
  int longest = 0;
  for (int d = 0; d < ndocs; d++) if (dlen[d] > longest) longest = dlen[d];
  best = xmalloc((longest + 2) * sizeof(int));
  mask = calloc(total, sizeof(u64));
}

typedef struct { u64 h; int p; } Item;
static int item_cmp(const void *a, const void *b) {
  const Item *x = a, *y = b;
  if (x->h != y->h) return x->h < y->h ? -1 : 1;
  return x->p - y->p;
}

// Every string of 2..L bytes that the policy makes eligible.
static void enumerate(int L) {
  capcand = 1 << 16;
  cands = xmalloc(capcand * sizeof(Cand));
  capocc = 1 << 22;
  occ = xmalloc(capocc * sizeof(int));
  unsigned char *alive = xmalloc(total);
  memset(alive, 1, total);
  u64 *hash = xmalloc(total * sizeof(u64));
  for (int p = 0; p < total; p++) hash[p] = text[p] + 1;
  Item *items = xmalloc(total * sizeof(Item));
  unsigned char *next = xmalloc(total);
  for (int l = 2; l <= L; l++) {
    int n = 0;
    for (int p = 0; p < total; p++) {
      int d = docof[p];
      if (!alive[p] || p + l > dstart[d] + dlen[d]) continue;
      hash[p] = (hash[p] * 0x100000001b3ULL) ^ (u64)(text[p + l - 1] + 1);
      hash[p] *= 0x9E3779B97F4A7C15ULL;
      items[n].h = hash[p];
      items[n].p = p;
      n++;
    }
    qsort(items, n, sizeof(Item), item_cmp);
    memset(next, 0, total);
    for (int i = 0; i < n;) {
      int j = i + 1;
      while (j < n && items[j].h == items[i].h) j++;
      for (int k = i + 1; k < j; k++)
        if (memcmp(text + items[k].p, text + items[i].p, l)) {
          fprintf(stderr, "hash collision at length %d\n", l);
          exit(4);
        }
      int docs = 0, last = -1, whole = 0;
      for (int k = i; k < j; k++) {
        int d = docof[items[k].p];
        if (d != last) { docs++; last = d; }
        if (items[k].p == dstart[d] && l == dlen[d]) whole = 1;
      }
      if (docs >= min_docs) {
        // A longer legal string can only start where this one has enough support.
        for (int k = i; k < j; k++) next[items[k].p] = 1;
        if (!whole || allow_whole) {
          if (ncand == capcand) {
            capcand *= 2;
            cands = realloc(cands, capcand * sizeof(Cand));
          }
          while (nocc + (j - i) > capocc) {
            capocc *= 2;
            occ = realloc(occ, capocc * sizeof(int));
          }
          Cand *c = &cands[ncand++];
          c->len = l;
          c->nocc = j - i;
          c->off = (int)nocc;
          c->docs = docs;
          int used = 0, end = -1, doc = -1;
          for (int k = i; k < j; k++) {
            int p = items[k].p;
            occ[nocc++] = p;
            if (docof[p] != doc) { doc = docof[p]; end = -1; }
            if (p >= end) { used++; end = p + l; }
          }
          c->ub = used * (l - 1);
        }
      }
      i = j;
    }
    memcpy(alive, next, total);
  }
  free(alive); free(hash); free(items); free(next);
}

static inline int doc_cost(int d) {
  int s = dstart[d], n = dlen[d];
  best[0] = 0;
  for (int i = 1; i <= n; i++) best[i] = INF;
  for (int i = 0; i < n; i++) {
    int here = best[i];
    if (here >= INF) continue;
    u64 m = mask[s + i];
    while (m) {
      int b = __builtin_ctzll(m);
      m &= m - 1;
      int j = i + b + 1;
      if (here + 1 < best[j]) best[j] = here + 1;
    }
  }
  return best[n];
}

static int *cost;
static long emissions;
static int present[256];

static void add_alphabet(FILE *out, int *k, long *bytes) {
  memset(present, 0, sizeof present);
  for (int p = 0; p < total; p++) { present[text[p]] = 1; mask[p] |= 1; }
  cost = xmalloc(ndocs * sizeof(int));
  emissions = total;
  for (int d = 0; d < ndocs; d++) cost[d] = dlen[d];
  int count = 0;
  for (int c = 0; c < 256; c++) count += present[c];
  for (int c = 0; c < 256; c++)
    if (present[c]) {
      (*k)++;
      *bytes += 2;
      fprintf(out, "E %d %ld %ld %d %02x\n", *k, *bytes,
              *k == count ? emissions : -1L, *k == count ? ndocs : 0, c);
    }
}

static void write_entry(FILE *out, int k, long bytes, long tokens, int spelled,
                        const unsigned char *s, int l) {
  fprintf(out, "E %d %ld %ld %d ", k, bytes, tokens, spelled);
  for (int i = 0; i < l; i++) fprintf(out, "%02x", s[i]);
  fputc('\n', out);
}

static int gain_of(const Cand *c) {
  u64 bit = 1ULL << (c->len - 1);
  int gain = 0;
  for (int i = 0; i < c->nocc;) {
    int d = docof[occ[c->off + i]], j = i;
    while (j < c->nocc && docof[occ[c->off + j]] == d) mask[occ[c->off + j++]] |= bit;
    gain += cost[d] - doc_cost(d);
    for (int k = i; k < j; k++) mask[occ[c->off + k]] &= ~bit;
    i = j;
  }
  return gain;
}

static void accept(const Cand *c) {
  u64 bit = 1ULL << (c->len - 1);
  for (int i = 0; i < c->nocc;) {
    int d = docof[occ[c->off + i]], j = i;
    while (j < c->nocc && docof[occ[c->off + j]] == d) mask[occ[c->off + j++]] |= bit;
    int next = doc_cost(d);
    emissions -= cost[d] - next;
    cost[d] = next;
    i = j;
  }
}

typedef struct { double key; int c, stamp, gain; } Node;
static Node *heap;
static int heap_n;
static inline int above(const Node *a, const Node *b) {
  return a->key > b->key || (a->key == b->key && a->c < b->c);
}
static void heap_push(Node x) {
  int i = heap_n++;
  while (i) {
    int up = (i - 1) / 2;
    if (!above(&x, &heap[up])) break;
    heap[i] = heap[up];
    i = up;
  }
  heap[i] = x;
}
static Node heap_pop(void) {
  Node top = heap[0], x = heap[--heap_n];
  int i = 0;
  for (;;) {
    int a = 2 * i + 1, b = a + 1, m = -1;
    if (a < heap_n) m = a;
    if (b < heap_n && above(&heap[b], &heap[a])) m = b;
    if (m < 0 || !above(&heap[m], &x)) break;
    heap[i] = heap[m];
    i = m;
  }
  if (heap_n) heap[i] = x;
  return top;
}

static void heap_build(void) {
  for (int s = heap_n / 2 - 1; s >= 0; s--) {
    Node x = heap[s];
    int i = s;
    for (;;) {
      int a = 2 * i + 1, b = a + 1, m = -1;
      if (a < heap_n) m = a;
      if (b < heap_n && above(&heap[b], &heap[a])) m = b;
      if (m < 0 || !above(&heap[m], &x)) break;
      heap[i] = heap[m];
      i = m;
    }
    heap[i] = x;
  }
}

static int run_greedy(FILE *out, int per_byte, int kmax, double limit) {
  int k = 0;
  long bytes = 0;
  add_alphabet(out, &k, &bytes);
  double start = now();
  heap = xmalloc((ncand + 1) * sizeof(Node));
  for (int c = 0; c < ncand; c++) {
    double weight = per_byte ? 1.0 + cands[c].len : 1.0;
    heap_push((Node){cands[c].ub / weight, c, -1, 0});
  }
  int step = 0;
  while (k < kmax && heap_n) {
    if ((step & 15) == 0 && now() - start > limit) return 1;
    Node top = heap_pop();
    const Cand *c = &cands[top.c];
    double weight = per_byte ? 1.0 + c->len : 1.0;
    if (top.stamp != step) {
      top.gain = gain_of(c);
      top.key = top.gain / weight;
      top.stamp = step;
      if (heap_n && above(&heap[0], &top)) { heap_push(top); continue; }
    }
    if (top.gain <= 0) break;
    accept(c);
    k++;
    bytes += 1 + c->len;
    write_entry(out, k, bytes, emissions, ndocs, text + occ[c->off], c->len);
    step++;
  }
  return 0;
}

static const long *rank_score;
static int rank_cmp(const void *a, const void *b) {
  int x = *(const int *)a, y = *(const int *)b;
  if (rank_score[x] != rank_score[y]) return rank_score[x] > rank_score[y] ? -1 : 1;
  return x - y;
}

static int run_freq(FILE *out, int by_docs, int kmax, double limit) {
  int k = 0;
  long bytes = 0;
  add_alphabet(out, &k, &bytes);
  double start = now();
  long *score = xmalloc(ncand * sizeof(long));
  int *order = xmalloc(ncand * sizeof(int));
  for (int c = 0; c < ncand; c++) {
    score[c] = by_docs ? (long)cands[c].docs * (cands[c].len - 1) : cands[c].ub;
    order[c] = c;
  }
  rank_score = score;
  qsort(order, ncand, sizeof(int), rank_cmp);
  for (int i = 0; i < ncand && k < kmax; i++) {
    if ((i & 15) == 0 && now() - start > limit) return 1;
    const Cand *c = &cands[order[i]];
    accept(c);
    k++;
    bytes += 1 + c->len;
    write_entry(out, k, bytes, emissions, ndocs, text + occ[c->off], c->len);
  }
  return 0;
}

// Exact lookup of an eligible string.
static int *cand_table;
static u64 cand_slots;

static u64 key_of(const unsigned char *s, int l) {
  u64 h = 0xcbf29ce484222325ULL ^ (u64)l;
  for (int i = 0; i < l; i++) { h ^= s[i]; h *= 0x100000001b3ULL; }
  return h ^ (h >> 29);
}

static int find_candidate(const unsigned char *s, int l) {
  if (!cand_table) {
    cand_slots = 1024;
    while (cand_slots < (u64)ncand * 2 + 2) cand_slots *= 2;
    cand_table = xmalloc(cand_slots * sizeof(int));
    memset(cand_table, -1, cand_slots * sizeof(int));
    for (int c = 0; c < ncand; c++) {
      u64 at = key_of(text + occ[cands[c].off], cands[c].len) & (cand_slots - 1);
      while (cand_table[at] >= 0) at = (at + 1) & (cand_slots - 1);
      cand_table[at] = c;
    }
  }
  for (u64 at = key_of(s, l) & (cand_slots - 1);; at = (at + 1) & (cand_slots - 1)) {
    int c = cand_table[at];
    if (c < 0) return -1;
    if (cands[c].len == l && !memcmp(text + occ[cands[c].off], s, l)) return c;
  }
}

// Byte pair encoding. Tokens are ids of distinct strings, merged in order of
// pair count, ties to the lower pair. The reported total is its own segmentation.
typedef struct { int off, len; } Str;
static Str *strs;
static int nstr, capstr;
static unsigned char *pool;
static long pool_n, pool_cap;
static int *str_table, str_cap;

static u64 fnv(const unsigned char *s, int l) {
  u64 h = 0xcbf29ce484222325ULL;
  for (int i = 0; i < l; i++) { h ^= s[i]; h *= 0x100000001b3ULL; }
  return h;
}

static int str_id(const unsigned char *s, int l, int *created) {
  u64 h = fnv(s, l);
  for (u64 i = h & (str_cap - 1);; i = (i + 1) & (str_cap - 1)) {
    int id = str_table[i];
    if (id < 0) {
      if (nstr == capstr) { capstr *= 2; strs = realloc(strs, capstr * sizeof(Str)); }
      while (pool_n + l > pool_cap) { pool_cap *= 2; pool = realloc(pool, pool_cap); }
      memcpy(pool + pool_n, s, l);
      strs[nstr] = (Str){(int)pool_n, l};
      pool_n += l;
      str_table[i] = nstr;
      *created = 1;
      return nstr++;
    }
    if (strs[id].len == l && !memcmp(pool + strs[id].off, s, l)) { *created = 0; return id; }
  }
}

typedef struct { u64 key; int count, docs, last, whole; } Pair;

static int run_bpe(FILE *out, int L, int kmax, double limit) {
  int k = 0;
  long bytes = 0;
  capstr = 1 << 14;
  strs = xmalloc(capstr * sizeof(Str));
  pool_cap = 1 << 20;
  pool = xmalloc(pool_cap);
  str_cap = 1 << 16;
  str_table = xmalloc(str_cap * sizeof(int));
  memset(str_table, -1, str_cap * sizeof(int));
  int *tok = xmalloc(total * sizeof(int));
  int *tok_n = xmalloc(ndocs * sizeof(int));
  int *tok_at = xmalloc(ndocs * sizeof(int));
  int created;
  int count_chars = 0;
  memset(present, 0, sizeof present);
  for (int p = 0; p < total; p++) present[text[p]] = 1;
  for (int c = 0; c < 256; c++) count_chars += present[c];
  for (int c = 0; c < 256; c++)
    if (present[c]) {
      unsigned char s = (unsigned char)c;
      str_id(&s, 1, &created);
      k++;
      bytes += 2;
      write_entry(out, k, bytes, k == count_chars ? total : -1L,
                  k == count_chars ? ndocs : 0, &s, 1);
    }
  int w = 0;
  for (int d = 0; d < ndocs; d++) {
    tok_at[d] = w;
    for (int i = 0; i < dlen[d]; i++) {
      unsigned char s = text[dstart[d] + i];
      tok[w++] = str_id(&s, 1, &created);
    }
    tok_n[d] = dlen[d];
  }
  long tokens = total;
  int tcap = 1 << 20;
  Pair *table = xmalloc(tcap * sizeof(Pair));
  double start = now();
  unsigned char *joined = xmalloc(L + 2);
  while (k < kmax) {
    if (now() - start > limit) { free(table); return 1; }
    memset(table, 0, tcap * sizeof(Pair));
    for (int d = 0; d < ndocs; d++) {
      int *t = tok + tok_at[d];
      u64 prev = ~0ULL;
      for (int i = 0; i + 1 < tok_n[d]; i++) {
        u64 key = ((u64)t[i] << 32) | (u64)(unsigned)t[i + 1];
        if (key == prev && t[i] == t[i + 1]) { prev = ~0ULL; continue; }
        prev = key;
        u64 slot = (key * 0x9E3779B97F4A7C15ULL) >> 44;
        while (table[slot].count && table[slot].key != key) slot = (slot + 1) & (tcap - 1);
        Pair *e = &table[slot];
        if (!e->count) { e->key = key; e->last = -1; }
        e->count++;
        if (e->last != d) { e->docs++; e->last = d; }
        if (tok_n[d] == 2) e->whole = 1;
      }
    }
    Pair *chosen = NULL;
    for (int i = 0; i < tcap; i++) {
      Pair *e = &table[i];
      if (e->count < 2) continue;
      int a = (int)(e->key >> 32), b = (int)(unsigned)e->key;
      if (strs[a].len + strs[b].len > L) continue;
      if (chosen && (e->count < chosen->count ||
                     (e->count == chosen->count && e->key >= chosen->key))) continue;
      memcpy(joined, pool + strs[a].off, strs[a].len);
      memcpy(joined + strs[a].len, pool + strs[b].off, strs[b].len);
      if (find_candidate(joined, strs[a].len + strs[b].len) < 0) continue;
      chosen = e;
    }
    if (!chosen) break;
    int a = (int)(chosen->key >> 32), b = (int)(unsigned)chosen->key;
    int la = strs[a].len, lb = strs[b].len;
    memcpy(joined, pool + strs[a].off, la);
    memcpy(joined + la, pool + strs[b].off, lb);
    int merged = str_id(joined, la + lb, &created);
    fprintf(out, "M ");
    for (int i = 0; i < la; i++) fprintf(out, "%02x", joined[i]);
    fputc(' ', out);
    for (int i = la; i < la + lb; i++) fprintf(out, "%02x", joined[i]);
    fputc('\n', out);
    for (int d = 0; d < ndocs; d++) {
      int *t = tok + tok_at[d], n = tok_n[d], out_n = 0;
      for (int i = 0; i < n;) {
        if (i + 1 < n && t[i] == a && t[i + 1] == b) { t[out_n++] = merged; i += 2; tokens--; }
        else t[out_n++] = t[i++];
      }
      tok_n[d] = out_n;
    }
    if (created) {
      k++;
      bytes += 1 + la + lb;
      write_entry(out, k, bytes, tokens, ndocs, joined, la + lb);
    }
  }
  free(table);
  return 0;
}

// Coverage when not every file need be spelled, or single characters are
// forbidden. Files are taken cheapest first, by how many new entries each needs.
static int *cand_at;
static int run_cover(FILE *out, int singles, int L, int kmax, double limit) {
  double start = now();
  long cells = (long)total * (L + 1);
  cand_at = xmalloc(cells * sizeof(int));
  memset(cand_at, -1, cells * sizeof(int));
  for (int c = 0; c < ncand; c++)
    for (int i = 0; i < cands[c].nocc; i++)
      cand_at[(long)occ[cands[c].off + i] * (L + 1) + cands[c].len] = c;
  int id_base = ncand;  // single characters take ids ncand + byte
  unsigned char *in_dict = calloc(ncand + 256, 1);
  if (singles)
    for (int p = 0; p < total; p++) cand_at[(long)p * (L + 1) + 1] = id_base + text[p];
  unsigned char *done = calloc(ndocs, 1);
  int *need = xmalloc((total + 2) * sizeof(int));
  int *from = xmalloc((total + 2) * sizeof(int));
  int *chosen = xmalloc(4096 * sizeof(int));
  int reachable = 0;
  for (int d = 0; d < ndocs; d++) {
    int s = dstart[d], n = dlen[d];
    unsigned char *r = calloc(n + 1, 1);
    r[0] = 1;
    for (int i = 0; i < n; i++)
      if (r[i])
        for (int l = 1; l <= L && i + l <= n; l++)
          if (cand_at[(long)(s + i) * (L + 1) + l] >= 0) r[i + l] = 1;
    if (r[n]) reachable++; else done[d] = 2;  // provably unspellable by this rule
    free(r);
  }
  fprintf(out, "R %d %d\n", reachable, ndocs);
  int k = 0, spelled = 0;
  long bytes = 0, tokens = 0;
  for (;;) {
    if (now() - start > limit) return 1;
    int pick = -1, pick_new = INF, pick_len = 0;
    for (int d = 0; d < ndocs; d++) {
      if (done[d]) continue;
      int s = dstart[d], n = dlen[d];
      for (int i = 1; i <= n; i++) need[i] = INF;
      need[0] = 0;
      for (int i = 0; i < n; i++) {
        if (need[i] >= INF) continue;
        for (int l = 1; l <= L && i + l <= n; l++) {
          int c = cand_at[(long)(s + i) * (L + 1) + l];
          if (c < 0) continue;
          int v = need[i] + (in_dict[c] ? 0 : 1);
          if (v < need[i + l]) need[i + l] = v;
        }
      }
      if (need[n] < pick_new || (need[n] == pick_new && n < pick_len)) {
        pick = d; pick_new = need[n]; pick_len = n;
      }
    }
    if (pick < 0 || k + pick_new > kmax) break;
    int s = dstart[pick], n = dlen[pick];
    for (int i = 1; i <= n; i++) need[i] = INF;
    need[0] = 0;
    for (int i = 0; i < n; i++) {
      if (need[i] >= INF) continue;
      for (int l = 1; l <= L && i + l <= n; l++) {
        int c = cand_at[(long)(s + i) * (L + 1) + l];
        if (c < 0) continue;
        int v = need[i] + (in_dict[c] ? 0 : 1);
        if (v < need[i + l]) { need[i + l] = v; from[i + l] = l; }
      }
    }
    int m = 0;
    for (int i = n; i > 0; i -= from[i]) {
      int c = cand_at[(long)(s + i - from[i]) * (L + 1) + from[i]];
      if (!in_dict[c]) { in_dict[c] = 1; if (m < 4096) chosen[m++] = c; }
    }
    done[pick] = 1;
    spelled++;
    for (int i = m - 1; i >= 0; i--) {
      int c = chosen[i];
      k++;
      if (c >= id_base) {
        unsigned char ch = (unsigned char)(c - id_base);
        bytes += 2;
        write_entry(out, k, bytes, -1, i ? spelled - 1 : spelled, &ch, 1);
      } else {
        bytes += 1 + cands[c].len;
        write_entry(out, k, bytes, -1, i ? spelled - 1 : spelled,
                    text + occ[cands[c].off], cands[c].len);
      }
    }
    if (!m) fprintf(out, "F %d %ld %d\n", k, bytes, spelled);
  }
  (void)tokens;
  return 0;
}

// Local search within the same rules: start from a greedy dictionary of K
// entries, drop a few of the entries that matter least, refill greedily, and
// keep the result only if total emissions fall. A fixed seed makes it repeatable.
static u64 rng_state = 0x9E3779B97F4A7C15ULL;
static u64 rng(void) {
  rng_state ^= rng_state << 13;
  rng_state ^= rng_state >> 7;
  rng_state ^= rng_state << 17;
  return rng_state;
}

static void remove_entry(const Cand *c) {
  u64 bit = 1ULL << (c->len - 1);
  for (int i = 0; i < c->nocc;) {
    int d = docof[occ[c->off + i]], j = i;
    while (j < c->nocc && docof[occ[c->off + j]] == d) mask[occ[c->off + j++]] &= ~bit;
    int next = doc_cost(d);
    emissions += next - cost[d];
    cost[d] = next;
    i = j;
  }
}

static int loss_of(const Cand *c) {
  u64 bit = 1ULL << (c->len - 1);
  int loss = 0;
  for (int i = 0; i < c->nocc;) {
    int d = docof[occ[c->off + i]], j = i;
    while (j < c->nocc && docof[occ[c->off + j]] == d) mask[occ[c->off + j++]] &= ~bit;
    loss += doc_cost(d) - cost[d];
    for (int k = i; k < j; k++) mask[occ[c->off + k]] |= bit;
    i = j;
  }
  return loss;
}

static int run_polish(FILE *out, int K, double limit, const char *seed) {
  int k = 0;
  long bytes = 0;
  FILE *null_out = fopen("/dev/null", "w");
  add_alphabet(null_out, &k, &bytes);
  fclose(null_out);
  int alphabet = k;
  if (K <= alphabet) return 0;
  int *inside = xmalloc((K + 1) * sizeof(int)), n = 0;
  unsigned char *member = calloc(ncand, 1);
  FILE *f = fopen(seed, "r");
  if (!f) { perror(seed); exit(2); }
  char line[512];
  unsigned char raw[70];
  while (fgets(line, sizeof line, f) && n < K - alphabet) {
    int ke, sp;
    long st, to;
    char hex[200];
    if (line[0] != 'E' || sscanf(line, "E %d %ld %ld %d %199s", &ke, &st, &to, &sp, hex) != 5) continue;
    int l = (int)strlen(hex) / 2;
    if (l < 2) continue;
    for (int i = 0; i < l; i++) { unsigned v; sscanf(hex + 2 * i, "%2x", &v); raw[i] = (unsigned char)v; }
    int c = find_candidate(raw, l);
    if (c < 0) { fprintf(stderr, "seed entry is not a candidate\n"); exit(5); }
    member[c] = 1;
    inside[n++] = c;
    accept(&cands[c]);
  }
  fclose(f);
  double start = now();
  int *saved = xmalloc(ndocs * sizeof(int));
  int *old_inside = xmalloc((K + 1) * sizeof(int));
  int *cached = xmalloc(ncand * sizeof(int));
  for (int c = 0; c < ncand; c++) cached[c] = cands[c].ub;
  heap = xmalloc((ncand + 1) * sizeof(Node));
  long best = emissions;
  long rounds = 0, improved = 0;
  while (now() - start < limit && n > 0) {
    rounds++;
    memcpy(saved, cost, ndocs * sizeof(int));
    memcpy(old_inside, inside, n * sizeof(int));
    int old_n = n;
    long before = emissions;
    int drop = 1 + (int)(rng() % (unsigned)(n / 12 + 2));
    if (drop > n) drop = n;
    for (int t = 0; t < drop && n > 0; t++) {
      int pick = -1, low = INF;
      for (int tries = 0; tries < 6; tries++) {
        int i = (int)(rng() % (unsigned)n);
        int loss = loss_of(&cands[inside[i]]);
        if (loss < low) { low = loss; pick = i; }
      }
      int c = inside[pick];
      inside[pick] = inside[--n];
      member[c] = 0;
      remove_entry(&cands[c]);
      cached[c] = low;
    }
    heap_n = 0;
    for (int c = 0; c < ncand; c++)
      if (!member[c] && cached[c] > 0) heap[heap_n++] = (Node){(double)cached[c], c, -1, 0};
    heap_build();
    int step = 0;
    while (n < K - alphabet && heap_n) {
      Node top = heap_pop();
      if (top.stamp != step) {
        top.gain = gain_of(&cands[top.c]);
        cached[top.c] = top.gain;
        top.key = top.gain;
        top.stamp = step;
        if (heap_n && above(&heap[0], &top)) { heap_push(top); continue; }
      }
      if (top.gain <= 0) break;
      accept(&cands[top.c]);
      member[top.c] = 1;
      inside[n++] = top.c;
      step++;
    }
    if (emissions < before) {
      improved++;
      best = emissions;
    } else {
      for (int i = 0; i < n; i++) {
        const Cand *c = &cands[inside[i]];
        u64 bit = 1ULL << (c->len - 1);
        for (int j = 0; j < c->nocc; j++) mask[occ[c->off + j]] &= ~bit;
        member[inside[i]] = 0;
      }
      n = old_n;
      memcpy(inside, old_inside, n * sizeof(int));
      for (int i = 0; i < n; i++) {
        const Cand *c = &cands[inside[i]];
        u64 bit = 1ULL << (c->len - 1);
        for (int j = 0; j < c->nocc; j++) mask[occ[c->off + j]] |= bit;
        member[inside[i]] = 1;
      }
      memcpy(cost, saved, ndocs * sizeof(int));
      emissions = before;
    }
  }
  int kk = 0;
  long bb = 0;
  for (int ch = 0; ch < 256; ch++)
    if (present[ch]) {
      kk++;
      bb += 2;
      unsigned char one = (unsigned char)ch;
      write_entry(out, kk, bb, -1, 0, &one, 1);
    }
  for (int i = 0; i < n; i++) {
    const Cand *c = &cands[inside[i]];
    kk++;
    bb += 1 + c->len;
    write_entry(out, kk, bb, i == n - 1 ? best : -1, i == n - 1 ? ndocs : 0,
                text + occ[c->off], c->len);
  }
  fprintf(out, "P rounds=%ld improved=%ld\n", rounds, improved);
  return 0;
}

#ifndef ENGINE_NO_MAIN
int main(int argc, char **argv) {
  if (argc != 8 && !(argc == 9 && !strcmp(argv[1], "polish"))) {
    fprintf(stderr, "usage: engine MODE POLICY L KMAX LIMIT_SECONDS LIST OUT [SEED_CHAIN]\n");
    return 2;
  }
  const char *mode = argv[1], *receipt = getenv("FSV2_RECEIPT");
  if (!receipt || !strstr(receipt, "manifest=") || !strstr(receipt, "pool=") ||
      !strstr(receipt, "impl=") || !strstr(receipt, "run=")) {
    fprintf(stderr, "FSV2_RECEIPT must bind manifest, pool, impl and run\n");
    return 2;
  }
  set_policy(argv[2]);
  int L = atoi(argv[3]), kmax = atoi(argv[4]);
  double limit = atof(argv[5]);
  if (L < 1 || L > 64) { fprintf(stderr, "L must be 1..64\n"); return 2; }
  load(argv[6]);
  double t0 = now();
  enumerate(L);
  double enumerated = now() - t0;
  FILE *out = fopen(argv[7], "w");
  if (!out) { perror(argv[7]); return 2; }
  fprintf(out, "H policy=%s mode=%s L=%d K=%d limit=%s %s\n", argv[2], mode, L, kmax, argv[5], receipt);
  int stopped;
  if (!strcmp(mode, "greedy-entry")) stopped = run_greedy(out, 0, kmax, limit);
  else if (!strcmp(mode, "greedy-byte")) stopped = run_greedy(out, 1, kmax, limit);
  else if (!strcmp(mode, "freq-occ")) stopped = run_freq(out, 0, kmax, limit);
  else if (!strcmp(mode, "freq-doc")) stopped = run_freq(out, 1, kmax, limit);
  else if (!strcmp(mode, "bpe")) stopped = run_bpe(out, L, kmax, limit);
  else if (!strcmp(mode, "cover-mixed")) stopped = run_cover(out, 1, L, kmax, limit);
  else if (!strcmp(mode, "cover-nosingle")) stopped = run_cover(out, 0, L, kmax, limit);
  else if (!strcmp(mode, "polish")) stopped = run_polish(out, kmax, limit, argv[8]);
  else { fprintf(stderr, "unknown mode\n"); return 2; }
  struct rusage use;
  getrusage(RUSAGE_SELF, &use);
  fprintf(out, "D %s L=%d candidates=%d occurrences=%ld stopped=%d seconds=%.1f enumerate_seconds=%.1f maxrss_kb=%ld\n",
          mode, L, ncand, nocc, stopped, now() - t0, enumerated, (long)use.ru_maxrss);
  fclose(out);
  return 0;
}
#endif
