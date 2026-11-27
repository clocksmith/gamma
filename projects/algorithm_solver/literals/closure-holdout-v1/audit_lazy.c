// Audit of the lazy greedy trainers (greedy-entry and greedy-closed).
//
// The frozen engine picks the next entry from a max-heap of cached gains (lazy evaluation). That is
// exact only if a candidate's gain never grows as the dictionary grows, and exact token gain under
// shortest-path parsing can grow (on "abcd" with bc present, cd gains nothing until ab is added).
// This program replays the same lazy procedure, checks that it reproduces the given chain entry for
// entry, and at every AUDIT_EVERY-th step recomputes the exact gain of every eligible candidate whose
// provable upper bound could beat the lazy pick:
//   open:   gain(w) <= (|w| - 1) * nonoverlapping occurrences(w)   (the engine's ub)
//   closed: gain(w) <= nonoverlapping occurrences(w)               (replacing each use of w = uv by u, v)
// It reports, per audited step, the lazy pick's gain and the exact best gain.
//
//   audit_lazy MODE L KMAX AUDIT_EVERY LIST CHAIN OUT_TSV      MODE = greedy-entry | greedy-closed
#define ENGINE_NO_MAIN
#include "../fixed-source-v3/engine.c"

static unsigned char *in_dict, *eligible, *in_heap;
static int *members, nmembers;
static unsigned char **chain_e;
static int *chain_l, chain_n, chain_singles;

static void load_chain(const char *path) {
  FILE *f = fopen(path, "r");
  if (!f) { perror(path); exit(2); }
  char line[1 << 12];
  int cap = 8192;
  chain_e = xmalloc(cap * sizeof(*chain_e));
  chain_l = xmalloc(cap * sizeof(int));
  while (fgets(line, sizeof line, f)) {
    if (line[0] != 'E') continue;
    char hex[512];
    int k; long b, t; int s;
    if (sscanf(line, "E %d %ld %ld %d %511s", &k, &b, &t, &s, hex) != 5) continue;
    int l = (int)strlen(hex) / 2;
    unsigned char *e = xmalloc(l);
    for (int i = 0; i < l; i++) sscanf(hex + 2 * i, "%2hhx", &e[i]);
    if (l == 1) { chain_singles++; continue; }
    chain_e[chain_n] = e;
    chain_l[chain_n++] = l;
  }
  fclose(f);
}

static void offer(const unsigned char *a, int la, const unsigned char *b, int lb, int L, unsigned char *buf, int closed) {
  if (la + lb > L) return;
  memcpy(buf, a, la);
  memcpy(buf + la, b, lb);
  int c = find_candidate(buf, la + lb);
  if (c < 0 || in_dict[c]) return;
  eligible[c] = 1;
  if (in_heap[c]) return;
  in_heap[c] = 1;
  heap_push((Node){closed ? (double)cands[c].ub : (double)cands[c].ub, c, -1, 0});
}

int main(int argc, char **argv) {
  if (argc != 8) {
    fprintf(stderr, "usage: audit_lazy MODE L KMAX AUDIT_EVERY LIST CHAIN OUT_TSV\n");
    return 2;
  }
  int closed = !strcmp(argv[1], "greedy-closed");
  if (!closed && strcmp(argv[1], "greedy-entry")) { fprintf(stderr, "mode\n"); return 2; }
  int L = atoi(argv[2]), kmax = atoi(argv[3]), every = atoi(argv[4]);
  set_policy("s1-whole");
  load(argv[5]);
  load_side_files();
  enumerate(L);
  load_chain(argv[6]);
  FILE *out = fopen(argv[7], "w");
  fprintf(out, "step\tlazy_gain\texact_best_gain\tcandidates_checked\tlazy_is_best\n");
  FILE *devnull = fopen("/dev/null", "w");
  int k = 0;
  long bytes = 0;
  add_alphabet(devnull, &k, &bytes);
  in_dict = calloc(ncand, 1);
  eligible = calloc(ncand, 1);
  in_heap = calloc(ncand, 1);
  members = xmalloc((kmax + 256) * sizeof(int));
  heap = xmalloc((ncand + 1) * sizeof(Node));
  heap_n = 0;
  unsigned char *buf = xmalloc(2 * L + 2);
  unsigned char alpha[256];
  int nalpha = 0;
  for (int c = 0; c < 256; c++)
    if (present[c]) alpha[nalpha++] = (unsigned char)c;
  if (closed) {
    for (int i = 0; i < nalpha; i++)
      for (int j = 0; j < nalpha; j++) offer(&alpha[i], 1, &alpha[j], 1, L, buf, 1);
  } else {
    for (int c = 0; c < ncand; c++) { eligible[c] = 1; heap_push((Node){(double)cands[c].ub, c, -1, 0}); }
  }
  int step = 0, audited = 0, diverged = 0, mismatch = 0;
  long worst = 0;
  while (k < kmax && heap_n) {
    Node top = heap_pop();
    const Cand *c = &cands[top.c];
    if (top.stamp != step) {
      top.gain = gain_of(c);
      top.key = top.gain;
      top.stamp = step;
      if (heap_n && above(&heap[0], &top)) { heap_push(top); continue; }
    }
    if (top.gain <= 0) {
      if (closed) { in_heap[top.c] = 0; continue; }
      break;
    }
    int idx = k - nalpha;
    if (idx >= chain_n || chain_l[idx] != c->len || memcmp(chain_e[idx], text + occ[c->off], c->len)) { mismatch = 1; break; }
    if (every > 0 && step % every == 0) {
      int best = top.gain, checked = 0;
      for (int x = 0; x < ncand; x++) {
        if (in_dict[x] || !eligible[x] || x == top.c) continue;
        int bound = closed ? cands[x].ub / (cands[x].len - 1) : cands[x].ub;
        if (bound <= best) continue;
        int g = gain_of(&cands[x]);
        checked++;
        if (g > best) best = g;
      }
      fprintf(out, "%d\t%d\t%d\t%d\t%d\n", step, top.gain, best, checked, best == top.gain);
      fflush(out);
      audited++;
      if (best > top.gain) { diverged++; if (best - top.gain > worst) worst = best - top.gain; }
    }
    accept(c);
    in_heap[top.c] = 0;
    in_dict[top.c] = 1;
    k++;
    if (closed) {
      const unsigned char *e = text + occ[c->off];
      for (int i = 0; i < nalpha; i++) { offer(e, c->len, &alpha[i], 1, L, buf, 1); offer(&alpha[i], 1, e, c->len, L, buf, 1); }
      for (int m = 0; m < nmembers; m++) {
        const Cand *xx = &cands[members[m]];
        const unsigned char *xs = text + occ[xx->off];
        offer(e, c->len, xs, xx->len, L, buf, 1);
        offer(xs, xx->len, e, c->len, L, buf, 1);
      }
      offer(e, c->len, e, c->len, L, buf, 1);
      members[nmembers++] = top.c;
    }
    step++;
  }
  fprintf(stderr, "%s: steps=%d reproduces_chain=%s audited=%d lazy_not_best=%d worst_gap=%ld\n",
          argv[1], step, mismatch ? "NO" : "yes", audited, diverged, worst);
  fclose(out);
  return mismatch ? 1 : 0;
}
