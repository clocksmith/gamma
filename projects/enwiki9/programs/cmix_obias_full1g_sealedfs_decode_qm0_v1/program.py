"""Descriptor for the sealed-filesystem full-1G second decode.

The executable proof is
``tools/cmix_obias_full1g_sealedfs_decode_qm0.py``. Bubblewrap exposes only the
writable work directory, a private temporary directory and devices, procfs,
and read-only standard system paths; the network and remaining host filesystem
are absent. The hash-bound external archive must reconstruct canonical enwik9.

This is a zero-score qualification gate. It is eligible to run only after the
unsealed full-1G decode terminally verifies the same archive and output.
"""
