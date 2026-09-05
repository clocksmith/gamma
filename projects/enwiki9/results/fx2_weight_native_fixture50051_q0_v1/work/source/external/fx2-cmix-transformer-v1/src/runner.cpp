#include <fstream>
#include <ctime>
#include <chrono>
#include <stdio.h>
#include <cstdlib>
#include <vector>
#include <string.h>
#include <errno.h>
#include <sys/stat.h>

#include "preprocess/preprocessor.h"
#include "preprocess/dictionary.h"
#include "coder/encoder.h"
#include "coder/decoder.h"
#include "predictor.h"

#include <cstdarg>
#include <cstdint>
#include <string>

#include "readalike_prepr/article_reorder.h"
#include "readalike_prepr/self_extract.h"
#include "readalike_prepr/phda9_preprocess.h"
#include "readalike_prepr/misc.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <algorithm>

namespace {
  const int kMinVocabFileSize = 10000;
}

int Help() {
  printf("fx2-cmix\n");
  printf("Compress:\n");
  printf("    to compress enwik9: cmix -e enwik9 [output]\n");
  printf("    to create a header for hutter prize: cmix -h comp_dict_size comp_new_order_size decomp_input_size tf_weights_size\n");
  printf("    with dictionary:    cmix -c [dictionary] [input] [output]\n");
  printf("    without dictionary: cmix -c [input] [output]\n");
  printf("    no preprocessing:   cmix -n [input] [output]\n");
  printf("    only preprocessing: cmix -s [dictionary] [input] [output]\n");
  printf("                        cmix -s [input] [output]\n");
  printf("Decompress:\n");
  printf("    with dictionary:    cmix -d [dictionary] [input] [output]\n");
  printf("    without dictionary: cmix -d [input] [output]\n");
  printf("    to decompress enwik9: cmix (no arguments)\n");
  printf("Optional flags (compression modes -c, -n, -e, and argument-less\n");
  printf("enwik9 decompression, which must be given the same model-affecting\n");
  printf("flags as the -e run that produced the archive):\n");
  printf("    --ppmd-only                       run only the ppmd, no other model\n");
  printf("                                      (intended for --save-ppmd-probs)\n");
  printf("    --transformer-only                run only the ppmd and the transformer it\n");
  printf("                                      feeds, no other model (intended for\n");
  printf("                                      --save-transformer-probs); requires a mode\n");
  printf("                                      that runs the transformer: -e, argument-less\n");
  printf("                                      enwik9 decompression, or -c/-n with\n");
  printf("                                      --transformer\n");
  printf("    --bytes-only                      run no model at all; only preprocess and\n");
  printf("                                      write the --save-* files (compression only)\n");
  printf("    --save-ppmd-bytes <file>          write the lstm-vocabulary index of every\n");
  printf("                                      byte the ppmd processes (one byte each)\n");
  printf("                                      (compression only)\n");
  printf("    --save-article-boundaries <file>  write int32 offsets into the\n");
  printf("                                      --save-ppmd-bytes stream: 0, the offset of\n");
  printf("                                      the first byte after every article\n");
  printf("                                      separator, and the stream size (-e only)\n");
  printf("    --save-ppmd-probs <file>          write every probability distribution the\n");
  printf("                                      ppmd outputs, restricted to the lstm\n");
  printf("                                      vocabulary, as float16\n");
  printf("    --load-transformer-probs <file>   do not run the ppmd or the\n");
  printf("                                      transformer; replace the transformer's\n");
  printf("                                      distributions with the ones in <file> (same\n");
  printf("                                      format as --save-ppmd-probs); requires a mode\n");
  printf("                                      that runs the transformer: -e, argument-less\n");
  printf("                                      enwik9 decompression, or -c/-n with\n");
  printf("                                      --transformer\n");
  printf("    --save-transformer-probs <file>   write every distribution passed downstream\n");
  printf("                                      in place of the lstm's output (the\n");
  printf("                                      transformer's rows, and the ppmd's rows at\n");
  printf("                                      the article-start tokens the transformer\n");
  printf("                                      cannot predict) as float16, in the format of\n");
  printf("                                      --save-ppmd-probs; requires a mode that runs\n");
  printf("                                      the transformer: -e, argument-less enwik9\n");
  printf("                                      decompression, or -c/-n with --transformer\n");
  printf("    --transformer <weights>           (testing; -c, -n and -d only) replace the\n");
  printf("                                      lstm with the pretrained transformer, as -e\n");
  printf("                                      and argument-less decompression do with the\n");
  printf("                                      embedded weights; compression and\n");
  printf("                                      decompression must both use it or neither\n");
  return -1;
}

struct ExtractionOptions {
  bool ppmd_only = false;
  // Like ppmd_only, but the transformer the ppmd feeds is run as well.
  bool transformer_only = false;
  bool bytes_only = false;
  std::string save_ppmd_bytes;
  std::string save_article_boundaries;
  std::string save_ppmd_probs;
  std::string load_transformer_probs;
  // Testing option: weights file enabling the transformer in -c, -n and -d
  // (the modes -e and argument-less decompression enable it themselves with
  // the embedded weights). Validated separately from AnySet.
  std::string transformer;
  // Testing option: dump of the distributions passed downstream in place of
  // the lstm's output (see PredictorOptions::save_transformer_probs).
  std::string save_transformer_probs;
  bool AnySet() const {
    return ppmd_only || transformer_only || bytes_only ||
        !save_ppmd_bytes.empty() ||
        !save_article_boundaries.empty() || !save_ppmd_probs.empty() ||
        !load_transformer_probs.empty();
  }
};

[[noreturn]] void UsageError(const char* fmt, ...) {
  va_list args;
  va_start(args, fmt);
  fprintf(stderr, "cmix: invalid command line: ");
  vfprintf(stderr, fmt, args);
  fprintf(stderr, "\n\n");
  va_end(args);
  Help();
  exit(1);
}

