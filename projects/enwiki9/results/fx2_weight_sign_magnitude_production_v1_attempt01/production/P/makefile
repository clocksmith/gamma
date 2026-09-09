CC = clang++-17

ROOT_DIR:=$(shell dirname $(realpath $(firstword $(MAKEFILE_LIST))))

CPPFLAGS_PART-THAT-SHOULD-BE-FAST := $(CFLAGS_DEFINES) -m64 -Wall -std=c++17 -ffp-model=fast -fno-exceptions -fno-threadsafe-statics -Wno-unknown-escape-sequence -Wno-unused-variable -ffp-model=fast -fno-exceptions -fno-threadsafe-statics -Wno-unneeded-internal-declaration -Wno-unused-but-set-variable -Wno-format 

# Instruction set. The default is the portable AVX2 baseline x86-64-v3
# (SSE*, AVX, AVX2, FMA, F16C, BMI1/2, LZCNT, MOVBE, POPCNT) -- exactly what
# the kernels are written against, and the largest set both Hutter Prize test
# machines have: the Intel Core i7-1165G7 (Tiger Lake) and the AMD Ryzen 7
# (Zen 2). The other three settings are for development only -- a submission
# must use the default. NATIVE=1 in particular bakes in whatever the *build*
# machine happens to support, and anything a test machine lacks is an illegal
# instruction (SIGILL) there: Zen 2 has no AVX-512 at all, and Tiger Lake has
# no AVX-VNNI -- and clang does fold the transformer's
# _mm256_add_epi32(_mm256_madd_epi16(..)) into an AVX-VNNI vpdpwssd whenever
# the build machine offers it. (ZEN2=1 is likewise AMD-only: znver2 enables
# SSE4A, which Tiger Lake does not have.)
ifdef NATIVE
$(info NATIVE defined -- development only, the binary is NOT portable)
ARCHFLAGS := -march=native -mtune=native
else
ifdef COREI7
$(info COREI7 defined)
ARCHFLAGS := -march=corei7 -mavx2 -mfma -mf16c -mbmi2
else
ifdef ZEN2
$(info ZEN2 defined)
ARCHFLAGS := -march=znver2
else
ARCHFLAGS := -march=x86-64-v3 -mtune=generic
$(info portable AVX2 baseline (x86-64-v3) used)
endif
endif
endif

# Bit-reproducibility across CPU vendors. -ffp-model=fast lets clang compute
# x/y and 1/sqrt(x) with the RCPPS/RCPSS/RSQRTPS/RSQRTSS *estimate*
# instructions plus a Newton-Raphson step. Those instructions are only
# specified to a relative error bound (1.5*2^-12); the bits they actually
# return come from a vendor-specific lookup table, so the same binary gives
# different low-order bits on Intel and on AMD. Every one of those bits feeds
# a model prediction, so an archive compressed on one vendor's CPU cannot be
# decompressed on the other's: the arithmetic coder desynchronises and the
# output is garbage. -mrecip=none forces true IEEE divides and square roots,
# which are exactly specified and therefore identical on every x86-64 CPU.
# Do not remove this; build_and_construct_comp.sh re-checks the built binary.
ARCHFLAGS += -mrecip=none

CPPFLAGS_PART-THAT-SHOULD-BE-FAST += $(ARCHFLAGS)

CPPFLAGS_PART-THAT-CAN-BE-SLOW    := $(CPPFLAGS_PART-THAT-SHOULD-BE-FAST)
CPPFLAGS_PART-THAT-CAN-BE-SLOW    += -Os -fdata-sections -ffunction-sections
CPPFLAGS_PART-THAT-SHOULD-BE-FAST += -O3 -fdata-sections -ffunction-sections

LFLAGS := -m64 -Wl,--gc-sections -std=c++17

# Transformer inference objects (cpp_infer). Compiled with the exact flag set
# of cpp_infer/Makefile: NO -ffp-model=fast (bit-exact IEEE arithmetic keeps
# the compressor and the decompressor's probability streams identical and
# matches the validated cpp_infer build), and NO PGO/LTO (the profiling run
# never exercises this code, and excluding it keeps its code generation
# identical to the hand-optimized, benchmarked cpp_infer objects).
# The kernels require AVX2/FMA/F16C, which every ARCHFLAGS variant provides.
CPPFLAGS_TRANSFORMER := -m64 -O3 -std=c++17 -Wall -Wextra -fno-math-errno -fdata-sections -ffunction-sections
CPPFLAGS_TRANSFORMER += $(ARCHFLAGS)

TRANSFORMER_OBJS := tf_weights_io.o tf_weights_io_compressed.o tf_qmat_dense.o tf_qmat_sparse.o tf_attn.o tf_kda.o tf_glue.o tf_arena_build.o tf_model_opt.o

tf_weights_io.o: cpp_infer/src/weights_io.cpp cpp_infer/src/weights_io.h
	$(CC) $(CPPFLAGS_TRANSFORMER) -c cpp_infer/src/weights_io.cpp -o $@

# load-time only: -Os keeps the range decoder at ~5KB of code (see
# cpp_infer/Makefile)
tf_weights_io_compressed.o: cpp_infer/src/weights_io_compressed.cpp cpp_infer/src/weights_io.h
	$(CC) $(filter-out -O3,$(CPPFLAGS_TRANSFORMER)) -Os -c cpp_infer/src/weights_io_compressed.cpp -o $@

