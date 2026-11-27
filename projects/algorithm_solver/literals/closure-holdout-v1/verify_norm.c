// Brute-force check that a chain is an exact greedy normalized-gain order:
//   score_norm(w | V) = gain(w | V) / ( d_V(w) - 1 ),  ties broken by lower candidate id.
//
// Replays the chain's multi-byte entries in order. At every EVERY-th step it computes the exact
// gain and current span cost of the chain's next entry and of every other candidate whose static
// non-overlapping use bound `used(x) = ub(x) / (|x| - 1)` could beat or tie it, using exact 64-bit
// integer cross-multiplication. Shares no selection code with engine_norm.c.
//
//   verify_norm POLICY L EVERY LIST CHAIN OUT_TSV
#define ENGINE_NO_MAIN
#include "../fixed-source-v3/engine.c"

static int span_cost_bf(int p, int l) {
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

int main(int argc, char **argv) {
  if (argc != 7) {
    fprintf(stderr, "usage: verify_norm POLICY L EVERY LIST CHAIN OUT_TSV\n");
    return 2;
  }
  set_policy(argv[1]);
  int L = atoi(argv[2]), every = atoi(argv[3]);
  load(argv[4]);
  load_side_files();
  if (cut_before) {
    fprintf(stderr, "verify_norm requires FSV3_CUTS unset\n");
    return 2;
  }
  enumerate(L);
  FILE *devnull = fopen("/dev/null", "w");
  int k = 0;
  long bytes = 0;
  add_alphabet(devnull, &k, &bytes);
  unsigned char *in_dict = calloc(ncand, 1);
  FILE *f = fopen(argv[5], "r");
  if (!f) { perror(argv[5]); return 2; }
  FILE *out = fopen(argv[6], "w");
  if (!out) { perror(argv[6]); return 2; }
  fprintf(out, "step\tchain_gain\tchain_span_cost\tbest_num\tbest_den\tbest_id_ok\tchecked\tchain_is_best\n");
  char line[1 << 12];
  int step = 0, audited = 0, worse = 0;
  unsigned char e[128];
  while (fgets(line, sizeof line, f)) {
    if (line[0] != 'E') continue;
    char hex[512];
    int kk, s;
    long b, t;
    if (sscanf(line, "E %d %ld %ld %d %511s", &kk, &b, &t, &s, hex) != 5) continue;
    int l = (int)strlen(hex) / 2;
    if (l == 1) continue;
    for (int i = 0; i < l; i++) sscanf(hex + 2 * i, "%2hhx", &e[i]);
    int c = find_candidate(e, l);
    if (c < 0) {
      fprintf(stderr, "entry is not a candidate at step %d\n", step);
      return 1;
    }
    if (every > 0 && step % every == 0) {
      int g = gain_of(&cands[c]);
      int sc_c = span_cost_bf(occ[cands[c].off], cands[c].len);
      long long my_num = g, my_den = sc_c - 1;
      long long best_num = my_num, best_den = my_den;
      int best_c = c;
      int checked = 0;
      for (int x = 0; x < ncand; x++) {
        if (in_dict[x] || x == c) continue;
        const Cand *y = &cands[x];
        long long used = y->ub / (y->len - 1);
        long long ub_lhs = used * best_den;
        if (ub_lhs < best_num) continue;
        if (ub_lhs == best_num && x > best_c) continue;
        int gx = gain_of(y);
        checked++;
        if (gx <= 0) continue;
        int sc_x = span_cost_bf(occ[y->off], y->len);
        long long num_x = gx, den_x = sc_x - 1;
        long long lhs = num_x * best_den, rhs = best_num * den_x;
        if (lhs > rhs || (lhs == rhs && x < best_c)) {
          best_num = num_x;
          best_den = den_x;
          best_c = x;
        }
      }
      int ok = (best_c == c);
      fprintf(out, "%d\t%d\t%d\t%lld\t%lld\t%d\t%d\t%d\n",
              step, g, sc_c, best_num, best_den, best_c == c, checked, ok);
      fflush(out);
      audited++;
      if (!ok) worse++;
    }
    accept(&cands[c]);
    in_dict[c] = 1;
    step++;
  }
  fprintf(stderr, "verify_norm %s: entries=%d audited=%d not_best=%d\n", argv[5], step, audited, worse);
  fclose(out);
  fclose(f);
  fclose(devnull);
  return worse ? 1 : 0;
}
