// Full-Archive Two-Part MDL Greedy Search + Dead-Entry Absorption Pruning (Rung 3 candidate).
//
// Compiles cleanly against `../fixed-source-v3/engine.c` via `#define ENGINE_NO_MAIN`
// without modifying `fixed-source-v3/` or `codenet-replication-v1/`.
//
// Usage:
//   archive_search TABLES POLICY L KMAX LIMIT_SECONDS LIST_FILE OUT_FILE
// where TABLES is 1 (Design A / C: 1 byte table overhead per entry) or 2 (Design B:
// 2 bytes table overhead per entry).
//
// Differences from `engine.c`:
//   1. Prices full archive bit delta on every greedy step:
//        delta_net_bits(c) = delta_payload_bits(c) - 8 * (1 + len(c) + tables)
//      rejecting rare long substrings (e.g. f=1..2, len=16) that save tokens while
//      inflating archive bytes, and stopping automatically when max delta_net_bits <= 0.
//   2. Runs exact forward-backward omission loss + frequency counting in C and prunes
//      intermediate substrings absorbed by later longer phrases (`omit_bits < header_bits`),
//      refilling freed slots with remaining positive-net-gain candidates within the
//      same wall-clock budget.
#include <math.h>
#define ENGINE_NO_MAIN
#include "../fixed-source-v3/engine.c"

static double estimate_net_archive_bits(
  const Cand *c,
  int gain,
  long cur_emissions,
  double avg_tok_bits,
  int tables
) {
  if (gain <= 0) return -1e9;
  int span = c->len > 1 ? (c->len - 1) : 1;
  long f_min = (gain + span - 1) / span;
  if (f_min < 1) f_min = 1;
  // Estimate actual emission count f in [f_min, min(nocc, gain)]
  long f = f_min;
  if (c->nocc < f) f = c->nocc;
  if (f < 1) f = 1;

  double n_before = (double)(cur_emissions + ndocs);
  double n_after = n_before - (double)gain;
  if (n_after < (double)(ndocs + 1)) n_after = (double)(ndocs + 1);

  // Replaced (gain + f) prior tokens of avg_tok_bits; emitted f copies of new symbol
  // with ideal prefix length log2(n_after / f), plus denominator shrinkage gain * log2(e).
  double code_new = log2(n_after / (double)f);
  if (code_new < 1.0) code_new = 1.0;
  double denom_saving = (double)gain * 1.4426950408889634;
  double payload_saved_bits = ((double)(gain + f) * avg_tok_bits) - ((double)f * code_new) + denom_saving * 0.35;
  double header_bits = 8.0 * (double)(1 + c->len + tables);
  return payload_saved_bits - header_bits;
}

