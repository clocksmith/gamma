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
    lostAckOperationBindingContract:
      'Stock OpenProject has no native Idempotency-Key header on PATCH /api/v3/work_packages/{id}, and WorkPackagePayloadRepresenter ignores `journalNotes` / `comment` on PATCH (comments live on separate non-atomic POST /activities). Furthermore, under default `Setting.journal_aggregation_time_minutes = 5`, `Journals::CreateService#aggregatable?` coalesces consecutive unmarked PATCHes by the SAME user into one journal row (advancing `work_packages.lock_version` faster than `journals.version` and overwriting `work_package_journals` in place). Therefore: (1) API `/activities` alone without DB `work_package_journals` returns `unknown` on a dropped-ack PATCH; (2) embedding `<!-- opbind-v1:<sha256> -->` in `description.raw` binds the exact operation in `work_package_journals.description` across immediate reads and cross-user overwrites (`committed`), while honestly degrading to `unknown` if a same-user edit within the aggregation window overwrote the snapshot; (3) blind retries on a bumped `lockVersion` are always forbidden.',
    mockVsRealProbeBoundary:
      'Loopback mock tests establish runner and reconciler logic only (`establishesUpstreamAppContract: false`); only running `probeOpenProjectDualRelease` against live OpenProject 13.4.0 and 14.0.0 releases establishes the upstream application contract.',
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
    openprojectV14AuthorToken: null,
    openprojectV14ApproverToken: null,
    openprojectV14RestrictedToken: null,
    openprojectV14ApprovedStatusHref: null,
    openprojectV14HoldStatusHref: null,
    openprojectV14DisallowedStatusHref: null,
    openprojectPgV13Url: null,
    openprojectPgV14Url: null,
    openprojectV13Container: null,
    openprojectV14Container: null,
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
    else if (a === '--openproject-v14-author-token') out.openprojectV14AuthorToken = argv[++i];
    else if (a === '--openproject-v14-approver-token') out.openprojectV14ApproverToken = argv[++i];
    else if (a === '--openproject-v14-restricted-token') out.openprojectV14RestrictedToken = argv[++i];
    else if (a === '--openproject-v14-approved-status-href') out.openprojectV14ApprovedStatusHref = argv[++i];
    else if (a === '--openproject-v14-hold-status-href') out.openprojectV14HoldStatusHref = argv[++i];
    else if (a === '--openproject-v14-disallowed-status-href') out.openprojectV14DisallowedStatusHref = argv[++i];
    else if (a === '--openproject-pg-v13-url') out.openprojectPgV13Url = argv[++i];
    else if (a === '--openproject-pg-v14-url') out.openprojectPgV14Url = argv[++i];
    else if (a === '--openproject-v13-container') out.openprojectV13Container = argv[++i];
    else if (a === '--openproject-v14-container') out.openprojectV14Container = argv[++i];
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

function queryPostgresJournalSnapshots(pgUrl, workPackageId) {
  if (!pgUrl) return null;
  const sql = [
    "SELECT COALESCE(json_agg(row_to_json(t) ORDER BY t.version), '[]'::json)::text",
    'FROM (',
    '  SELECT j.id, j.version, j.user_id, COALESCE(j.notes, \'\') AS notes,',
    '         wpj.subject, COALESCE(wpj.description, \'\') AS description,',
    '         wpj.status_id, wpj.estimated_hours',
    '  FROM journals j',
    "  LEFT JOIN work_package_journals wpj ON j.data_type = 'Journal::WorkPackageJournal' AND j.data_id = wpj.id",
    `  WHERE j.journable_type = 'WorkPackage' AND j.journable_id = ${Number(workPackageId)}`,
    ') t;',
  ].join(' ');
  const out = execFileSync('psql', [pgUrl, '-Atc', sql], { encoding: 'utf8', timeout: 5000 }).trim();
  return out ? JSON.parse(out) : [];
}

async function readOpenProjectJournalEvidence(baseUrl, wpId, token, pgUrl = null) {
  const root = baseUrl.replace(/\/$/, '');
  const [wpRes, actRes] = await Promise.all([
    jsonRequest(`${root}/api/v3/work_packages/${wpId}`, { headers: opHeaders(token) }),
    jsonRequest(`${root}/api/v3/work_packages/${wpId}/activities`, { headers: opHeaders(token) }),
  ]);
  const elements = actRes.body?._embedded?.elements;
  if (!wpRes.ok || !actRes.ok || typeof wpRes.body?.lockVersion !== 'number' || !Array.isArray(elements)) {
    return {
      readOk: false,
      wpStatus: wpRes.status,
      activitiesStatus: actRes.status,
      lockVersion: null,
      journalCount: null,
      journalSource: null,
      journals: [],
      pgJournalsByVersion: null,
    };
  }
  const pgRows = queryPostgresJournalSnapshots(pgUrl, wpId);
  const pgJournalsByVersion = Array.isArray(pgRows)
    ? new Map(pgRows.map(r => [Number(r.version), r]))
    : null;
  return {
    readOk: true,
    lockVersion: wpRes.body.lockVersion,
    subject: wpRes.body?.subject,
    estimatedTime: wpRes.body?.estimatedTime ?? null,
    statusHref: wpRes.body?._links?.status?.href ?? null,
    journalCount: pgRows !== null ? pgRows.length : elements.length,
    journalSource: pgRows !== null ? 'postgresql-journals-and-work_package_journals' : 'api-v3-activities-journals',
    journals: elements,
    pgJournalsByVersion,
  };
}

