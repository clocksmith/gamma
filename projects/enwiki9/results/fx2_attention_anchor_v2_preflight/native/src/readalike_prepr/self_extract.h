#ifndef SELF_EXTRACT_H 
#define SELF_EXTRACT_H 

#include <stdio.h>
#include <stdlib.h>
#include <malloc.h>

#include <string>

// The dictionary is a fixed asset of this submission (dictionary/english.dic).
// It travels in the archive in cmix-compressed form, so recovering it runs the
// full model over 100KB of input -- about a minute -- before anything else
// happens. That makes it a cheap end-to-end self-test of the machine the
// archive is about to be decompressed on: if the model does not reproduce the
// bits the compressor saw, the dictionary comes out wrong, every prediction
// after it is made against different words, and the arithmetic coder
// desynchronises. Without this check that failure surfaces either as a
// segfault in an unrelated place (the codeword table is indexed by words that
// were never loaded) or as thirty hours of decompression producing garbage.
// Update both constants if dictionary/english.dic is ever replaced.
static const long long kExpectedDictSize = 411996;
static const unsigned long long kExpectedDictHash = 0x2c3946082300051aULL;  // FNV-1a 64

// Opens the running executable, which the self-extractor reads its appended
// payload out of. It has to be found under its own name in the working
// directory: bailing out with a message beats the segmentation fault an
// unchecked fopen would produce if the file was renamed or the program was
// started from another directory.
FILE* OpenSelf(const char* name) {
  FILE* f = fopen(name, "rb");
  if (f == NULL) {
    fprintf(stderr, "\ncmix error: cannot open '%s' in the current "
        "directory.\nRun it as ./%s, from the directory the file is in, and "
        "do not rename it.\n", name, name);
    exit(EXIT_FAILURE);
  }
  return f;
}

// Reads the whole of `f` (already sized at `size`) into a fresh buffer.
unsigned char* ReadWholeFile(FILE* f, size_t size, const char* name) {
  unsigned char* buffer = (unsigned char*)malloc(size);
  if (buffer == NULL) {
    fprintf(stderr, "\ncmix error: cannot allocate %zu bytes to read '%s'.\n",
        size, name);
    exit(EXIT_FAILURE);
  }
  if (fread(buffer, 1, size, f) != size) {
    fprintf(stderr, "\ncmix error: '%s' is %zu bytes long but could not be "
        "read in full. The file is truncated or the disk returned an error.\n",
        name, size);
    exit(EXIT_FAILURE);
  }
  return buffer;
}

// Runs a decompression subprocess and aborts if it did not exit cleanly.
void RunSubprocess(const char* command) {
  int status = system(command);
  if (status != 0) {
    fprintf(stderr, "\ncmix error: '%s' failed (exit status %d).\n", command,
        status);
    exit(EXIT_FAILURE);
  }
}

// Aborts unless `path` holds exactly the expected dictionary.
void VerifyDictionary(const char* path) {
  FILE* f = fopen(path, "rb");
  if (f == NULL) {
    fprintf(stderr, "\ncmix error: the dictionary (%s) was not produced. The "
        "archive is truncated or corrupt.\n", path);
    exit(EXIT_FAILURE);
  }
  unsigned long long hash = 0xcbf29ce484222325ULL;
  long long size = 0;
  unsigned char buffer[1 << 16];
  size_t n;
  while ((n = fread(buffer, 1, sizeof(buffer), f)) > 0) {
    for (size_t i = 0; i < n; ++i) {
      hash = (hash ^ buffer[i]) * 0x100000001b3ULL;
    }
    size += (long long)n;
  }
  fclose(f);
  if (size != kExpectedDictSize || hash != kExpectedDictHash) {
    fprintf(stderr,
        "\ncmix error: the dictionary decompressed to %lld bytes with hash "
        "%016llx, expected %lld bytes with hash %016llx.\n"
        "This machine does not reproduce the model the archive was built "
        "with, so decompression cannot succeed. The usual cause is "
        "floating-point results that are not bit-identical across CPUs -- see "
        "the -mrecip=none note in the makefile.\n",
        size, hash, kExpectedDictSize, kExpectedDictHash);
    exit(EXIT_FAILURE);
  }
}

struct HeaderInfo {
  int dict_size;
  int new_article_order_size;
  int decomp_input_size;
  // Size of the compressed transformer weights (FX2TFWC2 format, appended
  // as-is and loaded directly — never run through cmix itself).
  int tf_weights_size;
};

void write(const std::string& file_name, HeaderInfo& data) {
  FILE *out = fopen(file_name.c_str() , "wb" );
  fwrite(&data , 1 , sizeof(HeaderInfo) , out );
  fclose(out);
}

