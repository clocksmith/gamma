"""Descriptor for the telemetry-normalized cmix-obias source qualification.

The executable proof is
``tools/cmix_obias_source_1m_roundtrip_qm2.py``. It retains q1's exact
Git-LFS materialization and changes only the package receipt schema: any
receipt missing ``scratch_usage_before_cleanup`` receives a direct observation
of the same unique scratch tree before the unchanged roundtrip contract runs.
"""
