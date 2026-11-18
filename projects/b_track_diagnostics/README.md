# B-track development diagnostics

Receipt audits and a stop-channel causal intervention, not a successor
confirmation study. Frozen B1 v4 and B2 v3 files are unchanged.

Tests:
    python -B -m unittest -v
    node --test test_stop_channel_control.mjs
    FASTWEIGHT_MODULE=/path/to/gamma/gamma/fastweight/doppler_fastweight.mjs node --test test_compiler_integration.mjs

The intervention scales only the final stop B row. Gain1 is identity; gain0
removes that direction without refitting or mutating the original adapter.
The integration test uses the actual compiler with tiny synthetic inputs.

Development runner:
    GAMMA_ROOT=/path/to/gamma B1_RESOURCE_CHECK='truthful availability record' node run_stop_development.mjs DOPPLER_ROOT MODEL_DIR NEW_OUTPUT_JSON 2 23017

Check actual resource availability and coordinate owners before running.
B1_RESOURCE_CHECK is a record, not permission or a claim of owner approval.
The runner uses independently authored development phrases, fixed seed23017,
24 tasks, identical compiled fits, alpha1, alternating identity/no-stop arm
order, and bare/context regimes. It rejects confirmation seeds and output
overwrites. Results and shutdown limitation are in RESULTS.md.

Receipt audit:
    python -B audit_receipts.py --b1 B1_RECEIPT --b2 B2_RECEIPT

These are post-hoc diagnostics. No scientific goal is declared complete.
Any successor qualification requires fresh preregistration and confirmation.
