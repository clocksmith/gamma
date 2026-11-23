# Bring-up for the upstream qualification applications

Scripts that start the stock OpenProject and ERPNext releases used by the live
gates on `clocksmith/deco#88`, and seed the Stage2 accounts and data. They make
no model call and cost nothing. Everything binds to `127.0.0.1`.

| Script | Starts | Ports |
| --- | --- | --- |
| `openproject-up.sh [old-tag] [new-tag]` | PostgreSQL 15 and two OpenProject releases (default `13.4.0-slim`, `14.0.0-slim`) | `28413` old, `28414` new, `28432` PostgreSQL |
| `erpnext-up.sh [old-tag] [new-tag]` | MariaDB 10.6, Redis 6.2 and two ERPNext releases (default `v15.10.0`, `v15.20.0`) | `28510` old, `28520` new |
| `openproject-down.sh`, `erpnext-down.sh` | Remove the containers, network and state file | |

Passwords and keys are generated on every run. They are written, with the API
tokens the seeders print, to a state file outside the repository, mode 600:
`$GAMMATRON_QUAL_STATE/openproject.json` and `erpnext.json` (default directory
`~/.local/state/gammatron-qual`). Runners read that file; pass nothing secret
on a command line you intend to keep, and commit none of it.

## What the seeders create

**OpenProject** (`seed_openproject_qual.rb`): statuses `Stage2New` (default),
`Stage2Approved`, `Stage2Hold`, `Stage2Disallowed` (closed); roles
`Stage2AuthorRole` and `Stage2ApproverRole`, where only the approver may move a
work package between statuses; projects `stage2-qual-proj`,
`stage2-partner-proj` and `stage2-quarantine-proj`; users `stage2_author` and
`stage2_approver`, each with an API token.

**ERPNext** (`seed_erpnext_qual.py`): companies `Stage2 Qual Corp`,
`Stage2 Partner Corp` and `Stage2 Quarantine Corp`; supplier
`Stage2 Approved Vendor`; item `STAGE2-UNIT`; users
`stage2_author@isolated.local` and `stage2_approver@isolated.local`, each with
an API key; change tracking switched on for Purchase Order and Supplier
Quotation.

## Provenance and what has been checked

The commands and both seed scripts were recovered from the session that ran
Gates 3 and 4, where they existed only as typed commands and scratch files.
Three things differ from that run: passwords are generated instead of fixed,
the two extra OpenProject projects are created by the seeder instead of by a
later one-off command, and containers and databases are named `old` and `new`
instead of by version, so that a second upgrade reuses the scripts.

- `openproject-up.sh` was run on 2026-11-23 with the default tags: ready and
  seeded in 88 seconds on an Apple-silicon Mac with both images cached. Both
  accounts authenticated on both releases, the three projects were listed, the
  status identifiers matched the ones Gate 3 was launched with (`16` approved,
  `17` hold), the image digests matched the Gate 3 pre-registration, and the
  single-release contract probe in `stage2-upstream-contract-probe.mjs` gave
  the same result on both releases as the committed Step 2 receipt.
- `erpnext-up.sh` has **not** been run since it was written. It is a
  transcription of the Gate 4 commands with the same three changes.

## Launching the earlier gate runners against a fresh bring-up

The Gate 3 and Gate 4 runners take URLs, tokens and status links as arguments.
Take them from the state file. Gate 3 was launched as:

```text
FAWN_CLAUDE_BIN=<claude binary> node gate3-openproject-5arm-runner.mjs \
  --expected-suite-sha256 <suite hash> --prereg-comment-url <issue comment URL> \
  --op13-url http://127.0.0.1:28413 --op14-url http://127.0.0.1:28414 \
  --author-token-13 <old.seed.authorToken> --approver-token-13 <old.seed.approverToken> \
  --author-token-14 <new.seed.authorToken> --approver-token-14 <new.seed.approverToken> \
  --approved-status-href-14 <new.seed.approvedStatusHref> --hold-status-href-14 <new.seed.holdStatusHref> \
  --pg13-url <old.pgUrl> --pg14-url <new.pgUrl> \
  --username stage2_approver --password <password> --approve-paid-pilot
```

Gate 4 took `--erp10-url`, `--erp20-url`, `--author-token-10`,
`--approver-token-10`, `--author-token-20`, `--approver-token-20`,
`--mariadb-container`, `--mariadb-password`, `--username`, `--password` in the
same way. `--approve-paid-pilot` makes real model calls: it needs the owner's
approval and a spend cap.
