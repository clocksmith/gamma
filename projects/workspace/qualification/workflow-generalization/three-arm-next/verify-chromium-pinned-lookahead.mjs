#!/usr/bin/env node
// Real Headless Chromium (`playwright-core`) Adversarial Verification for Digest-Pinned Relational Lookahead.
//
// Exercises real Chromium (`branchExpression` from `src/client/branch-verifier.js` inside network-blocked
// zero-egress contexts emitting Fawn's exact `Page.fawnBranchStatus` wire format) against a live local
// `node:http` server across all 4 upstream-documented API breaking upgrades (`OpenProject 17.8`,
// `NetBox v4.1`, `NetBox v4.2`, `GitLab 16.0`):
//   1. Valid Upgrade Repair + Closure Preservation (`4/4` certified, `0` escaped server preview mutations).
//   2. Server-Only Upgrade Policy Trap (`4/4` blocked pre-branch in `0` Chromium branches vs `4/4` wrong
//      certifications for `fawn-branch-only`).
//   3. In-Memory JS Closure Value-Spoofing Trap (`bodyFields` field names match while JS closure mutates
//      values in `fetch()`!): proves `unpinned-bodyFields-lookahead` certifies `4/4` spoofed writes,
//      whereas `pinned-relational-lookahead` blocks `4/4` (`branch-body-digest-mismatch`) while keeping
//      branch exports digest-only!
//   4. Concurrent Pre-to-Post-Preview Server `ABA` / `TOCTOU` Race (`lockVersion` bumped during preview):
//      proves `pinned-relational-lookahead` blocks `4/4` (`concurrent-version-drift` / `post-branch-guard-mismatch`).
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { existsSync, mkdirSync, writeFileSync } from 'node:fs';
import { createServer } from 'node:http';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { chromium } from 'playwright-core';
import { verifyBranches } from '../../../src/client/branch-verifier.js';
import { createAdaptiveRelationalSession } from './adaptive-relational-guard.mjs';
import { evaluatePinnedRelationalLookahead } from './pinned-relational-lookahead.mjs';
import { extractTypedTraceFacts } from './relational-trace-guard.mjs';

const HERE = dirname(fileURLToPath(import.meta.url));
const sha256 = s => createHash('sha256').update(s, 'utf8').digest('hex');
const getRow = (role, json) => ({ sameOrigin: true, method: 'GET', transport: 'fetch', status: 200, sourceRole: role, json });

function findBrowserExecutable() {
  if (process.env.BRANCH_VERIFIER_BROWSER && existsSync(process.env.BRANCH_VERIFIER_BROWSER)) {
    return process.env.BRANCH_VERIFIER_BROWSER;
  }
  const candidates = [
    `${process.env.HOME}/Library/Caches/ms-playwright/chromium_headless_shell-1208/chrome-headless-shell-mac-arm64/chrome-headless-shell`,
    '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
    '/Applications/Chromium.app/Contents/MacOS/Chromium',
  ];
  return candidates.find(p => existsSync(p)) ?? null;
}

