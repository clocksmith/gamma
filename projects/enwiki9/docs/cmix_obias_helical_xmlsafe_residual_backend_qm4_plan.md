# QM4 matched residual backend driver

This driver runs the frozen 249,407,080-byte XML-safe residual through the
same native `cmix-obias` executable, head asset, memory setting, working
directory shape, and self-packaging termination path as the completed 250M
baseline.

Before execution it binds all executable, head, residual, and baseline hashes.
It deterministically packages the complete QM4 transform/inverse and driver
sources with LZMA. The monitor aborts only when the monotone payload plus the
fixed 291,697-byte wrapper, 36,640-byte ledger, and measured incremental source
package can no longer beat the baseline archive.

A completed encode must reproduce the fixed wrapper overhead. Its receipt
reports gross and fully paid archive deltas. Decode and exact inversion are a
separate mandatory gate; this driver alone cannot claim roundtrip, full-corpus
transfer, official runtime, or score credit.
