import assert from 'node:assert/strict';
import { mkdtempSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import {
  AttestedSkillBook,
  createAttestedSkillPlanner,
  recordAttestedSkillTeaching,
} from '../../src/client/attested-skill.js';
import { InvestigationStore } from '../../src/client/investigation.js';
import { SuffixIndex, normalizeAttestationAnswers } from '../../src/client/suffix-eligibility.js';
import { TraceDag } from '../../src/client/trace-dag.js';
import { runWorkflow } from '../../src/client/workflow-agent.js';
import { loadServiceConfig } from '../../src/config.js';
import { WorkspaceService } from '../../src/service.js';
import { findElement } from '../../src/workflows/owner-session.js';
import { FakeAdapter, ORIGIN } from '../support/fake-adapter.js';
import { FORM_INTENT, WORKSPACE_ID, createClock } from '../support/harness.js';

const LIMITS = Object.freeze({ maxNodes: 96, maxEdges: 96, maxSteps: 32 });
const CONFIG = Object.freeze({ maxTurns: 20, maxInputBytes: 60000 });
const FORM_URL = `${ORIGIN}/form`;
const DONE = { completedWhen: [{ kind: 'element-present', selector: '#receipt' }] };

// ---------------------------------------------------------------------------
// 1. Versioned `(account, record, predicate, version)` attestation parsing
// ---------------------------------------------------------------------------
{
  const ok = normalizeAttestationAnswers([
    { holds: true, account: 'acct-a', record: 'ORD-1', predicate: 'order-loaded', version: 3 },
    { holds: false, account: 'acct-a', record: 'ORD-1', predicate: 'id-approved', version: 'v2' },
    { status: 'unavailable', predicate: 'external-registry', reason: 'no-api' },
  ], { expectedCount: 3, accountScope: 'acct-a', recordId: 'ORD-1' });
  assert.equal(ok.valid, true);
  assert.deepEqual(ok.holdsByIndex, [true, false, false]);
  assert.deepEqual(ok.refutableByIndex, [true, true, false]);
  assert.equal(ok.predicateVersions.length, 1);
  assert.deepEqual(ok.predicateVersions[0], {
    account: 'acct-a',
    record: 'ORD-1',
    predicate: 'order-loaded',
    version: 3,
  });
  assert.equal(ok.unavailable.length, 1);

  // Wrong account or wrong record is refutable and fails closed.
  const wrongAcct = normalizeAttestationAnswers([
    { holds: true, account: 'acct-b', record: 'ORD-1', predicate: 'order-loaded', version: 1 },
  ], { expectedCount: 1, accountScope: 'acct-a', recordId: 'ORD-1' });
  assert.equal(wrongAcct.valid, true);
  assert.deepEqual(wrongAcct.holdsByIndex, [false]);
  assert.deepEqual(wrongAcct.refutableByIndex, [true]);
  assert.equal(wrongAcct.predicateVersions.length, 0);

  const wrongRec = normalizeAttestationAnswers([
    { holds: true, account: 'acct-a', record: 'ORD-999', predicate: 'order-loaded', version: 1 },
  ], { expectedCount: 1, accountScope: 'acct-a', recordId: 'ORD-1' });
  assert.deepEqual(wrongRec.holdsByIndex, [false]);
  assert.deepEqual(wrongRec.refutableByIndex, [true]);

  // Missing version fails closed as invalid.
  const missingVer = normalizeAttestationAnswers([
    { holds: true, account: 'acct-a', record: 'ORD-1', predicate: 'order-loaded' },
  ], { expectedCount: 1, accountScope: 'acct-a', recordId: 'ORD-1' });
  assert.equal(missingVer.valid, false);
}

// ---------------------------------------------------------------------------
// 2. Single-record ETag insufficiency vs. atomic multi-predicate writes & server-journal dedup
// ---------------------------------------------------------------------------
{
  const config = loadServiceConfig();
  const root = mkdtempSync(join(tmpdir(), 'multi-pred-svc-'));
  const serverDb = {
    recordEtag: 'rec-v1',
    approvalStatus: 'approved',
    approvalVersion: 'app-v1',
    singleEtagCommits: 0,
    multiPredicateCommits: 0,
    journal: new Map(),
  };
  let dropResponseAfterCommit = false;
  let revokeApprovalAfterCheck = false;

  const baseAdapter = new FakeAdapter({ receiptsPath: join(root, 'receipts.jsonl') });
  baseAdapter.supportsConditionalWrites = true;
  baseAdapter.supportsMultiPredicateWrites = true;
  baseAdapter.close = async () => { baseAdapter.pages.clear(); return []; };
  const origExecute = baseAdapter.execute.bind(baseAdapter);
  baseAdapter.execute = async (workspaceId, request, uploadFiles) => {
    if (request.kind === 'submit') {
      const idemKey = request.effect?.externalIdempotencyKey ?? null;
      if (idemKey && serverDb.journal.has(idemKey)) {
        return origExecute(workspaceId, request, uploadFiles);
      }
      if (Array.isArray(request.predicateVersions) && request.predicateVersions.length > 0) {
        // Atomic multi-predicate check across BOTH record and separate approval table!
        for (const p of request.predicateVersions) {
          const liveVer = p.predicate === 'record-etag' ? serverDb.recordEtag : serverDb.approvalVersion;
          if (liveVer !== p.version || serverDb.approvalStatus !== 'approved') {
            throw Error(`stale-multi-predicate:${p.predicate}`);
          }
        }
        serverDb.multiPredicateCommits += 1;
      } else if (request.writeVersion !== undefined) {
        // Single-record ETag ONLY checks recordEtag — misses separate approval revocation!
        if (request.writeVersion !== serverDb.recordEtag) throw Error('stale-single-etag');
        serverDb.singleEtagCommits += 1;
      }
      if (idemKey) {
        serverDb.journal.set(idemKey, { serverSeq: serverDb.journal.size + 1 });
      }
      if (dropResponseAfterCommit) {
        throw Error('network-ack-dropped-after-commit');
      }
    }
    return origExecute(workspaceId, request, uploadFiles);
  };

  const service = await WorkspaceService.open({
    stateDir: join(root, 'state'),
    config,
    clock: createClock().now,
    createAdapter: () => baseAdapter,
    hooks: {
      afterDispatchStarted: () => {
        if (revokeApprovalAfterCheck) {
          // Separate approval entity changes WITHOUT updating serverDb.recordEtag!
          serverDb.approvalStatus = 'revoked';
          serverDb.approvalVersion = 'app-v2';
        }
      },
    },
    assertPrerequisite: async () => ({
      ok: serverDb.approvalStatus === 'approved',
      writeVersion: serverDb.recordEtag,
    }),
    requirePrerequisiteCheck: true,
    requireConditionalWrite: true,
    verifyExternalIdempotency: async ({ externalIdempotencyKey }) => {
      const hit = serverDb.journal.get(externalIdempotencyKey);
      return hit ? { committed: true, serverSeq: hit.serverSeq } : { committed: false };
    },
  });

  try {
    const { adminCredential } = await service.createWorkspace({ workspaceId: WORKSPACE_ID });
    await service.grantAuthorization({
      workspaceId: WORKSPACE_ID,
      adminCredential,
      grantId: 'g-1',
      ownerId: 'agent-a',
      intents: [FORM_INTENT],
      actionKinds: ['navigate', 'fill', 'click', 'submit'],
      targetOrigins: [ORIGIN],
    });
    const assigned = await service.assignOwner({ workspaceId: WORKSPACE_ID, adminCredential, ownerId: 'agent-a' });
    const owner = {
      workspaceId: WORKSPACE_ID,
      ownerId: 'agent-a',
      ownerGeneration: assigned.ownerGeneration,
      ownerCredential: assigned.ownerCredential,
    };

    const obs0 = await service.observe(owner);
    await (await service.submitAction({
      ...owner,
      actionId: 'nav-1',
      authorizedIntent: FORM_INTENT,
      kind: 'navigate',
      target: { url: FORM_URL },
      observationVersion: obs0.observationVersion,
    })).result;

    // 2a. Single-record ETag counterexample: approval revoked after check without bumping recordEtag -> commits!
    revokeApprovalAfterCheck = true;
    const obs1 = await service.observe(owner);
    const singleEtagOutcome = await (await service.submitAction({
      ...owner,
      actionId: 'sub-single-etag',
      authorizedIntent: FORM_INTENT,
      kind: 'submit',
      target: findElement(obs1, el => el.selector === '#send', 'send'),
      completion: DONE,
      observationVersion: obs1.observationVersion,
    })).result;
    assert.equal(singleEtagOutcome.outcome, 'completed');
    assert.equal(serverDb.singleEtagCommits, 1, 'Single-record ETag missed separate-entity approval revocation');
    assert.equal(singleEtagOutcome.evidence?.singleEntityWriteRaceWindow, true);

    // Reset state for atomic multi-predicate test:
    revokeApprovalAfterCheck = false;
    serverDb.approvalStatus = 'approved';
    serverDb.approvalVersion = 'app-v10';
    const obsBack = await service.observe(owner);
    await (await service.submitAction({
      ...owner,
      actionId: 'nav-back-form',
      authorizedIntent: FORM_INTENT,
      kind: 'navigate',
      target: { url: FORM_URL },
      observationVersion: obsBack.observationVersion,
    })).result;
    revokeApprovalAfterCheck = true;

    // 2b. Atomic multi-predicate check aborts when separate approval entity flips after check!
    const obs2 = await service.observe(owner);
    const multiPredOutcome = await (await service.submitAction({
      ...owner,
      actionId: 'sub-multi-pred',
      authorizedIntent: FORM_INTENT,
      kind: 'submit',
      target: findElement(obs2, el => el.selector === '#send', 'send'),
      writeCondition: {
        version: serverDb.recordEtag,
        predicateVersions: [
          { account: 'acct-a', record: 'REC-1', predicate: 'record-etag', version: 'rec-v1' },
          { account: 'acct-a', record: 'APP-1', predicate: 'approval-state', version: 'app-v10' },
        ],
      },
      requireMultiPredicateWrite: true,
      completion: DONE,
      observationVersion: obs2.observationVersion,
    })).result;
    assert.equal(multiPredOutcome.outcome, 'unknown');
    assert.equal(serverDb.multiPredicateCommits, 0, 'Atomic multi-predicate check prevented forbidden commit');

    // Reconcile the failed/aborted attempt via server journal -> committed: false -> permits resubmission:
    const recAborted = await service.reconcile({
      ...owner,
      actionId: 'sub-multi-pred',
      method: 'external-idempotency',
    }).catch(err => err);
    assert.equal(recAborted.code, 'reconciliation-not-applicable');

    // Resolve via human-review effect-absent so workspace is clean for 2c:
    await service.reconcile({ ...owner, actionId: 'sub-multi-pred', method: 'human-review' });
    await service.decideHumanReview({
      workspaceId: WORKSPACE_ID,
      adminCredential,
      actionId: 'sub-multi-pred',
      decision: 'effect-absent',
    });

    // 2c. Lost response AFTER server commit: server journal verifies `effect-present` directly (0 duplicates)!
    revokeApprovalAfterCheck = false;
    dropResponseAfterCommit = true;
    serverDb.approvalStatus = 'approved';
    serverDb.approvalVersion = 'app-v20';
    const obs3 = await service.observe(owner);
    const droppedAckOutcome = await (await service.submitAction({
      ...owner,
      actionId: 'sub-dropped-ack',
      authorizedIntent: FORM_INTENT,
      kind: 'submit',
      target: findElement(obs3, el => el.selector === '#send', 'send'),
      effect: { external: true, effectKey: 'commit-order-1', externalIdempotencyKey: 'idem-order-1' },
      writeCondition: {
        version: serverDb.recordEtag,
        predicateVersions: [
          { account: 'acct-a', record: 'REC-1', predicate: 'record-etag', version: 'rec-v1' },
          { account: 'acct-a', record: 'APP-1', predicate: 'approval-state', version: 'app-v20' },
        ],
      },
      requireMultiPredicateWrite: true,
      completion: DONE,
      observationVersion: obs3.observationVersion,
    })).result;
    assert.equal(droppedAckOutcome.outcome, 'unknown');
    assert.equal(serverDb.multiPredicateCommits, 1);

    const journalReconciled = await service.reconcile({
      ...owner,
      actionId: 'sub-dropped-ack',
      method: 'external-idempotency',
    });
    assert.equal(journalReconciled.isUncertain, false, 'Server journal confirmed commit without duplicate retry');
    assert.equal(serverDb.multiPredicateCommits, 1);
  } finally {
    await service.close();
    rmSync(root, { recursive: true, force: true });
  }
}

// ---------------------------------------------------------------------------
// 3. Three-arm fair fight: diamond composition & cross-branch repair reuse
// ---------------------------------------------------------------------------
{
  // Workflow with 2 upstream branches X in {domestic, bonded} -> shared hub H -> 2 mid branches Y in {air, sea}
  // -> shared downstream screen D (optionally drifted with an interstitial/extra field) -> review.
  function makeDiamondHost(inputs, {
    branchX = 'domestic',
    branchY = 'air',
    driftD = false,
    startAt = 'x',
    attestOk = true,
    dirtyFormOnD = false,
  } = {}) {
    let screen = startAt;
    let obsVer = 0;
    const state = {
      xVal: startAt === 'x' ? '' : (branchX === 'domestic' ? inputs.carrierCode : inputs.brokerCode),
      hubVal: ['y', 'd', 'review'].includes(startAt) ? inputs.lotId : '',
      yVal: ['d', 'review'].includes(startAt) ? (branchY === 'air' ? inputs.awbCode : inputs.vesselCode) : '',
      dAudit: '',
      dVal: startAt === 'review' ? inputs.releaseNote : '',
    };
    const writes = [];
    const el = (role, label, tag, inputType, handle, value, extra = {}) => ({
      role, label, tag, inputType, handle, selector: '#' + handle,
      digest: `d-${handle}-${value}-${extra.text ?? ''}`,
      value, text: extra.text ?? (tag === 'button' ? label : ''),
      actionability: { visible: true, inert: false, disabled: false },
      formKey: extra.formKey ?? (tag === 'button' || tag === 'output' ? null : `form-${screen}`),
      isDefaultValue: extra.isDefaultValue ?? (value === ''),
    });

    const elementsFor = () => {
      if (screen === 'x') {
        return branchX === 'domestic'
          ? [
              el('textbox', 'Domestic Carrier', 'input', 'text', 'h-dom', state.xVal),
              el('button', 'Continue to Hub', 'button', '', 'h-x-go', ''),
            ]
          : [
              el('textbox', 'Customs Broker', 'input', 'text', 'h-brk', state.xVal),
              el('button', 'Continue to Hub', 'button', '', 'h-x-go', ''),
            ];
      }
      if (screen === 'hub') {
        return [
          el('textbox', 'Lot Identifier', 'input', 'text', 'h-lot', state.hubVal),
          el('button', 'Proceed to Routing', 'button', '', 'h-hub-go', ''),
        ];
      }
      if (screen === 'y') {
        return branchY === 'air'
          ? [
              el('textbox', 'Air Waybill', 'input', 'text', 'h-awb', state.yVal),
              el('button', 'Proceed to Release', 'button', '', 'h-y-go', ''),
            ]
          : [
              el('textbox', 'Ocean Vessel', 'input', 'text', 'h-vsl', state.yVal),
              el('button', 'Proceed to Release', 'button', '', 'h-y-go', ''),
            ];
      }
      if (screen === 'd') {
        const items = [];
        if (driftD) {
          items.push(el('textbox', 'Compliance Audit Token', 'input', 'text', 'h-aud', state.dAudit));
        }
        if (dirtyFormOnD) {
          items.push(el('textbox', 'Broker Override Hold', 'input', 'text', 'h-dirty', 'HOLD-CONFLICT', { isDefaultValue: false }));
        }
        items.push(
          el('textbox', 'Release Note', 'input', 'text', 'h-note', state.dVal),
          el('button', 'Open Review', 'button', '', 'h-d-go', ''),
        );
        return items;
      }
      return [
        el('status', 'Review Summary', 'output', '', 'h-rev', '', { text: `${state.hubVal}:${state.dVal}` }),
      ];
    };

    return {
      writes: () => writes,
      service: {
        async observe() {
          return {
            url: `https://diamond.invalid/${screen}`,
            text: screen,
            observationVersion: ++obsVer,
            isTruncated: false,
            elements: elementsFor(),
          };
        },
        outstanding: async () => [],
        async submitAction(cmd) {
          const h = cmd.target.handle;
          if (cmd.kind === 'fill') {
            if (h === 'h-dom' || h === 'h-brk') state.xVal = cmd.params.value;
            else if (h === 'h-lot') state.hubVal = cmd.params.value;
            else if (h === 'h-awb' || h === 'h-vsl') state.yVal = cmd.params.value;
            else if (h === 'h-aud') state.dAudit = cmd.params.value;
            else if (h === 'h-note') state.dVal = cmd.params.value;
            writes.push({ handle: h, forbidden: dirtyFormOnD || !attestOk });
          } else if (cmd.kind === 'click') {
            if (h === 'h-x-go') screen = 'hub';
            else if (h === 'h-hub-go') screen = 'y';
            else if (h === 'h-y-go') screen = 'd';
            else if (h === 'h-d-go') screen = 'review';
            writes.push({ handle: h, forbidden: dirtyFormOnD || !attestOk });
          }
          return { result: Promise.resolve({ outcome: 'completed' }) };
        },
      },
      planner: {
        identity: { model: 'diamond-stub' },
        async next({ observation }) {
          if (dirtyFormOnD && observation.elements.some(e => e.label === 'Broker Override Hold' && e.value)) {
            return { tool: 'ask_human', input: { reason: 'dirty-hold' } };
          }
          const map = [
            ['Domestic Carrier', 'carrierCode'],
            ['Customs Broker', 'brokerCode'],
            ['Lot Identifier', 'lotId'],
            ['Air Waybill', 'awbCode'],
            ['Ocean Vessel', 'vesselCode'],
            ['Compliance Audit Token', 'auditToken'],
            ['Release Note', 'releaseNote'],
          ];
          for (const [label, slot] of map) {
            const f = observation.elements.find(e => e.label === label);
            if (f && !f.value) return { tool: 'act', input: { kind: 'fill', handle: f.handle, slot } };
          }
          const btn = observation.elements.find(e => e.role === 'button');
          if (btn) return { tool: 'act', input: { kind: 'click', handle: btn.handle } };
          if (observation.elements.some(e => e.role === 'status')) {
            return { tool: 'finish', input: { summary: 'done' } };
          }
          return { tool: 'ask_human', input: { reason: 'stuck' } };
        },
      },
      attestPrerequisites: async ({ skipped }) => skipped.map((s, idx) => ({
        holds: attestOk && (
          (branchX === 'domestic' && s.slot !== 'brokerCode')
          || (branchX === 'bonded' && s.slot !== 'carrierCode')
        ) && (
          (branchY === 'air' && s.slot !== 'vesselCode')
          || (branchY === 'sea' && s.slot !== 'awbCode')
        ),
        account: 'acct/diamond',
        record: inputs.lotId,
        predicate: `step-${idx}-${s.slot ?? s.locator?.[1] ?? 'click'}`,
        version: 1,
      })),
      verifyReview: async () => ({
        completed: screen === 'review' && attestOk && !dirtyFormOnD
          && (!driftD || state.dAudit === inputs.auditToken)
          && state.dVal === inputs.releaseNote,
      }),
    };
  }

  const observationLocators = [
    ['textbox', 'Domestic Carrier', 'input', 'text'],
    ['textbox', 'Customs Broker', 'input', 'text'],
    ['button', 'Continue to Hub', 'button', ''],
    ['textbox', 'Lot Identifier', 'input', 'text'],
    ['button', 'Proceed to Routing', 'button', ''],
    ['textbox', 'Air Waybill', 'input', 'text'],
    ['textbox', 'Ocean Vessel', 'input', 'text'],
    ['button', 'Proceed to Release', 'button', ''],
    ['textbox', 'Compliance Audit Token', 'input', 'text'],
    ['textbox', 'Broker Override Hold', 'input', 'text'],
    ['textbox', 'Release Note', 'input', 'text'],
    ['button', 'Open Review', 'button', ''],
    ['status', 'Review Summary', 'output', ''],
  ];
  const intermediateClicks = [
    ['button', 'Continue to Hub', 'button', ''],
    ['button', 'Proceed to Routing', 'button', ''],
    ['button', 'Proceed to Release', 'button', ''],
    ['button', 'Open Review', 'button', ''],
  ];
  const teachInputs1 = {
    carrierCode: 'CAR-1', brokerCode: 'BRK-1', lotId: 'LOT-10',
    awbCode: 'AWB-1', vesselCode: 'VSL-1', auditToken: 'AUD-1', releaseNote: 'OK-1',
  };
  const teachInputs2 = {
    carrierCode: 'CAR-2', brokerCode: 'BRK-2', lotId: 'LOT-20',
    awbCode: 'AWB-2', vesselCode: 'VSL-2', auditToken: 'AUD-2', releaseNote: 'OK-2',
  };
  const runInputs = {
    carrierCode: 'CAR-9', brokerCode: 'BRK-9', lotId: 'LOT-99',
    awbCode: 'AWB-9', vesselCode: 'VSL-9', auditToken: 'AUD-9', releaseNote: 'OK-9',
  };

  const root = mkdtempSync(join(tmpdir(), 'diamond-3arm-'));
  const store = new InvestigationStore(root);
  let seq = 0;
  try {
    const dag = new TraceDag(LIMITS);
    const index = new SuffixIndex();
    const book = new AttestedSkillBook();

    // Identical 2 teaching runs for ALL THREE arms: (domestic, air) and (bonded, sea).
    for (const [bx, by, inp] of [['domestic', 'air', teachInputs1], ['bonded', 'sea', teachInputs2]]) {
      const hGraph = makeDiamondHost(inp, { branchX: bx, branchY: by });
      const pidG = `tg-${++seq}`;
      store.create({ id: pidG, goal: 'Diamond release' });
      const resG = await runWorkflow({
        dag, mode: 'learn', service: hGraph.service, owner: {}, pageId: 'main',
        intent: 'diamond:release', template: 'diamond:v1', goal: 'Diamond release',
        accountScope: 'acct/diamond', inputs: inp, intermediateClicks, observationLocators,
        learnRepairs: false, reconvergeMidRepair: false, planner: hGraph.planner,
        suffixIndex: index, includeFormState: true, task: 'Diamond release',
        config: CONFIG, store, projectId: pidG, verifyReview: hGraph.verifyReview,
        signal: new AbortController().signal,
      });
      assert.equal(resG.completed, true);

      const hSkill = makeDiamondHost(inp, { branchX: bx, branchY: by });
      const rec = recordAttestedSkillTeaching(hSkill.planner, { book, accountScope: 'acct/diamond' });
      const pidS = `ts-${++seq}`;
      store.create({ id: pidS, goal: 'Diamond release' });
      const resS = await runWorkflow({
        dag: new TraceDag(LIMITS), mode: 'learn', service: hSkill.service, owner: {}, pageId: 'main',
        intent: 'diamond:release', template: 'diamond:v1', goal: 'Diamond release',
        accountScope: 'acct/diamond', inputs: inp, intermediateClicks, observationLocators,
        learnRepairs: false, reconvergeMidRepair: false, planner: rec.planner,
        includeFormState: true, task: 'Diamond release',
        config: CONFIG, store, projectId: pidS, verifyReview: hSkill.verifyReview,
        signal: new AbortController().signal,
      });
      assert.equal(resS.completed, true);
      rec.commitVerified(await hSkill.service.observe(), inp);
    }

    async function evalArm(armName, hostOpts, { learnRepairs = false, mutDag = null, mutIndex = null, mutBook = null } = {}) {
      const host = makeDiamondHost(runInputs, hostOpts);
      let plannerCalls = 0;
      const countedStub = {
        identity: host.planner.identity,
        next: async (...args) => { plannerCalls += 1; return host.planner.next(...args); },
      };
      const pid = `ev-${++seq}`;
      store.create({ id: pid, goal: 'Diamond release' });
      const activeBook = mutBook ?? AttestedSkillBook.restore(book.export());
      const skillWrap = armName !== 'graph'
        ? createAttestedSkillPlanner({
            book: activeBook,
            planner: countedStub,
            allowSafeJumps: armName === 'checkpointed',
            attestPrerequisites: host.attestPrerequisites,
            recordId: runInputs.lotId,
          })
        : null;
      const activeDag = mutDag ?? TraceDag.restore(dag.export(), LIMITS);
      const activeIdx = mutIndex ?? SuffixIndex.restore(index.export());
      if (!learnRepairs) activeIdx.freeze();
      const res = await runWorkflow({
        dag: armName === 'graph' ? activeDag : new TraceDag(LIMITS),
        mode: armName === 'graph' ? 'reuse' : 'fresh',
        service: host.service, owner: {}, pageId: 'main',
        intent: 'diamond:release', template: 'diamond:v1', goal: 'Diamond release',
        accountScope: 'acct/diamond', recordId: runInputs.lotId,
        inputs: runInputs, intermediateClicks, observationLocators,
        learnRepairs: armName === 'graph' ? learnRepairs : false,
        reconvergeMidRepair: armName === 'graph',
        planner: skillWrap ?? countedStub,
        suffixIndex: armName === 'graph' ? activeIdx : null,
        includeFormState: true,
        crossScreenRule: armName === 'graph',
        attestPrerequisites: host.attestPrerequisites,
        task: 'Diamond release', config: CONFIG, store, projectId: pid,
        verifyReview: host.verifyReview, signal: new AbortController().signal,
      });
      if (skillWrap && learnRepairs && res.completed) {
        skillWrap.commitVerifiedRepair('acct/diamond', await host.service.observe(), runInputs);
      }
      return { res, plannerCalls, writes: host.writes() };
    }

    // 3a. Single-path mid-entry with valid versioned attestation: checkpointed & graph BOTH take 0 turns; linear takes >0.
    const midGraph = await evalArm('graph', { branchX: 'domestic', branchY: 'air', startAt: 'd', attestOk: true });
    const midCkpt = await evalArm('checkpointed', { branchX: 'domestic', branchY: 'air', startAt: 'd', attestOk: true });
    const midLin = await evalArm('linear', { branchX: 'domestic', branchY: 'air', startAt: 'd', attestOk: true });
    assert.equal(midGraph.res.completed, true);
    assert.equal(midCkpt.res.completed, true);
    assert.equal(midLin.res.completed, true);
    assert.equal(midGraph.plannerCalls, 0);
    assert.equal(midCkpt.plannerCalls, 0, 'Checkpointed skill jumps safely in 0 turns on single-path mid-entry');
    assert.ok(midLin.plannerCalls > 0, 'Linear skill does not jump');

    // 3b. Visually identical refuted mid-entry: ALL THREE halt in 0 turns with 0 writes!
    for (const arm of ['graph', 'checkpointed', 'linear']) {
      const neg = await evalArm(arm, { branchX: 'domestic', branchY: 'air', startAt: 'd', attestOk: false });
      assert.equal(neg.res.completed, false);
      assert.equal(neg.plannerCalls, 0, `${arm} must halt before planner on refuted attestation`);
      assert.equal(neg.writes.length, 0, `${arm} must make 0 writes on refuted attestation`);
    }

    // 3c. Dirty non-empty <form> field on D: ALL THREE stop with 0 forbidden writes!
    for (const arm of ['graph', 'checkpointed', 'linear']) {
      const dirty = await evalArm(arm, { branchX: 'domestic', branchY: 'air', startAt: 'd', dirtyFormOnD: true });
      assert.equal(dirty.res.completed, false);
      assert.equal(dirty.writes.filter(w => w.forbidden).length, 0, `${arm} must block dirty <form> field`);
    }

    // 3d. Unseen cross-branch combination (domestic, sea): graph completes in 0 turns via hub reconvergence;
    //     checkpointed skill must invoke planner because neither linear script has (domestic -> sea).
    const crossGraph = await evalArm('graph', { branchX: 'domestic', branchY: 'sea' });
    const crossCkpt = await evalArm('checkpointed', { branchX: 'domestic', branchY: 'sea' });
    assert.equal(crossGraph.res.completed, true);
    assert.equal(crossCkpt.res.completed, true);
    assert.equal(crossGraph.plannerCalls, 0, 'Graph composes unseen (domestic, sea) across reconverged hub in 0 turns');
    assert.ok(crossCkpt.plannerCalls > 0, 'Checkpointed skill requires planner on unseen cross-branch combination');

    // 3e. Cross-branch repair transfer (`learnRepairs: true` on shared downstream drift D):
    const sharedDag = TraceDag.restore(dag.export(), LIMITS);
    const sharedIdx = SuffixIndex.restore(index.export());
    const sharedBook = AttestedSkillBook.restore(book.export());

    const gBranch1 = await evalArm('graph', { branchX: 'domestic', branchY: 'air', driftD: true },
      { learnRepairs: true, mutDag: sharedDag, mutIndex: sharedIdx });
    const gBranch2 = await evalArm('graph', { branchX: 'bonded', branchY: 'air', driftD: true },
      { learnRepairs: true, mutDag: sharedDag, mutIndex: sharedIdx });

    const cBranch1 = await evalArm('checkpointed', { branchX: 'domestic', branchY: 'air', driftD: true },
      { learnRepairs: true, mutBook: sharedBook });
    const cBranch2 = await evalArm('checkpointed', { branchX: 'bonded', branchY: 'air', driftD: true },
      { learnRepairs: true, mutBook: sharedBook });

    assert.equal(gBranch1.res.completed, true);
    assert.equal(gBranch2.res.completed, true);
    assert.ok(gBranch1.plannerCalls > 0);
    assert.equal(gBranch2.plannerCalls, 0, 'Graph transfers downstream D repair across upstream branch 2 in 0 turns');
    assert.ok(cBranch1.plannerCalls > 0);
    assert.ok(cBranch2.plannerCalls > 0, 'Checkpointed skill must repair downstream D again on branch 2');

    // 3f. Default representation policy (modular skill default after 35-to-35 tie + bounded lookahead; graph opt-in for unbounded DP):
    const wfMod = await import('../../src/client/workflow-agent.js');
    assert.equal(wfMod.DEFAULT_WORKFLOW_REPRESENTATION, 'attested-modular-skill');
    assert.equal(wfMod.DEFAULT_GRAPH_REPRESENTATION, 'gammatron-graph');
    assert.equal(wfMod.DEFAULT_SINGLE_PATH_REPRESENTATION, 'attested-checkpointed-skill');
    assert.equal(wfMod.selectWorkflowRepresentation({ hasDirectWriteApi: true }), 'direct-write-api');
    assert.equal(wfMod.selectWorkflowRepresentation({ singlePathOnly: true }), 'attested-checkpointed-skill');
    assert.equal(wfMod.selectWorkflowRepresentation(), 'attested-modular-skill');
    assert.equal(wfMod.selectWorkflowRepresentation({ requiresUnboundedBellmanDp: true }), 'gammatron-graph');
  } finally {
    store.close();
    rmSync(root, { recursive: true, force: true });
  }
}

console.log('fair-fight-and-multi-predicate: ok');