// Every path named on the command line is checked here, up front, so that a
// typo or a missing file is reported immediately with the offending path
// instead of surfacing much later as a crash, an empty output or the generic
// usage text. `what` names the argument, e.g. "input file".
void RequireReadableFile(const char* what, const std::string& path) {
  FILE* f = fopen(path.c_str(), "rb");
  if (f == NULL) {
    UsageError("%s '%s' cannot be read: %s", what, path.c_str(),
        strerror(errno));
  }
  fclose(f);
  struct stat st;
  if (stat(path.c_str(), &st) == 0 && S_ISDIR(st.st_mode)) {
    UsageError("%s '%s' is a directory, not a file", what, path.c_str());
  }
}

// Extracts the long options from argv (compacting argv in place) so the
// positional arguments can be handled afterwards.
ExtractionOptions ParseExtractionOptions(int* argc, char** argv) {
  ExtractionOptions options;
  int out = 1;
  for (int i = 1; i < *argc; ++i) {
    std::string arg = argv[i];
    if (arg.rfind("--", 0) != 0) {
      argv[out++] = argv[i];
      continue;
    }
    if (arg == "--ppmd-only") {
      if (options.ppmd_only) UsageError("duplicate --ppmd-only");
      options.ppmd_only = true;
      continue;
    }
    if (arg == "--transformer-only") {
      if (options.transformer_only) UsageError("duplicate --transformer-only");
      options.transformer_only = true;
      continue;
    }
    if (arg == "--bytes-only") {
      if (options.bytes_only) UsageError("duplicate --bytes-only");
      options.bytes_only = true;
      continue;
    }
    std::string* value = NULL;
    if (arg == "--save-ppmd-bytes") value = &options.save_ppmd_bytes;
    else if (arg == "--save-article-boundaries") {
      value = &options.save_article_boundaries;
    } else if (arg == "--save-ppmd-probs") value = &options.save_ppmd_probs;
    else if (arg == "--load-transformer-probs") {
      value = &options.load_transformer_probs;
    }
    else if (arg == "--transformer") value = &options.transformer;
    else if (arg == "--save-transformer-probs") {
      value = &options.save_transformer_probs;
    }
    else UsageError("unknown option '%s'", arg.c_str());
    if (!value->empty()) UsageError("duplicate %s", arg.c_str());
    if (i + 1 >= *argc || argv[i + 1][0] == '\0') {
      UsageError("%s requires a filename", arg.c_str());
    }
    *value = argv[++i];
  }
  *argc = out;
  return options;
}

// mode == 0 is the argument-less enwik9 decompression: the counterpart of -e,
// running the same models on the same data. The options that change what the
// predictor does therefore apply to it exactly as they do to -e (and have to,
// since the decompressor's models must match the compressor's); the ones that
// dump or replace the compressor's input have no counterpart there.
void ValidateExtractionOptions(const ExtractionOptions& options, char mode) {
  bool enwik9_decompression = mode == 0;
  // The options that name an existing file (the --save-* ones name files to be
  // created, so they are not checked here).
  if (!options.transformer.empty()) {
    RequireReadableFile("--transformer weights file", options.transformer);
  }
  if (!options.load_transformer_probs.empty()) {
    RequireReadableFile("--load-transformer-probs file",
        options.load_transformer_probs);
  }
  if (!options.transformer.empty()) {
    if (mode != 'c' && mode != 'n' && mode != 'd') {
      UsageError("--transformer can only be used with -c, -n or -d (-e and "
          "argument-less decompression use the embedded weights themselves)");
    }
    if (options.ppmd_only || options.bytes_only) {
      UsageError("--transformer cannot be combined with --ppmd-only or "
          "--bytes-only: those options do not run the model the transformer "
          "replaces");
    }
  }
  bool transformer_runs = mode == 'e' || enwik9_decompression ||
      (!options.transformer.empty() && (mode == 'c' || mode == 'n'));
  if (!options.save_transformer_probs.empty()) {
    if (!transformer_runs) {
      UsageError("--save-transformer-probs requires a mode that runs the "
          "transformer: -e, argument-less enwik9 decompression, or -c/-n with "
          "--transformer");
    }
    if (!options.load_transformer_probs.empty()) {
      UsageError("--save-transformer-probs cannot be used with "
          "--load-transformer-probs: the transformer is not run, so there are "
          "no distributions to save");
    }
  }
  if (!options.AnySet()) return;
  if (mode != 'c' && mode != 'n' && mode != 'e' && !enwik9_decompression) {
    UsageError("--ppmd-only, --transformer-only, --bytes-only, "
        "--save-ppmd-bytes, "
        "--save-article-boundaries, --save-ppmd-probs and "
        "--load-transformer-probs can only be used when compressing (-c, -n "
        "or -e) or when decompressing enwik9 (no arguments)");
  }
  if (enwik9_decompression) {
    if (options.bytes_only) {
      UsageError("--bytes-only cannot be used with argument-less enwik9 "
          "decompression: it runs no model, and without the models there is "
          "nothing to decode");
    }
    if (!options.save_ppmd_bytes.empty()) {
      UsageError("--save-ppmd-bytes can only be used when compressing (-c, -n "
          "or -e): it dumps the bytes the compressor feeds the ppmd");
    }
  }
  if (!options.save_article_boundaries.empty() && mode != 'e') {
    UsageError("--save-article-boundaries can only be used with -e: article "
        "boundaries are specific to the enwik9 preprocessing pipeline");
  }
  if (options.transformer_only && !transformer_runs) {
    UsageError("--transformer-only requires a mode that runs the "
        "transformer: -e, argument-less enwik9 decompression, or -c/-n with "
        "--transformer");
  }
  if (options.ppmd_only && options.bytes_only) {
    UsageError("--ppmd-only and --bytes-only cannot be used together");
  }
  if (options.transformer_only && options.ppmd_only) {
    UsageError("--transformer-only and --ppmd-only cannot be used together");
  }
  if (options.transformer_only && options.bytes_only) {
    UsageError("--transformer-only and --bytes-only cannot be used together");
  }
  if (!options.load_transformer_probs.empty()) {
    if (options.transformer_only) {
      UsageError("--load-transformer-probs cannot be used with "
          "--transformer-only: --load-transformer-probs replaces the "
          "transformer's output instead of running it");
    }
    if (options.ppmd_only) {
      UsageError("--load-transformer-probs cannot be used with --ppmd-only: "
          "--load-transformer-probs does not run the ppmd, while --ppmd-only "
          "runs only the ppmd");
    }
    if (options.bytes_only) {
      UsageError("--load-transformer-probs cannot be used with --bytes-only: "
          "--bytes-only runs no model, so there is nothing to feed the "
          "loaded probabilities to");
    }
    if (!options.save_ppmd_probs.empty()) {
      UsageError("--load-transformer-probs cannot be used with "
          "--save-ppmd-probs: the ppmd is not run when "
          "--load-transformer-probs is given, so there are no ppmd "
          "probabilities to save");
    }
    if (mode != 'e' && !enwik9_decompression && options.transformer.empty()) {
      UsageError("--load-transformer-probs replaces the transformer's output "
          "distributions, but this mode runs the lstm and not the "
          "transformer: use -e, argument-less enwik9 decompression, or -c/-n "
          "with --transformer");
    }
  }
  if (options.bytes_only) {
    if (!options.save_ppmd_probs.empty()) {
      UsageError("--save-ppmd-probs cannot be used with --bytes-only: the "
          "ppmd is not run with --bytes-only, so there are no probabilities "
          "to save");
    }
    if (options.save_ppmd_bytes.empty() &&
        options.save_article_boundaries.empty()) {
      UsageError("--bytes-only without --save-ppmd-bytes or "
          "--save-article-boundaries would produce no output at all");
    }
  }
}

