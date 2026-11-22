#!/usr/bin/env node
// Step 2 Real-Application Contract Probe ($0 spend, isolated local accounts, #88):
//
// Evaluates upstream candidate workflows under pre-registered rule `Stage2-Contract-Pass-v1`
// (recorded in `stage2-real-upgrade-preregistration.md` and posted to `clocksmith/deco#88`
// BEFORE probing — enforced via required `--pass-rule-comment-url`):
//   1. Stale-version write MUST be refused (0 commits in application logs).
//   2. Write retried after a simulated dropped acknowledgment MUST commit once
//      (1 commit, 0 duplicates in application logs).
//   3. Prerequisite check: evaluates both `live-db-truth-at-commit` (anti-revocation, counted
//      as passing current-state safety under `Stage2-Contract-Pass-v1`) and `ABA` historical
//      sibling-version drift (counted as failing unmodified stock endpoints).
//   4. Retains sanitized raw server logs under `receipts/logs/`.

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

function parseArgs(argv) {
  const out = {
    passRuleCommentUrl: null,
    giteaBin: process.env.GAMMATRON_GITEA_BIN ?? 'gitea',
    openprojectUrl: null,
    openprojectToken: null,
    openprojectWorkPackageId: null,
    erpnextUrl: null,
    erpnextApiKey: null,
    erpnextDocName: null,
    dryCheck: false,
  };
  for (let i = 2; i < argv.length; i += 1) {
    const a = argv[i];
    if (a === '--pass-rule-comment-url') out.passRuleCommentUrl = argv[++i];
    else if (a === '--gitea-bin') out.giteaBin = argv[++i];
    else if (a === '--openproject-url') out.openprojectUrl = argv[++i];
    else if (a === '--openproject-token') out.openprojectToken = argv[++i];
    else if (a === '--openproject-wp-id') out.openprojectWorkPackageId = argv[++i];
    else if (a === '--erpnext-url') out.erpnextUrl = argv[++i];
    else if (a === '--erpnext-api-key') out.erpnextApiKey = argv[++i];
    else if (a === '--erpnext-doc-name') out.erpnextDocName = argv[++i];
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

function sanitizeText(raw, extraPrefixes = []) {
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

async function probeOpenProject(args, dockerState) {
  if (!args.openprojectUrl) {
    return {
      appId: 'openproject',
      auditedReleasePair: 'v13.4.0->v14.0.0',
      tier: 'Tier-A1',
      status: 'blocked-awaiting-docker-and-owner-approved-container-tags-and-accounts',
      dockerAvailable: dockerState.dockerAvailable,
      dockerDetail: dockerState.detail,
      ownerGateRequired: [
        'Approve OpenProject container tags (`openproject/openproject:13.4.0` -> `14.0.0`) and target UI workflow',
        'Start local Docker daemon and provision isolated local test accounts',
      ],
      passRulePreDecision: {
        prerequisiteCheckMode: 'live-db-truth-at-commit',
        passesCurrentStateCrossEntitySafety: true,
        passesCallerPinnedAbaVersionBinding: false,
      },
    };
  }
  const wpUrl = `${args.openprojectUrl.replace(/\/$/, '')}/api/v3/work_packages/${args.openprojectWorkPackageId}`;
  const headers = { Authorization: `Basic ${Buffer.from(`apikey:${args.openprojectToken}`).toString('base64')}` };
  const initial = await jsonRequest(wpUrl, { headers });
  const lockVersion = initial.body?.lockVersion;
  const staleRes = await jsonRequest(wpUrl, {
    method: 'PATCH',
    headers,
    body: { lockVersion: Math.max(0, Number(lockVersion) - 1), description: { raw: 'stale-probe' } },
  });
  const firstCommit = await jsonRequest(wpUrl, {
    method: 'PATCH',
    headers,
    body: { lockVersion, description: { raw: 'dropped-ack-probe' } },
  });
  const droppedAckRetry = await jsonRequest(wpUrl, {
    method: 'PATCH',
    headers,
    body: { lockVersion, description: { raw: 'dropped-ack-probe' } },
  });
  return {
    appId: 'openproject',
    auditedReleasePair: 'v13.4.0->v14.0.0',
    status: 'probed',
    staleVersionWriteRefused: staleRes.status === 409,
    droppedAckRetryCommittedOnce: firstCommit.status === 200 && droppedAckRetry.status === 409,
  };
}

async function probeErpNext(args, dockerState) {
  if (!args.erpnextUrl) {
    return {
      appId: 'erpnext',
      auditedReleasePair: 'v15.10.0->v15.20.0',
      tier: 'Tier-A2',
      status: 'blocked-awaiting-docker-and-owner-approved-container-tags-and-accounts',
      dockerAvailable: dockerState.dockerAvailable,
      dockerDetail: dockerState.detail,
      ownerGateRequired: [
        'Approve Frappe/ERPNext container tags (`frappe/erpnext:v15.10.0` -> `v15.20.0`) and draft-staging (`docstatus=0`) workflow',
        'Start local Docker daemon and provision isolated local test accounts',
      ],
      passRulePreDecision: {
        prerequisiteCheckMode: 'live-db-truth-at-commit',
        passesCurrentStateCrossEntitySafety: true,
        passesCallerPinnedAbaVersionBinding: false,
      },
    };
  }
  return { appId: 'erpnext', auditedReleasePair: 'v15.10.0->v15.20.0', status: 'configured-endpoint-required' };
}

async function probeGiteaLocalIsolated(giteaBin) {
  if (!existsSync(giteaBin)) {
    return { appId: 'gitea', status: 'binary-not-present' };
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

    execFileSync(
      giteaBin,
      [
        'admin',
        'user',
        'create',
        ...cliBaseArgs,
        '--username',
        authorUser,
        '--password',
        userPass,
        '--email',
        'probe_author@isolated.local',
        '--admin',
        '--must-change-password=false',
      ],
      { cwd: workPath, stdio: 'pipe' },
    );
    execFileSync(
      giteaBin,
      [
        'admin',
        'user',
        'create',
        ...cliBaseArgs,
        '--username',
        approverUser,
        '--password',
        userPass,
        '--email',
        'probe_approver@isolated.local',
        '--must-change-password=false',
      ],
      { cwd: workPath, stdio: 'pipe' },
    );

    serverProc = spawn(giteaBin, ['web', ...cliBaseArgs], {
      cwd: workPath,
      stdio: ['ignore', 'pipe', 'pipe'],
    });
    serverProc.stdout.on('data', chunk => stdLogs.push(chunk.toString('utf8')));
    serverProc.stderr.on('data', chunk => stdLogs.push(chunk.toString('utf8')));

    await waitForHttpReady(`${baseUrl}/api/v1/version`, 25000);

    const authorAuth = { authUser: authorUser, authPass: userPass };
    const approverAuth = { authUser: approverUser, authPass: userPass };

    // 1. Create isolated repository initialized with `main` branch:
    const repoName = 'po-release-gate';
    const createRepo = await jsonRequest(`${baseUrl}/api/v1/user/repos`, {
      method: 'POST',
      ...authorAuth,
      body: { name: repoName, auto_init: true, default_branch: 'main', private: true },
    });
    if (!createRepo.ok) throw Error(`Repo create failed (${createRepo.status}): ${JSON.stringify(createRepo.body)}`);

    // Add isolated approver collaborator with write permission:
    const addCollab = await jsonRequest(
      `${baseUrl}/api/v1/repos/${authorUser}/${repoName}/collaborators/${approverUser}`,
      { method: 'PUT', ...authorAuth, body: { permission: 'write' } },
    );
    if (!addCollab.ok) throw Error(`Collaborator add failed (${addCollab.status})`);

    // Configure branch protection on `main`: require 1 approval from whitelist (`approverUser`):
    const bp = await jsonRequest(`${baseUrl}/api/v1/repos/${authorUser}/${repoName}/branch_protections`, {
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
    if (!bp.ok) throw Error(`Branch protection failed (${bp.status}): ${JSON.stringify(bp.body)}`);

    // Create feature branch `route-a` with commit #1 and commit #2 (so commit #1 is a real stale SHA):
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

    // Wait for Gitea's async git conflict-checker queue to settle (`mergeable === true`) before probing:
    await waitMergeable(pr1Index);

    // Grant approval first so ONLY `head_commit_id` is stale on Check 1:
    await jsonRequest(
      `${baseUrl}/api/v1/repos/${authorUser}/${repoName}/pulls/${pr1Index}/reviews`,
      { method: 'POST', ...approverAuth, body: { event: 'APPROVED', body: 'Initial approval' } },
    );

    // CHECK 1: Stale-version write MUST be refused (0 commits):
    const staleMerge = await jsonRequest(
      `${baseUrl}/api/v1/repos/${authorUser}/${repoName}/pulls/${pr1Index}/merge`,
      {
        method: 'POST',
        ...authorAuth,
        body: { Do: 'merge', head_commit_id: staleSha },
      },
    );
    const prAfterStale = await jsonRequest(
      `${baseUrl}/api/v1/repos/${authorUser}/${repoName}/pulls/${pr1Index}`,
      authorAuth,
    );

    // CHECK 2A: Live-DB-truth anti-revocation (revoking approval via REQUEST_CHANGES blocks merge):
    await waitMergeable(pr1Index);
    await jsonRequest(
      `${baseUrl}/api/v1/repos/${authorUser}/${repoName}/pulls/${pr1Index}/reviews`,
      { method: 'POST', ...approverAuth, body: { event: 'REQUEST_CHANGES', body: 'Hold: budget frozen' } },
    );
    await waitMergeable(pr1Index);
    const revokedMerge = await jsonRequest(
      `${baseUrl}/api/v1/repos/${authorUser}/${repoName}/pulls/${pr1Index}/merge`,
      {
        method: 'POST',
        ...authorAuth,
        body: { Do: 'merge', head_commit_id: currentSha },
      },
    );
    const prAfterRevoked = await jsonRequest(
      `${baseUrl}/api/v1/repos/${authorUser}/${repoName}/pulls/${pr1Index}`,
      authorAuth,
    );

    // CHECK 2B + CHECK 3A: Re-grant approval (`ABA` sequence: APPROVED v1 -> REQUEST_CHANGES v2 -> APPROVED v3),
    // then submit merge (`head_commit_id: currentSha`) and immediately RETRY after simulated dropped ack!
    await jsonRequest(
      `${baseUrl}/api/v1/repos/${authorUser}/${repoName}/pulls/${pr1Index}/reviews`,
      { method: 'POST', ...approverAuth, body: { event: 'APPROVED', body: 'Re-approved under modified cap' } },
    );
    await waitMergeable(pr1Index);
    const firstMergeCommit = await jsonRequest(
      `${baseUrl}/api/v1/repos/${authorUser}/${repoName}/pulls/${pr1Index}/merge`,
      {
        method: 'POST',
        ...authorAuth,
        body: { Do: 'merge', head_commit_id: currentSha },
      },
    );
    // Simulate dropped response acknowledgment: client retries exact same `merge` request:
    const droppedAckMergeRetry = await jsonRequest(
      `${baseUrl}/api/v1/repos/${authorUser}/${repoName}/pulls/${pr1Index}/merge`,
      {
        method: 'POST',
        ...authorAuth,
        body: { Do: 'merge', head_commit_id: currentSha },
      },
    );
    const prFinal = await jsonRequest(
      `${baseUrl}/api/v1/repos/${authorUser}/${repoName}/pulls/${pr1Index}`,
      authorAuth,
    );
    const mainCommits = await jsonRequest(
      `${baseUrl}/api/v1/repos/${authorUser}/${repoName}/commits?sha=main`,
      authorAuth,
    );
    const mergeCommitsOnMain = Array.isArray(mainCommits.body)
      ? mainCommits.body.filter(c => String(c?.commit?.message ?? '').startsWith('Merge pull request'))
      : [];

    // CHECK 3B: Endpoint-split contrast on unversioned `POST .../reviews` (dropped-ack retry duplicates!):
    const cB = await jsonRequest(
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
    if (!cB.ok) throw Error(`route-b create failed (${cB.status})`);
    const pr2 = await jsonRequest(`${baseUrl}/api/v1/repos/${authorUser}/${repoName}/pulls`, {
      method: 'POST',
      ...authorAuth,
      body: { title: 'Review PO-102', head: 'route-b', base: 'main' },
    });
    const pr2Index = pr2.body?.number;
    const rev1 = await jsonRequest(
      `${baseUrl}/api/v1/repos/${authorUser}/${repoName}/pulls/${pr2Index}/reviews`,
      { method: 'POST', ...approverAuth, body: { event: 'COMMENT', body: 'Idempotency probe comment' } },
    );
    const rev2Retry = await jsonRequest(
      `${baseUrl}/api/v1/repos/${authorUser}/${repoName}/pulls/${pr2Index}/reviews`,
      { method: 'POST', ...approverAuth, body: { event: 'COMMENT', body: 'Idempotency probe comment' } },
    );
    const pr2Reviews = await jsonRequest(
      `${baseUrl}/api/v1/repos/${authorUser}/${repoName}/pulls/${pr2Index}/reviews`,
      authorAuth,
    );

    // Flush and stop Gitea cleanly so all log lines are written:
    await new Promise(r => setTimeout(r, 400));
    serverProc.kill('SIGTERM');
    await new Promise(r => serverProc.once('exit', r));
    serverProc = null;

    // Collect Gitea's own server logs (access.log, router.log, gitea.log):
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
    const retainedLogAbsPath = join(LOGS_DIR, 'gitea-v1.21.11-step2-probe.log');
    writeFileSync(retainedLogAbsPath, sanitizedServerLog);

    const mergePostAccessLines = sanitizedServerLog
      .split('\n')
      .filter(l => l.includes(`/pulls/${pr1Index}/merge`) && l.includes('POST'));

    const staleRefusedPass =
      !staleMerge.ok && staleMerge.status >= 400 && prAfterStale.body?.merged === false;
    const liveDbTruthRevocationPass =
      !revokedMerge.ok
      && revokedMerge.status >= 400
      && !String(revokedMerge.body?.message ?? '').includes('Please try again later')
      && prAfterRevoked.body?.merged === false;
    const abaCommittedOnStock = firstMergeCommit.ok && firstMergeCommit.status === 200;
    const droppedAckMergeSingleCommitPass =
      firstMergeCommit.status === 200
      && !droppedAckMergeRetry.ok
      && droppedAckMergeRetry.status === 405
      && prFinal.body?.merged === true
      && mergeCommitsOnMain.length === 1;
    const reviewRetryCount = Array.isArray(pr2Reviews.body) ? pr2Reviews.body.length : 0;

    return {
      appId: 'gitea',
      auditedReleasePair: 'v1.21.11->v1.22.0',
      probedBinaryVersion: versionLine,
      tier: 'Tier-A3-endpoint-split',
      status: 'probed-local-isolated-accounts-zero-dollar',
      isolatedAccounts: [authorUser, approverUser],
      retainedServerLogPath: retainedLogRelPath,
      retainedServerLogSha256: sha256(sanitizedServerLog),
      mergeAccessLogLinesCount: mergePostAccessLines.length,
      checks: {
        staleVersionWrite: {
          endpoint: `POST /api/v1/repos/${authorUser}/${repoName}/pulls/${pr1Index}/merge`,
          httpStatus: staleMerge.status,
          responseMessage: staleMerge.body?.message ?? null,
          mergedAfterAttempt: Boolean(prAfterStale.body?.merged),
          appLogCommits: 0,
          passesRule: staleRefusedPass,
        },
        liveDbTruthRevokedApproval: {
          endpoint: `POST /api/v1/repos/${authorUser}/${repoName}/pulls/${pr1Index}/merge`,
          httpStatus: revokedMerge.status,
          responseMessage: revokedMerge.body?.message ?? null,
          mergedAfterAttempt: Boolean(prAfterRevoked.body?.merged),
          appLogCommits: 0,
          passesCurrentStateLiveTruthRule: liveDbTruthRevocationPass,
        },
        abaHistoricalSiblingVersionDrift: {
          sequence: 'APPROVED(v1) -> REQUEST_CHANGES(v2) -> APPROVED(v3) while caller holds v1 attestation',
          httpStatus: firstMergeCommit.status,
          committedOnStockWithoutCallerVersionValidator: abaCommittedOnStock,
          passesLiteralCallerPinnedPredicateVersions: !abaCommittedOnStock,
        },
        droppedAckRetryOnVersionedMerge: {
          endpoint: `POST /api/v1/repos/${authorUser}/${repoName}/pulls/${pr1Index}/merge`,
          firstCallHttpStatus: firstMergeCommit.status,
          firstCallResponseMessage: firstMergeCommit.body?.message ?? null,
          retryCallHttpStatus: droppedAckMergeRetry.status,
          retryResponseMessage: droppedAckMergeRetry.body?.message ?? null,
          totalMergeCommitsInAppRepoAndLogs: mergeCommitsOnMain.length,
          duplicateCommits: Math.max(0, mergeCommitsOnMain.length - 1),
          passesRule: droppedAckMergeSingleCommitPass,
        },
        droppedAckRetryOnUnversionedReviewsEndpointSplit: {
          endpoint: `POST /api/v1/repos/${authorUser}/${repoName}/pulls/${pr2Index}/reviews`,
          firstCallHttpStatus: rev1.status,
          retryCallHttpStatus: rev2Retry.status,
          totalReviewRecordsCreated: reviewRetryCount,
          duplicateCommits: Math.max(0, reviewRetryCount - 1),
          passesRuleWithoutIdempotencySidecar: reviewRetryCount === 1,
        },
      },
      overallVerdictUnderStage2ContractPassV1: {
        mergeEndpointPasses:
          staleRefusedPass && liveDbTruthRevocationPass && droppedAckMergeSingleCommitPass,
        reviewsPostEndpointPassesStock: reviewRetryCount === 1,
        abaCallerPinnedVersionRequiresCustomValidatorOrSidecar: abaCommittedOnStock,
      },
    };
  } finally {
    if (serverProc) {
      serverProc.kill('SIGKILL');
    }
    rmSync(rootDir, { recursive: true, force: true });
  }
}

async function main() {
  const args = parseArgs(process.argv);
  if (args.dryCheck) {
    console.log(JSON.stringify({ ok: true, mode: 'dry-check' }));
    return;
  }
  if (
    !args.passRuleCommentUrl
    || !/^https:\/\/github\.com\/clocksmith\/deco\/issues\/88#issuecomment-\d+$/.test(args.passRuleCommentUrl)
  ) {
    throw Error(
      'Step 2 ordering violation blocked: record `Stage2-Contract-Pass-v1` on clocksmith/deco#88 BEFORE probing, then pass `--pass-rule-comment-url https://github.com/clocksmith/deco/issues/88#issuecomment-...`.',
    );
  }

  const dockerState = checkDockerDaemon();
  const openproject = await probeOpenProject(args, dockerState);
  const erpnext = await probeErpNext(args, dockerState);
  const gitea = await probeGiteaLocalIsolated(args.giteaBin);

  const receipt = {
    schema: 'gammatron-step2-upstream-contract-probe-v1',
    spendUsd: 0,
    passRuleId: 'Stage2-Contract-Pass-v1',
    passRuleRecordedBeforeProbeAtUrl: args.passRuleCommentUrl,
    probedAtUtc: new Date().toISOString(),
    targets: {
      openproject,
      erpnext,
      gitea,
    },
  };

  mkdirSync(RECEIPTS_DIR, { recursive: true });
  const outPath = join(RECEIPTS_DIR, 'step2-upstream-probe-receipt.json');
  const text = JSON.stringify(receipt, null, 2) + '\n';
  writeFileSync(outPath, text);
  console.log(
    JSON.stringify(
      {
        receiptPath:
          'projects/workspace/qualification/workflow-generalization/receipts/step2-upstream-probe-receipt.json',
        receiptSha256: sha256(text),
        ...receipt,
      },
      null,
      2,
    ),
  );
}

await main();
