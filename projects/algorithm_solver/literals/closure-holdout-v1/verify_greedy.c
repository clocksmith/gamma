// Brute-force check that a chain is an exact greedy order.
//
// Replays the chain's multi-byte entries in order. At every EVERY-th step it computes the exact
// token gain of the chain's next entry and of every other eligible candidate whose static bound
// could exceed it (open: (|w| - 1) x non-overlapping occurrences; closed: non-overlapping
// occurrences, and only concatenations of two current members), and reports whether the chain's
// entry has the largest gain. Shares no selection code with engine_exact.c.
//
//   verify_greedy open|closed L EVERY LIST CHAIN OUT_TSV
#define ENGINE_NO_MAIN
#include "../fixed-source-v3/engine.c"

int main(int argc, char **argv) {
  if (argc != 7) { fprintf(stderr, "usage: verify_greedy open|closed L EVERY LIST CHAIN OUT_TSV\n"); return 2; }
  int closed = !strcmp(argv[1], "closed");
  int L = atoi(argv[2]), every = atoi(argv[3]);
  set_policy("s1-whole");
  load(argv[4]);
  load_side_files();
  enumerate(L);
  FILE *devnull = fopen("/dev/null", "w");
  int k = 0;
  long bytes = 0;
  add_alphabet(devnull, &k, &bytes);
  unsigned char *in_dict = calloc(ncand, 1);
  FILE *f = fopen(argv[5], "r");
  FILE *out = fopen(argv[6], "w");
  fprintf(out, "step\tchain_gain\tbest_gain\tchecked\tchain_is_best\n");
  char line[1 << 12];
  int step = 0, audited = 0, worse = 0;
  unsigned char e[128];
  while (fgets(line, sizeof line, f)) {
    if (line[0] != 'E') continue;
    char hex[512];
    int kk, s; long b, t;
    if (sscanf(line, "E %d %ld %ld %d %511s", &kk, &b, &t, &s, hex) != 5) continue;
    int l = (int)strlen(hex) / 2;
    if (l == 1) continue;
    for (int i = 0; i < l; i++) sscanf(hex + 2 * i, "%2hhx", &e[i]);
    int c = find_candidate(e, l);
    if (c < 0) { fprintf(stderr, "entry is not a candidate at step %d\n", step); return 1; }
    if (every > 0 && step % every == 0) {
      int g = gain_of(&cands[c]), best = g, checked = 0;
      for (int x = 0; x < ncand; x++) {
        if (in_dict[x] || x == c) continue;
        const Cand *y = &cands[x];
        int bound = closed ? y->ub / (y->len - 1) : y->ub;
        if (bound <= best) continue;
        if (closed) {  // eligible only if some split is two current members (single bytes included)
          const unsigned char *s0 = text + occ[y->off];
          int ok = 0;
          for (int cut = 1; cut < y->len && !ok; cut++) {
            int a = cut == 1 ? 1 : (find_candidate(s0, cut) >= 0 && in_dict[find_candidate(s0, cut)]);
            int bb = y->len - cut == 1 ? 1 : (find_candidate(s0 + cut, y->len - cut) >= 0 && in_dict[find_candidate(s0 + cut, y->len - cut)]);
            ok = a && bb;
          }
          if (!ok) continue;
        }
        int gx = gain_of(y);
        checked++;
        if (gx > best) best = gx;
      }
      fprintf(out, "%d\t%d\t%d\t%d\t%d\n", step, g, best, checked, best == g);
      fflush(out);
      audited++;
      if (best > g) worse++;
    }
    accept(&cands[c]);
    in_dict[c] = 1;
    step++;
  }
  fprintf(stderr, "%s %s: entries=%d audited=%d not_best=%d\n", argv[1], argv[5], step, audited, worse);
  return 0;
}