size_t getFileSize(const std::string& path) {
  // // get the size of the output file
  FILE *f = fopen(path.c_str(), "rb");
  if (f == NULL) {
    printf("can't open file for measuring its size");
    return 0;
  }
  fseek(f, 0, SEEK_END);
  size_t output_size = ftell(f);
  fclose(f);
  return output_size;
}

void WriteHeader(unsigned long long length, const std::vector<bool>& vocab,
    bool dictionary_used, std::ofstream* os) {
  for (int i = 4; i >= 0; --i) {
    char c = length >> (8*i);
    if (i == 4) {
      c &= 0x7F;
      if (dictionary_used) c |= 0x80;
    }
    os->put(c);
  }
  if (length < kMinVocabFileSize) return;
  for (int i = 0; i < 32; ++i) {
    unsigned char c = 0;
    for (int j = 0; j < 8; ++j) {
      if (vocab[i * 8 + j]) c += 1<<j;
    }
    os->put(c);
  }
}

void WriteStorageHeader(FILE* out, bool dictionary_used) {
  for (int i = 4; i >= 0; --i) {
    char c = 0;
    if (i == 4 && dictionary_used) c = 0x80;
    putc(c, out);
  }
}

void ReadHeader(std::ifstream* is, unsigned long long* length,
    bool* dictionary_used, std::vector<bool>* vocab) {
  *length = 0;
  for (int i = 0; i <= 4; ++i) {
    *length <<= 8;
    unsigned char c = is->get();
    if (i == 0) {
      if (c&0x80) *dictionary_used = true;
      else *dictionary_used = false;
      c &= 0x7F;
    }
    *length += c;
  }
  if (*length == 0) return;
  if (*length < kMinVocabFileSize) {
    std::fill(vocab->begin(), vocab->end(), true);
    return;
  }
  for (int i = 0; i < 32; ++i) {
    unsigned char c = is->get();
    for (int j = 0; j < 8; ++j) {
      if (c & (1<<j)) (*vocab)[i * 8 + j] = true;
    }
  }
}

void ExtractVocab(unsigned long long num_bytes, std::ifstream* is,
    std::vector<bool>* vocab) {
  for (size_t pos = 0; pos < num_bytes; ++pos) {
    unsigned char c = is->get();
    (*vocab)[c] = true;
  }
  assert(num_bytes >= 2);
  std::valarray<int> byte_map(0, 256);
  uint16_t offset = 0;
  for (int i = 0; i < 256; ++i) {
    byte_map[i] = offset;
    if ((*vocab)[i]) ++offset;
  }
}

void ClearOutput() {
  fprintf(stderr, "\r%*s\r", 70, "");
  fflush(stderr);
}

void FormatDuration(double seconds, char* out, size_t out_size) {
  int total = (int)(seconds + 0.5);
  snprintf(out, out_size, "%02d:%02d:%02d", total / 3600, (total / 60) % 60,
      total % 60);
}

void PrintProgress(double frac,
    const std::chrono::steady_clock::time_point& start) {
  double elapsed = std::chrono::duration<double>(
      std::chrono::steady_clock::now() - start).count();
  char elapsed_str[16];
  FormatDuration(elapsed, elapsed_str, sizeof(elapsed_str));
  if (frac > 0) {
    char remaining_str[16];
    FormatDuration(elapsed * (100.0 - frac) / frac, remaining_str,
        sizeof(remaining_str));
    fprintf(stderr, "\rprogress: %.2f%%  elapsed: %s  remaining: %s ", frac,
        elapsed_str, remaining_str);
  } else {
    fprintf(stderr, "\rprogress: %.2f%%  elapsed: %s ", frac, elapsed_str);
  }
  fflush(stderr);
}

