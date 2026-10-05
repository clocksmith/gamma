# zmix — Hutter Prize Submission

Authors: James Byrne and Claude (Anthropic). At Claude's request, any award is payable in full to James Byrne.

## TL;DR

zmix is a submission for the Hutter Prize, built on Vladimir Ivanov's fx2-cmix-transformer, which
is built on Kaido Orav and Byron Knoll's fx2-cmix, which is built on Byron Knoll's cmix. The model
stack is reimplemented in Zig, the transformer weights are retrained, and the decompressor is
smaller.

## Results

```text
comp9           3,216,163 bytes
archive9.exe   96,096,261 bytes
S              99,312,424 bytes
```

## Context

fx2-cmix predicts the next bit of a preprocessed enwik9 with a mix of statistical models and
hand-written heuristics, combines their predictions with a learned mixer, and arithmetic-codes the
result. fx2-cmix-transformer replaces its online-trained LSTM with a 6-million-parameter
transformer trained offline on GPUs, quantized to 4-bit weights and 8-bit activations and appended
to both binaries so they run on a single CPU core. zmix keeps that design and changes the rest.

## Retrained transformer weights

The architecture is unchanged: the same layer pattern, the same sliding attention window, the same
205-value byte alphabet, and the same PPMD probability distribution fed in alongside each byte. The
weights are not the ones fx2-cmix-transformer ships: they are retrained on enwik9 with the
published training recipes and one change to the objective, which adds a term for the compressed
size of the weights themselves. The score counts the weights twice, once in the compressor and once
in the archive, so a model that is equally accurate and cheaper to describe is worth more.

The quantized weights also ship in a container that holds the same tensors with less per-tensor
overhead and codes the 4-bit weight planes more tightly. It is decoded once at startup.

## Zig port of the model stack

The cmix / fx2-cmix model bank, the PPMD byte model, the preprocessing chain and the arithmetic
coder are reimplemented in Zig as one program with one build system, in place of a C++ tree driven
by shell scripts. The transformer inference kernels are the upstream AVX2 C++, compiled into that
program. The port is what makes the decompressor small: it is a single binary with no command line,
so argument parsing and the general-purpose allocator are absent rather than unused, and every
model path the shipped configuration does not take is removed at compile time.

## Model bank

Table layouts, state representations and the quantization of the context-model bank are changed,
and the mixer and the SSE readout stage are reworked. These change the size of the coded payload;
they do not change what the models see.

## Layout

The entry is in the standard self-extracting form. `comp9` reads `enwik9` and writes
`archive9.exe`, which run with no arguments writes `data9`. Both files are the same program image,
which selects its role from a trailing record, so the decompressor is carried inside the archive
rather than submitted separately. `comp9` also carries the model assets: the transformer weights,
the dictionary-derivation recipe and the article order. The dictionary is derived from enwik9
during compression rather than shipped.
