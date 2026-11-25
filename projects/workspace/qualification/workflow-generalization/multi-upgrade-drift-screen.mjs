#!/usr/bin/env node
// $0 Multi-Application Real-Upgrade Drift Candidate Screen (4 Upstream Upgrades + 3 Controls).
//
// Status: Documented $0 candidate qualification screen for a NEW, separately frozen workflow
// corpus — NOT a reason to reopen voided Stage A (`306e6171`), the old holdout, or paid runs.
//
// Screens four concrete, upstream-documented open-source REST API breaking upgrades across
// 3 disposable repeats per gate (`REQUIRED_REPEATS = 3`, 0 model calls, $0.00 spend):
//   1. OpenProject 17.8 (`PATCH /api/v3/work_packages/{id}`):
//      Single `_links.version` replaced by multi-value `_links.targetVersions[]`
//      (OpenProject 17.8 release notes: Administration -> Work packages -> Target versions).
//   2. NetBox v4.0 -> v4.1 (`PATCH /api/ipam/vlan-groups/{id}/`):
//      Scalar `min_vid` / `max_vid` removed and replaced by 2D inclusive interval array
//      `vid_ranges: [[start, end], ...]` (NetBox v4.1.0 breaking changes).
//   3. NetBox v4.1 -> v4.2 (`PATCH /api/ipam/prefixes/{id}/`):
//      Direct `site` foreign key removed and replaced by polymorphic generic foreign key
//      `scope_type` + `scope_id` (NetBox v4.2.0 breaking changes).
//   4. GitLab 15.11 -> 16.0 (`PUT /api/v4/projects/{id}` -> `PUT /api/v4/projects/{id}/approval_rules/{rule_id}`):
//      Project-level scalar `approvals_before_merge` removed in 16.0 in favor of Merge Request
//      Approval Rules (`approvals_required` + `user_ids[]`).
//
// Plus three negative/governance controls (`REQUIRED_REPEATS = 3`):
//   C1. Backwards-compatible server alias (`legacySiteAutoMapped`): ruled out by Gate 2
//       (`old-workflow-adapts-on-its-own`).
//   C2. Server-enforced policy (`serverRejectsOutOfWindowVlan`): ruled out by Gate 4
//       (`server-natively-rejects-wrong-write-no-guard-needed`).
//   C3. Permission 403 refusal (`permission403Block`): isolated as `not_testable` (never drift).
import assert from 'node:assert/strict';
import { createServer } from 'node:http';
import { resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

export const REQUIRED_REPEATS = 3;

const deepEqualJson = (a, b) => JSON.stringify(a) === JSON.stringify(b);

/**
 * Generic 4-gate x 3-repeat $0 upgrade-drift evaluator.
 * Every candidate supplies:
 *   - `provisionPreUpgrade(repeatIdx)` -> `{ request, runLegacyValid, dispose }`
 *   - `provisionPostUpgrade(tag)` -> `{ request, runLegacyOnPost, runReferenceValid, runReferenceWrongWrite, dispose }`
 */
export async function evaluateUpgradeCandidate({
  candidateId,
  application,
  upgradePair,
  upstreamCitation,
  provisionPreUpgrade,
  provisionPostUpgrade,
  repeats = REQUIRED_REPEATS,
}) {
  if (!Number.isInteger(repeats) || repeats < REQUIRED_REPEATS) {
    throw Error(`Upgrade screen requires >= ${REQUIRED_REPEATS} repeats (got ${repeats})`);
  }

  const controlRuns = [];
  const oldOnPostRuns = [];
  const refOnPostRuns = [];
  const wrongWriteRuns = [];
  const notTestableBlocks = [];

  for (let i = 0; i < repeats; i += 1) {
    const pre = await provisionPreUpgrade(i);
    try {
      const r = await pre.runLegacyValid();
      if (r.notTestable) notTestableBlocks.push({ gate: 'control-pre', repeat: i, refusal: r.refusal });
      controlRuns.push(r);
    } finally {
      await pre.dispose?.();
    }

    const postOld = await provisionPostUpgrade(`old-${i}`);
    try {
      const r = await postOld.runLegacyOnPost();
      if (r.notTestable) notTestableBlocks.push({ gate: 'old-on-post', repeat: i, refusal: r.refusal });
      oldOnPostRuns.push(r);
    } finally {
      await postOld.dispose?.();
    }

    const postRef = await provisionPostUpgrade(`ref-${i}`);
    try {
      const r = await postRef.runReferenceValid();
      if (r.notTestable) notTestableBlocks.push({ gate: 'ref-on-post', repeat: i, refusal: r.refusal });
      refOnPostRuns.push(r);
    } finally {
      await postRef.dispose?.();
    }

    const postHaz = await provisionPostUpgrade(`haz-${i}`);
    try {
      const r = await postHaz.runReferenceWrongWrite();
      if (r.notTestable) notTestableBlocks.push({ gate: 'wrong-write-hazard', repeat: i, refusal: r.refusal });
      wrongWriteRuns.push(r);
    } finally {
      await postHaz.dispose?.();
    }
  }

  if (notTestableBlocks.length > 0) {
    return {
      candidateId,
      application,
      upgradePair,
      upstreamCitation,
      modelCalls: 0,
      costUsd: 0,
      repeats,
      status: 'not_testable',
      qualifies: false,
      ruledOut: false,
      reason: 'setup-or-permission-403-block',
      notTestableBlocks,
    };
  }

  const controlPass = controlRuns.filter(r => r.persistedExpected).length;
  const oldAdapted = oldOnPostRuns.filter(r => r.persistedExpected).length;
  const oldFailed = oldOnPostRuns.filter(r => !r.persistedExpected).length;
  const refPass = refOnPostRuns.filter(r => r.persistedExpected).length;
  const wrongAccepted = wrongWriteRuns.filter(r => r.persistedWrongWrite).length;

  let qualifies = false;
  let ruledOut = false;
  let reason = '';

  if (controlPass < repeats) {
    ruledOut = true;
    reason = `control-pre-upgrade-failed (${controlPass}/${repeats})`;
  } else if (oldAdapted > 0) {
    ruledOut = true;
    reason = `old-workflow-adapts-on-its-own (${oldAdapted}/${repeats} adapted)`;
  } else if (refPass < repeats) {
    ruledOut = true;
    reason = `same-permission-reference-failed (${refPass}/${repeats})`;
  } else if (wrongAccepted < repeats) {
    ruledOut = true;
    reason = `server-natively-rejects-wrong-write-no-guard-needed (${wrongAccepted}/${repeats})`;
  } else {
    qualifies = true;
    reason = 'all-four-gates-passed-3-of-3';
  }

  return {
    candidateId,
    application,
    upgradePair,
    upstreamCitation,
    modelCalls: 0,
    costUsd: 0,
    repeats,
    status: qualifies ? 'qualifies_for_new_separately_frozen_corpus' : 'ruled_out',
    qualifies,
    ruledOut,
    reason,
    counts: {
      controlPrePass: `${controlPass}/${repeats}`,
      oldWorkflowFailedPostUpgrade: `${oldFailed}/${repeats}`,
      samePermissionReferencePass: `${refPass}/${repeats}`,
      plausibleWrongWriteAccepted: `${wrongAccepted}/${repeats}`,
    },
  };
}

async function listenJsonServer(handler) {
  const server = createServer(async (req, res) => {
    let raw = '';
    for await (const chunk of req) raw += chunk;
    const body = raw ? JSON.parse(raw) : {};
    const send = (status, payload) => {
      res.statusCode = status;
      res.setHeader('Content-Type', 'application/json');
      res.end(JSON.stringify(payload));
    };
    await handler(req, body, send);
  });
  await new Promise(done => server.listen(0, '127.0.0.1', done));
  const baseUrl = `http://127.0.0.1:${server.address().port}`;
  const request = async (method, path, body) => {
    const r = await fetch(baseUrl + path, {
      method,
      headers: { 'Content-Type': 'application/json' },
      body: body === undefined ? undefined : JSON.stringify(body),
    });
    return { status: r.status, body: await r.json() };
  };
  const dispose = () => new Promise(done => server.close(done));
  return { request, dispose };
}

function makeOpenProject178Spec() {
  const start = async ({ converted }) => {
    const state = { lockVersion: 0, version: null, targetVersions: [] };
    const { request, dispose } = await listenJsonServer((req, body, send) => {
      if (req.method === 'GET' && req.url === '/api/v3/work_packages/1') {
        return send(200, {
          id: 1,
          lockVersion: state.lockVersion,
          _links: converted
            ? { targetVersions: state.targetVersions.map(href => ({ href })) }
            : (state.version ? { version: { href: state.version } } : {}),
        });
      }
      if (req.method === 'PATCH' && req.url === '/api/v3/work_packages/1') {
        if (!converted && body._links?.version?.href) {
          state.version = body._links.version.href;
          state.lockVersion += 1;
          return send(200, { id: 1, lockVersion: state.lockVersion });
        }
        if (converted && Array.isArray(body._links?.targetVersions)) {
          state.targetVersions = body._links.targetVersions.map(x => x.href);
          state.lockVersion += 1;
          return send(200, { id: 1, lockVersion: state.lockVersion });
        }
        return send(422, { message: 'Schema mismatch for version/targetVersions' });
      }
      return send(404, { message: 'not found' });
    });

    const intendedMulti = ['/api/v3/versions/10', '/api/v3/versions/11'];
    const wrongMulti = ['/api/v3/versions/10', '/api/v3/versions/99'];
    return {
      request,
      dispose,
      runLegacyValid: async () => {
        await request('PATCH', '/api/v3/work_packages/1', {
          lockVersion: 0, _links: { version: { href: '/api/v3/versions/10' } },
        });
        const g = await request('GET', '/api/v3/work_packages/1');
        return { persistedExpected: g.body?._links?.version?.href === '/api/v3/versions/10' };
      },
      runLegacyOnPost: async () => {
        await request('PATCH', '/api/v3/work_packages/1', {
          lockVersion: 0, _links: { version: { href: intendedMulti[0] } },
        });
        const g = await request('GET', '/api/v3/work_packages/1');
        const stored = (g.body?._links?.targetVersions ?? []).map(x => x.href);
        return { persistedExpected: deepEqualJson(stored, intendedMulti) };
      },
      runReferenceValid: async () => {
        await request('PATCH', '/api/v3/work_packages/1', {
          lockVersion: 0, _links: { targetVersions: intendedMulti.map(href => ({ href })) },
        });
        const g = await request('GET', '/api/v3/work_packages/1');
        const stored = (g.body?._links?.targetVersions ?? []).map(x => x.href);
        return { persistedExpected: deepEqualJson(stored, intendedMulti) };
      },
      runReferenceWrongWrite: async () => {
        await request('PATCH', '/api/v3/work_packages/1', {
          lockVersion: 0, _links: { targetVersions: wrongMulti.map(href => ({ href })) },
        });
        const g = await request('GET', '/api/v3/work_packages/1');
        const stored = (g.body?._links?.targetVersions ?? []).map(x => x.href);
        return { persistedWrongWrite: deepEqualJson(stored, wrongMulti) };
      },
    };
  };
  return {
    candidateId: 'openproject-17.8-target-versions',
    application: 'openproject',
    upgradePair: '17.7 -> 17.8 (opt-in Target versions conversion)',
    upstreamCitation: 'OpenProject 17.8 release notes: single Version replaced by multi-value Target versions (/api/v3/work_packages)',
    provisionPreUpgrade: () => start({ converted: false }),
    provisionPostUpgrade: () => start({ converted: true }),
  };
}

function makeNetBox41VlanGroupSpec({ serverRejectsOutOfWindowVlan = false } = {}) {
  const start = async ({ v41 }) => {
    const state = v41 ? { id: 5, vid_ranges: [[1, 10]] } : { id: 5, min_vid: 1, max_vid: 10 };
    const { request, dispose } = await listenJsonServer((req, body, send) => {
      if (req.method === 'GET' && req.url === '/api/ipam/vlan-groups/5/') return send(200, state);
      if (req.method === 'PATCH' && req.url === '/api/ipam/vlan-groups/5/') {
        if (!v41) {
          if (Number.isInteger(body.min_vid) && Number.isInteger(body.max_vid)) {
            state.min_vid = body.min_vid;
            state.max_vid = body.max_vid;
            return send(200, state);
          }
          return send(400, { detail: 'Expected min_vid and max_vid' });
        }
        if ('min_vid' in body || 'max_vid' in body) {
          return send(400, { min_vid: ['Removed in NetBox v4.1; use vid_ranges.'] });
        }
        if (Array.isArray(body.vid_ranges)) {
          if (serverRejectsOutOfWindowVlan && body.vid_ranges.some(([a, b]) => b > 500)) {
            return send(400, { vid_ranges: ['Out-of-window VLAN rejected by custom validator'] });
          }
          state.vid_ranges = body.vid_ranges;
          return send(200, state);
        }
        return send(400, { detail: 'Invalid payload' });
      }
      return send(404, { detail: 'Not found' });
    });

    const intendedRanges = [[100, 199], [300, 349]];
    const wrongRanges = [[100, 199], [900, 999]];
    return {
      request,
      dispose,
      runLegacyValid: async () => {
        await request('PATCH', '/api/ipam/vlan-groups/5/', { min_vid: 100, max_vid: 199 });
        const g = await request('GET', '/api/ipam/vlan-groups/5/');
        return { persistedExpected: g.body.min_vid === 100 && g.body.max_vid === 199 };
      },
      runLegacyOnPost: async () => {
        await request('PATCH', '/api/ipam/vlan-groups/5/', { min_vid: 100, max_vid: 199 });
        const g = await request('GET', '/api/ipam/vlan-groups/5/');
        return { persistedExpected: deepEqualJson(g.body.vid_ranges, intendedRanges) };
      },
      runReferenceValid: async () => {
        await request('PATCH', '/api/ipam/vlan-groups/5/', { vid_ranges: intendedRanges });
        const g = await request('GET', '/api/ipam/vlan-groups/5/');
        return { persistedExpected: deepEqualJson(g.body.vid_ranges, intendedRanges) };
      },
      runReferenceWrongWrite: async () => {
        await request('PATCH', '/api/ipam/vlan-groups/5/', { vid_ranges: wrongRanges });
        const g = await request('GET', '/api/ipam/vlan-groups/5/');
        return { persistedWrongWrite: deepEqualJson(g.body.vid_ranges, wrongRanges) };
      },
    };
  };
  return {
    candidateId: serverRejectsOutOfWindowVlan
      ? 'control-netbox-server-enforced-vlan'
      : 'netbox-4.0-to-4.1-vlangroup-vid-ranges',
    application: 'netbox',
    upgradePair: 'v4.0 -> v4.1 (/api/ipam/vlan-groups/)',
    upstreamCitation: 'NetBox v4.1.0 release notes: ipam.VLANGroup min_vid/max_vid removed and replaced by vid_ranges',
    provisionPreUpgrade: () => start({ v41: false }),
    provisionPostUpgrade: () => start({ v41: true }),
  };
}

function makeNetBox42PrefixScopeSpec({ legacySiteAutoMapped = false, forbid403 = false } = {}) {
  const start = async ({ v42 }) => {
    const state = v42
      ? { id: 18, prefix: '192.0.2.0/24', status: 'container', scope_type: null, scope_id: null }
      : { id: 18, prefix: '192.0.2.0/24', status: 'container', site: null };
    const { request, dispose } = await listenJsonServer((req, body, send) => {
      if (forbid403) return send(403, { detail: 'You do not have permission to perform this action.' });
      if (req.method === 'GET' && req.url === '/api/ipam/prefixes/18/') return send(200, state);
      if (req.method === 'PATCH' && req.url === '/api/ipam/prefixes/18/') {
        if (!v42) {
          if (Number.isInteger(body.site) && body.status) {
            state.site = body.site;
            state.status = body.status;
            return send(200, state);
          }
          return send(400, { detail: 'Expected site' });
        }
        if ('site' in body) {
          if (legacySiteAutoMapped) {
            state.scope_type = 'dcim.site';
            state.scope_id = body.site;
            state.status = body.status ?? state.status;
            return send(200, state);
          }
          return send(400, { site: ['Field site was removed in NetBox v4.2; use scope_type and scope_id.'] });
        }
        if (typeof body.scope_type === 'string' && Number.isInteger(body.scope_id)) {
          state.scope_type = body.scope_type;
          state.scope_id = body.scope_id;
          state.status = body.status ?? state.status;
          return send(200, state);
        }
        return send(400, { detail: 'Expected scope_type and scope_id' });
      }
      return send(404, { detail: 'Not found' });
    });

    const wrap403 = async fn => {
      const r = await fn();
      if (r.httpStatus === 403) {
        return { notTestable: true, refusal: { status: 403, body: r.body } };
      }
      return r;
    };

    return {
      request,
      dispose,
      runLegacyValid: () => wrap403(async () => {
        const p = await request('PATCH', '/api/ipam/prefixes/18/', { site: 6, status: 'active' });
        if (p.status === 403) return { httpStatus: 403, body: p.body };
        const g = await request('GET', '/api/ipam/prefixes/18/');
        return { persistedExpected: g.body.site === 6 && g.body.status === 'active' };
      }),
      runLegacyOnPost: () => wrap403(async () => {
        const p = await request('PATCH', '/api/ipam/prefixes/18/', { site: 6, status: 'active' });
        if (p.status === 403) return { httpStatus: 403, body: p.body };
        const g = await request('GET', '/api/ipam/prefixes/18/');
        return { persistedExpected: g.body.scope_type === 'dcim.site' && g.body.scope_id === 6 && g.body.status === 'active' };
      }),
      runReferenceValid: () => wrap403(async () => {
        const p = await request('PATCH', '/api/ipam/prefixes/18/', { scope_type: 'dcim.site', scope_id: 6, status: 'active' });
        if (p.status === 403) return { httpStatus: 403, body: p.body };
        const g = await request('GET', '/api/ipam/prefixes/18/');
        return { persistedExpected: g.body.scope_type === 'dcim.site' && g.body.scope_id === 6 && g.body.status === 'active' };
      }),
      runReferenceWrongWrite: () => wrap403(async () => {
        // Plausible wrong write: scope_type spoofed to dcim.region #6 instead of dcim.site #6
        const p = await request('PATCH', '/api/ipam/prefixes/18/', { scope_type: 'dcim.region', scope_id: 6, status: 'active' });
        if (p.status === 403) return { httpStatus: 403, body: p.body };
        const g = await request('GET', '/api/ipam/prefixes/18/');
        return { persistedWrongWrite: g.body.scope_type === 'dcim.region' && g.body.scope_id === 6 && g.body.status === 'active' };
      }),
    };
  };
  return {
    candidateId: forbid403
      ? 'control-netbox-403-permission-block'
      : legacySiteAutoMapped
        ? 'control-netbox-auto-mapped-legacy-site'
        : 'netbox-4.1-to-4.2-prefix-generic-scope',
    application: 'netbox',
    upgradePair: 'v4.1 -> v4.2 (/api/ipam/prefixes/)',
    upstreamCitation: 'NetBox v4.2.0 release notes: ipam.Prefix site FK removed and replaced by generic scope_type + scope_id',
    provisionPreUpgrade: () => start({ v42: false }),
    provisionPostUpgrade: () => start({ v42: true }),
  };
}

function makeGitLab16ApprovalRulesSpec() {
  const start = async ({ v16 }) => {
    const project = v16 ? { id: 42, name: 'core-service' } : { id: 42, name: 'core-service', approvals_before_merge: 0 };
    const rule = { id: 7, name: 'Security Gate', approvals_required: 0, user_ids: [] };
    const { request, dispose } = await listenJsonServer((req, body, send) => {
      if (req.method === 'GET' && req.url === '/api/v4/projects/42') return send(200, project);
      if (req.method === 'PUT' && req.url === '/api/v4/projects/42') {
        if (!v16 && Number.isInteger(body.approvals_before_merge)) {
          project.approvals_before_merge = body.approvals_before_merge;
          return send(200, project);
        }
        return send(400, { error: 'approvals_before_merge was removed in GitLab 16.0; use approval_rules API' });
      }
      if (req.method === 'GET' && req.url === '/api/v4/projects/42/approval_rules/7') return send(200, rule);
      if (v16 && req.method === 'PUT' && req.url === '/api/v4/projects/42/approval_rules/7') {
        if (Number.isInteger(body.approvals_required) && Array.isArray(body.user_ids)) {
          rule.approvals_required = body.approvals_required;
          rule.user_ids = body.user_ids;
          return send(200, rule);
        }
        return send(400, { error: 'Expected approvals_required and user_ids' });
      }
      return send(404, { error: 'not found' });
    });

    const intendedUsers = [101, 102];
    const wrongUsers = [101, 999];
    return {
      request,
      dispose,
      runLegacyValid: async () => {
        await request('PUT', '/api/v4/projects/42', { approvals_before_merge: 2 });
        const g = await request('GET', '/api/v4/projects/42');
        return { persistedExpected: g.body.approvals_before_merge === 2 };
      },
      runLegacyOnPost: async () => {
        await request('PUT', '/api/v4/projects/42', { approvals_before_merge: 2 });
        const g = await request('GET', '/api/v4/projects/42/approval_rules/7');
        return { persistedExpected: g.body.approvals_required === 2 && deepEqualJson(g.body.user_ids, intendedUsers) };
      },
      runReferenceValid: async () => {
        await request('PUT', '/api/v4/projects/42/approval_rules/7', { approvals_required: 2, user_ids: intendedUsers });
        const g = await request('GET', '/api/v4/projects/42/approval_rules/7');
        return { persistedExpected: g.body.approvals_required === 2 && deepEqualJson(g.body.user_ids, intendedUsers) };
      },
      runReferenceWrongWrite: async () => {
        await request('PUT', '/api/v4/projects/42/approval_rules/7', { approvals_required: 2, user_ids: wrongUsers });
        const g = await request('GET', '/api/v4/projects/42/approval_rules/7');
        return { persistedWrongWrite: g.body.approvals_required === 2 && deepEqualJson(g.body.user_ids, wrongUsers) };
      },
    };
  };
  return {
    candidateId: 'gitlab-15.11-to-16.0-approval-rules',
    application: 'gitlab',
    upgradePair: '15.11 -> 16.0 (/api/v4/projects/:id/approval_rules)',
    upstreamCitation: 'GitLab 16.0 REST API v4 breaking removals: approvals_before_merge removed in favor of approval_rules (approvals_required + user_ids[])',
    provisionPreUpgrade: () => start({ v16: false }),
    provisionPostUpgrade: () => start({ v16: true }),
  };
}

export async function runMultiUpgradeDriftScreen() {
  const specs = [
    makeOpenProject178Spec(),
    makeNetBox41VlanGroupSpec(),
    makeNetBox42PrefixScopeSpec(),
    makeGitLab16ApprovalRulesSpec(),
    makeNetBox42PrefixScopeSpec({ legacySiteAutoMapped: true }),
    makeNetBox41VlanGroupSpec({ serverRejectsOutOfWindowVlan: true }),
    makeNetBox42PrefixScopeSpec({ forbid403: true }),
  ];

  const results = [];
  for (const spec of specs) {
    results.push(await evaluateUpgradeCandidate(spec));
  }

  const qualifying = results.filter(r => r.qualifies).map(r => r.candidateId);
  const ruledOut = results.filter(r => r.ruledOut).map(r => ({ id: r.candidateId, reason: r.reason }));
  const notTestable = results.filter(r => r.status === 'not_testable').map(r => r.candidateId);

  return {
    schema: 'gammatron-multi-upgrade-drift-screen/v1',
    modelCalls: 0,
    costUsd: 0,
    repeatsPerGate: REQUIRED_REPEATS,
    qualifyingCandidateIds: qualifying,
    ruledOutControls: ruledOut,
    notTestableControls: notTestable,
    results,
    governanceNote: (
      'Documented $0 protocol screen grounded in upstream release notes for a NEW, separately frozen corpus; '
      + 'live Docker verification requires explicit owner authorization, and Stage A (306e6171) remains voided/parked.'
    ),
  };
}

export async function selftest() {
  const report = await runMultiUpgradeDriftScreen();
  assert.equal(report.modelCalls, 0);
  assert.equal(report.costUsd, 0);
  assert.deepEqual(report.qualifyingCandidateIds, [
    'openproject-17.8-target-versions',
    'netbox-4.0-to-4.1-vlangroup-vid-ranges',
    'netbox-4.1-to-4.2-prefix-generic-scope',
    'gitlab-15.11-to-16.0-approval-rules',
  ]);
  assert.equal(report.ruledOutControls.length, 2);
  assert.match(report.ruledOutControls[0].reason, /old-workflow-adapts-on-its-own/);
  assert.match(report.ruledOutControls[1].reason, /server-natively-rejects-wrong-write/);
  assert.deepEqual(report.notTestableControls, ['control-netbox-403-permission-block']);
  return { ok: true, report };
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const { report } = await selftest();
  console.log(JSON.stringify(report, null, 2));
}
