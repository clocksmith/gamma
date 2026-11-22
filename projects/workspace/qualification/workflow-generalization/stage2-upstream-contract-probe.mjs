#!/usr/bin/env node
// Step 2 Upstream Real-Application Qualification Probe ($0 spend, #88):
//
// Enforces `Stage2-Contract-Pass-v2` (sequential OpenProject-first qualification):
//   1. Qualify ONE isolated OpenProject 13.4.0 -> 14.0.0 workflow FIRST across BOTH
//      releases (`--openproject-v13-url` and `--openproject-v14-url`) on isolated local
//      accounts before bringing ERPNext in.
//   2. Verify from BOTH upstream server code (`OPENPROJECT_SERVER_CODE_AUDIT`) and
//      database/journal evidence (`work_packages.lock_version` + `journals` / `activities`
//      + optional direct PostgreSQL `psql` query) that:
//        (a) Stale-version writes and concurrent racing writes on the same `lockVersion`
//            are refused (`409 UpdateConflict`) with `0` extra DB commits;
//        (b) Disallowed workflow/role mutations are refused at commit (`0` DB commits);
//        (c) When a human approved SPECIFIC TERMS, binding to that exact approval version
//            and terms digest is REQUIRED ("a fresh approval is not necessarily the same
//            approval": `ABA` revoke-and-regrant under altered terms MUST be refused);
//        (d) A lost post-commit acknowledgment reconciles deterministically via `GET` +
//            `journals` version inspection (`reconcileOpenProjectLostAck`) to ONE durable
//            effect (`0` duplicates).
//   3. Gitea 1.21.11 local probe records sequential endpoint behavior ONLY
//      (`establishesTransactionAtomicity: false`, `establishesGeneralRetrySafety: false`).
//   4. Zero container launches or paid calls are initiated by this script.

import { execFileSync, spawn } from 'node:child_process';
import { createHash } from 'node:crypto';
import { existsSync, mkdirSync, mkdtempSync, readFileSync, realpathSync, rmSync, writeFileSync } from 'node:fs';
import { createServer } from 'node:net';
import { tmpdir, userInfo } from 'node:os';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
const RECEIPTS_DIR = join(HERE, 'receipts');
const LOGS_DIR = join(RECEIPTS_DIR, 'logs');

const sha256 = text => createHash('sha256').update(text, 'utf8').digest('hex');

/**
 * Verified upstream `opf/openproject` server-code transaction & concurrency audit
 * (`v13.4.0` commit `f8d6a196a180155d69998d73f796fa1f177b16bb`,
 *  `v14.0.0` commit `aa7a72a913cb619b3f976ff5f411ef7af97b6caa`).
 */
export const OPENPROJECT_SERVER_CODE_AUDIT = Object.freeze({
  v13_4_0_commit: 'f8d6a196a180155d69998d73f796fa1f177b16bb',
  v14_0_0_commit: 'aa7a72a913cb619b3f976ff5f411ef7af97b6caa',
  inspectedFiles: [
    'lib/api/v3/work_packages/work_packages_api.rb',
    'app/services/work_packages/update_service.rb',
    'app/services/base_services/base_contracted.rb',
    'app/services/base_services/write.rb',
    'app/services/shared/service_context.rb',
    'lib/open_project/mutex.rb',
    'app/contracts/work_packages/update_contract.rb',
    'app/contracts/work_packages/base_contract.rb',
  ],
  findings: {
    sameWorkPackageSerialization:
      'Shared::ServiceContext#in_mutex_context wraps SetAttributesService (UpdateContract) + WorkPackage#save + Journal write inside OpenProject::Mutex.with_advisory_lock_transaction(model) (`mutex_on_WorkPackage_<id>`) plus ActiveRecord optimistic locking (`WHERE id = $1 AND lock_version = $2`). Concurrent mutations on the SAME WorkPackage row serialize atomically.',
    crossEntityReadCommittedGap:
      'As documented in lib/open_project/mutex.rb, PostgreSQL runs at READ COMMITTED isolation and the advisory lock keys only on `mutex_on_WorkPackage_<id>`. Plain SELECTs in UpdateContract against separate tables (`member_roles`, `workflows`, `versions`, or a separate parent/approval WorkPackage) do NOT lock those rows; concurrent revocations on separate entities between validate and COMMIT are not blocked without explicit row/advisory locking.',
    specificTermsApprovalVersionBinding:
      'If human-approved terms live on the target WorkPackage row itself, any revoke-or-edit bumps `work_packages.lock_version`, so binding `lockVersion: v_approved` rejects ABA re-approvals under altered terms (`409`). If human-approved terms live on a separate entity/row, stock UpdateContract does NOT bind that entity\'s version or terms digest—requiring an atomic validator/gateway checking `(approval_id, approval_lock_version, terms_sha256)`.',
  },
});

function parseArgs(argv) {
  const out = {
    passRuleCommentUrl: null,
    giteaBin: process.env.GAMMATRON_GITEA_BIN ?? 'gitea',
    openprojectV13Url: null,
    openprojectV14Url: null,
    openprojectProjectId: null,
    openprojectAuthorToken: null,
    openprojectApproverToken: null,
    openprojectRestrictedToken: null,
    openprojectApprovedStatusHref: '/api/v3/statuses/2',
    openprojectHoldStatusHref: '/api/v3/statuses/3',
    openprojectDisallowedStatusHref: '/api/v3/statuses/99',
    openprojectPgV13Url: null,
    openprojectPgV14Url: null,
    erpnextV15_10Url: null,
    erpnextV15_20Url: null,
    erpnextAuthorApiKey: null,
    erpnextApproverApiKey: null,
    erpnextDoctype: 'Purchase Order',
    dryCheck: false,
  };
  for (let i = 2; i < argv.length; i += 1) {
    const a = argv[i];
    if (a === '--pass-rule-comment-url') out.passRuleCommentUrl = argv[++i];
    else if (a === '--gitea-bin') out.giteaBin = argv[++i];
    else if (a === '--openproject-v13-url') out.openprojectV13Url = argv[++i];
    else if (a === '--openproject-v14-url') out.openprojectV14Url = argv[++i];
    else if (a === '--openproject-project') out.openprojectProjectId = argv[++i];
    else if (a === '--openproject-author-token') out.openprojectAuthorToken = argv[++i];
    else if (a === '--openproject-approver-token') out.openprojectApproverToken = argv[++i];
    else if (a === '--openproject-restricted-token') out.openprojectRestrictedToken = argv[++i];
    else if (a === '--openproject-approved-status-href') out.openprojectApprovedStatusHref = argv[++i];
    else if (a === '--openproject-hold-status-href') out.openprojectHoldStatusHref = argv[++i];
    else if (a === '--openproject-disallowed-status-href') out.openprojectDisallowedStatusHref = argv[++i];
    else if (a === '--openproject-pg-v13-url') out.openprojectPgV13Url = argv[++i];
    else if (a === '--openproject-pg-v14-url') out.openprojectPgV14Url = argv[++i];
    else if (a === '--erpnext-v15-10-url') out.erpnextV15_10Url = argv[++i];
    else if (a === '--erpnext-v15-20-url') out.erpnextV15_20Url = argv[++i];
    else if (a === '--erpnext-author-api-key') out.erpnextAuthorApiKey = argv[++i];
    else if (a === '--erpnext-approver-api-key') out.erpnextApproverApiKey = argv[++i];
    else if (a === '--erpnext-doctype') out.erpnextDoctype = argv[++i];
    else if (a === '--dry-check') out.dryCheck = true;
  }
  return out;
}