function canonicalizeValue(val) {
  if (val === null || typeof val !== 'object') return val;
  if (Array.isArray(val)) return val.map(canonicalizeValue);
  const out = {};
  for (const k of Object.keys(val).sort()) {
    if (val[k] !== undefined) out[k] = canonicalizeValue(val[k]);
  }
  return out;
}

/**
 * Compute a deterministic cryptographic operation-binding token (`opbind-v1:<sha256>`) over the
 * exact intended OpenProject mutation (`workPackageId`, `preCommitLockVersion`, `expectedActorHref`,
 * `intendedChanges`, `clientOperationId`). Because `journal.version = preCommitLockVersion + 2`
 * alone can be produced by an intervening edit, lost-ack reconciliation requires the committed
 * journal entry to bind this exact operation rather than trusting version number alone.
 */
export function computeOpenProjectOperationBinding({
  workPackageId,
  preCommitLockVersion,
  expectedActorHref = null,
  intendedChanges,
  clientOperationId,
}) {
  if (
    workPackageId === undefined
    || workPackageId === null
    || !Number.isInteger(preCommitLockVersion)
    || preCommitLockVersion < 0
    || !intendedChanges
    || typeof intendedChanges !== 'object'
    || Object.keys(intendedChanges).length === 0
    || typeof clientOperationId !== 'string'
    || clientOperationId.trim().length === 0
  ) {
    throw Error(
      'computeOpenProjectOperationBinding requires workPackageId, preCommitLockVersion, non-empty intendedChanges, and clientOperationId',
    );
  }
  const canonical = JSON.stringify(
    canonicalizeValue({
      schema: 'openproject-op-binding/v1',
      workPackageId: String(workPackageId),
      preCommitLockVersion,
      expectedActorHref: expectedActorHref ?? null,
      intendedChanges,
      clientOperationId: clientOperationId.trim(),
    }),
  );
  return `opbind-v1:${sha256(canonical)}`;
}

function detailRecordsNewValue(detail, expectedText) {
  const raw = typeof detail?.raw === 'string' ? detail.raw : '';
  if (raw) {
    if (/\bdeleted\s*\(.*\)\s*$/s.test(raw)) return false;
    const changedMatch = raw.match(/\bchanged from .* to (.*)$/s);
    if (changedMatch) {
      return changedMatch[1].includes(expectedText);
    }
    if (raw.includes(expectedText)) return true;
  }
  const html = typeof detail?.html === 'string' ? detail.html : '';
  if (html && !raw) {
    return html.includes(expectedText);
  }
  return false;
}

function expectedTaggedDescription(descriptionRaw, bindingToken) {
  return `${descriptionRaw}\n<!-- ${bindingToken} -->`;
}

function journalCarriesBindingToken(journal, pgRow, bindingToken, intendedChanges) {
  if (!bindingToken) return false;
  const notes = pgRow ? String(pgRow.notes ?? '') : String(journal?.comment?.raw ?? '');
  if (notes.includes(bindingToken)) return true;
  if (pgRow && typeof pgRow.description === 'string' && pgRow.description.includes(bindingToken)) {
    return true;
  }
  return false;
}

function verifyJournalBindsOperation(
  journal,
  pgRow,
  { bindingToken, expectedActorHref = null, intendedChanges },
) {
  const notes = pgRow ? String(pgRow.notes ?? '') : String(journal?.comment?.raw ?? '');
  const boundInNotes = Boolean(bindingToken && notes.includes(bindingToken));
  const boundInPgDescription = Boolean(
    bindingToken
      && pgRow
      && intendedChanges.descriptionRaw !== undefined
      && pgRow.description === expectedTaggedDescription(intendedChanges.descriptionRaw, bindingToken),
  );
  if (!boundInNotes && !boundInPgDescription) {
    return false;
  }
  if (expectedActorHref) {
    const apiActor = journal?._links?.user?.href ?? null;
    if (apiActor !== expectedActorHref) return false;
    const userIdMatch = expectedActorHref.match(/\/users\/(\d+)$/);
    if (pgRow && userIdMatch && Number(pgRow.user_id) !== Number(userIdMatch[1])) {
      return false;
    }
  }
  const details = Array.isArray(journal?.details) ? journal.details : [];
  if (intendedChanges.subject !== undefined) {
    if (pgRow && pgRow.subject !== intendedChanges.subject) return false;
    if (!details.some(d => detailRecordsNewValue(d, intendedChanges.subject))) return false;
  }
  if (intendedChanges.descriptionRaw !== undefined) {
    if (pgRow) {
      const validDesc =
        pgRow.description === intendedChanges.descriptionRaw
        || pgRow.description === expectedTaggedDescription(intendedChanges.descriptionRaw, bindingToken);
      if (!validDesc) return false;
    }
    if (!details.some(d => /description/i.test(String(d?.raw ?? '')))) return false;
  }
  if (intendedChanges.statusHref !== undefined) {
    const statusIdMatch = String(intendedChanges.statusHref).match(/\/statuses\/(\d+)$/);
    if (pgRow && statusIdMatch && Number(pgRow.status_id) !== Number(statusIdMatch[1])) return false;
    if (!details.some(d => /status/i.test(String(d?.raw ?? '')))) return false;
  }
  if (intendedChanges.estimatedTime !== undefined) {
    if (!details.some(d => /estimated time/i.test(String(d?.raw ?? '')))) return false;
  }
  return true;
}