static double compute_empirical_avg_bits_and_prune(
  int *inside,
  int *n_inside,
  unsigned char *member,
  int alphabet,
  int L,
  int tables,
  int do_prune,
  int *pruned_out
) {
  int longest = 0;
  for (int d = 0; d < ndocs; d++) if (dlen[d] > longest) longest = dlen[d];
  int *pl = xmalloc((longest + 2) * sizeof(int));
  int *back = xmalloc((longest + 2) * sizeof(int));
  int *width = xmalloc((longest + 2) * sizeof(int));
  long *freq = calloc((size_t)(ncand + 1), sizeof(long));
  long *omit_tok_loss = calloc((size_t)(ncand + 1), sizeof(long));
  long byte_freq[256];
  memset(byte_freq, 0, sizeof byte_freq);

  long total_toks = 0;
  for (int d = 0; d < ndocs; d++) {
    int s = dstart[d], n = dlen[d];
    for (int i = 0; i <= n; i++) { pl[i] = INF; width[i] = 0; }
    pl[0] = 0;
    for (int i = 0; i < n; i++) {
      if (pl[i] >= INF) continue;
      for (u64 m = mask[s + i]; m; m &= m - 1) {
        int w = __builtin_ctzll(m) + 1, j = i + w, v = pl[i] + 1;
        if (v < pl[j] || (v == pl[j] && w > width[j])) { pl[j] = v; width[j] = w; }
      }
    }
    back[n] = 0;
    for (int i = n - 1; i >= 0; i--) {
      int low = INF;
      for (u64 m = mask[s + i]; m; m &= m - 1) {
        int w = __builtin_ctzll(m) + 1;
        if (back[i + w] < INF && 1 + back[i + w] < low) low = 1 + back[i + w];
      }
      back[i] = low;
    }
    int total_here = pl[n];
    total_toks += total_here;
    for (int e = n; e > 0; e -= width[e]) {
      int l = width[e], i = e - l;
      if (l == 1) {
        byte_freq[text[s + i]]++;
        continue;
      }
      int c = find_candidate(text + s + i, l);
      if (c < 0 || !member[c]) continue;
      freq[c]++;
      if (do_prune) {
        int low = INF;
        for (int j = i + 1; j < e; j++)
          if (pl[j] < INF && back[j] < INF && pl[j] + back[j] - total_here < low)
            low = pl[j] + back[j] - total_here;
        for (int a = i >= L - 1 ? i - L + 1 : 0; a <= i; a++) {
          if (pl[a] >= INF) continue;
          for (u64 m = mask[s + a]; m; m &= m - 1) {
            int w = __builtin_ctzll(m) + 1;
            if (a + w < e || (a == i && w == l) || back[a + w] >= INF) continue;
            if (pl[a] + 1 + back[a + w] - total_here < low)
              low = pl[a] + 1 + back[a + w] - total_here;
          }
        }
        if (low < INF) omit_tok_loss[c] += low;
      }
    }
  }

  double n_sym = (double)(total_toks + ndocs);
  double h_bits = 0.0;
  for (int b = 0; b < 256; b++) {
    if (byte_freq[b] > 0) h_bits += (double)byte_freq[b] * log2(n_sym / (double)byte_freq[b]);
  }
  for (int i = 0; i < *n_inside; i++) {
    int c = inside[i];
    if (freq[c] > 0) h_bits += (double)freq[c] * log2(n_sym / (double)freq[c]);
  }
  if (ndocs > 0) h_bits += (double)ndocs * log2(n_sym / (double)ndocs);
  double avg_bits = n_sym > 0 ? (h_bits / n_sym) : 6.0;

  int dropped = 0;
  if (do_prune) {
    int kept = 0;
    for (int i = 0; i < *n_inside; i++) {
      int c = inside[i];
      const Cand *cand = &cands[c];
      double hdr_bits = 8.0 * (double)(1 + cand->len + tables);
      long f = freq[c];
      long d_tok = omit_tok_loss[c];
      double payload_loss_bits = 0.0;
      if (f > 0 && d_tok > 0) {
        double own_bits = (double)f * log2(n_sym / (double)f);
        double repl_bits = (double)(f + d_tok) * avg_bits;
        payload_loss_bits = repl_bits - own_bits;
      }
      // Prune absorbed / unamortized entry when its marginal payload value < header cost
      if (f == 0 || payload_loss_bits < hdr_bits * 0.96) {
        member[c] = 0;
        remove_entry(cand);
        dropped++;
      } else {
        inside[kept++] = c;
      }
    }
    *n_inside = kept;
  }
  if (pruned_out) *pruned_out = dropped;

  free(pl); free(back); free(width); free(freq); free(omit_tok_loss);
  return avg_bits;
}

