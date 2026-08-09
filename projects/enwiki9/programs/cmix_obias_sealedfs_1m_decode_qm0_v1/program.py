"""Descriptor for the sealed-filesystem opening decode preflight.

The executable proof is
``tools/cmix_obias_sealedfs_1m_decode_qm0.py``. Bubblewrap exposes only the
writable work directory, a private temporary directory and devices, procfs,
and read-only standard system paths; the network and remaining host filesystem
are absent. The source-built opening archive must reconstruct the exact prefix.
"""