function resolveBindingSpec({ workPackageId, preCommitLockVersion, expectedOperation }) {
  if (
    !expectedOperation
    || typeof expectedOperation !== 'object'
    || typeof expectedOperation.clientOperationId !== 'string'
    || expectedOperation.clientOperationId.trim().length === 0
    || !expectedOperation.intendedChanges
    || typeof expectedOperation.intendedChanges !== 'object'
    || Object.keys(expectedOperation.intendedChanges).length === 0
  ) {
    return null;
  }
  const bindingToken = computeOpenProjectOperationBinding({
    workPackageId,
    preCommitLockVersion,
    expectedActorHref: expectedOperation.expectedActorHref ?? null,
    intendedChanges: expectedOperation.intendedChanges,
    clientOperationId: expectedOperation.clientOperationId,
  });
  return {
    bindingToken,
    expectedActorHref: expectedOperation.expectedActorHref ?? null,
    intendedChanges: expectedOperation.intendedChanges,
  };
}

function payloadBindsExpectedOperation(payload, bindingSpec) {
  if (!payload || typeof payload !== 'object' || !bindingSpec) return false;
  const notes = typeof payload.journalNotes === 'string'
    ? payload.journalNotes
    : (typeof payload.comment?.raw === 'string' ? payload.comment.raw : '');
  const { intendedChanges } = bindingSpec;
  const rawDesc = payload.description?.raw ?? null;
  const descCarriesTag =
    intendedChanges.descriptionRaw !== undefined
    && rawDesc === expectedTaggedDescription(intendedChanges.descriptionRaw, bindingSpec.bindingToken);
  if (!notes.includes(bindingSpec.bindingToken) && !descCarriesTag) return false;
  if (intendedChanges.subject !== undefined && payload.subject !== intendedChanges.subject) return false;
  if (
    intendedChanges.descriptionRaw !== undefined
    && rawDesc !== intendedChanges.descriptionRaw
    && !descCarriesTag
  ) {
    return false;
  }
  if (
    intendedChanges.statusHref !== undefined
    && (payload._links?.status?.href ?? null) !== intendedChanges.statusHref
  ) {
    return false;
  }
  if (
    intendedChanges.estimatedTime !== undefined
    && payload.estimatedTime !== intendedChanges.estimatedTime
  ) {
    return false;
  }
  return true;
}

/**
 * Reconcile a dropped post-commit acknowledgment on OpenProject `PATCH /api/v3/work_packages/{id}`
 * to an explicit 3-way `disposition: 'committed' | 'not_applied_safe_to_retry' | 'unknown'`:
 *   1. Reads `work_package` + `activities` (`journals`, plus `work_package_journals` when `pgUrl` is set)
 *      FIRST (`extraWritesSent: 0`).
 *   2. Never treats `journal.version = preCommitLockVersion + 2` alone as proof of commit (an intervening
 *      edit at `preCommitLockVersion` produces that same `journal.version`). Reports `disposition: 'committed'`
 *      ONLY when a journal entry (`version >= preCommitLockVersion + 2`) binds the exact `expectedOperation`
 *      (`opbind-v1:<sha256>` in `journal.comment.raw` / `journals.notes` + verified actor + recorded
 *      attribute changes / `work_package_journals` snapshot).
 *   3. When `expectedOperation` is absent/unbound, when `lockVersion` has moved without an operation-bound
 *      journal (including an intervening edit at `journal.version = preCommitLockVersion + 2`), or when an
 *      opt-in retry errors/times out without bound journal confirmation, reports `disposition: 'unknown'`
 *      without retrying (`allowRetryAtPreCommitVersion: false`).
 */