static int run_mdl_archive_search(FILE *out, int tables, int L, int kmax, double limit) {
  int alphabet = 0;
  long alpha_bytes = 0;
  FILE *null_out = fopen("/dev/null", "w");
  add_alphabet(null_out, &alphabet, &alpha_bytes);
  fclose(null_out);

  double start = now();
  int max_multi = kmax > alphabet ? (kmax - alphabet) : 0;
  int *inside = xmalloc((size_t)(max_multi + 4) * sizeof(int));
  int n_inside = 0;
  unsigned char *member = calloc((size_t)(ncand + 1), 1);
  int *last_gain = xmalloc((size_t)(ncand + 1) * sizeof(int));
  for (int c = 0; c < ncand; c++) last_gain[c] = cands[c].ub;

  heap = xmalloc((size_t)(ncand + 1) * sizeof(Node));

  // Initial empirical byte entropy
  int dummy_pruned = 0;
  double avg_bits = compute_empirical_avg_bits_and_prune(
    inside, &n_inside, member, alphabet, L, tables, 0, &dummy_pruned
  );

  int stopped = 0;
  int total_pruned = 0;

  for (int round = 0; round < 3; round++) {
    if (now() - start > limit) { stopped = 1; break; }
    heap_n = 0;
    for (int c = 0; c < ncand; c++) {
      if (member[c] || last_gain[c] <= 0) continue;
      double net_ub = estimate_net_archive_bits(&cands[c], last_gain[c], emissions, avg_bits, tables);
      if (net_ub > 0.0) {
        double hdr = (double)(1 + cands[c].len + tables);
        heap_push((Node){net_ub / hdr, c, -1, last_gain[c]});
      }
    }

    int step = 0;
    int added_this_round = 0;
    while (n_inside < max_multi && heap_n > 0) {
      if ((step & 15) == 0 && now() - start > limit) { stopped = 1; break; }
      Node top = heap_pop();
      const Cand *cand = &cands[top.c];
      if (top.stamp != step) {
        int g = gain_of(cand);
        last_gain[top.c] = g;
        double net_b = estimate_net_archive_bits(cand, g, emissions, avg_bits, tables);
        if (net_b <= 0.0) continue;
        double hdr = (double)(1 + cand->len + tables);
        top.gain = g;
        top.key = net_b / hdr;
        top.stamp = step;
        if (heap_n && above(&heap[0], &top)) { heap_push(top); continue; }
      }
      double final_net = estimate_net_archive_bits(cand, top.gain, emissions, avg_bits, tables);
      if (final_net <= 0.0) continue;

      accept(cand);
      member[top.c] = 1;
      inside[n_inside++] = top.c;
      added_this_round++;
      step++;

      if ((added_this_round & 127) == 0) {
        avg_bits = compute_empirical_avg_bits_and_prune(
          inside, &n_inside, member, alphabet, L, tables, 0, &dummy_pruned
        );
      }
    }

    if (stopped || added_this_round == 0) break;

    int pruned_now = 0;
    avg_bits = compute_empirical_avg_bits_and_prune(
      inside, &n_inside, member, alphabet, L, tables, 1, &pruned_now
    );
    total_pruned += pruned_now;
    if (pruned_now == 0) break;
  }

  // Final cleanup prune pass if time remains
  if (!stopped && now() - start < limit) {
    int p_fin = 0;
    compute_empirical_avg_bits_and_prune(
      inside, &n_inside, member, alphabet, L, tables, 1, &p_fin
    );
    total_pruned += p_fin;
  }

  // Emit exact chain file in standard `E` format
  int kk = 0;
  long bb = 0;
  for (int ch = 0; ch < 256; ch++) {
    if (present[ch]) {
      kk++;
      bb += 2;
      unsigned char one = (unsigned char)ch;
      write_entry(out, kk, bb, (n_inside == 0 && kk == alphabet) ? emissions : -1L,
                  (n_inside == 0 && kk == alphabet) ? ndocs : 0, &one, 1);
    }
  }
  for (int i = 0; i < n_inside; i++) {
    const Cand *cand = &cands[inside[i]];
    kk++;
    bb += 1 + cand->len;
    write_entry(out, kk, bb, (i == n_inside - 1) ? emissions : -1L,
                (i == n_inside - 1) ? ndocs : 0, text + occ[cand->off], cand->len);
  }
  fprintf(out, "P pruned=%d final_entries=%d\n", total_pruned, kk);

  free(inside); free(member); free(last_gain);
  return stopped;
}

int main(int argc, char **argv) {
  if (argc != 8) {
    fprintf(stderr, "usage: archive_search TABLES(1|2) POLICY L KMAX LIMIT_SECONDS LIST OUT\n");
    return 2;
  }
  int tables = atoi(argv[1]);
  if (tables != 1 && tables != 2) {
    fprintf(stderr, "TABLES must be 1 or 2\n");
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
  fprintf(out, "H mode=mdl-archive-prune tables=%d policy=%s L=%d K=%d limit=%s\n",
          tables, argv[2], L, kmax, argv[5]);
  int stopped = run_mdl_archive_search(out, tables, L, kmax, limit);
  fprintf(out, "D mdl-archive-prune L=%d candidates=%d occurrences=%ld stopped=%d seconds=%.3f enumerate_seconds=%.3f\n",
          L, ncand, nocc, stopped, now() - t0, enumerated);
  fclose(out);
  return 0;
}
