"""Descriptor for the Git-LFS-corrected cmix-obias source qualification.

The executable proof is
``tools/cmix_obias_source_1m_roundtrip_qm1.py``. It changes only q0's clean
source export: the tracked PGO pointer is smudged from the local Git-LFS object
store and verified before the unchanged build and roundtrip contract runs.
"""