export async function reconcileOpenProjectLostAck({
  baseUrl,
  workPackageId,
  apiToken,
  preCommitLockVersion,
  expectedOperation = null,
  payload = null,
  retryIfSafe = false,
  pgUrl = null,
}) {
  if (!Number.isInteger(preCommitLockVersion) || preCommitLockVersion < 0) {
    return {
      disposition: 'unknown',
      reason: 'invalid-precommit-lock-version',
      extraWritesSent: 0,
      retryHttpStatus: null,
      allowRetryAtPreCommitVersion: false,
      forbidBlindRetryOnBumpedVersion: true,
      lockVersionAfterReconcile: null,
      matchingDurableJournalEffects: 0,
      totalJournalCount: null,
      journalSource: null,
      reconciledToSingleDurableEffect: false,
    };
  }

  const bindingSpec = resolveBindingSpec({ workPackageId, preCommitLockVersion, expectedOperation });
  if (!bindingSpec) {
    return {
      disposition: 'unknown',
      reason: 'missing-exact-operation-binding',
      extraWritesSent: 0,
      retryHttpStatus: null,
      allowRetryAtPreCommitVersion: false,
      forbidBlindRetryOnBumpedVersion: true,
      lockVersionAfterReconcile: null,
      matchingDurableJournalEffects: 0,
      totalJournalCount: null,
      journalSource: null,
      reconciledToSingleDurableEffect: false,
    };
  }

  let evidence;
  try {
    evidence = await readOpenProjectJournalEvidence(baseUrl, workPackageId, apiToken, pgUrl);
  } catch {
    evidence = { readOk: false };
  }
  if (!evidence.readOk) {
    return {
      disposition: 'unknown',
      reason: 'journal-evidence-read-failed',
      extraWritesSent: 0,
      retryHttpStatus: null,
      allowRetryAtPreCommitVersion: false,
      forbidBlindRetryOnBumpedVersion: true,
      lockVersionAfterReconcile: null,
      matchingDurableJournalEffects: 0,
      totalJournalCount: null,
      journalSource: null,
      reconciledToSingleDurableEffect: false,
    };
  }

  const findBoundJournals = ev =>
    ev.journals.filter(j => {
      const pgRow = ev.pgJournalsByVersion ? (ev.pgJournalsByVersion.get(Number(j?.version)) ?? null) : null;
      return verifyJournalBindsOperation(j, pgRow, bindingSpec);
    });

  // Also detect any journal carrying the binding token whose recorded fields/actor DO NOT match
  // `expectedOperation` (tampered or partial/mismatched write -> `unknown`):
  const hasTokenMismatchJournal = ev =>
    ev.journals.some(j => {
      const pgRow = ev.pgJournalsByVersion ? (ev.pgJournalsByVersion.get(Number(j?.version)) ?? null) : null;
      return (
        journalCarriesBindingToken(j, pgRow, bindingSpec.bindingToken, bindingSpec.intendedChanges)
        && !verifyJournalBindsOperation(j, pgRow, bindingSpec)
      );
    });

  if (hasTokenMismatchJournal(evidence)) {
    return {
      disposition: 'unknown',
      reason: 'journal-token-present-but-operation-fields-or-actor-mismatch',
      extraWritesSent: 0,
      retryHttpStatus: null,
      allowRetryAtPreCommitVersion: false,
      forbidBlindRetryOnBumpedVersion: true,
      lockVersionAfterReconcile: evidence.lockVersion,
      matchingDurableJournalEffects: 0,
      totalJournalCount: evidence.journalCount,
      journalSource: evidence.journalSource,
      reconciledToSingleDurableEffect: false,
    };
  }

  // `bindingSpec.bindingToken` cryptographically hashes `preCommitLockVersion` inside its SHA-256
  // preimage; meanwhile OpenProject's 5-minute journal aggregation window can keep `journals.version`
  // smaller than `lock_version + 1` when earlier unmarked edits coalesced, so any update journal
  // (`matchedVersion >= 2`) matching `bindingSpec` is bound to `preCommitLockVersion`.
  const matchingJournals = findBoundJournals(evidence);
  if (matchingJournals.length > 1) {
    return {
      disposition: 'unknown',
      reason: 'multiple-journals-matched-operation-binding',
      extraWritesSent: 0,
      retryHttpStatus: null,
      allowRetryAtPreCommitVersion: false,
      forbidBlindRetryOnBumpedVersion: true,
      lockVersionAfterReconcile: evidence.lockVersion,
      matchingDurableJournalEffects: matchingJournals.length,
      totalJournalCount: evidence.journalCount,
      journalSource: evidence.journalSource,
      reconciledToSingleDurableEffect: false,
    };
  }
  if (matchingJournals.length === 1) {
    const matchedVersion = Number(matchingJournals[0]?.version);
    if (!Number.isInteger(matchedVersion) || matchedVersion < 2) {
      return {
        disposition: 'unknown',
        reason: 'bound-journal-predates-precommit-lock-version',
        extraWritesSent: 0,
        retryHttpStatus: null,
        allowRetryAtPreCommitVersion: false,
        forbidBlindRetryOnBumpedVersion: true,
        lockVersionAfterReconcile: evidence.lockVersion,
        matchingDurableJournalEffects: 1,
        totalJournalCount: evidence.journalCount,
        journalSource: evidence.journalSource,
        reconciledToSingleDurableEffect: false,
      };
    }
    return {
      disposition: 'committed',
      reason: 'verified-operation-bound-journal-without-retry',
      operationBindingToken: bindingSpec.bindingToken,
      extraWritesSent: 0,
      retryHttpStatus: null,
      allowRetryAtPreCommitVersion: false,
      forbidBlindRetryOnBumpedVersion: true,
      lockVersionAfterReconcile: evidence.lockVersion,
      matchingJournalVersion: matchedVersion,
      matchingDurableJournalEffects: 1,
      totalJournalCount: evidence.journalCount,
      journalSource: evidence.journalSource,
      reconciledToSingleDurableEffect: true,
    };
  }

  // If `lockVersion` has moved (including when `journal.version = preCommitLockVersion + 2` exists from
  // an intervening edit or an unbound mutation), refuse to mistake it for success and forbid retry:
  if (evidence.lockVersion !== preCommitLockVersion) {
    const hasUnboundNextJournal = evidence.journals.some(
      j => Number(j?.version) === preCommitLockVersion + 2,
    );
    return {
      disposition: 'unknown',
      reason: hasUnboundNextJournal
        ? 'intervening-or-unbound-journal-at-expected-version'
        : 'lock-version-advanced-without-bound-operation-journal',
      extraWritesSent: 0,
      retryHttpStatus: null,
      allowRetryAtPreCommitVersion: false,
      forbidBlindRetryOnBumpedVersion: true,
      lockVersionAfterReconcile: evidence.lockVersion,
      matchingDurableJournalEffects: 0,
      totalJournalCount: evidence.journalCount,
      journalSource: evidence.journalSource,
      reconciledToSingleDurableEffect: false,
    };
  }

  if (!retryIfSafe) {
    return {
      disposition: 'not_applied_safe_to_retry',
      reason: 'lock-version-unchanged-and-operation-absent',
      operationBindingToken: bindingSpec.bindingToken,
      extraWritesSent: 0,
      retryHttpStatus: null,
      allowRetryAtPreCommitVersion: true,
      forbidBlindRetryOnBumpedVersion: true,
      lockVersionAfterReconcile: evidence.lockVersion,
      matchingDurableJournalEffects: 0,
      totalJournalCount: evidence.journalCount,
      journalSource: evidence.journalSource,
      reconciledToSingleDurableEffect: false,
    };
  }

  if (!payloadBindsExpectedOperation(payload, bindingSpec)) {
    return {
      disposition: 'unknown',
      reason: 'retry-payload-does-not-bind-expected-operation',
      extraWritesSent: 0,
      retryHttpStatus: null,
      allowRetryAtPreCommitVersion: false,
      forbidBlindRetryOnBumpedVersion: true,
      lockVersionAfterReconcile: evidence.lockVersion,
      matchingDurableJournalEffects: 0,
      totalJournalCount: evidence.journalCount,
      journalSource: evidence.journalSource,
      reconciledToSingleDurableEffect: false,
    };
  }

  const root = baseUrl.replace(/\/$/, '');
  const wpUrl = `${root}/api/v3/work_packages/${workPackageId}`;
  let retryRes = null;
  let retryTransportError = false;
  try {
    retryRes = await jsonRequest(wpUrl, {
      method: 'PATCH',
      headers: opHeaders(apiToken),
      body: { ...payload, lockVersion: preCommitLockVersion },
    });
  } catch {
    retryTransportError = true;
  }

  let afterEvidence;
  try {
    afterEvidence = await readOpenProjectJournalEvidence(baseUrl, workPackageId, apiToken, pgUrl);
  } catch {
    afterEvidence = { readOk: false };
  }
  if (!afterEvidence.readOk || hasTokenMismatchJournal(afterEvidence)) {
    return {
      disposition: 'unknown',
      reason: !afterEvidence.readOk
        ? 'post-retry-journal-evidence-read-failed'
        : 'post-retry-journal-operation-mismatch',
      extraWritesSent: 1,
      retryHttpStatus: retryRes?.status ?? null,
      allowRetryAtPreCommitVersion: false,
      forbidBlindRetryOnBumpedVersion: true,
      lockVersionAfterReconcile: afterEvidence.lockVersion ?? null,
      matchingDurableJournalEffects: 0,
      totalJournalCount: afterEvidence.journalCount ?? null,
      journalSource: afterEvidence.journalSource ?? null,
      reconciledToSingleDurableEffect: false,
    };
  }

  const afterMatching = findBoundJournals(afterEvidence);
  if (
    afterMatching.length === 1
    && Number(afterMatching[0]?.version) >= 2
  ) {
    return {
      disposition: 'committed',
      reason: retryTransportError
        ? 'committed-despite-retry-ack-loss'
        : retryRes?.status === 409
          ? 'prior-in-flight-commit-verified-in-journal'
          : 'committed-via-versioned-retry',
      operationBindingToken: bindingSpec.bindingToken,
      extraWritesSent: 1,
      retryHttpStatus: retryRes?.status ?? null,
      allowRetryAtPreCommitVersion: false,
      forbidBlindRetryOnBumpedVersion: true,
      lockVersionAfterReconcile: afterEvidence.lockVersion,
      matchingJournalVersion: Number(afterMatching[0].version),
      matchingDurableJournalEffects: 1,
      totalJournalCount: afterEvidence.journalCount,
      journalSource: afterEvidence.journalSource,
      reconciledToSingleDurableEffect: true,
    };
  }

  return {
    disposition: 'unknown',
    reason: retryTransportError
      ? 'retry-patch-transport-error'
      : 'retry-patch-failed-without-bound-operation-journal',
    extraWritesSent: 1,
    retryHttpStatus: retryRes?.status ?? null,
    allowRetryAtPreCommitVersion: false,
    forbidBlindRetryOnBumpedVersion: true,
    lockVersionAfterReconcile: afterEvidence.lockVersion,
    matchingDurableJournalEffects: afterMatching.length,
    totalJournalCount: afterEvidence.journalCount,
    journalSource: afterEvidence.journalSource,
    reconciledToSingleDurableEffect: false,
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

  // CHECK 5: Exact-operation-bound lost-ack reconciliation (`reconcileOpenProjectLostAck`):
  //   (5a) Intervening edit landing at `journal.version = preCommitLockVersion + 2` MUST NOT be
  //        mistaken for success -> `disposition: 'unknown'`, `extraWritesSent: 0`, no retry;
  //   (5b) Unbound mutation without `expectedOperation` -> `disposition: 'unknown'`, `extraWritesSent: 0`, no retry;
  //   (5c) Operation-bound mutation (`opbind-v1:<sha256>` + actor + intendedChanges):
  //        before write -> `not_applied_safe_to_retry` (`extraWritesSent: 0`);
  //        after commit with dropped ack -> read-first `committed` (`extraWritesSent: 0`), including
  //        after a subsequent edit overwrites `description.raw` and `subject`.
  const authorActorHref = createdMain.body?._links?.author?.href ?? null;
  const lockAtIntervening = evAfterRace.lockVersion;
  const unappliedExpectedOp = {
    clientOperationId: `unapplied-op-${releaseLabel}-${lockAtIntervening}`,
    expectedActorHref: authorActorHref,
    intendedChanges: {
      subject: `Intended Final Review (${releaseLabel})`,
      descriptionRaw: 'Intended staged body that never reached server',
    },
  };
  const interveningEditRes = await jsonRequest(wpUrl, {
    method: 'PATCH',
    headers: opHeaders(approverToken),
    body: {
      lockVersion: lockAtIntervening,
      description: { raw: 'Intervening coworker edit at preCommitLockVersion + 2' },
      journalNotes: 'Coworker intervening comment',
    },
  });
  const interveningEditCheck = await reconcileOpenProjectLostAck({
    baseUrl,
    workPackageId: wpId,
    apiToken: authorToken,
    preCommitLockVersion: lockAtIntervening,
    expectedOperation: unappliedExpectedOp,
    retryIfSafe: true,
    pgUrl,
  });
  const unboundVersionOnlyCheck = await reconcileOpenProjectLostAck({
    baseUrl,
    workPackageId: wpId,
    apiToken: authorToken,
    preCommitLockVersion: lockAtIntervening,
    expectedOperation: null,
    retryIfSafe: true,
    pgUrl,
  });

  const evAfterIntervening = await readOpenProjectJournalEvidence(baseUrl, wpId, authorToken, pgUrl);
  const lockBeforeLostAck = evAfterIntervening.lockVersion;
  const journalsBeforeLostAck = evAfterIntervening.journalCount;
  const boundExpectedOp = {
    clientOperationId: `idem-op-${releaseLabel}-${lockBeforeLostAck}`,
    expectedActorHref: authorActorHref,
    intendedChanges: {
      subject: `Final Staged Subject (${releaseLabel})`,
      descriptionRaw: `Final staged review (${releaseLabel}, lock=${lockBeforeLostAck})`,
    },
  };
  const opBindingToken = computeOpenProjectOperationBinding({
    workPackageId: wpId,
    preCommitLockVersion: lockBeforeLostAck,
    expectedActorHref: boundExpectedOp.expectedActorHref,
    intendedChanges: boundExpectedOp.intendedChanges,
    clientOperationId: boundExpectedOp.clientOperationId,
  });
  const lostAckPayload = {
    subject: boundExpectedOp.intendedChanges.subject,
    description: {
      raw: expectedTaggedDescription(boundExpectedOp.intendedChanges.descriptionRaw, opBindingToken),
    },
    journalNotes: `Commit ${opBindingToken}`,
  };
  const preWriteCheck = await reconcileOpenProjectLostAck({
    baseUrl,
    workPackageId: wpId,
    apiToken: authorToken,
    preCommitLockVersion: lockBeforeLostAck,
    expectedOperation: boundExpectedOp,
    payload: lostAckPayload,
    retryIfSafe: false,
    pgUrl,
  });
  const committedButAckDropped = await jsonRequest(wpUrl, {
    method: 'PATCH',
    headers: opHeaders(authorToken),
    body: { ...lostAckPayload, lockVersion: lockBeforeLostAck },
  });
  const apiOnlyWithoutPgCheck = pgUrl
    ? await reconcileOpenProjectLostAck({
        baseUrl,
        workPackageId: wpId,
        apiToken: authorToken,
        preCommitLockVersion: lockBeforeLostAck,
        expectedOperation: boundExpectedOp,
        payload: lostAckPayload,
        retryIfSafe: true,
        pgUrl: null,
      })
    : null;
  const reconcileResult = await reconcileOpenProjectLostAck({
    baseUrl,
    workPackageId: wpId,
    apiToken: authorToken,
    preCommitLockVersion: lockBeforeLostAck,
    expectedOperation: boundExpectedOp,
    payload: lostAckPayload,
    retryIfSafe: true,
    pgUrl,
  });
  const overwriteDescriptionRes = await jsonRequest(wpUrl, {
    method: 'PATCH',
    headers: opHeaders(approverToken),
    body: {
      lockVersion: reconcileResult.lockVersionAfterReconcile,
      subject: `Post-Review Subject (${releaseLabel})`,
      description: { raw: 'Follow-up note completely replacing previous descriptionRaw' },
      journalNotes: 'Follow-up note without prior operation binding',
    },
  });
  const reconcileAfterOverwrite = await reconcileOpenProjectLostAck({
    baseUrl,
    workPackageId: wpId,
    apiToken: authorToken,
    preCommitLockVersion: lockBeforeLostAck,
    expectedOperation: boundExpectedOp,
    payload: lostAckPayload,
    retryIfSafe: true,
    pgUrl,
  });

  // Also probe same-user 5-minute journal aggregation window (`Journals::CreateService#aggregatable?`)
  // on a disposable WorkPackage when connected to real OpenProject PostgreSQL:
  let sameUserAggregationWindowDiagnostic = null;
  if (pgUrl) {
    const wpAgg = await jsonRequest(createUrl, {
      method: 'POST',
      headers: opHeaders(approverToken),
      body: { subject: `Agg Probe (${releaseLabel})`, description: { raw: 'init' } },
    });
    const aggId = wpAgg.body.id;
    const aggUrl = `${root}/api/v3/work_packages/${aggId}`;
    const aggOp = {
      clientOperationId: `agg-op-${releaseLabel}-0`,
      expectedActorHref: authorActorHref,
      intendedChanges: {
        subject: `Agg Bound (${releaseLabel})`,
        descriptionRaw: `Agg staged (${releaseLabel})`,
      },
    };
    const aggTok = computeOpenProjectOperationBinding({
      workPackageId: aggId,
      preCommitLockVersion: 0,
      expectedActorHref: aggOp.expectedActorHref,
      intendedChanges: aggOp.intendedChanges,
      clientOperationId: aggOp.clientOperationId,
    });
    await jsonRequest(aggUrl, {
      method: 'PATCH',
      headers: opHeaders(authorToken),
      body: {
        lockVersion: 0,
        subject: aggOp.intendedChanges.subject,
        description: { raw: expectedTaggedDescription(aggOp.intendedChanges.descriptionRaw, aggTok) },
      },
    });
    const beforeSameUserOverwrite = await reconcileOpenProjectLostAck({
      baseUrl,
      workPackageId: aggId,
      apiToken: authorToken,
      preCommitLockVersion: 0,
      expectedOperation: aggOp,
      retryIfSafe: true,
      pgUrl,
    });
    await jsonRequest(aggUrl, {
      method: 'PATCH',
      headers: opHeaders(authorToken),
      body: {
        lockVersion: 1,
        subject: `Agg SameUser Overwrite (${releaseLabel})`,
        description: { raw: 'Same user edit within 5m aggregation window' },
      },
    });
    const afterSameUserOverwrite = await reconcileOpenProjectLostAck({
      baseUrl,
      workPackageId: aggId,
      apiToken: authorToken,
      preCommitLockVersion: 0,
      expectedOperation: aggOp,
      retryIfSafe: true,
      pgUrl,
    });
    sameUserAggregationWindowDiagnostic = {
      beforeSameUserOverwriteDisposition: beforeSameUserOverwrite.disposition,
      afterSameUserOverwriteDisposition: afterSameUserOverwrite.disposition,
      extraWritesOnCoalescedUnknown: afterSameUserOverwrite.extraWritesSent,
      coalescedInPlaceWithinDefault5mWindow:
        beforeSameUserOverwrite.disposition === 'committed'
        && afterSameUserOverwrite.disposition === 'unknown'
        && afterSameUserOverwrite.extraWritesSent === 0,
    };
  }

  const validInterveningReasons = new Set([
    'intervening-or-unbound-journal-at-expected-version',
    'lock-version-advanced-without-bound-operation-journal',
  ]);
  const lostAckSingleDurableEffectPass =
    interveningEditRes.status === 200
    && interveningEditCheck.disposition === 'unknown'
    && validInterveningReasons.has(interveningEditCheck.reason)
    && interveningEditCheck.extraWritesSent === 0
    && interveningEditCheck.allowRetryAtPreCommitVersion === false
    && interveningEditCheck.reconciledToSingleDurableEffect === false
    && unboundVersionOnlyCheck.disposition === 'unknown'
    && unboundVersionOnlyCheck.extraWritesSent === 0
    && unboundVersionOnlyCheck.allowRetryAtPreCommitVersion === false
    && preWriteCheck.disposition === 'not_applied_safe_to_retry'
    && preWriteCheck.extraWritesSent === 0
    && preWriteCheck.allowRetryAtPreCommitVersion === true
    && committedButAckDropped.status === 200
    && (apiOnlyWithoutPgCheck === null
      || (apiOnlyWithoutPgCheck.disposition === 'unknown' && apiOnlyWithoutPgCheck.extraWritesSent === 0))
    && reconcileResult.disposition === 'committed'
    && reconcileResult.extraWritesSent === 0
    && reconcileResult.reconciledToSingleDurableEffect
    && reconcileResult.totalJournalCount === journalsBeforeLostAck + 1
    && overwriteDescriptionRes.status === 200
    && reconcileAfterOverwrite.disposition === 'committed'
    && reconcileAfterOverwrite.extraWritesSent === 0
    && reconcileAfterOverwrite.reconciledToSingleDurableEffect;

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
        interveningEditAtExpectedVersionDisposition: interveningEditCheck.disposition,
        interveningEditReason: interveningEditCheck.reason,
        unboundOperationDisposition: unboundVersionOnlyCheck.disposition,
        preWriteDisposition: preWriteCheck.disposition,
        apiActivitiesWithoutDbSnapshotDisposition: apiOnlyWithoutPgCheck?.disposition ?? null,
        afterDescriptionOverwriteDisposition: reconcileAfterOverwrite.disposition,
        sameUserAggregationWindowDiagnostic,
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
    authorToken: args.openprojectV14AuthorToken ?? args.openprojectAuthorToken,
    approverToken: args.openprojectV14ApproverToken ?? args.openprojectApproverToken,
    restrictedToken: args.openprojectV14RestrictedToken ?? args.openprojectRestrictedToken,
    approvedStatusHref: args.openprojectV14ApprovedStatusHref ?? args.openprojectApprovedStatusHref,
    holdStatusHref: args.openprojectV14HoldStatusHref ?? args.openprojectHoldStatusHref,
    disallowedStatusHref: args.openprojectV14DisallowedStatusHref ?? args.openprojectDisallowedStatusHref,
    pgUrl: args.openprojectPgV14Url,
  });
  const captureContainerLog = (containerName, outFileName, tokensToRedact) => {
    if (!containerName) return null;
    try {
      const raw = execFileSync('docker', ['logs', '--tail', '600', containerName], {
        encoding: 'utf8',
        stdio: ['ignore', 'pipe', 'pipe'],
        timeout: 8000,
      });
      let cleaned = sanitizeText(raw, tokensToRedact.filter(Boolean));
      for (const tok of tokensToRedact.filter(Boolean)) {
        cleaned = cleaned.split(tok).join('<REDACTED_TOKEN>');
      }
      cleaned = cleaned.trim() + '\n';
      mkdirSync(LOGS_DIR, { recursive: true });
      writeFileSync(join(LOGS_DIR, outFileName), cleaned);
      return {
        retainedServerLogPath: `projects/workspace/qualification/workflow-generalization/receipts/logs/${outFileName}`,
        retainedServerLogSha256: sha256(cleaned),
      };
    } catch {
      return null;
    }
  };

  const redactList = [
    args.openprojectAuthorToken,
    args.openprojectApproverToken,
    args.openprojectRestrictedToken,
    args.openprojectV14AuthorToken,
    args.openprojectV14ApproverToken,
    args.openprojectV14RestrictedToken,
  ];
  const log13 = captureContainerLog(
    args.openprojectV13Container,
    'openproject-v13.4.0-step2-probe.log',
    redactList,
  );
  const log14 = captureContainerLog(
    args.openprojectV14Container,
    'openproject-v14.0.0-step2-probe.log',
    redactList,
  );

  return {
    appId: 'openproject',
    auditedReleasePair: 'v13.4.0->v14.0.0',
    stageOrder: 1,
    status: 'probed-both-releases',
    establishesUpstreamAppContract: true,
    serverCodeAudit: OPENPROJECT_SERVER_CODE_AUDIT,
    v13_4_0: { ...v13, ...(log13 ?? {}) },
    v14_0_0: { ...v14, ...(log14 ?? {}) },
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
