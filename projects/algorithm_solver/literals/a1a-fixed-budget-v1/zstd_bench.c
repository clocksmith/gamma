// Lean-framed Zstandard complete-archive and per-record decode-latency benchmark.
// Uses libzstd in-process (no subprocess fork overhead) to measure genuine per-record
// decompression latency (p50, p95, p99, mean) and exact 100% byte-for-byte recovery.
//
// Lean framing: ZSTD_c_checksumFlag=0, ZSTD_c_dictIDFlag=0, ZSTD_c_contentSizeFlag=1
// (self-delimiting, self-sized frames without 4-byte dictID or 4-byte xxHash checksum).
//
// Usage:
//   zstd_bench LEVEL LEAN(0|1) DICT_PATH(or "none") REPS FILE_LIST
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/resource.h>
#include <time.h>
#include <zstd.h>

static uint64_t now_ns(void) {
  struct timespec ts;
  clock_gettime(CLOCK_MONOTONIC, &ts);
  return (uint64_t)ts.tv_sec * 1000000000ULL + (uint64_t)ts.tv_nsec;
}

static int varint_len(size_t n) {
  int k = 1;
  while (n >= 0x80) { n >>= 7; k++; }
  return k;
}

static unsigned char *read_all(const char *path, size_t *out_len) {
  FILE *f = fopen(path, "rb");
  if (!f) { perror(path); exit(2); }
  fseek(f, 0, SEEK_END);
  long sz = ftell(f);
  fseek(f, 0, SEEK_SET);
  if (sz < 0) { fprintf(stderr, "ftell failed\n"); exit(2); }
  unsigned char *buf = malloc((size_t)sz + 1);
  if (!buf) { fprintf(stderr, "oom\n"); exit(3); }
  if (sz > 0 && fread(buf, 1, (size_t)sz, f) != (size_t)sz) {
    fprintf(stderr, "short read %s\n", path);
    exit(2);
  }
  fclose(f);
  *out_len = (size_t)sz;
  return buf;
}

static int cmp_double(const void *a, const void *b) {
  double x = *(const double *)a, y = *(const double *)b;
  return (x > y) - (x < y);
}

