"""Descriptor for the first source-built full-1G cmix-obias roundtrip.

The executable proof is
``tools/cmix_obias_source_full1g_roundtrip_a_qm0.py``. It freezes the q2/q3
byte-identical source-built program, encodes canonical enwik9, counts the
self-extracting archive plus program and head, then bare-decodes the archive
under explicit memory and temporary-disk guards.
"""
