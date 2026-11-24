// Lagrangian lower bounds on total emissions (FREEZE.md, "bound").
//   bound POLICY L K ITERATIONS UPPER LIST CERTIFICATE
// For prices u >= 0 on occurrences of eligible strings,
//   sum over files of shortest path with edge cost 1 + u
//   minus the K largest per-string totals of u
// is at most the emissions of every dictionary of K entries. The certificate
// holds integer prices scaled by 65536; check_bound.py recomputes the value
// in exact integers without this code.
#define ENGINE_NO_MAIN
#include "engine.c"
#include <math.h>

static const int64_t SCALE = 65536;
typedef struct { int p, len, str; double u; } Edge;
static Edge *edges; static int nedges; static int *edge_at; static int *edge_n;
static double *dist; static int *via; static int *on_path; static double *total_u;

static int cmp_desc(const void *a, const void *b) {
  double x = *(const double *)a, y = *(const double *)b;
  return x < y ? 1 : x > y ? -1 : 0;
}

int main(int argc, char **argv) {
  if (argc != 8) { fprintf(stderr, "usage: bound POLICY L K ITER UPPER LIST CERT\n"); return 2; }
  int policy = set_policy(argv[1]);
  int L = atoi(argv[2]), K = atoi(argv[3]), iters = atoi(argv[4]);
  double upper = atof(argv[5]);
  load(argv[6]);
  enumerate(L);
  int strings = ncand + 256;
  nedges = total;
  for (int c = 0; c < ncand; c++) nedges += cands[c].nocc;
  edges = xmalloc(nedges * sizeof(Edge));
  edge_n = calloc(total + 1, sizeof(int));
  for (int p = 0; p < total; p++) edge_n[p]++;
  for (int c = 0; c < ncand; c++)
    for (int i = 0; i < cands[c].nocc; i++) edge_n[occ[cands[c].off + i]]++;
  edge_at = xmalloc((total + 1) * sizeof(int));
  int sum = 0;
  for (int p = 0; p <= total; p++) { edge_at[p] = sum; if (p < total) sum += edge_n[p]; }
  memset(edge_n, 0, (total + 1) * sizeof(int));
  for (int p = 0; p < total; p++)
    edges[edge_at[p] + edge_n[p]++] = (Edge){p, 1, ncand + text[p], 0};
  for (int c = 0; c < ncand; c++)
    for (int i = 0; i < cands[c].nocc; i++) {
      int p = occ[cands[c].off + i];
      edges[edge_at[p] + edge_n[p]++] = (Edge){p, cands[c].len, c, 0};
    }
  int longest = 0;
  for (int d = 0; d < ndocs; d++) if (dlen[d] > longest) longest = dlen[d];
  dist = xmalloc((longest + 1) * sizeof(double));
  via = xmalloc((longest + 1) * sizeof(int));
  on_path = xmalloc(nedges * sizeof(int));
  total_u = xmalloc(strings * sizeof(double));
  double *sorted = xmalloc(strings * sizeof(double));
  double *grad_s = xmalloc(strings * sizeof(double));
  double best = -1e18, theta = 1.0;
  float *keep = xmalloc(nedges * sizeof(float));
  int since = 0;
  for (int it = 0; it < iters; it++) {
    memset(total_u, 0, strings * sizeof(double));
    for (int e = 0; e < nedges; e++) total_u[edges[e].str] += edges[e].u;
    double path = 0;
    memset(on_path, 0, nedges * sizeof(int));
    for (int d = 0; d < ndocs; d++) {
      int s = dstart[d], n = dlen[d];
      for (int i = 1; i <= n; i++) dist[i] = 1e18;
      dist[0] = 0;
      for (int i = 0; i < n; i++)
        for (int e = edge_at[s + i]; e < edge_at[s + i + 1]; e++) {
          int j = i + edges[e].len;
          double v = dist[i] + 1 + edges[e].u;
          if (v < dist[j]) { dist[j] = v; via[j] = e; }
        }
      path += dist[n];
      for (int i = n; i > 0; i -= edges[via[i]].len) on_path[via[i]] = 1;
    }
    memcpy(sorted, total_u, strings * sizeof(double));
    qsort(sorted, strings, sizeof(double), cmp_desc);
    double top = 0;
    for (int i = 0; i < K && i < strings; i++) if (sorted[i] > 0) top += sorted[i];
    double cut = K <= strings ? sorted[K - 1] : 0;
    double value = path - top;
    if (value > best + 1e-9) {
      best = value;
      since = 0;
      for (int e = 0; e < nedges; e++) keep[e] = (float)edges[e].u;
    } else if (++since >= 30) { theta *= 0.7; since = 0; }
    // x = 1 for the K strings of largest total price.
    double norm = 0;
    for (int e = 0; e < nedges; e++) {
      double x = total_u[edges[e].str] > 0 && total_u[edges[e].str] >= cut ? 1 : 0;
      double g = on_path[e] - x;
      norm += g * g;
    }
    if (norm < 1e-9) break;
    double step = theta * (upper - value) / norm;
    for (int e = 0; e < nedges; e++) {
      double x = total_u[edges[e].str] > 0 && total_u[edges[e].str] >= cut ? 1 : 0;
      double next = edges[e].u + step * (on_path[e] - x);
      edges[e].u = next > 0 ? next : 0;
    }
    if (theta < 1e-4) break;
  }
  (void)grad_s;
  // Scale down slightly, so rounding never turns a price into a larger one.
  FILE *cert = fopen(argv[7], "wb");
  if (!cert) { perror(argv[7]); return 2; }
  uint32_t head[5] = {0x32534642u, (uint32_t)policy, (uint32_t)L, (uint32_t)K, 0};
  long nz = 0;
  for (int e = 0; e < nedges; e++) if ((int64_t)(keep[e] * SCALE) > 0) nz++;
  head[4] = (uint32_t)nz;
  fwrite(head, 4, 5, cert);
  for (int e = 0; e < nedges; e++) {
    int64_t v = (int64_t)(keep[e] * SCALE);
    if (v <= 0) continue;
    uint32_t row[3] = {(uint32_t)edges[e].p, (uint32_t)edges[e].len, (uint32_t)v};
    fwrite(row, 4, 3, cert);
  }
  fclose(cert);
  printf("%s %s L=%d K=%d float_bound=%.3f nonzero=%ld\n", argv[1], argv[6], L, K, best, nz);
  return 0;
}