int main(int argc, char **argv) {
  if (argc != 6) {
    fprintf(stderr, "usage: zstd_bench LEVEL LEAN(0|1) DICT_PATH|none REPS FILE_LIST\n");
    return 2;
  }
  int level = atoi(argv[1]);
  int lean = atoi(argv[2]);
  const char *dict_path = argv[3];
  int reps = atoi(argv[4]);
  const char *list_path = argv[5];
  if (reps < 1) reps = 1;

  unsigned char *dict_buf = NULL;
  size_t dict_size = 0;
  ZSTD_CDict *cdict = NULL;
  ZSTD_DDict *ddict = NULL;
  if (strcmp(dict_path, "none") != 0) {
    dict_buf = read_all(dict_path, &dict_size);
    cdict = ZSTD_createCDict(dict_buf, dict_size, level);
    ddict = ZSTD_createDDict(dict_buf, dict_size);
    if (!cdict || !ddict) { fprintf(stderr, "failed to create zstd dict\n"); return 2; }
  }

  FILE *lf = fopen(list_path, "r");
  if (!lf) { perror(list_path); return 2; }
  int cap = 1024, nfiles = 0;
  unsigned char **raws = malloc((size_t)cap * sizeof(unsigned char *));
  size_t *raw_lens = malloc((size_t)cap * sizeof(size_t));
  char path[4096];
  size_t total_raw = 0;
  while (fgets(path, sizeof path, lf)) {
    path[strcspn(path, "\n")] = 0;
    if (!path[0]) continue;
    if (nfiles == cap) {
      cap *= 2;
      raws = realloc(raws, (size_t)cap * sizeof(unsigned char *));
      raw_lens = realloc(raw_lens, (size_t)cap * sizeof(size_t));
    }
    raws[nfiles] = read_all(path, &raw_lens[nfiles]);
    total_raw += raw_lens[nfiles];
    nfiles++;
  }
  fclose(lf);

  ZSTD_CCtx *cctx = ZSTD_createCCtx();
  ZSTD_DCtx *dctx = ZSTD_createDCtx();
  if (!cctx || !dctx) { fprintf(stderr, "failed to create zstd ctx\n"); return 2; }

  unsigned char **frames = malloc((size_t)nfiles * sizeof(unsigned char *));
  size_t *frame_lens = malloc((size_t)nfiles * sizeof(size_t));
  size_t total_frames = 0;
  size_t ra_index_bytes = 0;
  size_t max_raw = 0;

  uint64_t enc_t0 = now_ns();
  for (int i = 0; i < nfiles; i++) {
    if (raw_lens[i] > max_raw) max_raw = raw_lens[i];
    size_t bound = ZSTD_compressBound(raw_lens[i]);
    frames[i] = malloc(bound);
    ZSTD_CCtx_reset(cctx, ZSTD_reset_session_and_parameters);
    ZSTD_CCtx_setParameter(cctx, ZSTD_c_compressionLevel, level);
    ZSTD_CCtx_setParameter(cctx, ZSTD_c_contentSizeFlag, 1);
    if (lean) {
      ZSTD_CCtx_setParameter(cctx, ZSTD_c_checksumFlag, 0);
      ZSTD_CCtx_setParameter(cctx, ZSTD_c_dictIDFlag, 0);
    } else {
      ZSTD_CCtx_setParameter(cctx, ZSTD_c_checksumFlag, 1);
      ZSTD_CCtx_setParameter(cctx, ZSTD_c_dictIDFlag, 1);
    }
    if (cdict) {
      size_t r = ZSTD_CCtx_refCDict(cctx, cdict);
      if (ZSTD_isError(r)) { fprintf(stderr, "refCDict error: %s\n", ZSTD_getErrorName(r)); return 3; }
    }
    size_t csz = ZSTD_compress2(cctx, frames[i], bound, raws[i], raw_lens[i]);
    if (ZSTD_isError(csz)) {
      fprintf(stderr, "compress2 error on file %d: %s\n", i, ZSTD_getErrorName(csz));
      return 3;
    }
    frame_lens[i] = csz;
    total_frames += csz;
    ra_index_bytes += (size_t)varint_len(csz);
  }
  uint64_t enc_ns = now_ns() - enc_t0;

  unsigned char *dec_buf = malloc(max_raw + 16);
  // First pass: verify 100% byte-for-byte recovery + warm caches.
  for (int i = 0; i < nfiles; i++) {
    size_t dsz = ddict
        ? ZSTD_decompress_usingDDict(dctx, dec_buf, max_raw + 16, frames[i], frame_lens[i], ddict)
        : ZSTD_decompressDCtx(dctx, dec_buf, max_raw + 16, frames[i], frame_lens[i]);
    if (ZSTD_isError(dsz) || dsz != raw_lens[i] || memcmp(dec_buf, raws[i], raw_lens[i]) != 0) {
      fprintf(stderr, "decode mismatch on file %d\n", i);
      return 4;
    }
  }

  // Timed per-record decode latency (microseconds per file, averaged over `reps` calls per file).
  double *per_file_us = malloc((size_t)nfiles * sizeof(double));
  for (int i = 0; i < nfiles; i++) {
    uint64_t t0 = now_ns();
    for (int r = 0; r < reps; r++) {
      size_t dsz = ddict
          ? ZSTD_decompress_usingDDict(dctx, dec_buf, max_raw + 16, frames[i], frame_lens[i], ddict)
          : ZSTD_decompressDCtx(dctx, dec_buf, max_raw + 16, frames[i], frame_lens[i]);
      if (ZSTD_isError(dsz)) { fprintf(stderr, "timed decode error\n"); return 4; }
    }
    uint64_t dt = now_ns() - t0;
    per_file_us[i] = (double)dt / (1000.0 * (double)reps);
  }
  qsort(per_file_us, (size_t)nfiles, sizeof(double), cmp_double);

  double sum_us = 0.0;
  for (int i = 0; i < nfiles; i++) sum_us += per_file_us[i];
  double mean_us = nfiles ? sum_us / nfiles : 0.0;
  double p50_us = nfiles ? per_file_us[(int)(0.50 * (nfiles - 1))] : 0.0;
  double p95_us = nfiles ? per_file_us[(int)(0.95 * (nfiles - 1))] : 0.0;
  double p99_us = nfiles ? per_file_us[(int)(0.99 * (nfiles - 1))] : 0.0;

  struct rusage use;
  getrusage(RUSAGE_SELF, &use);

  size_t complete_bytes = dict_size + total_frames;
  size_t ra_complete_bytes = complete_bytes + (size_t)varint_len((size_t)nfiles) + ra_index_bytes;

  printf("{\n");
  printf("  \"zstd_version\": \"%s\",\n", ZSTD_versionString());
  printf("  \"level\": %d,\n", level);
  printf("  \"lean_framing\": %s,\n", lean ? "true" : "false");
  printf("  \"files\": %d,\n", nfiles);
  printf("  \"source_bytes\": %zu,\n", total_raw);
  printf("  \"dict_bytes\": %zu,\n", dict_size);
  printf("  \"payload_bytes\": %zu,\n", total_frames);
  printf("  \"complete_bytes\": %zu,\n", complete_bytes);
  printf("  \"complete_bits\": %zu,\n", complete_bytes * 8);
  printf("  \"random_access_complete_bytes\": %zu,\n", ra_complete_bytes);
  printf("  \"random_access_complete_bits\": %zu,\n", ra_complete_bytes * 8);
  printf("  \"roundtrip_ok\": true,\n");
  printf("  \"encode_ms\": %.3f,\n", (double)enc_ns / 1e6);
  printf("  \"decode_mean_us\": %.3f,\n", mean_us);
  printf("  \"decode_p50_us\": %.3f,\n", p50_us);
  printf("  \"decode_p95_us\": %.3f,\n", p95_us);
  printf("  \"decode_p99_us\": %.3f,\n", p99_us);
  printf("  \"decode_reps\": %d,\n", reps);
  printf("  \"maxrss_bytes\": %ld\n", (long)use.ru_maxrss);
  printf("}\n");

  for (int i = 0; i < nfiles; i++) { free(raws[i]); free(frames[i]); }
  free(raws); free(raw_lens); free(frames); free(frame_lens); free(dec_buf); free(per_file_us);
  if (dict_buf) free(dict_buf);
  if (cdict) ZSTD_freeCDict(cdict);
  if (ddict) ZSTD_freeDDict(ddict);
  ZSTD_freeCCtx(cctx); ZSTD_freeDCtx(dctx);
  return 0;
}