// Writes, for every byte of the preprocessed stream (which is exactly the
// sequence of bytes the ppmd processes), its index in the lstm's vocabulary.
void SavePpmdBytes(const std::string& temp_path,
    unsigned long long temp_bytes, const std::vector<bool>& vocab,
    const std::string& out_path) {
  int byte_to_index[256];
  int index = 0;
  for (int i = 0; i < 256; ++i) {
    byte_to_index[i] = vocab[i] ? index++ : -1;
  }
  FILE* in = fopen(temp_path.c_str(), "rb");
  if (!in) Fail("cannot open temporary file %s", temp_path.c_str());
  FILE* out = fopen(out_path.c_str(), "wb");
  if (!out) Fail("cannot open %s for writing", out_path.c_str());
  std::vector<unsigned char> buffer(1 << 20);
  unsigned long long pos = 0;
  while (pos < temp_bytes) {
    size_t n = fread(buffer.data(), 1, buffer.size(), in);
    if (n == 0) Fail("unexpected end of temporary file %s", temp_path.c_str());
    for (size_t i = 0; i < n; ++i) {
      int mapped = byte_to_index[buffer[i]];
      if (mapped < 0) {
        Fail("--save-ppmd-bytes: byte 0x%02x at position %llu of the "
            "preprocessed input is not in the lstm's vocabulary",
            buffer[i], pos + i);
      }
      buffer[i] = (unsigned char)mapped;
    }
    if (fwrite(buffer.data(), 1, n, out) != n) {
      Fail("failed writing to %s (disk full?)", out_path.c_str());
    }
    pos += n;
  }
  fclose(in);
  fclose(out);
  printf("saved %llu byte indices to %s\n", pos, out_path.c_str());
}

// Encodes a snippet of the input exactly like preprocessor::encode_text does
// (WRT dictionary transform followed by its byte remapping). The snippet must
// start and end with non-word bytes and be delimited by non-word bytes in the
// stream (article markers are: '\n' on both sides), so this standalone
// encoding is byte-identical to how the snippet appears inside the encoded
// stream.
std::vector<unsigned char> BuildEncodedPattern(FILE* dictionary,
    const char* text) {
  const int text_len = (int)strlen(text);
  std::vector<char> buf(text, text + text_len);
  preprocessor::Dictionary dict(dictionary, true, false);
  FILE* in = fmemopen(buf.data(), text_len, "rb");
  FILE* out = tmpfile();
  if (in == NULL || out == NULL) Fail("cannot create a temporary file");
  dict.Encode(in, text_len, out);
  long size = ftell(out);
  if (size <= 2) Fail("failed to encode the pattern '%s'", text);
  std::vector<unsigned char> pattern(size);
  rewind(out);
  if (fread(pattern.data(), 1, size, out) != (size_t)size) {
    Fail("failed to read back the encoded pattern");
  }
  fclose(in);
  fclose(out);
  for (auto& byte : pattern) {  // the byte remapping from encode_text
    int c = byte;
    if (c>='{' && c<127) c+='P'-'{';
    else if (c>='P' && c<'T') c-='P'-'{';
    else if ( (c>=':' && c<='?') || (c>='J' && c<='O') ) c^=0x70;
    if (c=='X' || c=='`') c^='X'^'`';
    byte = (unsigned char)c;
  }
  return pattern;
}

