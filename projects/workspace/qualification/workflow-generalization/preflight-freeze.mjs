#!/usr/bin/env node
// Step 1 Preflight & Freeze Recorder (#88):
// Captures the live Google Chrome revision via Playwright, Gamma and Fawn commits,
// frozen source tree hashes, exact commands, and SHA-256 hashes of all retained receipts,
// without rescoring blind-holdout-v3 or adding any synthetic suite ($0 spend).

import { execFileSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import { existsSync, mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import { createRequire } from 'node:module';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
const WORKSPACE_ROOT = resolve(HERE, '../..');
const GAMMA_ROOT = resolve(HERE, '../../../..');
const FAWN_SIBLING = resolve(GAMMA_ROOT, '../fawn');
const FAWN_DONOR_COMMIT = '9234bc55953c43af7d53c7335d8fe24282e59dc6';

function loadPlaywrightChromium() {
  const candidates = [
    join(WORKSPACE_ROOT, 'package.json'),
    process.env.GAMMATRON_WORKSPACE_PKG ?? '',
  ].filter(Boolean);
  for (const pkgPath of candidates) {
    try {
      const req = createRequire(pkgPath);
      return req('playwright-core').chromium;
    } catch {
      // try next candidate
    }
  }
  throw Error('Unable to resolve playwright-core; install workspace dependencies first.');
}

const chromium = loadPlaywrightChromium();
const sha256Bytes = buf => createHash('sha256').update(buf).digest('hex');
const sha256File = p => sha256Bytes(readFileSync(p));

async function detectChromeRevision() {
  const browser = await chromium.launch({ channel: 'chrome', headless: true });
  try {
    return `Google Chrome ${browser.version()}`;
  } finally {
    await browser.close();
  }
}

const PINNED_RECEIPTS = [
  {
    id: 'blind-holdout-v3-frozen-score',
    classification: 'frozen-single-pass-blind-score',
    frozenAtCommit: 'b4627512111e2662fdc7fcb767b3af6bd2859464',
    relativePath:
      'projects/workspace/qualification/workflow-generalization/receipts/blind-holdout-v3-receipt.json',
    exactReplayCommand:
      'node projects/workspace/qualification/workflow-generalization/replay-verify-v3-receipt.mjs',
  },
  {
    id: 'blind-holdout-v3-independent-replay',
    classification: 'independent-detached-worktree-replay-verification',
    frozenAtCommit: '8f41cac9de7c68fb468f254f74b47e256108294d',
    relativePath:
      'projects/workspace/qualification/workflow-generalization/receipts/v3-independent-replay-verification.json',
    exactReplayCommand:
      'node projects/workspace/qualification/workflow-generalization/replay-verify-v3-receipt.mjs',
  },
  {
    id: 'post-v3-modular-revision-diagnostic',
    classification: 'post-v3-diagnostic-not-blind-score',
    frozenAtCommit: '34ae03d5b864162c6704e0580259296422645873',
    relativePath:
      'projects/workspace/qualification/workflow-generalization/receipts/post-v3-modular-revision-receipt.json',
    exactReplayCommand:
      'node projects/workspace/qualification/workflow-generalization/modular-revision-eval.mjs',
  },
  {
    id: 'host-contract-chrome-sqlite-rest-benchmark',
    classification: 'contract-and-integration-cost-benchmark',
    frozenAtCommit: '0569aaa84066a979504e599465b12361a7e24259',
    relativePath:
      'projects/workspace/qualification/workflow-generalization/receipts/host-contract-benchmark-receipt.json',
    exactReplayCommand:
      'node projects/workspace/qualification/workflow-generalization/host-contract-benchmark.mjs',
  },
];

async function main() {
  const chromeRevision = await detectChromeRevision();
  const gammaCommit = execFileSync('git', ['rev-parse', 'HEAD'], {
    cwd: GAMMA_ROOT,
    encoding: 'utf8',
  }).trim();
  const gammaDirty = Boolean(
    execFileSync('git', ['status', '--porcelain', '--ignore-submodules=all'], {
      cwd: GAMMA_ROOT,
      encoding: 'utf8',
    }).trim(),
  );
  const workspaceSrcTree = execFileSync('git', ['rev-parse', 'HEAD:projects/workspace/src'], {
    cwd: GAMMA_ROOT,
    encoding: 'utf8',
  }).trim();

  let fawnWorkspaceCommit = process.env.GAMMATRON_FAWN_COMMIT ?? null;
  if (!fawnWorkspaceCommit && existsSync(join(FAWN_SIBLING, '.git'))) {
    fawnWorkspaceCommit = execFileSync('git', ['rev-parse', 'HEAD'], {
      cwd: FAWN_SIBLING,
      encoding: 'utf8',
    }).trim();
  }

  // Verify blind-holdout-v3 SHA256SUMS unchanged on disk:
  const v3SumsRaw = readFileSync(join(HERE, 'blind-holdout-v3/SHA256SUMS'), 'utf8')
    .trim()
    .split('\n');
  const v3Files = v3SumsRaw.map(line => {
    const [expectedSha, file] = line.trim().split(/\s+/);
    const actualSha = sha256File(join(HERE, 'blind-holdout-v3', file));
    if (actualSha !== expectedSha) {
      throw Error(`Frozen blind-holdout-v3 file modified: ${file}`);
    }
    return { file, sha256: actualSha, verified: true };
  });

  const receipts = PINNED_RECEIPTS.map(item => {
    const abs = join(GAMMA_ROOT, item.relativePath);
    return {
      id: item.id,
      classification: item.classification,
      frozenAtCommit: item.frozenAtCommit,
      path: item.relativePath,
      sha256: sha256File(abs),
      exactReplayCommand: item.exactReplayCommand,
    };
  });

  const payload = {
    schema: 'gammatron-step1-preflight-freeze-v1',
    spendUsd: 0,
    nodeVersion: process.version,
    chromeRevision,
    gammaCommit,
    gammaDirty,
    workspaceSrcTree,
    fawnCommit: fawnWorkspaceCommit,
    fawnDonorImportCommit: FAWN_DONOR_COMMIT,
    preflightCommand:
      'node projects/workspace/qualification/workflow-generalization/preflight-freeze.mjs',
    blindHoldoutV3FrozenCommit: 'b4627512111e2662fdc7fcb767b3af6bd2859464',
    blindHoldoutV3FilesVerified: v3Files,
    retainedReceipts: receipts,
  };

  const outJsonPath = join(HERE, 'receipts/preflight-freeze-receipt.json');
  mkdirSync(dirname(outJsonPath), { recursive: true });
  const jsonText = JSON.stringify(payload, null, 2) + '\n';
  writeFileSync(outJsonPath, jsonText);
  const receiptSha256 = sha256Bytes(Buffer.from(jsonText, 'utf8'));

  const mdLines = [
    '# Step 1 Preflight and Freeze Record (`#88`)',
    '',
    'Generated at **$0.00 spend** without rescoring `blind-holdout-v3` (`b4627512111e2662fdc7fcb767b3af6bd2859464`) or adding any synthetic suite.',
    '',
    '## Environment & Pinned Revisions',
    '',
    `- **Chrome revision:** \`${chromeRevision}\``,
    `- **Node runtime:** \`${process.version}\``,
    `- **Gamma frozen runtime commit:** \`${gammaCommit}\` (\`gammaDirty: ${gammaDirty}\`, \`projects/workspace/src\` tree \`${workspaceSrcTree}\`)`,
    `- **Fawn commit:** \`${fawnWorkspaceCommit}\` (donor workspace import commit: \`${FAWN_DONOR_COMMIT}\`)`,
    '- **Exact preflight command:** `node projects/workspace/qualification/workflow-generalization/preflight-freeze.mjs`',
    `- **Preflight receipt:** [\`receipts/preflight-freeze-receipt.json\`](./receipts/preflight-freeze-receipt.json) — SHA-256 \`${receiptSha256}\``,
    '',
    '## Retained Receipt SHA-256 Ledger (Evidence Separation)',
    '',
    '| Receipt | Classification | Pinned Commit | SHA-256 | Exact `$0` Replay Command |',
    '| --- | --- | --- | --- | --- |',
    ...receipts.map(
      r =>
        `| [\`${r.path.split('/').slice(-2).join('/')}\`](./${r.path.split('/').slice(-2).join('/')}) | \`${r.classification}\` | \`${r.frozenAtCommit.slice(0, 9)}\` | \`${r.sha256}\` | \`${r.exactReplayCommand}\` |`,
    ),
    '',
    '## Frozen `blind-holdout-v3` Integrity (`3/3` Files Verified Unchanged)',
    '',
    ...v3Files.map(f => `- \`blind-holdout-v3/${f.file}\`: \`${f.sha256}\` (\`verified: ${f.verified}\`)`),
    '',
  ];
  writeFileSync(join(HERE, 'preflight-freeze.md'), mdLines.join('\n'));

  console.log(
    JSON.stringify(
      {
        receiptPath:
          'projects/workspace/qualification/workflow-generalization/receipts/preflight-freeze-receipt.json',
        markdownPath:
          'projects/workspace/qualification/workflow-generalization/preflight-freeze.md',
        receiptSha256,
        ...payload,
      },
      null,
      2,
    ),
  );
}

await main();
