// capture_qkv: run article22 through the reference Transformer (debug capture
// build, see src/test_components.cpp) and record, for the 3 vanilla-attention
// layers (3/7/11), the post-rope int8 q/k/v ints of every dumped position plus
// the static per-head scales. Output drives test_attn / bench_attn (real-data
// validation, kept-count stats, realistic-cache benchmark).
//
// File format (little-endian), default data/attn_qkv_article22.bin:
//   char     magic[8] = "ATNQKV22"
//   u32      n_pos, u32 n_layers(=3), u32 d(=192), u32 rope_offset
//   f32      scales[n_layers][3(q,k,v)][3(head)]
//   i8       q[n_layers][n_pos][192]
//   i8       k[n_layers][n_pos][192]
//   i8       v[n_layers][n_pos][192]
// layer index order = {3, 7, 11}.
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <string>
#include <vector>

#include "../model.h"
#include "../testdata.h"
#include "../weights_io.h"

int main(int argc, char** argv) {
  const char* data_dir = nullptr;
  int article = 22;
  long max_pos = 4096;
  for (int i = 1; i < argc; i++) {
    if (std::strcmp(argv[i], "--data") == 0 && i + 1 < argc)
      data_dir = argv[++i];
    else if (std::strcmp(argv[i], "--article") == 0 && i + 1 < argc)
      article = std::atoi(argv[++i]);
    else if (std::strcmp(argv[i], "--max-pos") == 0 && i + 1 < argc)
      max_pos = std::atol(argv[++i]);
    else {
      std::fprintf(stderr, "usage: %s [--data DIR] [--article N] [--max-pos N]\n",
                   argv[0]);
      return 2;
    }
  }

  std::string dir = fx2::find_data_dir(data_dir);
  fx2::TestData td;
  td.load(dir, /*with_ref_probs=*/false);

  long g0 = td.bounds[article];
  long len = td.bounds[article + 1] - g0;
  long n_pos = std::min(len - 1, max_pos);
  long rope_off = td.rope_offsets[article];
  const int van_layers[3] = {3, 7, 11};

  std::printf("capture article %d: %ld tokens, capturing %ld positions, "
              "rope offset %ld\n", article, len, n_pos, rope_off);

  // per-head scales straight from the weights file (bf16 bits -> fp32)
  float scales[3][3][3];
  {
    fx2::WeightsFile wf = fx2::WeightsFile::load((dir + "/weights.bin").c_str());
    const char* sites[3] = {"quantize_queries", "quantize_keys",
                            "quantize_values"};
    for (int li = 0; li < 3; li++)
      for (int s = 0; s < 3; s++) {
        std::string nm = "blocks." + std::to_string(van_layers[li]) +
                         ".attention." + sites[s] + ".scale";
        const fx2::WTensor& t = wf.get(nm, fx2::DT_BF16, {3});
        for (int h = 0; h < 3; h++)
          scales[li][s][h] = fx2::bf16_to_f32(t.bf16_bits()[h]);
      }
  }

  fx2::Transformer model((dir + "/weights.bin").c_str());

  size_t plane = size_t(n_pos) * 192;
  std::vector<int8_t> q(3 * plane), k(3 * plane), v(3 * plane);

  long cur_t = 0;
  model.set_capture([&](const char* name, const float* d, int n) {
    // names: "NN_attn_q_int8" etc. (ints passed as floats)
    if (std::strlen(name) != 14 || std::strncmp(name + 2, "_attn_", 6) != 0 ||
        std::strcmp(name + 9, "_int8") != 0)
      return;
    int layer = (name[0] - '0') * 10 + (name[1] - '0');
    int li = layer == 3 ? 0 : layer == 7 ? 1 : layer == 11 ? 2 : -1;
    if (li < 0 || n != 192) return;
    int8_t* dst = nullptr;
    if (name[8] == 'q') dst = q.data();
    else if (name[8] == 'k') dst = k.data();
    else if (name[8] == 'v') dst = v.data();
    else return;
    dst += size_t(li) * plane + size_t(cur_t) * 192;
    for (int i = 0; i < 192; i++) dst[i] = static_cast<int8_t>(d[i]);
  });

  std::vector<float> probs(205);
  model.begin_article(rope_off);
  for (long t = 0; t < n_pos; t++) {
    cur_t = t;
    model.step(td.tokens[g0 + t], td.prior_row(g0 + t), probs.data());
  }

  std::string out_path = dir + "/attn_qkv_article" + std::to_string(article) + ".bin";
  FILE* f = std::fopen(out_path.c_str(), "wb");
  if (!f) { std::perror("fopen"); return 1; }
  std::fwrite("ATNQKV22", 1, 8, f);
  uint32_t hdr[4] = {uint32_t(n_pos), 3u, 192u, uint32_t(rope_off)};
  std::fwrite(hdr, 4, 4, f);
  std::fwrite(scales, 4, 27, f);
  std::fwrite(q.data(), 1, q.size(), f);
  std::fwrite(k.data(), 1, k.size(), f);
  std::fwrite(v.data(), 1, v.size(), f);
  std::fclose(f);

  // quick sanity: int ranges + scale table
  for (int li = 0; li < 3; li++)
    std::printf("layer %2d scales: sq=(%g,%g,%g) sk=(%g,%g,%g) sv=(%g,%g,%g)\n",
                van_layers[li], scales[li][0][0], scales[li][0][1],
                scales[li][0][2], scales[li][1][0], scales[li][1][1],
                scales[li][1][2], scales[li][2][0], scales[li][2][1],
                scales[li][2][2]);
  std::printf("wrote %s (%ld positions)\n", out_path.c_str(), n_pos);
  return 0;
}