void read(const std::string& file_name, HeaderInfo& data) {
  FILE *in = fopen(file_name.c_str() , "rb" );
  fread(&data , 1 , sizeof(HeaderInfo) , in );
  fclose(in);
}


// This function splits the ./cmix binary file into 4 parts:
// 1) actual compressor/decompressor binary
// 2) dictionary (get's it in compressed form and decompresses it)
// 3) new order of articles (get's it in compressed form and decompresses it)
// 4) transformer weights (compressed FX2TFWC2 file, used as extracted)
int selfextract_comp() {
  HeaderInfo header;

// open itslef to read auxilary data (dictionary and neworder)
  FILE *f = NULL, *fo = NULL;
  f = OpenSelf("cmix");

  // get the size of the whole binary
  fseek(f, 0, SEEK_END);
  size_t fsize = ftell(f);
  fseek(f, 0, SEEK_SET);

  // read the whole binary to memory
  unsigned char *p1 = ReadWholeFile(f, fsize, "cmix");
  fclose(f);

  // read header info
  fo = fopen("test.dat", "wb");
  memcpy(&header, p1 + fsize - sizeof(HeaderInfo), sizeof(HeaderInfo));
  fwrite(p1 + fsize - sizeof(HeaderInfo), sizeof(HeaderInfo), 1, fo);
  fclose(fo);

  //Remove dictionary if present
  remove(".dict");
  
  size_t decmpressor_binary_size = fsize - header.dict_size - header.new_article_order_size - header.tf_weights_size - sizeof(HeaderInfo);

// produce actual decompressor binary
  fo = fopen(".decomp_bin", "wb");
  fwrite(p1, decmpressor_binary_size, 1, fo);
  fclose(fo);

// produce dictionary and decompress it
  fo = fopen(".dict.comp", "wb");
  fwrite(p1 + decmpressor_binary_size, header.dict_size, 1, fo);
  fclose(fo);


// produce article order and decompress it
  fo = fopen(".new_article_order.comp", "wb");
  fwrite(p1 + decmpressor_binary_size + header.dict_size, header.new_article_order_size, 1, fo);
  fclose(fo);

// produce the transformer weights (already in their loadable compressed
// format, so no decompression subprocess is run on them)
  fo = fopen(".tfweights", "wb");
  fwrite(p1 + decmpressor_binary_size + header.dict_size + header.new_article_order_size, header.tf_weights_size, 1, fo);
  fclose(fo);
//  std::cout << "Decompressing the file with the new article order..." << std::endl;
  RunSubprocess("./cmix -d .new_article_order.comp .new_article_order");

//  std::cout << "Decompressing dictionary..." << std::endl;
  RunSubprocess("./cmix -d .dict.comp .dict");
  VerifyDictionary(".dict");
  free(p1);
  malloc_trim(0);
  return 0;
}

// Same as previous function, but used in decompressor
// This function splits the ./archive9 binary file into 4 parts:
// 1) actual decompressor binary
// 2) dictionary (get's it in compressed form and decompresses it)
// 3) transformer weights (compressed FX2TFWC2 file, used as extracted)
// 4) the cmix-compressed enwik9 payload
int selfextract_decomp() {
  HeaderInfo header;
  FILE *f = NULL, *fo = NULL;
  f = OpenSelf("archive9");

  fseek(f, 0, SEEK_END);
  size_t fsize = ftell(f);
  fseek(f, 0, SEEK_SET);

  unsigned char *p1 = ReadWholeFile(f, fsize, "archive9");
  fclose(f);

  // read header info
  fo = fopen("test.dat", "wb");
  fwrite(p1 + fsize - sizeof(HeaderInfo), sizeof(HeaderInfo), 1, fo);
  fclose(fo);
  read("test.dat", header);

  //Remove dictionary if present
  remove(".dict");
  
  size_t decmpressor_binary_size = fsize - header.dict_size - header.tf_weights_size - header.decomp_input_size - sizeof(HeaderInfo);

  fo = fopen(".dict.comp_decomp", "wb");
  fwrite(p1 + decmpressor_binary_size, header.dict_size, 1, fo);
  fclose(fo);

  RunSubprocess("./archive9 -d .dict.comp_decomp .dict");//_decomp
  VerifyDictionary(".dict");

  fo = fopen(".tfweights", "wb");
  fwrite(p1 + decmpressor_binary_size + header.dict_size, header.tf_weights_size, 1, fo);
  fclose(fo);

  fo = fopen(".ready4cmix_decomp", "wb");
  fwrite(p1 + decmpressor_binary_size + header.dict_size + header.tf_weights_size, header.decomp_input_size, 1, fo);
  fclose(fo);

  free(p1);
  malloc_trim(0);
  return 0;
}

#endif // PREPR_H
