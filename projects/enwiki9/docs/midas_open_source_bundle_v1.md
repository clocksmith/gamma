# Relocatable open MIDAS source bundle

The new `tools/midas_open_source_bundle_v1.py` packages the unchanged default
incremental codec. It preserves the Gamma-relative source layout and LICENSE,
including the forward `.cpp` included by the incremental translation unit.
The build-cache compiler dependency list supplies the C++ closure; the Python
driver, its local helpers, this materializer and its ZIP writer are also included.
The optional reference backend is not promised by this bundle.

From the project directory, with a caller-owned cache and a new output path:

```bash
python3 tools/midas_open_source_bundle_v1.py pack \
  --cache-dir /tmp/owned-midas-cache --output /tmp/midas-source.zip
```

Retain the resulting `bundle_sha256` separately. Pass that exact digest to
`verify --bundle ... --expected-sha256 ...` or
`extract --bundle ... --expected-sha256 ... --output-dir NEW_DIRECTORY`.
Extraction verifies the digest, every member, canonical metadata, and bounded
expanded size before publishing a new directory. Existing targets are refused,
including empty directories and symlinks. No extracted code runs automatically.
The digest is an integrity binding, not a signature or authority to trust code.

The extracted project is `NEW_DIRECTORY/projects/enwiki9`. Its unchanged
`tools/midas_open_codec_v1.py` supports build, inventory, encode and decode with
the same explicit limits as the original driver. Build from that directory with
a separate caller-owned cache. Cache keys include absolute paths and therefore
change after relocation; a different key is not a probability mismatch.

Bundle entries have sorted names, fixed metadata and SHA-256/size records.
Bundle production reuses `tools/build_reproducible_source_zip.py`; byte identity
is tested under the measured Python/zlib implementation. ZIP creation and
extraction are capped at 512 files and 16 MiB compressed/expanded content.
Forced interruption can leave a private staging directory, never a sealed result.

This materializes and counts source bytes, not a complete submission package.
Compiler, system headers, Python, `prlimit`, `/usr/bin/ldd`, ELF runtime/loader, operating-system assumptions,
license closure and accepted submission accounting remain external requirements.
Bundling Gamma LICENSE does not adjudicate every included source's provenance.
No trained assets, teacher state, corpus data or compression gain are implied.
Synthetic source reconstruction and codec replay do not qualify resources or
award full-corpus objective credit. No scientific gate is queued or launched.
