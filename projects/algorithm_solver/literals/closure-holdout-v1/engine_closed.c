// Constituent-closed greedy token gain, built on the frozen fixed-source-v3 engine.
//
// The frozen engine is included unchanged (ENGINE_NO_MAIN), so enumeration, the
// exact shortest-path cost and the gain computation are byte-for-byte the ones
// that produced the objective-holdout-v1 token-gain arm. This file adds one mode:
//
//   greedy-closed  Greedy by exact training token gain, like greedy-entry, but a
//                  string is a candidate only once it is the concatenation of two
//                  members of the current dictionary (single bytes are members).
//                  This is the structure byte pair encoding has: every entry is a
//                  merge of two earlier entries. The objective stays token gain.
//
//   engine_closed MODE POLICY L KMAX LIMIT_SECONDS LIST OUT
// MODE is greedy-closed, or any mode of the frozen engine (passed through).
#define ENGINE_NO_MAIN
#include "../fixed-source-v3/engine.c"

static unsigned char *in_dict, *in_heap;
static int *members, nmembers;

static void offer(const unsigned char *a, int la, const unsigned char *b, int lb, int L,
                  unsigned char *buf) {
  if (la + lb > L) return;
  memcpy(buf, a, la);
  memcpy(buf + la, b, lb);
  int c = find_candidate(buf, la + lb);
  if (c < 0 || in_dict[c] || in_heap[c]) return;
  in_heap[c] = 1;
  heap_push((Node){(double)cands[c].ub, c, -1, 0});
}

static int run_greedy_closed(FILE *out, int L, int kmax, double limit) {
  int k = 0;
  long bytes = 0;
  add_alphabet(out, &k, &bytes);
  double start = now();
  in_dict = xmalloc(ncand);
  in_heap = xmalloc(ncand);
  memset(in_dict, 0, ncand);
  memset(in_heap, 0, ncand);
  members = xmalloc((kmax + 256) * sizeof(int));
  heap = xmalloc((ncand + 1) * sizeof(Node));
  heap_n = 0;
  unsigned char *buf = xmalloc(2 * L + 2);
  unsigned char alpha[256];
  int nalpha = 0;
  for (int c = 0; c < 256; c++)
    if (present[c]) alpha[nalpha++] = (unsigned char)c;
  for (int i = 0; i < nalpha; i++)
    for (int j = 0; j < nalpha; j++) offer(&alpha[i], 1, &alpha[j], 1, L, buf);
  int step = 0;
  while (k < kmax && heap_n) {
    if ((step & 15) == 0 && now() - start > limit) return 1;
    Node top = heap_pop();
    const Cand *c = &cands[top.c];
    if (top.stamp != step) {
      top.gain = gain_of(c);
      top.key = top.gain;
      top.stamp = step;
      if (heap_n && above(&heap[0], &top)) { heap_push(top); continue; }
    }
    if (top.gain <= 0) { in_heap[top.c] = 0; continue; }
    accept(c);
    in_heap[top.c] = 0;
    in_dict[top.c] = 1;
    k++;
    bytes += 1 + c->len;
    const unsigned char *e = text + occ[c->off];
    write_entry(out, k, bytes, emissions, ndocs, e, c->len);
    // New concatenations that the accepted entry makes legal.
    for (int i = 0; i < nalpha; i++) {
      offer(e, c->len, &alpha[i], 1, L, buf);
      offer(&alpha[i], 1, e, c->len, L, buf);
    }
    for (int m = 0; m < nmembers; m++) {
      const Cand *x = &cands[members[m]];
      const unsigned char *xs = text + occ[x->off];
      offer(e, c->len, xs, x->len, L, buf);
      offer(xs, x->len, e, c->len, L, buf);
    }
    offer(e, c->len, e, c->len, L, buf);
    members[nmembers++] = top.c;
    step++;
  }
  return 0;
}

int main(int argc, char **argv) {
  if (argc != 8) {
    fprintf(stderr, "usage: engine_closed MODE POLICY L KMAX LIMIT_SECONDS LIST OUT\n");
    return 2;
  }
  const char *mode = argv[1], *receipt = getenv("FSV3_RECEIPT");
  if (!receipt || !strstr(receipt, "manifest=") || !strstr(receipt, "pool=") ||
      !strstr(receipt, "cuts=") || !strstr(receipt, "impl=") || !strstr(receipt, "run=")) {
    fprintf(stderr, "FSV3_RECEIPT must bind manifest, pool, cuts, impl and run\n");
    return 2;
  }
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
  int stopped;
  if (!strcmp(mode, "greedy-closed")) stopped = run_greedy_closed(out, L, kmax, limit);
  else if (!strcmp(mode, "greedy-entry")) stopped = run_greedy(out, 0, kmax, limit);
  else if (!strcmp(mode, "bpe")) stopped = run_bpe(out, L, kmax, limit);
  else if (!strcmp(mode, "freq-occ")) stopped = run_freq(out, 0, kmax, limit);
  else { fprintf(stderr, "unknown mode\n"); return 2; }
  struct rusage use;
  getrusage(RUSAGE_SELF, &use);
  fprintf(out, "D %s L=%d candidates=%d occurrences=%ld stopped=%d seconds=%.1f enumerate_seconds=%.1f maxrss_kb=%ld\n",
          mode, L, ncand, nocc, stopped, now() - t0, enumerated, (long)use.ru_maxrss);
  fclose(out);
  return 0;
}