function buildFourUpgradeScenarios(origin) {
  const mkSession = (id, posList, negList) => createAdaptiveRelationalSession({
    intendedEffect: `opbind-v1:${sha256(id)}`,
    positiveObservations: posList.map(ex => extractTypedTraceFacts(Object.entries(ex.roles).map(([r, j]) => getRow(r, j)), ex.intent)),
    negativeObservations: negList.map(ex => extractTypedTraceFacts(Object.entries(ex.roles).map(([r, j]) => getRow(r, j)), ex.intent)),
  });

  return [
    {
      id: 'op178-target-versions',
      endpoint: '/api/v3/work_packages/1',
      method: 'PATCH',
      session: mkSession('op178', [
        { intent: { _links: { targetVersions: [{ href: '/api/v3/versions/10' }, { href: '/api/v3/versions/11' }] } }, roles: { approval: { lockVersion: 1, _links: { status: { href: '/api/v3/statuses/16' }, targetVersions: [{ href: '/api/v3/versions/10' }, { href: '/api/v3/versions/11' }, { href: '/api/v3/versions/12' }] } } } },
        { intent: { _links: { targetVersions: [{ href: '/api/v3/versions/11' }, { href: '/api/v3/versions/12' }] } }, roles: { approval: { lockVersion: 1, _links: { status: { href: '/api/v3/statuses/16' }, targetVersions: [{ href: '/api/v3/versions/10' }, { href: '/api/v3/versions/11' }, { href: '/api/v3/versions/12' }] } } } },
      ], [
        { intent: { _links: { targetVersions: [{ href: '/api/v3/versions/10' }, { href: '/api/v3/versions/99' }] } }, roles: { approval: { lockVersion: 1, _links: { status: { href: '/api/v3/statuses/16' }, targetVersions: [{ href: '/api/v3/versions/10' }, { href: '/api/v3/versions/11' }] } } } },
        { intent: { _links: { targetVersions: [{ href: '/api/v3/versions/10' }] } }, roles: { approval: { lockVersion: 1, _links: { status: { href: '/api/v3/statuses/17' }, targetVersions: [{ href: '/api/v3/versions/10' }, { href: '/api/v3/versions/11' }] } } } },
      ]),
      validIntent: { _links: { targetVersions: [{ href: '/api/v3/versions/10' }, { href: '/api/v3/versions/12' }] } },
      spoofedJsBody: { _links: { targetVersions: [{ href: '/api/v3/versions/10' }, { href: '/api/v3/versions/99' }] } },
      validRoles: { approval: { lockVersion: 1, _links: { status: { href: '/api/v3/statuses/16' }, targetVersions: [{ href: '/api/v3/versions/10' }, { href: '/api/v3/versions/12' }, { href: '/api/v3/versions/15' }] } } },
      serverInvalidRoles: { approval: { lockVersion: 1, _links: { status: { href: '/api/v3/statuses/16' }, targetVersions: [{ href: '/api/v3/versions/10' }] } } },
      abaPostRoles: { approval: { lockVersion: 2, _links: { status: { href: '/api/v3/statuses/16' }, targetVersions: [{ href: '/api/v3/versions/10' }, { href: '/api/v3/versions/12' }, { href: '/api/v3/versions/15' }] } } },
      legacyBrokenJs: `fetch('${origin}/api/v3/work_packages/1', { method: 'PATCH', body: JSON.stringify({ _links: { version: { href: '/api/v3/versions/10' } } }) })`,
    },
    {
      id: 'netbox41-vid-ranges',
      endpoint: '/api/ipam/vlan-groups/5/',
      method: 'PATCH',
      session: mkSession('nb41', [
        { intent: { vid_ranges: [[100, 199], [300, 349]] }, roles: { approval: { lockVersion: 1, status: 'approved', authorized_vid_ranges: [[100, 299], [300, 399]] } } },
        { intent: { vid_ranges: [[150, 250]] }, roles: { approval: { lockVersion: 1, status: 'approved', authorized_vid_ranges: [[100, 299], [400, 499]] } } },
      ], [
        { intent: { vid_ranges: [[100, 199], [900, 999]] }, roles: { approval: { lockVersion: 1, status: 'approved', authorized_vid_ranges: [[100, 299], [300, 399]] } } },
        { intent: { vid_ranges: [[100, 199]] }, roles: { approval: { lockVersion: 1, status: 'staged', authorized_vid_ranges: [[100, 299]] } } },
      ]),
      validIntent: { vid_ranges: [[120, 180], [310, 330]] },
      spoofedJsBody: { vid_ranges: [[120, 180], [900, 999]] },
      validRoles: { approval: { lockVersion: 1, status: 'approved', authorized_vid_ranges: [[100, 200], [300, 350]] } },
      serverInvalidRoles: { approval: { lockVersion: 1, status: 'approved', authorized_vid_ranges: [[100, 150]] } },
      abaPostRoles: { approval: { lockVersion: 2, status: 'approved', authorized_vid_ranges: [[100, 200], [300, 350]] } },
      legacyBrokenJs: `fetch('${origin}/api/ipam/vlan-groups/5/', { method: 'PATCH', body: JSON.stringify({ min_vid: 120, max_vid: 180 }) })`,
    },
    {
      id: 'netbox42-generic-scope',
      endpoint: '/api/ipam/prefixes/18/',
      method: 'PATCH',
      session: mkSession('nb42', [
        { intent: { scope_type: 'dcim.site', scope_id: 6 }, roles: { approval: { lockVersion: 1, status: 'approved', scope_type: 'dcim.site', scope_id: 6 } } },
        { intent: { scope_type: 'dcim.location', scope_id: 12 }, roles: { approval: { lockVersion: 1, status: 'approved', scope_type: 'dcim.location', scope_id: 12 } } },
      ], [
        { intent: { scope_type: 'dcim.site', scope_id: 6 }, roles: { approval: { lockVersion: 1, status: 'pending', scope_type: 'dcim.site', scope_id: 6 } } },
        { intent: { scope_type: 'dcim.site', scope_id: 99 }, roles: { approval: { lockVersion: 1, status: 'approved', scope_type: 'dcim.site', scope_id: 6 } } },
      ]),
      validIntent: { scope_type: 'dcim.site', scope_id: 21 },
      spoofedJsBody: { scope_type: 'dcim.region', scope_id: 21 },
      validRoles: { approval: { lockVersion: 1, status: 'approved', scope_type: 'dcim.site', scope_id: 21 } },
      serverInvalidRoles: { approval: { lockVersion: 1, status: 'approved', scope_type: 'dcim.location', scope_id: 21 } },
      abaPostRoles: { approval: { lockVersion: 2, status: 'approved', scope_type: 'dcim.site', scope_id: 21 } },
      legacyBrokenJs: `fetch('${origin}/api/ipam/prefixes/18/', { method: 'PATCH', body: JSON.stringify({ site: 21 }) })`,
    },
    {
      id: 'gitlab16-approval-rules',
      endpoint: '/api/v4/projects/42/approval_rules/7',
      method: 'PUT',
      session: mkSession('gl16', [
        { intent: { approvals_required: 2, user_ids: [101, 102] }, roles: { approval: { lockVersion: 1, status: 'active', min_approvals: 2, eligible_approver_ids: [101, 102, 103] } } },
        { intent: { approvals_required: 3, user_ids: [102, 103] }, roles: { approval: { lockVersion: 1, status: 'active', min_approvals: 3, eligible_approver_ids: [101, 102, 103, 104] } } },
      ], [
        { intent: { approvals_required: 2, user_ids: [101, 999] }, roles: { approval: { lockVersion: 1, status: 'active', min_approvals: 2, eligible_approver_ids: [101, 102, 103] } } },
        { intent: { approvals_required: 2, user_ids: [101, 102] }, roles: { approval: { lockVersion: 1, status: 'draft', min_approvals: 2, eligible_approver_ids: [101, 102, 103] } } },
      ]),
      validIntent: { approvals_required: 2, user_ids: [201, 202] },
      spoofedJsBody: { approvals_required: 1, user_ids: [201, 999] },
      validRoles: { approval: { lockVersion: 1, status: 'active', min_approvals: 2, eligible_approver_ids: [201, 202, 203] } },
      serverInvalidRoles: { approval: { lockVersion: 1, status: 'active', min_approvals: 3, eligible_approver_ids: [201, 202, 203] } },
      abaPostRoles: { approval: { lockVersion: 2, status: 'active', min_approvals: 2, eligible_approver_ids: [201, 202, 203] } },
      legacyBrokenJs: `fetch('${origin}/api/v4/projects/42', { method: 'PUT', body: JSON.stringify({ approvals_before_merge: 2 }) })`,
    },
  ];
}