tf_%.o: cpp_infer/src/opt/%.cpp $(wildcard cpp_infer/src/opt/*.h) cpp_infer/src/weights_io.h
	$(CC) $(CPPFLAGS_TRANSFORMER) -c $< -o $@


prof_gen: CPPFLAGS_PART-THAT-CAN-BE-SLOW    += -fprofile-generate=$(ROOT_DIR)/pgo_data
prof_gen: CPPFLAGS_PART-THAT-SHOULD-BE-FAST += -fprofile-generate=$(ROOT_DIR)/pgo_data
prof_gen: LFLAGS                            += -fprofile-generate=$(ROOT_DIR)/pgo_data
prof_gen: clean cmix

prof_use: CPPFLAGS_PART-THAT-CAN-BE-SLOW    += -fprofile-use=$(ROOT_DIR)/pgo_data -flto
prof_use: CPPFLAGS_PART-THAT-SHOULD-BE-FAST += -fprofile-use=$(ROOT_DIR)/pgo_data -flto
prof_use: LFLAGS                            += -fprofile-use=$(ROOT_DIR)/pgo_data -flto
prof_use: clean cmix


slow: src/preprocess/preprocessor.cpp src/preprocess/preprocessor.h src/preprocess/dictionary.cpp src/preprocess/dictionary.h
	$(CC) $(CPPFLAGS_PART-THAT-CAN-BE-SLOW) src/preprocess/preprocessor.cpp src/preprocess/dictionary.cpp -c 

fast: src/coder/decoder.cpp src/coder/decoder.h src/coder/encoder.cpp src/coder/encoder.h src/context-manager.cpp src/context-manager.h src/contexts/bit-context.cpp src/contexts/bit-context.h src/contexts/bracket-context.cpp src/contexts/bracket-context.h src/contexts/combined-context.cpp src/contexts/combined-context.h src/contexts/context-hash.cpp src/contexts/context-hash.h src/contexts/context.h src/contexts/indirect-hash.cpp src/contexts/indirect-hash.h src/contexts/interval-hash.cpp src/contexts/interval-hash.h src/contexts/interval.cpp src/contexts/interval.h src/contexts/sparse.cpp src/contexts/sparse.h  src/models/bracket.cpp src/models/bracket.h src/models/byte-model.cpp src/models/byte-model.h src/models/direct-hash.cpp src/models/direct-hash.h src/models/direct.cpp src/models/direct.h src/models/indirect.cpp src/models/indirect.h src/models/match.cpp src/models/match.h src/models/model.h src/models/fxcmv1.h src/models/ppmd.cpp src/models/ppmd.h src/states/nonstationary.cpp src/states/nonstationary.h src/states/run-map.cpp src/states/run-map.h src/states/state.h src/mixer/byte-mixer.cpp src/mixer/byte-mixer.h src/mixer/lstm-layer.h src/mixer/lstm.h src/mixer/mixer-input.cpp src/mixer/mixer-input.h src/mixer/mixer.cpp src/mixer/mixer.h src/mixer/sigmoid.cpp src/mixer/sigmoid.h src/mixer/sse.cpp src/mixer/sse.h src/predictor.h src/predictor.cpp src/runner.cpp
	$(CC) $(CPPFLAGS_PART-THAT-SHOULD-BE-FAST) src/coder/decoder.cpp src/coder/encoder.cpp src/context-manager.cpp src/contexts/bit-context.cpp src/contexts/bracket-context.cpp src/contexts/combined-context.cpp src/contexts/context-hash.cpp src/contexts/indirect-hash.cpp src/contexts/interval-hash.cpp src/contexts/interval.cpp src/contexts/sparse.cpp src/models/bracket.cpp src/models/byte-model.cpp src/models/direct-hash.cpp src/models/direct.cpp src/models/indirect.cpp src/models/match.cpp src/models/fxcmv1.cpp src/models/ppmd.cpp src/states/nonstationary.cpp src/states/run-map.cpp src/mixer/byte-mixer.cpp src/mixer/mixer-input.cpp src/mixer/mixer.cpp src/mixer/sigmoid.cpp src/mixer/sse.cpp -c src/predictor.cpp src/runner.cpp

cmix: fast slow $(TRANSFORMER_OBJS)
	$(CC) $(LFLAGS) bit-context.o bracket-context.o bracket.o byte-mixer.o byte-model.o combined-context.o context-hash.o context-manager.o decoder.o dictionary.o direct-hash.o direct.o encoder.o indirect-hash.o indirect.o interval-hash.o interval.o match.o mixer-input.o mixer.o nonstationary.o fxcmv1.o ppmd.o predictor.o preprocessor.o run-map.o runner.o sigmoid.o sparse.o sse.o $(TRANSFORMER_OBJS) -s -o cmix
	rm -f *.o

remap: src/readalike_prepr/article_remap.cpp
	$(CC) src/readalike_prepr/article_remap.cpp -o remap

clean:
	rm -f *.o
	rm -f cmix
	rm -f remap

all: cmix remap

data/enwik9:
	mkdir -p data/
	wget -P data/ http://mattmahoney.net/dc/enwik9.zip
	unzip data/enwik9.zip -d data/
	rm data/enwik9.zip