// Every article in the preprocessed stream starts with the encoding of
// "  <page>\n    <title>" (15 bytes with the WRT dictionary transform); call
// that the separator. Writes the boundaries as int32s: 0, the offset of the
// first byte after every occurrence of the separator (in ascending order),
// and finally the size of the stream. Each consecutive pair of boundaries
// delimits one chunk; every chunk except the last therefore ends with the
// separator (the stream does not end with one: enwik9 is cut mid-article).
// The first chunk is the block/preprocessor headers plus the first
// separator, the last chunk is the truncated final article.
//
// The same scan also recomputes the boundaries this code used to write (0,
// the offset of every line-start "  <page>" marker except the first, the
// stream size) and fails loudly unless the new list is exactly: 0, the end
// of the first separator (offset 28 + 15, which the old list did not
// record), every old boundary + 15, and the stream size once.
void SaveArticleBoundaries(const std::string& temp_path,
    unsigned long long temp_bytes, FILE* dictionary,
    const std::vector<bool>& vocab, const std::string& out_path) {
  if (temp_bytes > 0x7FFFFFFFULL) {
    Fail("--save-article-boundaries: the preprocessed input has %llu bytes, "
        "which does not fit in an int32", temp_bytes);
  }
  FILE* in = fopen(temp_path.c_str(), "rb");
  if (!in) Fail("cannot open temporary file %s", temp_path.c_str());

  // The stream starts with a 5 byte block header (type + length). TEXT
  // blocks have one more byte saying whether the WRT dictionary transform
  // was applied.
  int type = getc(in);
  for (int i = 0; i < 4; ++i) getc(in);
  unsigned long long payload_start = 5;
  bool wrt = false;
  if (type == preprocessor::TEXT) {
    wrt = getc(in) != 0;
    payload_start = 6;
  }
  std::vector<unsigned char> marker;     // encoded "  <page>"
  std::vector<unsigned char> separator;  // encoded "  <page>\n    <title>"
  if (wrt) {
    if (dictionary == NULL) {
      Fail("--save-article-boundaries: the stream is dictionary-encoded but "
          "no dictionary is available");
    }
    marker = BuildEncodedPattern(dictionary, "  <page>");
    separator = BuildEncodedPattern(dictionary, "  <page>\n    <title>");
  } else {
    const char* raw_marker = "  <page>";
    const char* raw_separator = "  <page>\n    <title>";
    marker.assign(raw_marker, raw_marker + strlen(raw_marker));
    separator.assign(raw_separator, raw_separator + strlen(raw_separator));
  }
  const size_t mlen = marker.size(), slen = separator.size();
  if (slen < mlen || memcmp(separator.data(), marker.data(), mlen) != 0) {
    Fail("--save-article-boundaries: the encoded separator does not start "
        "with the encoded page marker");
  }
  if (wrt) {
    if (slen != 15) {
      Fail("--save-article-boundaries: the encoded separator has %zu bytes, "
          "expected 15", slen);
    }
    // In --save-ppmd-bytes vocabulary indices the separator must be exactly
    // the 15-byte sequence the downstream training code splits on.
    static const unsigned char kExpected[15] = {
        0x08, 0x08, 0x25, 0xac, 0x65, 0x27, 0x05,
        0x08, 0x08, 0x08, 0x08, 0x25, 0xac, 0x68, 0x27};
    int byte_to_index[256];
    int index = 0;
    for (int i = 0; i < 256; ++i) byte_to_index[i] = vocab[i] ? index++ : -1;
    for (size_t i = 0; i < slen; ++i) {
      if (byte_to_index[separator[i]] != (int)kExpected[i]) {
        Fail("--save-article-boundaries: byte %zu of the encoded separator "
            "maps to vocabulary index %d, expected 0x%02x", i,
            byte_to_index[separator[i]], kExpected[i]);
      }
    }
  }

  // temp_bytes fits in an int32, so the whole stream fits in memory.
  rewind(in);
  std::vector<unsigned char> data(temp_bytes);
  if (fread(data.data(), 1, temp_bytes, in) != temp_bytes) {
    Fail("failed to read temporary file %s", temp_path.c_str());
  }
  fclose(in);

  // One scan collects both boundary flavours. The marker's encoding of '<'
  // is rarer than that of ' ', so anchor the search on it.
  std::vector<int32_t> old_boundaries;
  old_boundaries.push_back(0);
  std::vector<int32_t> separator_ends;
  long long first_marker = -1;  // the line-start match the old code skipped
  const unsigned char anchor = marker[2];
  if (temp_bytes >= mlen) {
    const size_t limit = temp_bytes - mlen + 1;
    size_t i = 0;
    while (i < limit) {
      const unsigned char* hit = static_cast<const unsigned char*>(
          memchr(data.data() + i + 2, anchor, limit - i));
      if (hit == NULL) break;
      size_t candidate = (size_t)(hit - data.data()) - 2;
      i = candidate + 1;
      if (memcmp(data.data() + candidate, marker.data(), mlen) != 0) {
        continue;
      }
      // Old semantics: a line-start (or payload-start) marker, first skipped.
      if (candidate == payload_start ||
          (candidate > 0 && data[candidate - 1] == '\n')) {
        if (first_marker < 0) {
          first_marker = (long long)candidate;
        } else {
          old_boundaries.push_back((int32_t)candidate);
        }
      }
      // New semantics: any occurrence of the full separator.
      if (candidate + slen <= temp_bytes &&
          memcmp(data.data() + candidate, separator.data(), slen) == 0) {
        separator_ends.push_back((int32_t)(candidate + slen));
      }
    }
  }
  old_boundaries.push_back((int32_t)temp_bytes);
  if (separator_ends.empty()) {
    Fail("--save-article-boundaries: no article separator found in the "
        "preprocessed stream");
  }

  std::vector<int32_t> boundaries;
  boundaries.push_back(0);
  boundaries.insert(boundaries.end(), separator_ends.begin(),
      separator_ends.end());
  if ((unsigned long long)boundaries.back() == temp_bytes) {
    // The stream ends with the separator, so the stream size is already the
    // last boundary; do not record it twice.
    fprintf(stderr, "warning: the preprocessed stream ends with the article "
        "separator; this did not use to be the case\n");
  } else {
    boundaries.push_back((int32_t)temp_bytes);
  }

  // Cross-check the new boundaries against the old semantics.
  if (first_marker < 0) {
    Fail("--save-article-boundaries: no line-start page marker found");
  }
  if (wrt && first_marker != 28) {
    Fail("--save-article-boundaries: first separator at offset %lld, "
        "expected 28 (right after the block and preprocessor headers)",
        first_marker);
  }
  if (boundaries.size() != old_boundaries.size() + 1) {
    Fail("--save-article-boundaries: %zu boundaries, expected %zu (the "
        "old-style count plus one for the first separator)",
        boundaries.size(), old_boundaries.size() + 1);
  }
  if (boundaries[0] != 0) {
    Fail("--save-article-boundaries: first boundary is %d, expected 0",
        boundaries[0]);
  }
  if ((unsigned long long)boundaries[1] !=
      (unsigned long long)first_marker + slen) {
    Fail("--save-article-boundaries: second boundary is %d, expected %lld "
        "(the end of the first separator, which is not an old-style "
        "boundary)", boundaries[1], first_marker + (long long)slen);
  }
  for (size_t j = 1; j + 1 < old_boundaries.size(); ++j) {
    if (boundaries[j + 1] != old_boundaries[j] + (int32_t)slen) {
      Fail("--save-article-boundaries: boundary %zu is %d, expected the "
          "old-style boundary %d + %zu", j + 1, boundaries[j + 1],
          old_boundaries[j], slen);
    }
  }
  if ((unsigned long long)boundaries.back() != temp_bytes) {
    Fail("--save-article-boundaries: last boundary is %d, expected the "
        "stream size %llu", boundaries.back(), temp_bytes);
  }
  if (boundaries[boundaries.size() - 2] == boundaries.back()) {
    Fail("--save-article-boundaries: the stream size appears twice at the "
        "end of the boundary list");
  }

  FILE* out = fopen(out_path.c_str(), "wb");
  if (!out) Fail("cannot open %s for writing", out_path.c_str());
  if (fwrite(boundaries.data(), sizeof(int32_t), boundaries.size(), out) !=
      boundaries.size()) {
    Fail("failed writing to %s (disk full?)", out_path.c_str());
  }
  fclose(out);
  printf("saved %zu article boundaries (%zu chunks) to %s\n",
      boundaries.size(), boundaries.size() - 1, out_path.c_str());
}