export async function runChromiumPinnedLookaheadSuite() {
  const executablePath = findBrowserExecutable();
  assert.ok(executablePath, 'Headless Chromium binary required for $0 Fawn branch verification');

  let serverPreviewMutationsObserved = 0;
  const server = createServer((req, res) => {
    if (req.method !== 'GET') {
      serverPreviewMutationsObserved += 1;
      res.statusCode = 500;
      res.end('MUTATION_ESCAPED_BRANCH');
      return;
    }
    res.setHeader('Content-Type', 'text/html; charset=utf-8');
    res.end(`<!doctype html><html><body>
      <div role="status">Ready</div>
      <script>window.__SESSION_CLOSURE_NONCE = 'closure-intact-v2';</script>
    </body></html>`);
  });

  await new Promise(done => server.listen(0, '127.0.0.1', done));
  const origin = `http://127.0.0.1:${server.address().port}`;
  const browser = await chromium.launch({ executablePath, args: ['--headless=new'] });

  try {
    const context = await browser.newContext();
    const page = await context.newPage();

    // Executes sealed zero-egress branch previews inside real Chromium, rejecting egress with
    // `DOMException('Blocked in branch', 'NotAllowedError')` matching Fawn's `Page.fawnBranchStatus` contract!
    const runZeroEgressBranches = async ({ controlExpression, candidates, pagePayloadOverride = null }) => {
      const evalOne = async expr => {
        await page.goto(`${origin}/app`);
        if (pagePayloadOverride !== null) {
          await page.evaluate(payload => { window.__LIVE_PAYLOAD = payload; }, pagePayloadOverride);
        }
        return page.evaluate(async wrappedExpr => {
          const attempts = [];
          const origFetch = window.fetch;
          window.fetch = function (input) {
            const rawTarget = typeof input === 'string' ? input : input.url;
            const resolved = new URL(rawTarget, document.baseURI).href;
            attempts.push({ attempt: 'fetch', target: resolved });
            return Promise.reject(new DOMException('Blocked in branch', 'NotAllowedError'));
          };
          try {
            const val = await (0, eval)(wrappedExpr);
            return ['finished', ...attempts.map(a => JSON.stringify(a)), JSON.stringify({ ok: true, value: val })].join('\n');
          } catch (err) {
            return ['finished', ...attempts.map(a => JSON.stringify(a)), JSON.stringify({ ok: false, value: String(err) })].join('\n');
          } finally {
            window.fetch = origFetch;
          }
        }, expr);
      };

      const control = await evalOne(controlExpression);
      const outCands = [];
      for (const c of candidates) {
        outCands.push({ id: c.id, text: await evalOne(c.expression) });
      }
      return { control, candidates: outCands };
    };

    const scenarios = buildFourUpgradeScenarios(origin);
    const summary = {
      validUpgradeRepairCertified: 0,
      fawnOnlyWrongOnServerTrap: 0,
      pinnedBlockedPreBranchOnServerTrap: 0,
      pinnedBranchesOnServerTrap: 0,
      unpinnedBodyFieldsWrongOnJsSpoof: 0,
      pinnedBlockedOnJsSpoof: 0,
      pinnedBlockedOnAbaRace: 0,
    };
    const perUpgrade = [];

    for (const sc of scenarios) {
      const targetUrl = `${origin}${sc.endpoint}`;
      const candidates = [
        {
          id: 'legacy-v1-action',
          action: sc.legacyBrokenJs,
          expect: { attempt: 'fetch', target: targetUrl, method: sc.method },
        },
        {
          id: 'repaired-v2-action',
          action: `(() => { if (window.__SESSION_CLOSURE_NONCE !== 'closure-intact-v2') throw new Error('LostClosure'); return fetch('${targetUrl}', { method: '${sc.method}', body: JSON.stringify(window.__LIVE_PAYLOAD) }); })()`,
          expect: { attempt: 'fetch', target: targetUrl, method: sc.method },
        },
      ];

      // 1. Valid upgrade repair (preserves closure nonce, rejects legacy v1, certifies v2!)
      const validCert = await evaluatePinnedRelationalLookahead({
        adaptiveSession: sc.session,
        intentPayload: sc.validIntent,
        candidates,
        fetchRole: async role => getRow(role, sc.validRoles[role]),
        runBranches: args => runZeroEgressBranches({ ...args, pagePayloadOverride: sc.validIntent }),
      });
      if (validCert.decision === 'certified' && validCert.winnerId === 'repaired-v2-action') {
        summary.validUpgradeRepairCertified += 1;
      }

      // 2. Server-only upgrade policy trap (`fawn-branch-only` vs `pinned-relational-lookahead`)
      const rawBranches = await runZeroEgressBranches({
        controlExpression: '(async () => 0)()', // unused for verifyBranches; use evaluatePinned's control via helper
        candidates: [],
      });
      void rawBranches;
      const pinnedServerTrap = await evaluatePinnedRelationalLookahead({
        adaptiveSession: sc.session,
        intentPayload: sc.validIntent,
        candidates,
        fetchRole: async role => getRow(role, sc.serverInvalidRoles[role]),
        runBranches: args => runZeroEgressBranches({ ...args, pagePayloadOverride: sc.validIntent }),
      });
      if (pinnedServerTrap.decision === 'abstain' && pinnedServerTrap.branchesRun === 0) {
        summary.pinnedBlockedPreBranchOnServerTrap += 1;
      }
      summary.pinnedBranchesOnServerTrap += pinnedServerTrap.branchesRun;

      // Also check `fawn-branch-only` (with declared `bodyFields` schema) on the exact same Chromium branches:
      const { branchExpression } = await import('../../../src/client/branch-verifier.js');
      const { computeExpectedBranchBodyPairs } = await import('./pinned-relational-lookahead.mjs');
      const expFieldNames = [...new Set(computeExpectedBranchBodyPairs(sc.validIntent).fields.map(f => f[0]))].sort();
      const fawnOuts = await runZeroEgressBranches({
        controlExpression: branchExpression('0'),
        candidates: candidates.map(c => ({ id: c.id, expression: branchExpression(c.action) })),
        pagePayloadOverride: sc.validIntent,
      });
      const fawnOnlyVerdict = verifyBranches({
        control: fawnOuts.control,
        candidates: candidates.map(c => ({
          id: c.id,
          text: fawnOuts.candidates.find(x => x.id === c.id).text,
          expect: { ...c.expect, bodyFields: expFieldNames },
        })),
      });
      if (fawnOnlyVerdict.decision === 'eligible') {
        summary.fawnOnlyWrongOnServerTrap += 1;
      }

      // 3. In-Memory JS Closure Value-Spoofing Trap (`window.__LIVE_PAYLOAD = sc.spoofedJsBody` — identical field names!)
      const unpinnedSpoof = await evaluatePinnedRelationalLookahead({
        adaptiveSession: sc.session,
        intentPayload: sc.validIntent,
        candidates,
        fetchRole: async role => getRow(role, sc.validRoles[role]),
        runBranches: args => runZeroEgressBranches({ ...args, pagePayloadOverride: sc.spoofedJsBody }),
        enforceBodyDigestPin: false, // Ablation: `bodyFields` field-name check ONLY (current `live-lookahead.js` behavior!)
      });
      if (unpinnedSpoof.decision === 'certified') {
        summary.unpinnedBodyFieldsWrongOnJsSpoof += 1;
      }

      const pinnedSpoof = await evaluatePinnedRelationalLookahead({
        adaptiveSession: sc.session,
        intentPayload: sc.validIntent,
        candidates,
        fetchRole: async role => getRow(role, sc.validRoles[role]),
        runBranches: args => runZeroEgressBranches({ ...args, pagePayloadOverride: sc.spoofedJsBody }),
        enforceBodyDigestPin: true,
      });
      if (pinnedSpoof.decision === 'abstain' && pinnedSpoof.reason === 'branch-body-digest-mismatch') {
        summary.pinnedBlockedOnJsSpoof += 1;
      }

      // 4. Concurrent Pre-to-Post-Preview Server `ABA` / `TOCTOU` Version Drift (`lockVersion: 1 -> 2`)
      const pinnedAba = await evaluatePinnedRelationalLookahead({
        adaptiveSession: sc.session,
        intentPayload: sc.validIntent,
        candidates,
        fetchRole: async (role, phase) => getRow(role, phase === 'pre' ? sc.validRoles[role] : sc.abaPostRoles[role]),
        runBranches: args => runZeroEgressBranches({ ...args, pagePayloadOverride: sc.validIntent }),
      });
      if (pinnedAba.decision === 'abstain' && String(pinnedAba.reason).startsWith('concurrent-version-drift:')) {
        summary.pinnedBlockedOnAbaRace += 1;
      }

      perUpgrade.push({
        upgradeId: sc.id,
        validRepairWinner: validCert.winnerId,
        serverTrapPreBranchReason: pinnedServerTrap.reason,
        unpinnedJsSpoofDecision: unpinnedSpoof.decision,
        pinnedJsSpoofReason: pinnedSpoof.reason,
        pinnedAbaReason: pinnedAba.reason,
      });
    }

    return {
      schema: 'gammatron-chromium-pinned-lookahead-verification/v1',
      modelCalls: 0,
      costUsd: 0,
      browserEngine: 'headless-chromium-playwright-core',
      serverPreviewMutationsObserved,
      upgradeScenariosTested: scenarios.length,
      summary,
      perUpgrade,
    };
  } finally {
    await browser.close();
    server.close();
  }
}

export async function selftest() {
  const report = await runChromiumPinnedLookaheadSuite();
  assert.equal(report.modelCalls, 0);
  assert.equal(report.costUsd, 0);
  assert.equal(report.serverPreviewMutationsObserved, 0);
  assert.equal(report.summary.validUpgradeRepairCertified, 4);
  assert.equal(report.summary.fawnOnlyWrongOnServerTrap, 4);
  assert.equal(report.summary.pinnedBlockedPreBranchOnServerTrap, 4);
  assert.equal(report.summary.pinnedBranchesOnServerTrap, 0);
  assert.equal(report.summary.unpinnedBodyFieldsWrongOnJsSpoof, 4);
  assert.equal(report.summary.pinnedBlockedOnJsSpoof, 4);
  assert.equal(report.summary.pinnedBlockedOnAbaRace, 4);
  return { ok: true, report };
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const { report } = await selftest();
  const outDir = join(HERE, 'receipts');
  mkdirSync(outDir, { recursive: true });
  const outPath = join(outDir, 'chromium_pinned_lookahead_v1.json');
  writeFileSync(outPath, `${JSON.stringify(report, null, 2)}\n`);
  console.log(`Wrote verified $0 Chromium pinned-lookahead receipt to ${outPath}`);
}
