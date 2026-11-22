#!/usr/bin/env node
// Gate 2 ($0) Live Chromium + OpenProject 14.0.0 + PostgreSQL 15 Observer & RepairBoundary Probe (#88).
//
// Closes the live capture seam on real upstream OpenProject 14.0.0 without paid LLM calls:
//   1. Launches headless Google Chrome (`playwright-core`, `channel: 'chrome'`) against live
//      OpenProject 14.0.0 (`--openproject-url`) backed by PostgreSQL 15 (`--pg-url`).
//   2. Attaches `attachTrustedSameOriginReadObserver` + `projectOpenProjectHalScalars` to the
//      live Playwright `Page`, navigates same-origin, and captures real browser `fetch` `GET`
//      responses from `/api/v3/work_packages/{id}`, `/api/v3/work_packages/{parentId}`, and
//      `/api/v3/work_packages/{id}/activities` directly into `collectObservedFacts` (`0d1c4d6eb`).
//   3. Teaches `learnRepairBoundary` from disposable 14.0.0 WorkPackages (matching terms vs.
//      superseded parent-approval `ABA` terms), SHA-256-freezes the 4-part qualification bundle,
//      and executes real `PATCH` requests on separate held-out 14.0.0 WorkPackages—verifying
//      outcomes directly from PostgreSQL `work_packages` and `journals`.

import { execFileSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import { mkdirSync, writeFileSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { chromium } from 'playwright-core';
import {
  attachTrustedSameOriginReadObserver,
  evaluateHeldOutRouteWithFrozenBundle,
  freezeQualificationRepairBundle,
  projectOpenProjectHalScalars,
} from './repair-boundary-qualification.mjs';
import { computeOpenProjectOperationBinding } from './stage2-upstream-contract-probe.mjs';

const HERE = dirname(fileURLToPath(import.meta.url));
const RECEIPTS_DIR = join(HERE, 'receipts');
const sha256 = t => createHash('sha256').update(t, 'utf8').digest('hex');

function parseArgs(argv) {
  const out = {
    openprojectUrl: null,
    projectId: null,
    authorToken: null,
    approverToken: null,
    approvedStatusHref: null,
    holdStatusHref: null,
    pgUrl: null,
  };
  for (let i = 2; i < argv.length; i += 1) {
    const a = argv[i];
    if (a === '--openproject-url') out.openprojectUrl = argv[++i];
    else if (a === '--project') out.projectId = argv[++i];
    else if (a === '--author-token') out.authorToken = argv[++i];
    else if (a === '--approver-token') out.approverToken = argv[++i];
    else if (a === '--approved-status-href') out.approvedStatusHref = argv[++i];
    else if (a === '--hold-status-href') out.holdStatusHref = argv[++i];
    else if (a === '--pg-url') out.pgUrl = argv[++i];
  }
  return out;
}

const opHeaders = token => ({
  Accept: 'application/json',
  'Content-Type': 'application/json',
  Authorization: `Basic ${Buffer.from(`apikey:${token}`).toString('base64')}`,
});

async function apiJson(url, { method = 'GET', token, body } = {}) {
  const res = await fetch(url, {
    method,
    headers: opHeaders(token),
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });
  const text = await res.text();
  return { status: res.status, ok: res.ok, body: text ? JSON.parse(text) : null };
}

function queryPgWpState(pgUrl, wpId) {
  const sql = `SELECT json_build_object('id', wp.id, 'lock_version', wp.lock_version, 'status_id', wp.status_id, 'estimated_hours', wp.estimated_hours, 'journal_count', (SELECT COUNT(*) FROM journals j WHERE j.journable_type = 'WorkPackage' AND j.journable_id = wp.id))::text FROM work_packages wp WHERE wp.id = ${Number(wpId)};`;
  const out = execFileSync('psql', [pgUrl, '-Atc', sql], { encoding: 'utf8', timeout: 5000 }).trim();
  return JSON.parse(out);
}

async function createParentChildPair({
  root,
  projectId,
  authorToken,
  approverToken,
  approvedStatusHref,
  holdStatusHref,
  initialApprovedDuration,
  alteredParentDuration = null,
  childDuration,
  label,
}) {
  const createUrl = `${root}/api/v3/projects/${encodeURIComponent(projectId)}/work_packages`;
  const parentCreated = await apiJson(createUrl, {
    method: 'POST',
    token: approverToken,
    body: {
      subject: `Approval Packet ${label}`,
      estimatedTime: initialApprovedDuration,
    },
  });
  if (!parentCreated.ok) throw Error(`Parent create failed (${parentCreated.status})`);
  const parentId = parentCreated.body.id;

  // Approver transitions parent packet to Approved:
  const pApprove1 = await apiJson(`${root}/api/v3/work_packages/${parentId}`, {
    method: 'PATCH',
    token: approverToken,
    body: {
      lockVersion: parentCreated.body.lockVersion,
      estimatedTime: initialApprovedDuration,
      _links: { status: { href: approvedStatusHref } },
    },
  });
  if (!pApprove1.ok) throw Error(`Parent approve failed (${pApprove1.status})`);

  if (alteredParentDuration !== null) {
    // ABA revoke -> re-approve parent under altered terms (`alteredParentDuration`):
    const pHold = await apiJson(`${root}/api/v3/work_packages/${parentId}`, {
      method: 'PATCH',
      token: approverToken,
      body: {
        lockVersion: pApprove1.body.lockVersion,
        _links: { status: { href: holdStatusHref } },
      },
    });
    await apiJson(`${root}/api/v3/work_packages/${parentId}`, {
      method: 'PATCH',
      token: approverToken,
      body: {
        lockVersion: pHold.body.lockVersion,
        estimatedTime: alteredParentDuration,
        _links: { status: { href: approvedStatusHref } },
      },
    });
  }

  const childCreated = await apiJson(createUrl, {
    method: 'POST',
    token: authorToken,
    body: {
      subject: `Execution Packet ${label}`,
      estimatedTime: childDuration,
      _links: { parent: { href: `/api/v3/work_packages/${parentId}` } },
    },
  });
  if (!childCreated.ok) throw Error(`Child create failed (${childCreated.status})`);

  return {
    parentId,
    childId: childCreated.body.id,
    childInitialLockVersion: childCreated.body.lockVersion,
    authorHref: childCreated.body._links?.author?.href ?? null,
  };
}

async function captureLiveBrowserFacts(page, { root, authorToken, childId, parentId }) {
  const observer = attachTrustedSameOriginReadObserver(page, {
    allowedOrigin: root,
    projectJson: projectOpenProjectHalScalars,
    roleMatchers: [
      { role: 'record', matches: p => p === `/api/v3/work_packages/${childId}` },
      { role: 'approval', matches: p => p === `/api/v3/work_packages/${parentId}` },
      { role: 'revisions', matches: p => p === `/api/v3/work_packages/${childId}/activities` },
    ],
  });
  try {
    const basicAuth = `Basic ${Buffer.from(`apikey:${authorToken}`).toString('base64')}`;
    await page.evaluate(
      async ({ paths, auth }) => {
        for (const p of paths) {
          const r = await fetch(p, {
            method: 'GET',
            headers: { Accept: 'application/json', Authorization: auth },
          });
          await r.json();
        }
      },
      {
        paths: [
          `/api/v3/work_packages/${childId}`,
          `/api/v3/work_packages/${parentId}`,
          `/api/v3/work_packages/${childId}/activities`,
        ],
        auth: basicAuth,
      },
    );
    return await observer.snapshotObservedFacts();
  } finally {
    observer.detach();
  }
}

async function main() {
  const args = parseArgs(process.argv);
  const root = args.openprojectUrl.replace(/\/$/, '');

  // 1. Provision disposable OpenProject 14.0.0 teaching records:
  //    - `pos1`: clean 1-pass approval (`PT8H === PT8H`, `approval:/lockVersion = 2` after child link)
  //    - `pos2`: benign pre-approval revision (`PT12H -> Hold -> PT16H` before child `PT16H` matches `PT16H`,
  //              giving `approval:/lockVersion = 4` so `learnRepairBoundary` refutes the 1-read
  //              `approval:/lockVersion === 2` shortcut and isolates `approval:/estimatedTime === record:/estimatedTime`!)
  //    - `neg1`: superseded-terms ABA near-miss (`parent` altered to `PT4H` while `child` stays `PT16H`, `lockVersion = 4`)
  const pos1 = await createParentChildPair({
    root,
    projectId: args.projectId,
    authorToken: args.authorToken,
    approverToken: args.approverToken,
    approvedStatusHref: args.approvedStatusHref,
    holdStatusHref: args.holdStatusHref,
    initialApprovedDuration: 'PT8H',
    childDuration: 'PT8H',
    label: 'teach-pos1-pt8h',
  });
  const pos2 = await createParentChildPair({
    root,
    projectId: args.projectId,
    authorToken: args.authorToken,
    approverToken: args.approverToken,
    approvedStatusHref: args.approvedStatusHref,
    holdStatusHref: args.holdStatusHref,
    initialApprovedDuration: 'PT12H',
    alteredParentDuration: 'PT16H',
    childDuration: 'PT16H',
    label: 'teach-pos2-revised-parent-pt16h',
  });
  const neg1 = await createParentChildPair({
    root,
    projectId: args.projectId,
    authorToken: args.authorToken,
    approverToken: args.approverToken,
    approvedStatusHref: args.approvedStatusHref,
    holdStatusHref: args.holdStatusHref,
    initialApprovedDuration: 'PT16H',
    alteredParentDuration: 'PT4H',
    childDuration: 'PT16H',
    label: 'teach-neg-aba-pt4h-vs-pt16h',
  });

  // 2. Provision held-out OpenProject 14.0.0 unseen sibling records:
  //    - `holdoutValid`: unseen `PT20H === PT20H` legitimate order WITH revised parent (`lockVersion = 4`)
  //      (also note OpenProject 14.0 canonicalizes `'PT24H'` -> `'P1D'` in HAL responses!)
  //    - `holdoutLookalikeUnguarded`: unseen `PT12H` child whose parent ABA-changed to `PT2H` (exposed to unguarded shared repair)
  //    - `holdoutLookalikeGuarded`: identical `PT12H` vs `PT2H` ABA order (protected by frozen RepairBoundary)
  const holdoutValid = await createParentChildPair({
    root,
    projectId: args.projectId,
    authorToken: args.authorToken,
    approverToken: args.approverToken,
    approvedStatusHref: args.approvedStatusHref,
    holdStatusHref: args.holdStatusHref,
    initialApprovedDuration: 'PT10H',
    alteredParentDuration: 'PT20H',
    childDuration: 'PT20H',
    label: 'holdout-valid-revised-parent-pt20h',
  });
  const holdoutLookalikeUnguarded = await createParentChildPair({
    root,
    projectId: args.projectId,
    authorToken: args.authorToken,
    approverToken: args.approverToken,
    approvedStatusHref: args.approvedStatusHref,
    holdStatusHref: args.holdStatusHref,
    initialApprovedDuration: 'PT12H',
    alteredParentDuration: 'PT2H',
    childDuration: 'PT12H',
    label: 'holdout-aba-unguarded',
  });
  const holdoutLookalikeGuarded = await createParentChildPair({
    root,
    projectId: args.projectId,
    authorToken: args.authorToken,
    approverToken: args.approverToken,
    approvedStatusHref: args.approvedStatusHref,
    holdStatusHref: args.holdStatusHref,
    initialApprovedDuration: 'PT12H',
    alteredParentDuration: 'PT2H',
    childDuration: 'PT12H',
    label: 'holdout-aba-guarded',
  });

  // 3. Launch real headless Chrome and capture live same-origin GET/XHR responses:
  const browser = await chromium.launch({ channel: 'chrome', headless: true });
  try {
    const browserVersion = browser.version();
    const context = await browser.newContext();
    const page = await context.newPage();
    await page.goto(`${root}/health_checks/default`, { waitUntil: 'domcontentloaded' });

    const pos1Cap = await captureLiveBrowserFacts(page, {
      root,
      authorToken: args.authorToken,
      childId: pos1.childId,
      parentId: pos1.parentId,
    });
    const pos2Cap = await captureLiveBrowserFacts(page, {
      root,
      authorToken: args.authorToken,
      childId: pos2.childId,
      parentId: pos2.parentId,
    });
    const neg1Cap = await captureLiveBrowserFacts(page, {
      root,
      authorToken: args.authorToken,
      childId: neg1.childId,
      parentId: neg1.parentId,
    });

    const approvedEffectContract = {
      schema: 'approved-effect-contract/v1',
      method: 'PATCH',
      endpointTemplate: '/api/v3/work_packages/{recordId}',
      allowedChangeKeys: ['statusHref', 'estimatedTime'],
      fixedChanges: { statusHref: args.approvedStatusHref },
      factBoundChanges: { estimatedTime: 'record:/estimatedTime' },
    };

    const teachingRefBinding = computeOpenProjectOperationBinding({
      workPackageId: String(pos1.childId),
      preCommitLockVersion: pos1.childInitialLockVersion,
      expectedActorHref: pos1.authorHref,
      intendedChanges: { statusHref: args.approvedStatusHref, estimatedTime: 'PT8H' },
      clientOperationId: `gate2-teach-${pos1.childId}`,
    });

    const frozenBundle = freezeQualificationRepairBundle({
      preUpgradeSteps: [
        { kind: 'fill', role: 'textbox', label: 'Review Note', slot: 'note', authority: 'ordinary-ui' },
        { kind: 'click', role: 'button', label: 'Approve Order', slot: null, authority: 'reviewed-write' },
      ],
      preUpgradeAuthorityScope: 'openproject/stage2-qual-proj',
      proposedRepair: {
        authorityScope: 'openproject/stage2-qual-proj',
        steps: [
          { kind: 'fill', role: 'textbox', label: 'Review Note', slot: 'note', authority: 'ordinary-ui' },
          { kind: 'click', role: 'button', label: 'Confirm v14 Approved Terms', slot: null, authority: 'reviewed-write' },
        ],
      },
      effectContract: approvedEffectContract,
      teachingReferenceBinding: teachingRefBinding,
      positiveExamples: [
        { recordId: String(pos1.childId), responses: pos1Cap.responses },
        { recordId: String(pos2.childId), responses: pos2Cap.responses },
      ],
      counterexamples: [
        {
          recordId: String(neg1.childId),
          label: 'live-openproject-14-parent-aba-superseded-terms',
          responses: neg1Cap.responses,
        },
      ],
    });

    // Also record naive 1-positive (`pos1` + `neg1`) ablation showing the 1-read `approval:/lockVersion === 2`
    // shortcut (and unnecessary abstention on revised-parent valid orders) vs contrastive 2-positive (`pos1` + `pos2` + `neg1`):
    const naiveSinglePosBundle = freezeQualificationRepairBundle({
      preUpgradeSteps: [
        { kind: 'fill', role: 'textbox', label: 'Review Note', slot: 'note', authority: 'ordinary-ui' },
        { kind: 'click', role: 'button', label: 'Approve Order', slot: null, authority: 'reviewed-write' },
      ],
      preUpgradeAuthorityScope: 'openproject/stage2-qual-proj',
      proposedRepair: {
        authorityScope: 'openproject/stage2-qual-proj',
        steps: [
          { kind: 'fill', role: 'textbox', label: 'Review Note', slot: 'note', authority: 'ordinary-ui' },
          { kind: 'click', role: 'button', label: 'Confirm v14 Approved Terms', slot: null, authority: 'reviewed-write' },
        ],
      },
      effectContract: approvedEffectContract,
      teachingReferenceBinding: teachingRefBinding,
      positiveExamples: [{ recordId: String(pos1.childId), responses: pos1Cap.responses }],
      counterexamples: [
        {
          recordId: String(neg1.childId),
          label: 'live-openproject-14-parent-aba-superseded-terms',
          responses: neg1Cap.responses,
        },
      ],
    });

    // 4. Evaluate held-out routes using live Chrome network capture + real OpenProject 14.0.0 writes:
    const validCap = await captureLiveBrowserFacts(page, {
      root,
      authorToken: args.authorToken,
      childId: holdoutValid.childId,
      parentId: holdoutValid.parentId,
    });
    const naiveValidEval = evaluateHeldOutRouteWithFrozenBundle(naiveSinglePosBundle, {
      recordId: String(holdoutValid.childId),
      actorHref: holdoutValid.authorHref,
      preCommitLockVersion: holdoutValid.childInitialLockVersion,
      clientOperationId: `gate2-naive-valid-${holdoutValid.childId}`,
      requestedMutation: {
        method: 'PATCH',
        path: `/api/v3/work_packages/${holdoutValid.childId}`,
        intendedChanges: { statusHref: args.approvedStatusHref, estimatedTime: 'PT20H' },
      },
      responses: validCap.responses,
    });
    const validEval = evaluateHeldOutRouteWithFrozenBundle(frozenBundle, {
      recordId: String(holdoutValid.childId),
      actorHref: holdoutValid.authorHref,
      preCommitLockVersion: holdoutValid.childInitialLockVersion,
      clientOperationId: `gate2-holdout-valid-${holdoutValid.childId}`,
      requestedMutation: {
        method: 'PATCH',
        path: `/api/v3/work_packages/${holdoutValid.childId}`,
        intendedChanges: { statusHref: args.approvedStatusHref, estimatedTime: 'PT20H' },
      },
      responses: validCap.responses,
    });

    let validCommitHttpStatus = null;
    if (validEval.status === 'eligible-for-review') {
      // Approver-authorized transition on valid held-out record:
      const res = await apiJson(`${root}/api/v3/work_packages/${holdoutValid.childId}`, {
        method: 'PATCH',
        token: args.approverToken,
        body: {
          lockVersion: holdoutValid.childInitialLockVersion,
          estimatedTime: 'PT20H',
          _links: { status: { href: args.approvedStatusHref } },
        },
      });
      validCommitHttpStatus = res.status;
    }
    const pgValidAfter = queryPgWpState(args.pgUrl, holdoutValid.childId);

    // Unguarded shared repair on ABA-superseded look-alike record (`PT12H` vs `PT2H`):
    const unguardedRes = await apiJson(
      `${root}/api/v3/work_packages/${holdoutLookalikeUnguarded.childId}`,
      {
        method: 'PATCH',
        token: args.approverToken,
        body: {
          lockVersion: holdoutLookalikeUnguarded.childInitialLockVersion,
          estimatedTime: 'PT12H',
          _links: { status: { href: args.approvedStatusHref } },
        },
      },
    );
    const pgUnguardedAfter = queryPgWpState(args.pgUrl, holdoutLookalikeUnguarded.childId);

    // Guarded selective reuse (`RepairBoundary`) on identical ABA-superseded look-alike record:
    const guardedAbaCap = await captureLiveBrowserFacts(page, {
      root,
      authorToken: args.authorToken,
      childId: holdoutLookalikeGuarded.childId,
      parentId: holdoutLookalikeGuarded.parentId,
    });
    const guardedAbaEval = evaluateHeldOutRouteWithFrozenBundle(frozenBundle, {
      recordId: String(holdoutLookalikeGuarded.childId),
      actorHref: holdoutLookalikeGuarded.authorHref,
      preCommitLockVersion: holdoutLookalikeGuarded.childInitialLockVersion,
      clientOperationId: `gate2-holdout-aba-${holdoutLookalikeGuarded.childId}`,
      requestedMutation: {
        method: 'PATCH',
        path: `/api/v3/work_packages/${holdoutLookalikeGuarded.childId}`,
        intendedChanges: { statusHref: args.approvedStatusHref, estimatedTime: 'PT12H' },
      },
      responses: guardedAbaCap.responses,
    });
    const pgGuardedAfter = queryPgWpState(args.pgUrl, holdoutLookalikeGuarded.childId);

    // Changed-write attempt on guard-passing `validCap` -> rejected by approved effect contract:
    const changedWriteEval = evaluateHeldOutRouteWithFrozenBundle(frozenBundle, {
      recordId: String(holdoutValid.childId),
      actorHref: holdoutValid.authorHref,
      preCommitLockVersion: holdoutValid.childInitialLockVersion,
      clientOperationId: `gate2-holdout-changed-write-${holdoutValid.childId}`,
      requestedMutation: {
        method: 'PATCH',
        path: `/api/v3/work_packages/${holdoutValid.childId}`,
        intendedChanges: { statusHref: args.holdStatusHref, estimatedTime: 'PT20H' },
      },
      responses: validCap.responses,
    });

    const receipt = {
      schema: 'gammatron-gate2-openproject-live-observer-receipt/v1',
      spendUsd: 0,
      probedAtUtc: new Date().toISOString(),
      browserRuntime: `Google Chrome ${browserVersion}`,
      upstreamServer: 'openproject/openproject:14.0.0-slim + postgres:15',
      frozenBundleSha256: frozenBundle.sha256,
      naiveSinglePositiveAblation: {
        learnedGuard: naiveSinglePosBundle.learnedGuard,
        decisionOnRevisedParentValidRoute: naiveValidEval.status,
        reason: naiveValidEval.reason,
        finding:
          'On live OpenProject 14.0.0, UpdateAncestorsService bumps parent.lockVersion to 2 on child link; with only 1 unrevised positive (`PT8H`, `lockVersion = 2`) vs 1 ABA negative (`PT4H`, `lockVersion = 4`), two 1-read literals (`approval:/estimatedTime === "PT8H"` and `approval:/lockVersion === 2`) tie at 1 scalar read so `learnRepairBoundary` abstains (`ambiguous-minimum`) rather than guessing. Adding a second disposable positive (`PT16H`, `lockVersion = 4`) breaks both spurious 1-read shortcuts and isolates the unique 2-read relational invariant `approval:/estimatedTime === record:/estimatedTime`.',
      },
      learnedGuard: frozenBundle.learnedGuard,
      liveResults: {
        validUnseenSiblingRoutePt20h: {
          boundaryDecision: validEval.status,
          commitHttpStatus: validCommitHttpStatus,
          pgLockVersionAfter: pgValidAfter.lock_version,
          pgJournalCountAfter: pgValidAfter.journal_count,
          verifiedZeroTurnTransfer:
            validEval.status === 'eligible-for-review'
            && validCommitHttpStatus === 200
            && pgValidAfter.lock_version === 1,
        },
        unguardedSharedRepairOnSupersededTermsAba: {
          commitHttpStatus: unguardedRes.status,
          pgLockVersionAfter: pgUnguardedAfter.lock_version,
          wrongCommitAppliedInPostgres:
            unguardedRes.status === 200 && pgUnguardedAfter.lock_version === 1,
        },
        repairBoundaryOnSupersededTermsAba: {
          boundaryDecision: guardedAbaEval.status,
          boundaryReason: guardedAbaEval.reason,
          pgLockVersionAfter: pgGuardedAfter.lock_version,
          pgJournalCountAfter: pgGuardedAfter.journal_count,
          wrongCommitPreventedBeforeWrite:
            guardedAbaEval.status === 'abstain'
            && guardedAbaEval.reason === 'guard-mismatch'
            && pgGuardedAfter.lock_version === 0,
        },
        changedWriteOnGuardPassingRoute: {
          boundaryDecision: changedWriteEval.status,
          rejectedByEffectContract: changedWriteEval.rejectedByEffectContract,
          reason: changedWriteEval.reason,
        },
      },
    };

    mkdirSync(RECEIPTS_DIR, { recursive: true });
    const outPath = join(RECEIPTS_DIR, 'gate2-openproject-live-observer-receipt.json');
    const serialized = JSON.stringify(receipt, null, 2) + '\n';
    writeFileSync(outPath, serialized);
    console.log(JSON.stringify({ receiptSha256: sha256(serialized), ...receipt }, null, 2));
  } finally {
    await browser.close();
  }
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  await main();
}
