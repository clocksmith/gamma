// Gamma research ABI wrapper. FSST remains the separately pinned MIT implementation.
#include "fsst.h"
extern "C" size_t gamma_fsst_decode(const fsst_decoder_t* decoder, size_t input_size,
                                    const unsigned char* input, size_t output_size, unsigned char* output) {
    return fsst_decompress(decoder,input_size,input,output_size,output);
}
extern "C" size_t gamma_fsst_decoder_size() { return sizeof(fsst_decoder_t); }
