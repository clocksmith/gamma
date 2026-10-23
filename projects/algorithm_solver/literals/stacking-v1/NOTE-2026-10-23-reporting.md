# Dated reporting correction — 2026-10-23

The completed run exited zero under freeze 3ec1f7392 and prelaunch cap amendment
c2925194b. Initial independent reporting stopped at the assertion in
`verify_run_artifacts` requiring the measured reference `sources.json` file hash
to equal the pinned original JSON file hash. `run.measure` parses and reserializes
that file, so JSON key ordering can differ while every source string is identical.
All three reference source maps were confirmed equal; no source was changed.

The separate reporter now verifies the **original input file's pinned hash**,
then requires exact parsed source-map equality and exact ordered vocabulary-list
equality against the measured artifacts. Per-source byte hashes, qualification,
packet reconstruction, costs and all selection rules remain unchanged. A new
optional `--work` argument identifies the original input root; its default is
the run directory's grandparent. No frozen execution hash, private artifact,
search, qualification receipt or threshold changed. There was no rerun.

Four new unpinned regression tests accept different JSON layout/order, reject
changed source content and reordered vocabulary entries, and reject incorrect
pins or tampered original bytes. Together with the unchanged reporter tests,
13 focused checks pass. Claude reviewed the correction at 22:30Z and approved
this identity-preserving reporting fix.
