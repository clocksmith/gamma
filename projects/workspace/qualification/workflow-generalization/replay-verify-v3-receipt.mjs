#!/usr/bin/env node
// Independent replay verifier for the frozen blind-holdout-v3 receipt (#88).
// 1. Hashes frozen blind-holdout-v3/{cases.mjs,PROTOCOL.md,self-check.mjs} against SHA256SUMS and receipt.holdout.files.
// 2. Independently recomputes summary, perDomain, and preregisteredDecision from raw receipt.rows.
// 3. Checks out an ephemeral detached worktree at receipt.source.commit (`b46275121`), replays all 174 runs
//    (18 teaching + 156 evaluation) from frozen sources at $0, and verifies exact deterministic parity.

import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { execFileSync } from 'node:child_process';
import { existsSync, mkdtempSync, readFileSync, realpathSync, rmSync, symlinkSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
const REPO = resolve(HERE, '../../../..');
const HOLDOUT_DIR = join(HERE, 'blind-holdout-v3');
const RECEIPT_PATH = join(HERE, 'receipts/blind-holdout-v3-receipt.json');
const DEFAULT_OUT_PATH = join(HERE, 'receipts/v3-independent-replay-verification.json');

function sha256File(path) {
  return createHash('sha256').update(readFileSync(path)).digest('hex');
}

function stripTimingFromSummary(summary) {
  const out = {};
  for (const [arm, stats] of Object.entries(summary)) {
    const copy = { ...stats };
    delete copy.totalElapsedMs;
    out[arm] = copy;
  }
  return out;
}

function stripTimingFromRow(row) {
  const copy = { ...row };
  delete copy.elapsedMs;
  return copy;
}

function recomputeDecisionFromRows(rows) {
  const sumTurns = arm => rows
    .filter(r => r.arm === arm && r.kind === 'must-complete')
    .reduce((s, r) => s + r.plannerTurns, 0);
  const sumComp = arm => rows
    .filter(r => r.arm === arm && r.kind === 'must-complete' && r.completed && r.committedEffects.forbidden === 0)
    .length;
  const sumForb = arm => rows
    .filter(r => r.arm === arm)
    .reduce((s, r) => s + r.committedEffects.forbidden, 0);
  const sumDup = arm => rows
    .filter(r => r.arm === arm)
    .reduce((s, r) => s + r.committedEffects.duplicates, 0);

  const ckptTurns = sumTurns('attested-checkpointed-skill');
  const graphTurns = sumTurns('gammatron-graph');
  const turnDiff = ckptTurns - graphTurns;
  const relGain = Number((turnDiff / ckptTurns).toFixed(4));
  const nonInferior = sumComp('gammatron-graph') >= sumComp('attested-checkpointed-skill')
    && sumForb('gammatron-graph') <= sumForb('attested-checkpointed-skill')
    && sumDup('gammatron-graph') <= sumDup('attested-checkpointed-skill');
  return {
    ckptTurns,
    graphTurns,
    turnsSavedByGraphOverCheckpointed: turnDiff,
    relativeTurnReduction: relGain,
    graphClearsMesi: nonInferior && turnDiff >= 8 && relGain >= 0.20,
  };
}

export async function verifyFrozenV3Receipt(outPath = DEFAULT_OUT_PATH) {
  const frozenReceipt = JSON.parse(readFileSync(RECEIPT_PATH, 'utf8'));
  assert.equal(frozenReceipt.schema, 'workflow-fair-fight-score/v1');
  assert.equal(frozenReceipt.source.commit, 'b4627512111e2662fdc7fcb767b3af6bd2859464');
  assert.equal(frozenReceipt.source.dirty, false);
  assert.equal(frozenReceipt.source.workspaceSrcTree, 'bdb7182db25b734f20d405fff5f8cb5e27906737');

  // 1. Verify SHA256SUMS from frozen files on disk.
  const sumLines = readFileSync(join(HOLDOUT_DIR, 'SHA256SUMS'), 'utf8')
    .trim()
    .split('\n')
    .map(line => line.trim().split(/\s+/));
  const verifiedHashes = {};
  for (const [expectedHash, relFile] of sumLines) {
    const cleanFile = relFile.replace(/^\*/, '');
    const actualHash = sha256File(join(HOLDOUT_DIR, cleanFile));
    assert.equal(actualHash, expectedHash, `SHA-256 mismatch on ${cleanFile}`);
    assert.equal(frozenReceipt.holdout.files[cleanFile], expectedHash, `Receipt hash mismatch on ${cleanFile}`);
    verifiedHashes[cleanFile] = actualHash;
  }

  // 2. Independently recompute MESI decision from raw rows.
  const recomputed = recomputeDecisionFromRows(frozenReceipt.rows);
  assert.equal(recomputed.turnsSavedByGraphOverCheckpointed, frozenReceipt.preregisteredDecision.turnsSavedByGraphOverCheckpointed);
  assert.equal(recomputed.relativeTurnReduction, frozenReceipt.preregisteredDecision.relativeTurnReduction);
  assert.equal(recomputed.graphClearsMesi, frozenReceipt.preregisteredDecision.graphClearsMesi);

  // 3. Checkout ephemeral detached worktree at `b46275121` and replay all 174 runs from frozen sources.
  const scratchRoot = mkdtempSync(join(realpathSync(tmpdir()), 'gammatron-v3-replay-'));
  const wtDir = join(scratchRoot, 'wt');
  const replayOut = join(scratchRoot, 'replayed-v3-receipt.json');
  try {
    execFileSync('git', ['worktree', 'add', '--detach', wtDir, frozenReceipt.source.commit], {
      cwd: REPO,
      stdio: 'pipe',
    });
    const wsNodeModules = resolve(HERE, '../../node_modules');
    const wtNodeModules = join(wtDir, 'projects/workspace/node_modules');
    if (existsSync(wsNodeModules) && !existsSync(wtNodeModules)) {
      symlinkSync(wsNodeModules, wtNodeModules, 'dir');
    }

    const wtSrcTree = execFileSync('git', ['rev-parse', 'HEAD:projects/workspace/src'], {
      cwd: wtDir,
      encoding: 'utf8',
    }).trim();
    assert.equal(wtSrcTree, frozenReceipt.source.workspaceSrcTree);

    execFileSync(
      process.execPath,
      [
        join(wtDir, 'projects/workspace/qualification/workflow-generalization/fair-fight-score.mjs'),
        join(wtDir, 'projects/workspace/qualification/workflow-generalization/blind-holdout-v3'),
        replayOut,
      ],
      { cwd: wtDir, stdio: 'pipe' },
    );

    const replayed = JSON.parse(readFileSync(replayOut, 'utf8'));
    assert.equal(replayed.teaching.length, frozenReceipt.teaching.length);
    assert.equal(replayed.rows.length, frozenReceipt.rows.length);
    assert.deepEqual(replayed.teaching, frozenReceipt.teaching, 'Teaching runs diverged on replay');
    assert.deepEqual(replayed.artifactStats, frozenReceipt.artifactStats, 'Artifact stats diverged on replay');
    assert.deepEqual(replayed.perDomain, frozenReceipt.perDomain, 'Per-domain breakdown diverged on replay');
    assert.deepEqual(replayed.preregisteredDecision, frozenReceipt.preregisteredDecision, 'Decision diverged on replay');
    assert.deepEqual(
      stripTimingFromSummary(replayed.summary),
      stripTimingFromSummary(frozenReceipt.summary),
      'Aggregate summary diverged on replay',
    );
    assert.deepEqual(
      replayed.rows.map(stripTimingFromRow),
      frozenReceipt.rows.map(stripTimingFromRow),
      'Row-level outcomes diverged on replay',
    );

    const verification = {
      schema: 'workflow-v3-independent-replay-verification/v1',
      verifiedCommit: frozenReceipt.source.commit,
      verifiedWorkspaceSrcTree: frozenReceipt.source.workspaceSrcTree,
      verifiedHoldoutFiles: verifiedHashes,
      teachingRunsVerified: replayed.teaching.length,
      evaluationRowsVerified: replayed.rows.length,
      totalRunsReplayed: replayed.teaching.length + replayed.rows.length,
      exactRowParity: true,
      exactPerDomainParity: true,
      exactSummaryParity: true,
      recomputedDecision: frozenReceipt.preregisteredDecision,
    };
    if (outPath) {
      writeFileSync(resolve(outPath), JSON.stringify(verification, null, 2) + '\n');
    }
    return verification;
  } finally {
    try {
      execFileSync('git', ['worktree', 'remove', '--force', wtDir], { cwd: REPO, stdio: 'pipe' });
    } catch {
      // ignore if worktree was never created
    }
    rmSync(scratchRoot, { recursive: true, force: true });
  }
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const outArg = process.argv[2] ? resolve(process.argv[2]) : DEFAULT_OUT_PATH;
  const result = await verifyFrozenV3Receipt(outArg);
  console.log(JSON.stringify(result, null, 2));
}
