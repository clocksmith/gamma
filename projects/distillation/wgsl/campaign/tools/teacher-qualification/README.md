# Host Teacher Qualification

This directory owns the hidden JavaScript and WGSL repair bank used to qualify
host coding teachers before their outputs can become Doppler training rows.

The bank has three disjoint splits:

- `qualification` selects a provider/model independently for each lane.
- `label` is run only with the selected lane teacher. Only passing label
  sessions are exported.
- `student_holdout` is reserved for student evaluation and is never sent to a
  teacher by the qualification command.

Every task is pinned to `baseRevision`. The harness archives that revision,
removes this directory and the qualification policy, applies the declared
mutation, initializes a fresh repository, and launches the host CLI inside the
disposable snapshot. A session passes only when the captured git diff stays in
the allowlist, forbidden commands are absent, the original source bytes are
recovered, the task validation commands pass, and the structured response is
valid.

Run the static and constructive contract checks with:

```bash
npm run training:teachers:verify
```

Run both lanes with an explicit host model identity and export passing label
rows with:

```bash
npm run training:teachers:qualify -- \
  --teacher codex=<full-model-id> \
  --with-labels
```

To compare both supported host adapters, add
`--teacher claude=<full-model-id>`. The command records CLI versions, model
identities, policy and bank hashes, command audits, validation hashes, exact
source hashes, patches, receipts, and a lane scoreboard under
`reports/training/teacher-qualification/`.

When changing a task, pin a reviewed base revision, keep modified paths
disjoint across splits within a lane, and run the contract verifier. Do not
weaken exact recovery to make a provider pass. A proxy, prose answer, or
provider exit code is not a qualification result.