async function pickSafeLoopbackPort(start = 28310, end = 28390) {
  for (let port = start; port <= end; port += 1) {
    const free = await new Promise(resolvePort => {
      const srv = createServer();
      srv.once('error', () => resolvePort(false));
      srv.listen(port, '127.0.0.1', () => srv.close(() => resolvePort(true)));
    });
    if (free) return port;
  }
  throw Error(`No free loopback port in ${start}..${end}`);
}

function checkDockerDaemon() {
  try {
    execFileSync('docker', ['info'], { stdio: 'pipe', timeout: 4000 });
    return { dockerAvailable: true, detail: 'docker daemon reachable' };
  } catch (err) {
    const msg = String(err?.stderr || err?.message || 'docker unavailable').split('\n')[0];
    return { dockerAvailable: false, detail: sanitizeText(msg, []) };
  }
}

export function sanitizeText(raw, extraPrefixes = []) {
  let out = String(raw ?? '');
  for (const p of extraPrefixes) {
    if (p) out = out.split(p).join('<TMP_PROBE_ROOT>');
  }
  const uname = userInfo().username;
  out = out.replace(/\/Users\/[^/\s"']+/g, '<USER_HOME>');
  out = out.replace(/\/private\/tmp\/[^\s"']+/g, '<TMP_PATH>');
  out = out.replace(/\/var\/folders\/[^\s"']+/g, '<TMP_VAR>');
  if (uname && uname.length >= 2) {
    out = out.replace(new RegExp(`\\b${uname}\\b`, 'g'), '<LOCAL_USER>');
  }
  return out;
}

async function jsonRequest(url, { method = 'GET', authUser = null, authPass = null, headers = {}, body = undefined } = {}) {
  const reqHeaders = { Accept: 'application/json', ...headers };
  if (authUser !== null) {
    reqHeaders.Authorization = `Basic ${Buffer.from(`${authUser}:${authPass}`).toString('base64')}`;
  }
  if (body !== undefined) {
    reqHeaders['Content-Type'] = 'application/json';
  }
  const res = await fetch(url, {
    method,
    headers: reqHeaders,
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });
  const text = await res.text();
  let parsed = null;
  try {
    parsed = text ? JSON.parse(text) : null;
  } catch {
    parsed = { rawText: text.slice(0, 400) };
  }
  return { status: res.status, ok: res.ok, body: parsed };
}

async function waitForHttpReady(url, timeoutMs = 20000) {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    try {
      const res = await fetch(url);
      if (res.status >= 200 && res.status < 500) return true;
    } catch {
      // retry
    }
    await new Promise(r => setTimeout(r, 250));
  }
  throw Error(`Timed out waiting for ${url}`);
}

function opHeaders(apiToken) {
  return { Authorization: `Basic ${Buffer.from(`apikey:${apiToken}`).toString('base64')}` };
}

function queryPostgresJournalCount(pgUrl, workPackageId) {
  if (!pgUrl) return null;
  const out = execFileSync(
    'psql',
    [
      pgUrl,
      '-Atc',
      `SELECT COUNT(*) FROM journals WHERE journable_type = 'WorkPackage' AND journable_id = ${Number(workPackageId)};`,
    ],
    { encoding: 'utf8', timeout: 5000 },
  ).trim();
  return Number(out);
}

async function readOpenProjectJournalEvidence(baseUrl, wpId, token, pgUrl = null) {
  const root = baseUrl.replace(/\/$/, '');
  const [wpRes, actRes] = await Promise.all([
    jsonRequest(`${root}/api/v3/work_packages/${wpId}`, { headers: opHeaders(token) }),
    jsonRequest(`${root}/api/v3/work_packages/${wpId}/activities`, { headers: opHeaders(token) }),
  ]);
  const elements = actRes.body?._embedded?.elements ?? [];
  const pgCount = queryPostgresJournalCount(pgUrl, wpId);
  return {
    lockVersion: wpRes.body?.lockVersion,
    subject: wpRes.body?.subject,
    estimatedTime: wpRes.body?.estimatedTime ?? null,
    descriptionRaw: wpRes.body?.description?.raw ?? '',
    statusHref: wpRes.body?._links?.status?.href ?? null,
    journalCount: pgCount ?? elements.length,
    journalSource: pgCount !== null ? 'postgresql-journals-table' : 'api-v3-activities-journals',
    journals: elements,
  };
}

/**
 * Reconcile a dropped post-commit acknowledgment on OpenProject `PATCH /api/v3/work_packages/{id}`
 * to exactly one durable effect using `(preCommitLockVersion, idempotencyMarker)` against DB journals,
 * without blindly re-applying the mutation on top of a newer version.
 */
export async function reconcileOpenProjectLostAck({
  baseUrl,
  workPackageId,
  apiToken,
  preCommitLockVersion,
  idempotencyMarker,
  payload,
  pgUrl = null,
}) {
  const root = baseUrl.replace(/\/$/, '');
  const wpUrl = `${root}/api/v3/work_packages/${workPackageId}`;
  // Attempt keyed/versioned retry at the EXACT pre-commit `lockVersion`:
  const retryAtSameVersion = await jsonRequest(wpUrl, {
    method: 'PATCH',
    headers: opHeaders(apiToken),
    body: { ...payload, lockVersion: preCommitLockVersion },
  });
  const evidence = await readOpenProjectJournalEvidence(baseUrl, workPackageId, apiToken, pgUrl);
  // OpenProject `work_packages.lock_version` starts at 0 while `journals.version` starts at 1
  // (version 1 = initial creation), so transitioning `lock_version` v -> v + 1 writes `journal.version = v + 2`:
  const matchingJournals = evidence.journals.filter(j =>
    String(j?.comment?.raw ?? '').includes(idempotencyMarker)
    || (j?.version === preCommitLockVersion + 2 && evidence.descriptionRaw.includes(idempotencyMarker)),
  );
  const reconciledCommittedOnce =
    (retryAtSameVersion.status === 409 && matchingJournals.length === 1)
    || (retryAtSameVersion.status === 200 && matchingJournals.length === 1);
  return {
    retryHttpStatus: retryAtSameVersion.status,
    lockVersionAfterReconcile: evidence.lockVersion,
    matchingDurableJournalEffects: matchingJournals.length,
    totalJournalCount: evidence.journalCount,
    journalSource: evidence.journalSource,
    reconciledToSingleDurableEffect: reconciledCommittedOnce,
  };
}

/**
 * Execute the full isolated-account qualification probe against ONE OpenProject release
 * (`13.4.0` or `14.0.0`), verifying stale-lock refusal, concurrent advisory-lock serialization,
 * commit-time prerequisite refusal, human-approved specific-terms version binding (`ABA`),
 * and lost-ack reconciliation from DB journal evidence.
 */
export async function runOpenProjectSingleReleaseProbe({
  releaseLabel,
  baseUrl,
  projectId,
  authorToken,
  approverToken,
  restrictedToken = null,
  approvedStatusHref = '/api/v3/statuses/2',
  holdStatusHref = '/api/v3/statuses/3',
  disallowedStatusHref = '/api/v3/statuses/99',
  pgUrl = null,
}) {
  const root = baseUrl.replace(/\/$/, '');
  const createUrl = `${root}/api/v3/projects/${encodeURIComponent(projectId)}/work_packages`;

  // Provision isolated target WorkPackage (`wpMain`) and separate approval WorkPackage (`wpSeparateApproval`):
  const createdMain = await jsonRequest(createUrl, {
    method: 'POST',
    headers: opHeaders(authorToken),
    body: {
      subject: `Stage2 Probe Target (${releaseLabel})`,
      estimatedTime: 'PT8H',
      description: { raw: 'Initial draft terms: budget=8h' },
    },
  });
  if (!createdMain.ok) {
    throw Error(`OpenProject (${releaseLabel}) work_package create failed (${createdMain.status})`);
  }
  const wpId = createdMain.body.id;
  const wpUrl = `${root}/api/v3/work_packages/${wpId}`;
  const ev0 = await readOpenProjectJournalEvidence(baseUrl, wpId, authorToken, pgUrl);

  // 1. Approver approves specific terms (`PT8H`) on `wpMain` (`lockVersion: v0 -> v1`):
  const approveTermsV1 = await jsonRequest(wpUrl, {
    method: 'PATCH',
    headers: opHeaders(approverToken),
    body: {
      lockVersion: ev0.lockVersion,
      estimatedTime: 'PT8H',
      _links: { status: { href: approvedStatusHref } },
      journalNotes: 'Approved specific terms: PT8H',
    },
  });
  if (!approveTermsV1.ok) {
    throw Error(`OpenProject (${releaseLabel}) initial approval failed (${approveTermsV1.status})`);
  }
  const pinnedApprovedLockVersion = approveTermsV1.body.lockVersion;
  const evAfterV1 = await readOpenProjectJournalEvidence(baseUrl, wpId, authorToken, pgUrl);

  // CHECK 1: Stale `lockVersion` write MUST be refused (`409`) with `0` new DB journal rows:
  const staleWrite = await jsonRequest(wpUrl, {
    method: 'PATCH',
    headers: opHeaders(authorToken),
    body: {
      lockVersion: ev0.lockVersion,
      description: { raw: 'Stale write attempt' },
    },
  });
  const evAfterStale = await readOpenProjectJournalEvidence(baseUrl, wpId, authorToken, pgUrl);
  const staleVersionRefusedPass =
    staleWrite.status === 409 && evAfterStale.journalCount === evAfterV1.journalCount;

  // CHECK 2: Commit-time prerequisite refusal (disallowed status transition or unauthorized role -> `403`/`422`, `0` DB commits):
  const prereqProbeToken = restrictedToken ?? authorToken;
  const disallowedWrite = await jsonRequest(wpUrl, {
    method: 'PATCH',
    headers: opHeaders(prereqProbeToken),
    body: {
      lockVersion: pinnedApprovedLockVersion,
      _links: { status: { href: disallowedStatusHref } },
    },
  });
  const evAfterDisallowed = await readOpenProjectJournalEvidence(baseUrl, wpId, authorToken, pgUrl);
  const commitPrerequisiteRefusedPass =
    !disallowedWrite.ok
    && (disallowedWrite.status === 403 || disallowedWrite.status === 422)
    && evAfterDisallowed.journalCount === evAfterV1.journalCount;

  // CHECK 3A: Specific-terms human approval version binding (`ABA` on same WorkPackage row):
  // Approver revokes (`holdStatusHref`) and re-approves (`approvedStatusHref`) under DIFFERENT terms (`PT4H` != `PT8H`).
  // Agent holding `pinnedApprovedLockVersion` (`PT8H`) MUST be refused (`409`, `0` commits for the stale-terms write)!
  const revokeStep = await jsonRequest(wpUrl, {
    method: 'PATCH',
    headers: opHeaders(approverToken),
    body: {
      lockVersion: pinnedApprovedLockVersion,
      _links: { status: { href: holdStatusHref } },
      journalNotes: 'Revoked PT8H approval',
    },
  });
  const reapproveAlteredTerms = await jsonRequest(wpUrl, {
    method: 'PATCH',
    headers: opHeaders(approverToken),
    body: {
      lockVersion: revokeStep.body.lockVersion,
      estimatedTime: 'PT4H',
      _links: { status: { href: approvedStatusHref } },
      journalNotes: 'Fresh approval under altered terms: PT4H',
    },
  });
  const evBeforeAbaAttempt = await readOpenProjectJournalEvidence(baseUrl, wpId, authorToken, pgUrl);
  const abaSameRowAttempt = await jsonRequest(wpUrl, {
    method: 'PATCH',
    headers: opHeaders(authorToken),
    body: {
      lockVersion: pinnedApprovedLockVersion,
      description: { raw: 'Proceeding assuming PT8H approval still stands' },
    },
  });
  const evAfterAbaAttempt = await readOpenProjectJournalEvidence(baseUrl, wpId, authorToken, pgUrl);
  const sameRowSpecificTermsAbaRefusedPass =
    reapproveAlteredTerms.ok
    && abaSameRowAttempt.status === 409
    && evAfterAbaAttempt.journalCount === evBeforeAbaAttempt.journalCount;

  // CHECK 3B: Separate-entity approval `ABA` diagnostic (parent approval WP revoked & re-approved under altered terms):
  const createdParent = await jsonRequest(createUrl, {
    method: 'POST',
    headers: opHeaders(approverToken),
    body: { subject: `Separate Approval Packet (${releaseLabel})`, estimatedTime: 'PT8H' },
  });
  const createdChild = await jsonRequest(createUrl, {
    method: 'POST',
    headers: opHeaders(authorToken),
    body: {
      subject: `Child Execution Packet (${releaseLabel})`,
      _links: { parent: { href: `/api/v3/work_packages/${createdParent.body.id}` } },
    },
  });
  const childInitialLock = createdChild.body.lockVersion;
  // Mutate parent approval twice (`ABA` under altered terms `PT2H`):
  const p1 = await jsonRequest(`${root}/api/v3/work_packages/${createdParent.body.id}`, {
    method: 'PATCH',
    headers: opHeaders(approverToken),
    body: { lockVersion: createdParent.body.lockVersion, _links: { status: { href: holdStatusHref } } },
  });
  await jsonRequest(`${root}/api/v3/work_packages/${createdParent.body.id}`, {
    method: 'PATCH',
    headers: opHeaders(approverToken),
    body: {
      lockVersion: p1.body.lockVersion,
      estimatedTime: 'PT2H',
      _links: { status: { href: approvedStatusHref } },
    },
  });
  const separateEntityAbaChildWrite = await jsonRequest(
    `${root}/api/v3/work_packages/${createdChild.body.id}`,
    {
      method: 'PATCH',
      headers: opHeaders(authorToken),
      body: { lockVersion: childInitialLock, description: { raw: 'Child mutation without parent lockVersion check' } },
    },
  );
  const separateEntityAbaRequiresExplicitVersionValidator = separateEntityAbaChildWrite.status === 200;

  // CHECK 4: Concurrent race (`Promise.all`) at identical `lockVersion` on `wpMain`:
  const lockBeforeRace = evAfterAbaAttempt.lockVersion;
  const journalsBeforeRace = evAfterAbaAttempt.journalCount;
  const [raceA, raceB] = await Promise.all([
    jsonRequest(wpUrl, {
      method: 'PATCH',
      headers: opHeaders(authorToken),
      body: { lockVersion: lockBeforeRace, description: { raw: 'Concurrent writer A' }, journalNotes: 'race-A' },
    }),
    jsonRequest(wpUrl, {
      method: 'PATCH',
      headers: opHeaders(approverToken),
      body: { lockVersion: lockBeforeRace, description: { raw: 'Concurrent writer B' }, journalNotes: 'race-B' },
    }),
  ]);
  const evAfterRace = await readOpenProjectJournalEvidence(baseUrl, wpId, authorToken, pgUrl);
  const statuses = [raceA.status, raceB.status].sort((a, b) => a - b);
  const concurrentRaceSerializedPass =
    statuses[0] === 200
    && statuses[1] === 409
    && evAfterRace.lockVersion === lockBeforeRace + 1
    && evAfterRace.journalCount === journalsBeforeRace + 1;

  // CHECK 5: Lost-acknowledgment reconciliation (`reconcileOpenProjectLostAck`) to 1 durable effect:
  const lockBeforeLostAck = evAfterRace.lockVersion;
  const journalsBeforeLostAck = evAfterRace.journalCount;
  const idemMarker = `idem-${releaseLabel}-${lockBeforeLostAck}`;
  const lostAckPayload = {
    description: { raw: `Final staged review (${idemMarker})` },
    journalNotes: `Commit ${idemMarker}`,
  };
  const committedButAckDropped = await jsonRequest(wpUrl, {
    method: 'PATCH',
    headers: opHeaders(authorToken),
    body: { ...lostAckPayload, lockVersion: lockBeforeLostAck },
  });
  const reconcileResult = await reconcileOpenProjectLostAck({
    baseUrl,
    workPackageId: wpId,
    apiToken: authorToken,
    preCommitLockVersion: lockBeforeLostAck,
    idempotencyMarker: idemMarker,
    payload: lostAckPayload,
    pgUrl,
  });
  const lostAckSingleDurableEffectPass =
    committedButAckDropped.status === 200
    && reconcileResult.reconciledToSingleDurableEffect
    && reconcileResult.totalJournalCount === journalsBeforeLostAck + 1;

  const releaseQualifiesForSameRowTermsWorkflow =
    staleVersionRefusedPass
    && commitPrerequisiteRefusedPass
    && sameRowSpecificTermsAbaRefusedPass
    && concurrentRaceSerializedPass
    && lostAckSingleDurableEffectPass;

  return {
    releaseLabel,
    status: 'probed-with-db-journal-evidence',
    journalSource: evAfterRace.journalSource,
    checks: {
      staleVersionRefused: { httpStatus: staleWrite.status, passes: staleVersionRefusedPass },
      commitPrerequisiteRefused: { httpStatus: disallowedWrite.status, passes: commitPrerequisiteRefusedPass },
      sameRowSpecificTermsAbaRefused: { httpStatus: abaSameRowAttempt.status, passes: sameRowSpecificTermsAbaRefusedPass },
      separateEntityAbaDiagnostic: {
        childHttpStatusOnStock: separateEntityAbaChildWrite.status,
        separateEntityAbaRequiresExplicitVersionValidator,
      },
      concurrentSameRowRaceSerialized: {
        httpStatuses: statuses,
        lockVersionDelta: evAfterRace.lockVersion - lockBeforeRace,
        journalDelta: evAfterRace.journalCount - journalsBeforeRace,
        passes: concurrentRaceSerializedPass,
      },
      lostAckReconciliation: {
        ...reconcileResult,
        passes: lostAckSingleDurableEffectPass,
      },
    },
    qualifiesSameRowTermsWorkflow: releaseQualifiesForSameRowTermsWorkflow,
    qualifiesSeparateEntityTermsWithoutValidator: !separateEntityAbaRequiresExplicitVersionValidator,
  };
}

export async function probeOpenProjectDualRelease(args, dockerState) {
  if (!args.openprojectV13Url || !args.openprojectV14Url) {
    return {
      appId: 'openproject',
      auditedReleasePair: 'v13.4.0->v14.0.0',
      stageOrder: 1,
      status: 'awaiting-owner-approval-of-isolated-openproject-workflow-and-local-accounts',
      dockerAvailable: dockerState.dockerAvailable,
      dockerDetail: dockerState.detail,
      probeImplementationReady: true,
      serverCodeAudit: OPENPROJECT_SERVER_CODE_AUDIT,
      requiredToRunDualReleaseProbe: [
        'Owner approval of one isolated OpenProject 13.4.0 -> 14.0.0 workflow and local test accounts (no container launches authorized yet)',
        'Pass `--openproject-v13-url`, `--openproject-v14-url`, `--openproject-project`, `--openproject-author-token`, and `--openproject-approver-token` (plus optional `--openproject-pg-v13-url` / `--openproject-pg-v14-url`)',
      ],
    };
  }
  const v13 = await runOpenProjectSingleReleaseProbe({
    releaseLabel: 'v13.4.0',
    baseUrl: args.openprojectV13Url,
    projectId: args.openprojectProjectId,
    authorToken: args.openprojectAuthorToken,
    approverToken: args.openprojectApproverToken,
    restrictedToken: args.openprojectRestrictedToken,
    approvedStatusHref: args.openprojectApprovedStatusHref,
    holdStatusHref: args.openprojectHoldStatusHref,
    disallowedStatusHref: args.openprojectDisallowedStatusHref,
    pgUrl: args.openprojectPgV13Url,
  });
  const v14 = await runOpenProjectSingleReleaseProbe({
    releaseLabel: 'v14.0.0',
    baseUrl: args.openprojectV14Url,
    projectId: args.openprojectProjectId,
    authorToken: args.openprojectAuthorToken,
    approverToken: args.openprojectApproverToken,
    restrictedToken: args.openprojectRestrictedToken,
    approvedStatusHref: args.openprojectApprovedStatusHref,
    holdStatusHref: args.openprojectHoldStatusHref,
    disallowedStatusHref: args.openprojectDisallowedStatusHref,
    pgUrl: args.openprojectPgV14Url,
  });
  return {
    appId: 'openproject',
    auditedReleasePair: 'v13.4.0->v14.0.0',
    stageOrder: 1,
    status: 'probed-both-releases',
    serverCodeAudit: OPENPROJECT_SERVER_CODE_AUDIT,
    v13_4_0: v13,
    v14_0_0: v14,
    dualReleaseQualified: v13.qualifiesSameRowTermsWorkflow && v14.qualifiesSameRowTermsWorkflow,
  };
}

export async function runErpNextSingleReleaseProbe({
  releaseLabel,
  baseUrl,
  authorApiKey,
  approverApiKey,
  doctype = 'Purchase Order',
}) {
  const root = baseUrl.replace(/\/$/, '');
  const auth = key => ({ Authorization: `token ${key}` });

  const created = await jsonRequest(`${root}/api/resource/${encodeURIComponent(doctype)}`, {
    method: 'POST',
    headers: auth(authorApiKey),
    body: { doctype, workflow_state: 'Draft', terms: 'Approved qty=10' },
  });
  if (!created.ok) throw Error(`ERPNext (${releaseLabel}) create failed (${created.status})`);
  const doc = created.body.data;
  const docUrl = `${root}/api/resource/${encodeURIComponent(doctype)}/${encodeURIComponent(doc.name)}`;
  const saveUrl = `${root}/api/method/frappe.desk.form.save.savedocs`;

  // Approve specific terms (`modified: m0 -> m1`):
  const approve1 = await jsonRequest(saveUrl, {
    method: 'POST',
    headers: auth(approverApiKey),
    body: { doc: JSON.stringify({ ...doc, workflow_state: 'Approved', terms: 'Approved qty=10' }), action: 'Save' },
  });
  const approvedDoc = approve1.body?.docs?.[0];
  const pinnedModified = approvedDoc?.modified;

  // Stale `modified` timestamp write refused (`417`/`409` TimestampMismatchError):
  const staleRes = await jsonRequest(saveUrl, {
    method: 'POST',
    headers: auth(authorApiKey),
    body: { doc: JSON.stringify({ ...approvedDoc, modified: doc.modified, terms: 'Stale overwrite' }), action: 'Save' },
  });

  // Specific-terms ABA (`Approved qty=10 -> Hold -> Approved qty=5`):
  const holdRes = await jsonRequest(saveUrl, {
    method: 'POST',
    headers: auth(approverApiKey),
    body: { doc: JSON.stringify({ ...approvedDoc, workflow_state: 'On Hold' }), action: 'Save' },
  });
  const heldDoc = holdRes.body?.docs?.[0];
  const reapproveRes = await jsonRequest(saveUrl, {
    method: 'POST',
    headers: auth(approverApiKey),
    body: { doc: JSON.stringify({ ...heldDoc, workflow_state: 'Approved', terms: 'Approved qty=5' }), action: 'Save' },
  });
  const currentDoc = reapproveRes.body?.docs?.[0];
  const abaAttempt = await jsonRequest(saveUrl, {
    method: 'POST',
    headers: auth(authorApiKey),
    body: { doc: JSON.stringify({ ...approvedDoc, modified: pinnedModified, notes: 'Proceeding under old qty=10' }), action: 'Save' },
  });

  // Lost-ack retry with pre-commit `modified`:
  const marker = `idem-erp-${releaseLabel}`;
  const commit1 = await jsonRequest(saveUrl, {
    method: 'POST',
    headers: auth(authorApiKey),
    body: { doc: JSON.stringify({ ...currentDoc, notes: marker }), action: 'Save' },
  });
  const retryDroppedAck = await jsonRequest(saveUrl, {
    method: 'POST',
    headers: auth(authorApiKey),
    body: { doc: JSON.stringify({ ...currentDoc, notes: marker }), action: 'Save' },
  });
  const versions = await jsonRequest(
    `${root}/api/resource/Version?filters=${encodeURIComponent(JSON.stringify([['ref_doctype', '=', doctype], ['docname', '=', doc.name]]))}`,
    { headers: auth(authorApiKey) },
  );
  const finalDoc = await jsonRequest(docUrl, { headers: auth(authorApiKey) });

  const staleRefused = !staleRes.ok && staleRes.status >= 400;
  const sameDocAbaRefused = !abaAttempt.ok && abaAttempt.status >= 400;
  const lostAckOnce = commit1.ok && !retryDroppedAck.ok && finalDoc.body?.data?.notes === marker;

  return {
    releaseLabel,
    status: 'probed-with-version-doctype-evidence',
    versionRowCount: Array.isArray(versions.body?.data) ? versions.body.data.length : null,
    staleVersionRefused: staleRefused,
    sameDocSpecificTermsAbaRefused: sameDocAbaRefused,
    lostAckReconciledToSingleEffect: lostAckOnce,
    qualifiesSameDocTermsWorkflow: staleRefused && sameDocAbaRefused && lostAckOnce,
  };
}

export async function probeErpNextAfterOpenProjectQualifies(args, openprojectResult) {
  if (!openprojectResult?.dualReleaseQualified) {
    return {
      appId: 'erpnext',
      auditedReleasePair: 'v15.10.0->v15.20.0',
      stageOrder: 2,
      status: 'deferred-until-openproject-13.4-to-14.0-workflow-qualifies',
      probeImplementationReady: true,
      gatingRule: 'Bring ERPNext in only after the isolated OpenProject 13.4.0 -> 14.0.0 workflow qualifies on both releases.',
    };
  }
  if (!args.erpnextV15_10Url || !args.erpnextV15_20Url) {
    return {
      appId: 'erpnext',
      auditedReleasePair: 'v15.10.0->v15.20.0',
      stageOrder: 2,
      status: 'awaiting-owner-approved-erpnext-containers-and-accounts',
      probeImplementationReady: true,
    };
  }
  const v15_10 = await runErpNextSingleReleaseProbe({
    releaseLabel: 'v15.10.0',
    baseUrl: args.erpnextV15_10Url,
    authorApiKey: args.erpnextAuthorApiKey,
    approverApiKey: args.erpnextApproverApiKey,
    doctype: args.erpnextDoctype,
  });
  const v15_20 = await runErpNextSingleReleaseProbe({
    releaseLabel: 'v15.20.0',
    baseUrl: args.erpnextV15_20Url,
    authorApiKey: args.erpnextAuthorApiKey,
    approverApiKey: args.erpnextApproverApiKey,
    doctype: args.erpnextDoctype,
  });
  return {
    appId: 'erpnext',
    auditedReleasePair: 'v15.10.0->v15.20.0',
    stageOrder: 2,
    status: 'probed-both-releases',
    v15_10_0: v15_10,
    v15_20_0: v15_20,
    dualReleaseQualified: v15_10.qualifiesSameDocTermsWorkflow && v15_20.qualifiesSameDocTermsWorkflow,
  };
}

async function probeGiteaLocalIsolated(giteaBin) {
  if (!existsSync(giteaBin)) {
    return {
      appId: 'gitea',
      auditedReleasePair: 'v1.21.11->v1.22.0',
      evidenceScope: 'sequential-endpoint-behavior-only',
      establishesTransactionAtomicity: false,
      establishesGeneralRetrySafety: false,
      status: 'binary-not-present-see-retained-log-receipt',
    };
  }
  const versionLine = execFileSync(giteaBin, ['--version'], { encoding: 'utf8' }).trim();
  const rootDir = mkdtempSync(join(realpathSync(tmpdir()), 'gitea-step2-probe-'));
  const workPath = join(rootDir, 'work');
  const customPath = join(workPath, 'custom');
  const confDir = join(customPath, 'conf');
  const dataDir = join(workPath, 'data');
  const repoRoot = join(workPath, 'repos');
  const logDir = join(workPath, 'log');
  for (const d of [workPath, customPath, confDir, dataDir, repoRoot, logDir]) {
    mkdirSync(d, { recursive: true });
  }

  const port = await pickSafeLoopbackPort();
  const baseUrl = `http://127.0.0.1:${port}`;
  const appIni = join(confDir, 'app.ini');
  writeFileSync(
    appIni,
    [
      'APP_NAME = Gammatron Step2 Isolated Probe',
      'RUN_MODE = prod',
      '',
      '[server]',
      'PROTOCOL = http',
      'HTTP_ADDR = 127.0.0.1',
      `HTTP_PORT = ${port}`,
      `ROOT_URL = ${baseUrl}/`,
      'DISABLE_SSH = true',
      `APP_DATA_PATH = ${dataDir}`,
      'OFFLINE_MODE = true',
      '',
      '[database]',
      'DB_TYPE = sqlite3',
      `PATH = ${join(dataDir, 'gitea.db')}`,
      '',
      '[repository]',
      `ROOT = ${repoRoot}`,
      'DEFAULT_BRANCH = main',
      '',
      '[security]',
      'INSTALL_LOCK = true',
      'SECRET_KEY = step2_isolated_probe_secret_key_local_only',
      'INTERNAL_TOKEN = eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.step2probe',
      '',
      '[service]',
      'DISABLE_REGISTRATION = true',
      'ENABLE_NOTIFY_MAIL = false',
      '',
      '[log]',
      `ROOT_PATH = ${logDir}`,
      'MODE = file',
      'LEVEL = Info',
      'ENABLE_ACCESS_LOG = true',
      'ACCESS = file',
      'ROUTER = file',
      '',
    ].join('\n'),
  );

  const cliBaseArgs = ['--work-path', workPath, '--custom-path', customPath, '--config', appIni];
  let serverProc = null;
  const stdLogs = [];

  try {
    execFileSync(giteaBin, ['migrate', ...cliBaseArgs], { cwd: workPath, stdio: 'pipe' });

    const authorUser = 'probe_author_isolated';
    const approverUser = 'probe_approver_isolated';
    const userPass = 'IsolatedProbePass!2026';

    for (const [u, admin] of [[authorUser, true], [approverUser, false]]) {
      execFileSync(
        giteaBin,
        [
          'admin',
          'user',
          'create',
          ...cliBaseArgs,
          '--username',
          u,
          '--password',
          userPass,
          '--email',
          `${u}@isolated.local`,
          ...(admin ? ['--admin'] : []),
          '--must-change-password=false',
        ],
        { cwd: workPath, stdio: 'pipe' },
      );
    }

    serverProc = spawn(giteaBin, ['web', ...cliBaseArgs], {
      cwd: workPath,
      stdio: ['ignore', 'pipe', 'pipe'],
    });
    serverProc.stdout.on('data', chunk => stdLogs.push(chunk.toString('utf8')));
    serverProc.stderr.on('data', chunk => stdLogs.push(chunk.toString('utf8')));

    await waitForHttpReady(`${baseUrl}/api/v1/version`, 25000);

    const authorAuth = { authUser: authorUser, authPass: userPass };
    const approverAuth = { authUser: approverUser, authPass: userPass };
    const repoName = 'po-release-gate';

    await jsonRequest(`${baseUrl}/api/v1/user/repos`, {
      method: 'POST',
      ...authorAuth,
      body: { name: repoName, auto_init: true, default_branch: 'main', private: true },
    });
    await jsonRequest(
      `${baseUrl}/api/v1/repos/${authorUser}/${repoName}/collaborators/${approverUser}`,
      { method: 'PUT', ...authorAuth, body: { permission: 'write' } },
    );
    await jsonRequest(`${baseUrl}/api/v1/repos/${authorUser}/${repoName}/branch_protections`, {
      method: 'POST',
      ...authorAuth,
      body: {
        branch_name: 'main',
        enable_push: true,
        enable_approvals_whitelist: true,
        approvals_whitelist_username: [approverUser],
        required_approvals: 1,
        block_on_rejected_reviews: true,
      },
    });

    const c1 = await jsonRequest(
      `${baseUrl}/api/v1/repos/${authorUser}/${repoName}/contents/order-a.json`,
      {
        method: 'POST',
        ...authorAuth,
        body: {
          branch: 'main',
          new_branch: 'route-a',
          content: Buffer.from(JSON.stringify({ order: 'PO-101', stage: 'v1' })).toString('base64'),
          message: 'Stage order PO-101 v1',
        },
      },
    );
    const staleSha = c1.body?.commit?.sha;
    const fileSha = c1.body?.content?.sha;
    const c2 = await jsonRequest(
      `${baseUrl}/api/v1/repos/${authorUser}/${repoName}/contents/order-a.json`,
      {
        method: 'PUT',
        ...authorAuth,
        body: {
          branch: 'route-a',
          sha: fileSha,
          content: Buffer.from(JSON.stringify({ order: 'PO-101', stage: 'v2' })).toString('base64'),
          message: 'Stage order PO-101 v2',
        },
      },
    );
    const currentSha = c2.body?.commit?.sha;

    const pr1 = await jsonRequest(`${baseUrl}/api/v1/repos/${authorUser}/${repoName}/pulls`, {
      method: 'POST',
      ...authorAuth,
      body: { title: 'Approve PO-101', head: 'route-a', base: 'main' },
    });
    const pr1Index = pr1.body?.number;

    const waitMergeable = async prNum => {
      for (let attempt = 0; attempt < 40; attempt += 1) {
        const checkPr = await jsonRequest(
          `${baseUrl}/api/v1/repos/${authorUser}/${repoName}/pulls/${prNum}`,
          authorAuth,
        );
        if (checkPr.body?.mergeable === true) return;
        await new Promise(r => setTimeout(r, 120));
      }
    };

    await waitMergeable(pr1Index);
    await jsonRequest(
      `${baseUrl}/api/v1/repos/${authorUser}/${repoName}/pulls/${pr1Index}/reviews`,
      { method: 'POST', ...approverAuth, body: { event: 'APPROVED', body: 'Initial approval (terms v1)' } },
    );

    const staleMerge = await jsonRequest(
      `${baseUrl}/api/v1/repos/${authorUser}/${repoName}/pulls/${pr1Index}/merge`,
      { method: 'POST', ...authorAuth, body: { Do: 'merge', head_commit_id: staleSha } },
    );
    const prAfterStale = await jsonRequest(
      `${baseUrl}/api/v1/repos/${authorUser}/${repoName}/pulls/${pr1Index}`,
      authorAuth,
    );

    await waitMergeable(pr1Index);
    await jsonRequest(
      `${baseUrl}/api/v1/repos/${authorUser}/${repoName}/pulls/${pr1Index}/reviews`,
      { method: 'POST', ...approverAuth, body: { event: 'REQUEST_CHANGES', body: 'Revoked v1 approval' } },
    );
    await waitMergeable(pr1Index);
    const revokedMerge = await jsonRequest(
      `${baseUrl}/api/v1/repos/${authorUser}/${repoName}/pulls/${pr1Index}/merge`,
      { method: 'POST', ...authorAuth, body: { Do: 'merge', head_commit_id: currentSha } },
    );
    const prAfterRevoked = await jsonRequest(
      `${baseUrl}/api/v1/repos/${authorUser}/${repoName}/pulls/${pr1Index}`,
      authorAuth,
    );

    await jsonRequest(
      `${baseUrl}/api/v1/repos/${authorUser}/${repoName}/pulls/${pr1Index}/reviews`,
      { method: 'POST', ...approverAuth, body: { event: 'APPROVED', body: 'Fresh approval under altered cap' } },
    );
    await waitMergeable(pr1Index);
    const firstMergeCommit = await jsonRequest(
      `${baseUrl}/api/v1/repos/${authorUser}/${repoName}/pulls/${pr1Index}/merge`,
      { method: 'POST', ...authorAuth, body: { Do: 'merge', head_commit_id: currentSha } },
    );
    const droppedAckMergeRetry = await jsonRequest(
      `${baseUrl}/api/v1/repos/${authorUser}/${repoName}/pulls/${pr1Index}/merge`,
      { method: 'POST', ...authorAuth, body: { Do: 'merge', head_commit_id: currentSha } },
    );
    const mainCommits = await jsonRequest(
      `${baseUrl}/api/v1/repos/${authorUser}/${repoName}/commits?sha=main`,
      authorAuth,
    );
    const mergeCommitsOnMain = Array.isArray(mainCommits.body)
      ? mainCommits.body.filter(c => String(c?.commit?.message ?? '').startsWith('Merge pull request'))
      : [];

    await jsonRequest(
      `${baseUrl}/api/v1/repos/${authorUser}/${repoName}/contents/order-b.json`,
      {
        method: 'POST',
        ...authorAuth,
        body: {
          branch: 'main',
          new_branch: 'route-b',
          content: Buffer.from(JSON.stringify({ order: 'PO-102', stage: 'v1' })).toString('base64'),
          message: 'Stage order PO-102',
        },
      },
    );
    const pr2 = await jsonRequest(`${baseUrl}/api/v1/repos/${authorUser}/${repoName}/pulls`, {
      method: 'POST',
      ...authorAuth,
      body: { title: 'Review PO-102', head: 'route-b', base: 'main' },
    });
    const pr2Index = pr2.body?.number;
    const rev1 = await jsonRequest(
      `${baseUrl}/api/v1/repos/${authorUser}/${repoName}/pulls/${pr2Index}/reviews`,
      { method: 'POST', ...approverAuth, body: { event: 'COMMENT', body: 'Retry probe comment' } },
    );
    const rev2Retry = await jsonRequest(
      `${baseUrl}/api/v1/repos/${authorUser}/${repoName}/pulls/${pr2Index}/reviews`,
      { method: 'POST', ...approverAuth, body: { event: 'COMMENT', body: 'Retry probe comment' } },
    );
    const pr2Reviews = await jsonRequest(
      `${baseUrl}/api/v1/repos/${authorUser}/${repoName}/pulls/${pr2Index}/reviews`,
      authorAuth,
    );

    await new Promise(r => setTimeout(r, 400));
    serverProc.kill('SIGTERM');
    await new Promise(r => serverProc.once('exit', r));
    serverProc = null;

    const collectedLogSections = [];
    for (const fname of ['access.log', 'router.log', 'gitea.log']) {
      const fpath = join(logDir, fname);
      if (existsSync(fpath)) {
        collectedLogSections.push(`=== ${fname} ===\n${readFileSync(fpath, 'utf8').trim()}`);
      }
    }
    if (stdLogs.length > 0) {
      collectedLogSections.push(`=== server-stdio ===\n${stdLogs.join('').trim()}`);
    }
    const sanitizedServerLog = sanitizeText(collectedLogSections.join('\n\n'), [rootDir, workPath]) + '\n';
    mkdirSync(LOGS_DIR, { recursive: true });
    const retainedLogRelPath =
      'projects/workspace/qualification/workflow-generalization/receipts/logs/gitea-v1.21.11-step2-probe.log';
    writeFileSync(join(LOGS_DIR, 'gitea-v1.21.11-step2-probe.log'), sanitizedServerLog);

    const reviewRetryCount = Array.isArray(pr2Reviews.body) ? pr2Reviews.body.length : 0;
    return {
      appId: 'gitea',
      auditedReleasePair: 'v1.21.11->v1.22.0',
      probedBinaryVersion: versionLine,
      evidenceScope: 'sequential-endpoint-behavior-only',
      establishesTransactionAtomicity: false,
      establishesGeneralRetrySafety: false,
      retainedServerLogPath: retainedLogRelPath,
      retainedServerLogSha256: sha256(sanitizedServerLog),
      observedSequentialBehavior: {
        mergeStaleHeadRejected: staleMerge.status === 409 && prAfterStale.body?.merged === false,
        mergeRevokedApprovalRejected: revokedMerge.status === 405 && prAfterRevoked.body?.merged === false,
        mergeAcceptsOldCallerAttestationAfterRevokeAndRegrant: firstMergeCommit.status === 200,
        mergeSequentialRetryLeftSingleCommit:
          firstMergeCommit.status === 200 && droppedAckMergeRetry.status === 405 && mergeCommitsOnMain.length === 1,
        reviewCreationSequentialRetryLeftTwoRecords:
          rev1.status === 200 && rev2Retry.status === 200 && reviewRetryCount === 2,
      },
      failsSpecificTermsApprovalVersionBindingOnStock: firstMergeCommit.status === 200,
    };
  } finally {
    if (serverProc) serverProc.kill('SIGKILL');
    rmSync(rootDir, { recursive: true, force: true });
  }
}

async function main() {
  const args = parseArgs(process.argv);
  if (args.dryCheck) {
    console.log(JSON.stringify({ ok: true, mode: 'dry-check', passRuleId: 'Stage2-Contract-Pass-v2' }));
    return;
  }
  if (
    !args.passRuleCommentUrl
    || !/^https:\/\/github\.com\/clocksmith\/deco\/issues\/88#issuecomment-\d+$/.test(args.passRuleCommentUrl)
  ) {
    throw Error(
      'Record the pass rule on clocksmith/deco#88 BEFORE probing, then pass `--pass-rule-comment-url https://github.com/clocksmith/deco/issues/88#issuecomment-...`.',
    );
  }

  const dockerState = checkDockerDaemon();
  const openproject = await probeOpenProjectDualRelease(args, dockerState);
  const erpnext = await probeErpNextAfterOpenProjectQualifies(args, openproject);
  const gitea = await probeGiteaLocalIsolated(args.giteaBin);

  const receipt = {
    schema: 'gammatron-step2-upstream-contract-probe-v2',
    spendUsd: 0,
    passRuleId: 'Stage2-Contract-Pass-v2',
    passRuleRecordedBeforeProbeAtUrl: args.passRuleCommentUrl,
    probedAtUtc: new Date().toISOString(),
    targets: { openproject, erpnext, gitea },
  };

  mkdirSync(RECEIPTS_DIR, { recursive: true });
  const outPath = join(RECEIPTS_DIR, 'step2-upstream-probe-receipt.json');
  const text = JSON.stringify(receipt, null, 2) + '\n';
  writeFileSync(outPath, text);
  console.log(JSON.stringify({ receiptSha256: sha256(text), ...receipt }, null, 2));
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  await main();
}