void Compress(unsigned long long input_bytes, std::ifstream* is,
    std::ofstream* os, unsigned long long* output_bytes, Predictor* p) {
  Encoder e(os, p);

  FILE* progress = fopen("./progress.log", "w");
  unsigned long long percent = 1 + (input_bytes / 10000);
  std::chrono::steady_clock::time_point start =
      std::chrono::steady_clock::now();
  ClearOutput();
  size_t buffer_size = 1 * 256 * 1024;
  size_t bytes_remaining = (size_t) input_bytes;
  char* buffer = new char[buffer_size];
  is->read(buffer, std::min(bytes_remaining, buffer_size));
  bytes_remaining -= std::min(bytes_remaining, buffer_size);
  for (unsigned long long pos = 0; pos < input_bytes; ++pos) {
    unsigned char c = buffer[pos % buffer_size];
    for (int j = 7; j >= 0; --j) {
      e.Encode((c>>j)&1);
    }
    if (pos % buffer_size == buffer_size - 1) {
      is->read(buffer, std::min(bytes_remaining, buffer_size));
      bytes_remaining -= std::min(bytes_remaining, buffer_size);
    }
    if (pos % percent == 0) {
      double frac = 100.0 * pos / input_bytes;
      PrintProgress(frac, start);

      fprintf(progress, "%.2f %zu\n", frac, e.OutputSize());
      fflush(progress);
    }
  }
  e.Flush();
  *output_bytes = os->tellp();
  delete [] buffer;
}

void Decompress(unsigned long long output_length, std::ifstream* is,
                std::ofstream* os, Predictor* p) {
  Decoder d(is, p);
  unsigned long long percent = 1 + (output_length / 10000);
  std::chrono::steady_clock::time_point start =
      std::chrono::steady_clock::now();
  ClearOutput();
  for(unsigned long long pos = 0; pos < output_length; ++pos) {
    int byte = 1;
    while (byte < 256) {
      byte += byte + d.Decode();
    }
    os->put(byte);
    if (pos % percent == 0) {
      double frac = 100.0 * pos / output_length;
      PrintProgress(frac, start);
    }
  }
}

bool Store(const std::string& input_path, const std::string& temp_path,
    const std::string& output_path, FILE* dictionary,
    unsigned long long* input_bytes, unsigned long long* output_bytes) {
  FILE* data_in = fopen(input_path.c_str(), "rb");
  if (!data_in) return false;
  FILE* data_out = fopen(output_path.c_str(), "wb");
  if (!data_out) return false;
  fseek(data_in, 0L, SEEK_END);
  *input_bytes = ftell(data_in);
  fseek(data_in, 0L, SEEK_SET);
  WriteStorageHeader(data_out, dictionary != NULL);
  fprintf(stderr, "\rpreprocessing...");
  fflush(stderr);
  preprocessor::Encode(data_in, data_out, *input_bytes, temp_path, dictionary);
  fseek(data_out, 0L, SEEK_END);
  *output_bytes = ftell(data_out);
  fclose(data_in);
  fclose(data_out);
  return true;
}

// If transformer_weights is nonempty, the lstm is replaced by the pretrained
// transformer loaded from that file (enwik9-specialized compression); with
// --load-transformer-probs the transformer is not run and its output
// distributions are read from that file instead.
bool RunCompression(bool enable_preprocess, const std::string& input_path,
    const std::string& temp_path, const std::string& output_path,
    FILE* dictionary, unsigned long long* input_bytes,
    unsigned long long* output_bytes, const ExtractionOptions& extraction,
    const std::string& transformer_weights = "") {
  FILE* data_in = fopen(input_path.c_str(), "rb");
  if (!data_in) Fail("cannot open input file %s", input_path.c_str());
  FILE* temp_out = fopen(temp_path.c_str(), "wb");
  if (!temp_out) {
    Fail("cannot open temporary file %s for writing", temp_path.c_str());
  }

  fseek(data_in, 0L, SEEK_END);
  *input_bytes = ftell(data_in);
  fseek(data_in, 0L, SEEK_SET);

  if (enable_preprocess) {
    fprintf(stderr, "\rpreprocessing...");
    fflush(stderr);
    preprocessor::Encode(data_in, temp_out, *input_bytes, temp_path,
        dictionary);
  } else {
    preprocessor::NoPreprocess(data_in, temp_out, *input_bytes);
  }
  fclose(data_in);
  fclose(temp_out);

  std::ifstream temp_in(temp_path, std::ios::in | std::ios::binary);
  if (!temp_in.is_open()) {
    Fail("cannot open temporary file %s", temp_path.c_str());
  }

  temp_in.seekg(0, std::ios::end);
  unsigned long long temp_bytes = temp_in.tellg();
  temp_in.seekg(0, std::ios::beg);

  std::vector<bool> vocab(256, false);
  if (temp_bytes < kMinVocabFileSize) {
    std::fill(vocab.begin(), vocab.end(), true);
  } else {
    ExtractVocab(temp_bytes, &temp_in, &vocab);
    temp_in.seekg(0, std::ios::beg);
  }

  if (!extraction.save_ppmd_bytes.empty()) {
    SavePpmdBytes(temp_path, temp_bytes, vocab, extraction.save_ppmd_bytes);
  }
  if (!extraction.save_article_boundaries.empty()) {
    SaveArticleBoundaries(temp_path, temp_bytes, dictionary, vocab,
        extraction.save_article_boundaries);
  }
  if (extraction.bytes_only) {
    temp_in.close();
    remove(temp_path.c_str());
    *output_bytes = 0;
    return true;
  }

  std::ofstream data_out(output_path, std::ios::out | std::ios::binary);
  if (!data_out.is_open()) {
    Fail("cannot open output file %s for writing", output_path.c_str());
  }

  WriteHeader(temp_bytes, vocab, dictionary != NULL, &data_out);
  PredictorOptions predictor_options;
  predictor_options.ppmd_only = extraction.ppmd_only;
  predictor_options.transformer_only = extraction.transformer_only;
  predictor_options.save_ppmd_probs = extraction.save_ppmd_probs;
  predictor_options.load_transformer_probs = extraction.load_transformer_probs;
  predictor_options.num_input_bytes = temp_bytes;
  predictor_options.transformer_weights = transformer_weights;
  predictor_options.save_transformer_probs = extraction.save_transformer_probs;
  Predictor p(vocab, predictor_options);
  if (enable_preprocess && !extraction.ppmd_only && !extraction.transformer_only) {
    // Pretraining only affects the models --ppmd-only and --transformer-only
    // skip; neither the ppmd nor the transformer is pretrained, so their
    // output is unchanged by skipping this.
    preprocessor::Pretrain(&p, dictionary);
  }
  Compress(temp_bytes, &temp_in, &data_out, output_bytes, &p);
  temp_in.close();
  data_out.close();
  remove(temp_path.c_str());
  return true;
}

