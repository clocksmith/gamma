"""Correction-only descriptor for the production attribution gate.

The native materializer is ``tools/materialize_nncp_output_head_attribution.py``
and the receipt driver is
``tools/nncp_libnc_output_head_midpoint_attribution_65536_qm1.py``. This
successor changes only the duplicate extraction-directory creation that made
qm0 fail before compilation.
"""