// If transformer_weights is nonempty, the lstm is replaced by the pretrained
// transformer loaded from that file (enwik9-specialized decompression). The
// compression and decompression sides must agree on this, or the decoded
// stream diverges.
bool RunDecompression(const std::string& input_path,
    const std::string& temp_path, const std::string& output_path,
    FILE* dictionary, unsigned long long* input_bytes,
    unsigned long long* output_bytes, const ExtractionOptions& extraction,
    const std::string& transformer_weights = "") {
  std::ifstream data_in(input_path, std::ios::in | std::ios::binary);
  if (!data_in.is_open()) {
    Fail("cannot open input file %s", input_path.c_str());
  }

  data_in.seekg(0, std::ios::end);
  *input_bytes = data_in.tellg();
  data_in.seekg(0, std::ios::beg);
  std::vector<bool> vocab(256, false);
  bool dictionary_used;
  ReadHeader(&data_in, output_bytes, &dictionary_used, &vocab);
  if (!dictionary_used && dictionary != NULL) {
    Fail("a dictionary was provided, but %s was compressed without one",
        input_path.c_str());
  }
  if (dictionary_used && dictionary == NULL) {
    Fail("%s was compressed with a dictionary, but none was provided",
        input_path.c_str());
  }

  if (*output_bytes == 0) {  // undo store
    data_in.close();
    FILE* in = fopen(input_path.c_str(), "rb");
    if (!in) return false;
    FILE* data_out = fopen(output_path.c_str(), "wb");
    if (!data_out) return false;
    fseek(in, 5L, SEEK_SET);
    fprintf(stderr, "\rdecoding...");
    fflush(stderr);
    preprocessor::Decode(in, data_out, dictionary);
    fseek(data_out, 0L, SEEK_END);
    *output_bytes = ftell(data_out);
    fclose(in);
    fclose(data_out);
    return true;
  }
  PredictorOptions predictor_options;
  predictor_options.transformer_weights = transformer_weights;
  predictor_options.num_input_bytes = *output_bytes;
  predictor_options.ppmd_only = extraction.ppmd_only;
  predictor_options.transformer_only = extraction.transformer_only;
  predictor_options.save_ppmd_probs = extraction.save_ppmd_probs;
  predictor_options.load_transformer_probs = extraction.load_transformer_probs;
  predictor_options.save_transformer_probs = extraction.save_transformer_probs;
  Predictor p(vocab, predictor_options);
  if (dictionary_used && !extraction.ppmd_only && !extraction.transformer_only) {
    // Mirrors RunCompression: pretraining only affects the models --ppmd-only
    // and --transformer-only skip.
    preprocessor::Pretrain(&p, dictionary);
  }

  std::ofstream temp_out(temp_path, std::ios::out | std::ios::binary);
  if (!temp_out.is_open()) return false;

  Decompress(*output_bytes, &data_in, &temp_out, &p);
  data_in.close();
  temp_out.close();

  FILE* temp_in = fopen(temp_path.c_str(), "rb");
  if (!temp_in) return false;
  FILE* data_out = fopen(output_path.c_str(), "wb");
  if (!data_out) return false;

  preprocessor::Decode(temp_in, data_out, dictionary);
  fseek(data_out, 0L, SEEK_END);
  *output_bytes = ftell(data_out);
  fclose(temp_in);
  fclose(data_out);
  remove(temp_path.c_str());
  return true;
}

int main(int argc, char** argv) {
  ExtractionOptions extraction = ParseExtractionOptions(&argc, argv);

  char mode = 0;
  if (argc > 1) {
    if (strlen(argv[1]) != 2 || argv[1][0] != '-' ||
        strchr("cdehnsx", argv[1][1]) == NULL) {
      UsageError("unknown mode '%s' (expected -c, -d, -e, -h, -n, -s or -x)",
          argv[1]);
    }
    mode = argv[1][1];
    if (mode == 'h') {
      if (argc != 6) {
        UsageError("-h requires exactly four arguments: comp_dict_size "
            "comp_new_order_size decomp_input_size tf_weights_size");
      }
    } else if (mode == 'c' || mode == 'd' || mode == 's') {
      if (argc != 4 && argc != 5) {
        UsageError("-%c requires two or three arguments: [dictionary] "
            "[input] [output]", mode);
      }
    } else {  // -e, -n, -x
      if (argc != 4) {
        UsageError("-%c requires exactly two arguments: [input] [output]",
            mode);
      }
    }
  }
  ValidateExtractionOptions(extraction, mode);

  srand(SEED);

  clock_t start = clock();

  bool enable_preprocess = true;
  std::string input_path ;
  std::string output_path;
  FILE* dictionary = NULL;


  if (mode != 0 && mode != 'h')  {
    if (mode == 'n') enable_preprocess = false;
    input_path = argv[2];
    output_path = argv[3];
    if (argc == 5) {
      RequireReadableFile("dictionary file", argv[2]);
      dictionary = fopen(argv[2], "rb");
      if (!dictionary) {
        UsageError("cannot open dictionary file '%s': %s", argv[2],
            strerror(errno));
      }
      input_path = argv[3];
      output_path = argv[4];
    }
    RequireReadableFile("input file", input_path);
  }

  std::string temp_path = output_path + ".cmix.temp";

  unsigned long long input_bytes = 0, output_bytes = 0;

  if (argc == 1) {
    //Decompress enwik9
    // unpack a) header b) cmix dictionary, c) new order of articles, d) actual cmix binary
    selfextract_decomp();

    // run compression
    std::cout << "Running cmix decompression..." << std::endl;
    input_path = ".ready4cmix_decomp";
    output_path = ".input_decomp" ;
    dictionary = fopen(".dict", "rb");//_decomp

    if (!RunDecompression(input_path, temp_path, output_path, dictionary,
        &input_bytes, &output_bytes, extraction, ".tfweights")) {
      return Help();
    }
    std::cout << "Cmix decompression finished" << std::endl;

    split4Decomp();

    // apply phda9 preprocessor
    phda9_resto();

    // change the order of articles in the input
    sort();

    // merge all input parts after preprocessing
    cat(".intro_decomp", ".main_decomp_restored_sorted", "un1_d");
    cat("un1_d", ".coda_decomp", "enwik9_uncompressed");

    goto print_end_message;
  }

  if (mode == 's') {
    if (!Store(input_path, temp_path, output_path, dictionary, &input_bytes,
        &output_bytes)) {
      Fail("preprocessing failed: cannot open %s or %s", input_path.c_str(),
          output_path.c_str());
    }
  } else if (mode == 'c' || mode == 'n') {
      remove(".dict");
    if (!RunCompression(enable_preprocess, input_path, temp_path, output_path,
        dictionary, &input_bytes, &output_bytes, extraction,
        extraction.transformer)) {
      return Help();
    }
  } else if (mode == 'e') {
    // Compress enwik9
    input_path = argv[2];
    output_path = argv[3]; //name of a compressor output

    // unpack a) cmix dictionary, b) new order of articles, c) actual cmix binary
    selfextract_comp();

    // Preparing enwik9 for reordering
    split4Comp(input_path.c_str());

    // change the order of articles in the input
    reorder();

    // apply phda9 preprocessor
    phda9_prepr();

    // merge all input parts after preprocessing
    cat(".main_phda9prepr", ".intro", "un1");
    cat("un1", ".coda", ".ready4cmix");

    // run compression
    input_path = ".ready4cmix";
    dictionary = fopen(".dict", "rb");
    if (!RunCompression(enable_preprocess, input_path, temp_path, output_path,
        dictionary, &input_bytes, &output_bytes, extraction, ".tfweights")) {
      return Help();
    }

    if (extraction.bytes_only || extraction.ppmd_only ||
        extraction.transformer_only) {
      // No real cmix archive was produced, so there is nothing to build a
      // self-extracting decompressor from.
      goto print_end_message;
    }

    // construct a selfextracting decompressor binary
    // archive9 = decomp_binary(upxed) + comp_dict + tf_weights + cmix_output
    //     + header.dat
    cat(".decomp_bin", ".dict.comp", "dec1");
    cat("dec1", ".tfweights", "dec1w");

    // get the size of the output file
    size_t output_size = getFileSize(output_path);

    HeaderInfo header;
    read("test.dat", header);
    header.decomp_input_size = output_size;
    write("header4archive.dat", header);

    cat("dec1w", output_path.c_str(), "dec2");
    cat("dec2", "header4archive.dat", "archive9");

    // make the decompressor binary executable
    char mode[] = "0777";
    char buf[100] = "archive9";
    int i = strtol(mode, 0, 8);
    chmod(buf, i);

  } else if (mode == 'h') {
    HeaderInfo header;
    header.dict_size = atoi(argv[2]);
    header.new_article_order_size = atoi(argv[3]);
    header.decomp_input_size = atoi(argv[4]);
    header.tf_weights_size = atoi(argv[5]);
    write("header.dat", header);
    goto exit;
  }  else if (mode == 'x') {
    // run compression
    input_path = argv[2];
    output_path = argv[3];
    dictionary = fopen(".dict", "rb");
    if (!RunDecompression(input_path, temp_path, output_path, dictionary,
        &input_bytes, &output_bytes, extraction)) {
      return Help();
    }
    goto print_end_message;
  }
  else {
    if (!RunDecompression(input_path, temp_path, output_path, dictionary,
        &input_bytes, &output_bytes, extraction, extraction.transformer)) {
      return Help();
    }
  }

print_end_message:
  ClearOutput();
  printf("\r%lld bytes -> %lld bytes in %1.2f s.\n",
      input_bytes, output_bytes,
      ((double)clock() - start) / CLOCKS_PER_SEC);

exit:
  return 0;
}

