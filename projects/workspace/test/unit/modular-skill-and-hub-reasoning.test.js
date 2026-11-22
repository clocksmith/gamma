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
import { SuffixIndex } from '../../src/client/suffix-eligibility.js';
import { TraceDag } from '../../src/client/trace-dag.js';
import {
  DEFAULT_MODULAR_SKILL_REPRESENTATION,
  DEFAULT_SINGLE_PATH_REPRESENTATION,
  DEFAULT_WORKFLOW_REPRESENTATION,
  evaluateReplayApplicability,
  runWorkflow,
  selectWorkflowRepresentation,
} from '../../src/client/workflow-agent.js';

const LIMITS = Object.freeze({ maxNodes: 128, maxEdges: 160, maxSteps: 36 });
const CONFIG = Object.freeze({ maxTurns: 20, maxInputBytes: 60000 });
const OWNER = Object.freeze({ callerId: 'test-mod', surfaceId: 'test' });

function el(role, label, tag, inputType, handle, value = '', extra = {}) {
  const isCtrl = tag === 'input' || tag === 'select' || tag === 'textarea';
  return {
    role,
    label,
    tag,
    inputType,
    handle,
    selector: `#${handle}`,
    digest: `d-${handle}-${value}-${extra.text ?? ''}`,
    value,
    text: extra.text ?? (tag === 'button' ? label : ''),
    actionability: { visible: true, inert: false, disabled: false },
    formKey: isCtrl ? (extra.formKey ?? 'form-main') : null,
    isDefaultValue: isCtrl ? (extra.isDefaultValue ?? (value === '')) : true,
  };
}

// 1. REST applicability & explicit domain business-prerequisite boundary:
{
  const direct = evaluateReplayApplicability({
    hasDirectWriteApi: true,
    requiresPreSubmitUiReview: false,
    requiresInBrowserContextGathering: false,
    explicitBusinessPrerequisites: ['clinical_approval_active', 'formulary_tier_permitted'],
  });
  assert.equal(direct.worthBuildingReplay, false);
  assert.equal(direct.recommendedChannel, 'direct-write-api');
  assert.equal(direct.reason, 'supported-write-api-solves-task');
  assert.deepEqual(direct.contractResponsibilities.middlewareStandardizable, [
    'optimistic-version-check',
    'idempotency-journal-deduplication',
  ]);
  assert.deepEqual(direct.contractResponsibilities.explicitDomainBusinessRules, [
    'clinical_approval_active',
    'formulary_tier_permitted',
  ]);
  assert.equal(direct.contractResponsibilities.schemaInferableAuthorization, false);

  const staged = evaluateReplayApplicability({
    hasDirectWriteApi: true,
    requiresPreSubmitUiReview: true,
    explicitBusinessPrerequisites: ['ehs_reticle_permit_valid'],
  });
  assert.equal(staged.worthBuildingReplay, true);
  assert.equal(staged.recommendedChannel, 'browser-workflow-replay');
  assert.equal(staged.reason, 'ui-review-or-browser-context-required');

  assert.equal(selectWorkflowRepresentation({ hasDirectWriteApi: true }), 'direct-write-api');
  assert.equal(
    selectWorkflowRepresentation({ hasDirectWriteApi: true, requiresPreSubmitUiReview: true, singlePathOnly: true }),
    DEFAULT_SINGLE_PATH_REPRESENTATION,
  );
  assert.equal(
    selectWorkflowRepresentation({ screenFactoredSharedSuffixesOnly: true }),
    DEFAULT_MODULAR_SKILL_REPRESENTATION,
  );
  assert.equal(selectWorkflowRepresentation(), DEFAULT_WORKFLOW_REPRESENTATION);
}

// 2. Hub reasoning, unavailable-prerequisite write gate, middle-field prefill, modular shared suffixes,
//    and multi-exit Bellman-DP routing separation:
{
  const root = mkdtempSync(join(tmpdir(), 'mod-rev4-'));
  const store = new InvestigationStore(join(root, 'store'));
  try {
    const observationLocators = [
      ['textbox', 'Route A1 Tool', 'input', 'text'],
      ['textbox', 'Route A1 Overlay', 'input', 'text'],
      ['textbox', 'Route A2 Probe', 'input', 'text'],
      ['button', 'To Hub', 'button', ''],
      ['textbox', 'Hub Lot', 'input', 'text'],
      ['combobox', 'Hub Bay', 'select', ''],
      ['textbox', 'Hub Chamber', 'input', 'text'],
      ['button', 'Proceed From Hub', 'button', ''],
      ['button', 'Open Track B1', 'button', ''],
      ['button', 'Open Track B2', 'button', ''],
      ['textbox', 'Track B1 Recipe', 'input', 'text'],
      ['textbox', 'Track B2 Split', 'input', 'text'],
      ['button', 'To Downstream', 'button', ''],
      ['textbox', 'Extra Audit Code', 'input', 'text'],
      ['textbox', 'QA Signoff', 'input', 'text'],
      ['button', 'Open Review', 'button', ''],
      ['status', 'Review Banner', 'output', ''],
    ];
    const intermediateClicks = [
      ['button', 'To Hub', 'button', ''],
      ['button', 'Proceed From Hub', 'button', ''],
      ['button', 'Open Track B1', 'button', ''],
      ['button', 'Open Track B2', 'button', ''],
      ['button', 'To Downstream', 'button', ''],
      ['button', 'Open Review', 'button', ''],
    ];

    function makeInputs(tag) {
      return {
        a1Tool: `TOOL-${tag}`,
        a1Overlay: `OVL-${tag}`,
        a2Probe: `PRB-${tag}`,
        hubLot: `LOT-${tag}`,
        hubBay: `BAY-${tag}`,
        hubChamber: `CHM-${tag}`,
        b1Recipe: `RCP-${tag}`,
        b2Split: `SPL-${tag}`,
        extraAudit: `AUD-${tag}`,
        qaSignoff: `QA-${tag}`,
      };
    }

    function createSite({
      startScreen = 'a',
      branchA = 'a1',
      branchB = 'b1',
      multiExitHub = false,
      reorderAndPrefillMiddleOnHub = false,
      driftDownstream = false,
      inputs,
      attestMode = 'all-hold', // 'all-hold' | 'a1-unavailable-a2-false' | 'both-false'
    }) {
      let screen = startScreen;
      let obsVer = 0;
      const writes = [];
      const state = {
        a1Tool: '',
        a1Overlay: '',
        a2Probe: '',
        hubLot: '',
        hubBay: reorderAndPrefillMiddleOnHub ? inputs.hubBay : '',
        hubChamber: '',
        b1Recipe: '',
        b2Split: '',
        extraAudit: '',
        qaSignoff: '',
      };

      const render = () => {
        if (screen === 'a') {
          return branchA === 'a1'
            ? [
                el('textbox', 'Route A1 Tool', 'input', 'text', 'h-a1-t', state.a1Tool),
                el('textbox', 'Route A1 Overlay', 'input', 'text', 'h-a1-o', state.a1Overlay),
                el('button', 'To Hub', 'button', '', 'h-a-go'),
              ]
            : [
                el('textbox', 'Route A2 Probe', 'input', 'text', 'h-a2-p', state.a2Probe),
                el('button', 'To Hub', 'button', '', 'h-a-go'),
              ];
        }
        if (screen === 'hub') {
          const pfx = reorderAndPrefillMiddleOnHub ? 'v2-' : '';
          const fields = [
            el('textbox', 'Hub Lot', 'input', 'text', `${pfx}h-lot`, state.hubLot),
            el('combobox', 'Hub Bay', 'select', '', `${pfx}h-bay`, state.hubBay, {
              isDefaultValue: !reorderAndPrefillMiddleOnHub && state.hubBay === '',
            }),
            el('textbox', 'Hub Chamber', 'input', 'text', `${pfx}h-chm`, state.hubChamber),
          ];
          if (reorderAndPrefillMiddleOnHub) fields.reverse();
          const buttons = multiExitHub
            ? [
                el('button', 'Open Track B1', 'button', '', `${pfx}h-b1`),
                el('button', 'Open Track B2', 'button', '', `${pfx}h-b2`),
              ]
            : [el('button', 'Proceed From Hub', 'button', '', `${pfx}h-hub-go`)];
          return [...fields, ...buttons];
        }
        if (screen === 'b1') {
          return [
            el('textbox', 'Track B1 Recipe', 'input', 'text', 'h-b1-r', state.b1Recipe),
            el('button', 'To Downstream', 'button', '', 'h-b-go'),
          ];
        }
        if (screen === 'b2') {
          return [
            el('textbox', 'Track B2 Split', 'input', 'text', 'h-b2-s', state.b2Split),
            el('button', 'To Downstream', 'button', '', 'h-b-go'),
          ];
        }
        if (screen === 'd') {
          const list = [];
          if (driftDownstream) {
            list.push(el('textbox', 'Extra Audit Code', 'input', 'text', 'h-aud', state.extraAudit));
          }
          list.push(
            el('textbox', 'QA Signoff', 'input', 'text', 'h-qa', state.qaSignoff),
            el('button', 'Open Review', 'button', '', 'h-d-go'),
          );
          return list;
        }
        return [
          el('status', 'Review Banner', 'output', '', 'h-rev', '', {
            text: `${state.hubLot}|${state.qaSignoff}`,
          }),
        ];
      };

      return {
        writes: () => writes,
        service: {
          async observe() {
            return {
              url: `https://fab.invalid/${screen}`,
              text: screen,
              observationVersion: ++obsVer,
              isTruncated: false,
              elements: render(),
            };
          },
          outstanding: async () => [],
          async submitAction(cmd) {
            const h = cmd.target.handle.replace(/^v2-/, '');
            if (cmd.kind === 'fill' || cmd.kind === 'select') {
              if (h === 'h-a1-t') state.a1Tool = cmd.params.value;
              else if (h === 'h-a1-o') state.a1Overlay = cmd.params.value;
              else if (h === 'h-a2-p') state.a2Probe = cmd.params.value;
              else if (h === 'h-lot') state.hubLot = cmd.params.value;
              else if (h === 'h-bay') state.hubBay = cmd.params.value;
              else if (h === 'h-chm') state.hubChamber = cmd.params.value;
              else if (h === 'h-b1-r') state.b1Recipe = cmd.params.value;
              else if (h === 'h-b2-s') state.b2Split = cmd.params.value;
              else if (h === 'h-aud') state.extraAudit = cmd.params.value;
              else if (h === 'h-qa') state.qaSignoff = cmd.params.value;
              writes.push({ kind: cmd.kind, handle: h, value: cmd.params.value });
            } else if (cmd.kind === 'click') {
              if (h === 'h-a-go') screen = 'hub';
              else if (h === 'h-hub-go') screen = branchB;
              else if (h === 'h-b1') screen = 'b1';
              else if (h === 'h-b2') screen = 'b2';
              else if (h === 'h-b-go') screen = 'd';
              else if (h === 'h-d-go') screen = 'review';
              writes.push({ kind: 'click', handle: h });
            }
            return { result: Promise.resolve({ outcome: 'completed' }) };
          },
        },
        planner: {
          identity: { model: 'unit-stub' },
          async next({ observation, inputs: inp }) {
            const labelSlot = [
              ['Route A1 Tool', 'a1Tool'],
              ['Route A1 Overlay', 'a1Overlay'],
              ['Route A2 Probe', 'a2Probe'],
              ['Hub Lot', 'hubLot'],
              ['Hub Bay', 'hubBay'],
              ['Hub Chamber', 'hubChamber'],
              ['Track B1 Recipe', 'b1Recipe'],
              ['Track B2 Split', 'b2Split'],
              ['Extra Audit Code', 'extraAudit'],
              ['QA Signoff', 'qaSignoff'],
            ];
            for (const [lbl, slot] of labelSlot) {
              const f = observation.elements.find(e => e.label === lbl);
              if (f && !f.value && typeof inp[slot] === 'string') {
                return { tool: 'act', input: { kind: f.tag === 'select' ? 'select' : 'fill', handle: f.handle, slot } };
              }
            }
            const b2Btn = observation.elements.find(e => e.label === 'Open Track B2');
            const b1Btn = observation.elements.find(e => e.label === 'Open Track B1');
            if (b1Btn && b2Btn) {
              const onlyB2 = typeof inp.b2Split === 'string' && typeof inp.b1Recipe !== 'string';
              const onlyB1 = typeof inp.b1Recipe === 'string' && typeof inp.b2Split !== 'string';
              const pick = onlyB2 ? b2Btn : (onlyB1 ? b1Btn : (branchB === 'b2' ? b2Btn : b1Btn));
              return { tool: 'act', input: { kind: 'click', handle: pick.handle } };
            }
            const btn = observation.elements.find(e => e.role === 'button');
            if (btn) return { tool: 'act', input: { kind: 'click', handle: btn.handle } };
            if (observation.elements.some(e => e.role === 'status')) {
              return { tool: 'finish', input: { summary: 'done' } };
            }
            return { tool: 'ask_human', input: { reason: 'stuck' } };
          },
        },
        attestPrerequisites: async ({ skipped }) => skipped.map((s, idx) => {
          if (attestMode === 'both-false') {
            return { holds: false, account: 'acct-fab', record: inputs.hubLot, predicate: `p-${idx}`, version: 1 };
          }
          if (attestMode === 'a1-unavailable-a2-false') {
            if (s.slot === 'a2Probe') {
              return { holds: false, account: 'acct-fab', record: inputs.hubLot, predicate: 'a2Probe', version: 1 };
            }
            if (s.slot === 'a1Overlay') {
              return { status: 'unavailable', predicate: 'a1Overlay', reason: 'scatterometry-offline' };
            }
            return { holds: true, account: 'acct-fab', record: inputs.hubLot, predicate: `p-${idx}`, version: 1 };
          }
          return { holds: true, account: 'acct-fab', record: inputs.hubLot, predicate: `p-${idx}`, version: 1 };
        }),
        verifyReview: async () => ({
          completed: screen === 'review'
            && state.hubLot === inputs.hubLot
            && state.hubBay === inputs.hubBay
            && state.hubChamber === inputs.hubChamber
            && (!driftDownstream || state.extraAudit === inputs.extraAudit)
            && state.qaSignoff === inputs.qaSignoff,
        }),
      };
    }

    // Teach `teach-a` (a1 -> hub -> b1 -> d) and `teach-b` (a2 -> hub -> b2 -> d) on server-routed hub:
    const dag = new TraceDag(LIMITS);
    const suffixIndex = new SuffixIndex();
    const book = new AttestedSkillBook();
    let pid = 0;
    const mkProj = prefix => {
      const id = `${prefix}-${++pid}`;
      store.create({ id, goal: 'mod-rev4-test' });
      return id;
    };

    for (const [tTag, branchA, branchB] of [['TA', 'a1', 'b1'], ['TB', 'a2', 'b2']]) {
      const inp = makeInputs(tTag);
      const gSite = createSite({ branchA, branchB, inputs: inp });
      const gp = mkProj('tg');
      const gTeach = await runWorkflow({
        dag,
        mode: 'learn',
        service: gSite.service,
        owner: OWNER,
        pageId: gp,
        intent: 'fab-disp',
        template: 'fab-v1',
        goal: 'review',
        accountScope: 'acct-fab',
        recordId: inp.hubLot,
        inputs: inp,
        intermediateClicks,
        observationLocators,
        task: 'fab',
        planner: gSite.planner,
        config: CONFIG,
        store,
        projectId: gp,
        verifyReview: gSite.verifyReview,
        signal: new AbortController().signal,
        suffixIndex,
        includeFormState: true,
      });
      assert.equal(gTeach.completed, true);

      const sSite = createSite({ branchA, branchB, inputs: inp });
      const rec = recordAttestedSkillTeaching(sSite.planner, { book, accountScope: 'acct-fab' });
      const spId = mkProj('ts');
      const sTeach = await runWorkflow({
        dag: new TraceDag(LIMITS),
        mode: 'fresh',
        service: sSite.service,
        owner: OWNER,
        pageId: spId,
        intent: 'fab-disp',
        template: 'fab-v1',
        goal: 'review',
        accountScope: 'acct-fab',
        recordId: inp.hubLot,
        inputs: inp,
        intermediateClicks,
        observationLocators,
        task: 'fab',
        planner: rec.planner,
        config: CONFIG,
        store,
        projectId: spId,
        verifyReview: sSite.verifyReview,
        signal: new AbortController().signal,
        includeFormState: true,
      });
      assert.equal(sTeach.completed, true);
      rec.commitVerified(await sSite.service.observe(), inp);
    }

    const compiledStats = book.compiledSubroutineStats();
    assert.equal(compiledStats.subroutineCount, 6, 'a1, a2, shared hub, b1, b2, shared downstream');

    async function runArm(arm, siteOpts, wfExtra = {}, { mutDag = null, mutIdx = null, mutBook = null } = {}) {
      const inp = siteOpts.inputs ?? makeInputs('RUN');
      const site = createSite({ ...siteOpts, inputs: inp });
      let turns = 0;
      const basePlanner = {
        identity: site.planner.identity,
        next: async (...args) => {
          turns += 1;
          return site.planner.next(...args);
        },
      };
      if (arm === 'graph') {
        const d = mutDag ?? TraceDag.restore(dag.export(), LIMITS);
        const idx = mutIdx ?? SuffixIndex.restore(suffixIndex.export());
        const rgId = mkProj('rg');
        const res = await runWorkflow({
          dag: d,
          mode: 'reuse',
          service: site.service,
          owner: OWNER,
          pageId: rgId,
          intent: 'fab-disp',
          template: 'fab-v1',
          goal: 'review',
          accountScope: 'acct-fab',
          recordId: inp.hubLot,
          inputs: inp,
          intermediateClicks,
          observationLocators,
          task: 'fab',
          planner: basePlanner,
          config: CONFIG,
          store,
          projectId: rgId,
          verifyReview: site.verifyReview,
          signal: new AbortController().signal,
          suffixIndex: mutDag ? idx : idx.freeze(),
          crossScreenRule: true,
          includeFormState: true,
          reconvergeMidRepair: true,
          attestPrerequisites: site.attestPrerequisites,
          ...wfExtra,
        });
        return { res, turns, writes: site.writes() };
      }
      const b = mutBook ?? AttestedSkillBook.restore(book.export());
      const sp = createAttestedSkillPlanner({
        book: b,
        planner: basePlanner,
        allowSafeJumps: true,
        allowCallableSharedSuffixes: arm === 'modular',
        attestPrerequisites: site.attestPrerequisites,
        recordId: inp.hubLot,
      });
      const rsId = mkProj('rs');
      const res = await runWorkflow({
        dag: new TraceDag(LIMITS),
        mode: 'fresh',
        service: site.service,
        owner: OWNER,
        pageId: rsId,
        intent: 'fab-disp',
        template: 'fab-v1',
        goal: 'review',
        accountScope: 'acct-fab',
        recordId: inp.hubLot,
        inputs: inp,
        intermediateClicks,
        observationLocators,
        task: 'fab',
        planner: sp,
        config: CONFIG,
        store,
        projectId: rsId,
        verifyReview: site.verifyReview,
        signal: new AbortController().signal,
        includeFormState: true,
        ...wfExtra,
      });
      if (wfExtra.learnRepairs && res.completed) {
        sp.commitVerifiedRepair('acct-fab', await site.service.observe(), inp);
      }
      return { res, turns, writes: site.writes(), skillStats: sp.stats() };
    }

    // 2a. Middle-field prefill on reordered Hub: both `graph` and `modular` finish in 0 turns and skip `h-bay`!
    const gPrefill = await runArm('graph', { reorderAndPrefillMiddleOnHub: true });
    const mPrefill = await runArm('modular', { reorderAndPrefillMiddleOnHub: true });
    assert.equal(gPrefill.res.completed, true);
    assert.equal(gPrefill.turns, 0, 'Graph finishes middle-prefilled reordered screen in 0 turns');
    assert.equal(gPrefill.writes.some(w => w.handle === 'h-bay'), false, 'Pre-filled middle slot is not overwritten');
    assert.equal(mPrefill.res.completed, true);
    assert.equal(mPrefill.turns, 0);

    // 2b. Hub reasoning + unavailable-prerequisite write gate:
    // Untaken branch A2 returns `holds: false`, taken branch A1 has one `unavailable` predicate:
    // - Under `requireVerifiedEntryPrerequisites: true` without live verification: does NOT say `attestation-refuted`,
    //   blocks write before dispatch (`0` writes)!
    const gBlocked = await runArm(
      'graph',
      { startScreen: 'hub', attestMode: 'a1-unavailable-a2-false' },
      { requireVerifiedEntryPrerequisites: true },
    );
    const mBlocked = await runArm(
      'modular',
      { startScreen: 'hub', attestMode: 'a1-unavailable-a2-false' },
      { requireVerifiedEntryPrerequisites: true },
    );
    assert.equal(gBlocked.res.completed, false);
    assert.notEqual(gBlocked.res.detail, 'Prerequisite attestation refused mid-workflow entry');
    assert.match(gBlocked.res.detail, /Unavailable prerequisite cannot authorize write/);
    assert.equal(gBlocked.writes.length, 0, 'Zero writes dispatched when unavailable prerequisite is unverified');
    assert.equal(mBlocked.res.completed, false);
    assert.match(mBlocked.res.detail, /Unavailable prerequisite cannot authorize write/);
    assert.equal(mBlocked.writes.length, 0);

    // - When live `assertPrerequisite` explicitly verifies the unavailable prerequisite (`verifiedUnavailable: true`):
    const gVerified = await runArm(
      'graph',
      { startScreen: 'hub', attestMode: 'a1-unavailable-a2-false' },
      {
        requireVerifiedEntryPrerequisites: true,
        assertPrerequisite: async () => ({ ok: true, verifiedUnavailable: true }),
      },
    );
    assert.equal(gVerified.res.completed, true);
    assert.equal(gVerified.res.unverifiedUnavailablePrerequisiteWrites, undefined);

    // - When BOTH branches return `holds: false`, universal refutation still halts at step 0 with 0 writes:
    const gBothFalse = await runArm('graph', { startScreen: 'hub', attestMode: 'both-false' });
    const mBothFalse = await runArm('modular', { startScreen: 'hub', attestMode: 'both-false' });
    assert.equal(gBothFalse.res.completed, false);
    assert.equal(gBothFalse.res.detail, 'Prerequisite attestation refused mid-workflow entry');
    assert.equal(gBothFalse.writes.length, 0);
    assert.equal(mBothFalse.res.completed, false);
    assert.equal(mBothFalse.res.detail, 'Prerequisite attestation refused mid-workflow entry');
    assert.equal(mBothFalse.writes.length, 0);

    // 2c. Screen-factored cross-branch composition & cross-branch repair reuse (`modular` matches `graph`!):
    const mCross1 = await runArm('modular', { branchA: 'a1', branchB: 'b2' });
    const mCross2 = await runArm('modular', { branchA: 'a2', branchB: 'b1' });
    assert.equal(mCross1.res.completed, true);
    assert.equal(mCross1.turns, 0, 'Modular skill composes unseen (A1 -> Hub -> B2 -> D) in 0 turns');
    assert.equal(mCross2.res.completed, true);
    assert.equal(mCross2.turns, 0, 'Modular skill composes unseen (A2 -> Hub -> B1 -> D) in 0 turns');

    const sharedBook = AttestedSkillBook.restore(book.export());
    const mRep1 = await runArm(
      'modular',
      { branchA: 'a1', branchB: 'b1', driftDownstream: true, inputs: makeInputs('R1') },
      { learnRepairs: true },
      { mutBook: sharedBook },
    );
    const mRep2 = await runArm(
      'modular',
      { branchA: 'a2', branchB: 'b2', driftDownstream: true, inputs: makeInputs('R2') },
      { learnRepairs: true },
      { mutBook: sharedBook },
    );
    assert.equal(mRep1.res.completed, true);
    assert.equal(mRep1.turns, 1, '1 turn to repair shared downstream D on branch 1');
    assert.equal(mRep2.res.completed, true);
    assert.equal(mRep2.turns, 0, '0 turns on branch 2 (even via A2 -> Hub -> B2!): shared callable suffix reused repair');

    // 2d. Genuine separation: multi-exit Hub where BOTH `Open Track B1` and `Open Track B2` are visible on `/hub`
    //     and only `b2Split` is supplied in `inputs` (`b1Recipe` omitted):
    const multiDag = new TraceDag(LIMITS);
    const multiIdx = new SuffixIndex();
    const multiBook = new AttestedSkillBook();
    for (const [tTag, branchA, branchB] of [['MA', 'a1', 'b1'], ['MB', 'a2', 'b2']]) {
      const inp = makeInputs(tTag);
      const gSite = createSite({ branchA, branchB, multiExitHub: true, inputs: inp });
      const mgId = mkProj('mg');
      await runWorkflow({
        dag: multiDag,
        mode: 'learn',
        service: gSite.service,
        owner: OWNER,
        pageId: mgId,
        intent: 'fab-multi',
        template: 'fab-multi-v1',
        goal: 'review',
        accountScope: 'acct-fab',
        recordId: inp.hubLot,
        inputs: inp,
        intermediateClicks,
        observationLocators,
        task: 'fab',
        planner: gSite.planner,
        config: CONFIG,
        store,
        projectId: mgId,
        verifyReview: gSite.verifyReview,
        signal: new AbortController().signal,
        suffixIndex: multiIdx,
        includeFormState: true,
      });

      const sSite = createSite({ branchA, branchB, multiExitHub: true, inputs: inp });
      const rec = recordAttestedSkillTeaching(sSite.planner, { book: multiBook, accountScope: 'acct-fab' });
      const msId = mkProj('ms');
      await runWorkflow({
        dag: new TraceDag(LIMITS),
        mode: 'fresh',
        service: sSite.service,
        owner: OWNER,
        pageId: msId,
        intent: 'fab-multi',
        template: 'fab-multi-v1',
        goal: 'review',
        accountScope: 'acct-fab',
        recordId: inp.hubLot,
        inputs: inp,
        intermediateClicks,
        observationLocators,
        task: 'fab',
        planner: rec.planner,
        config: CONFIG,
        store,
        projectId: msId,
        verifyReview: sSite.verifyReview,
        signal: new AbortController().signal,
        includeFormState: true,
      });
      rec.commitVerified(await sSite.service.observe(), inp);
    }

    const partialInputs = makeInputs('ONLY-B2');
    delete partialInputs.b1Recipe; // only Track B2 is feasible downstream!

    const gMultiSite = createSite({ branchA: 'a1', branchB: 'b2', multiExitHub: true, inputs: partialInputs });
    let gMultiTurns = 0;
    const egId = mkProj('eg');
    const gMultiRes = await runWorkflow({
      dag: TraceDag.restore(multiDag.export(), LIMITS),
      mode: 'reuse',
      service: gMultiSite.service,
      owner: OWNER,
      pageId: egId,
      intent: 'fab-multi',
      template: 'fab-multi-v1',
      goal: 'review',
      accountScope: 'acct-fab',
      recordId: partialInputs.hubLot,
      inputs: partialInputs,
      intermediateClicks,
      observationLocators,
      task: 'fab',
      planner: { identity: { model: 'stub' }, next: async (...a) => { gMultiTurns += 1; return gMultiSite.planner.next(...a); } },
      config: CONFIG,
      store,
      projectId: egId,
      verifyReview: gMultiSite.verifyReview,
      signal: new AbortController().signal,
      suffixIndex: SuffixIndex.restore(multiIdx.export()).freeze(),
      crossScreenRule: true,
      includeFormState: true,
      reconvergeMidRepair: true,
      attestPrerequisites: gMultiSite.attestPrerequisites,
    });
    assert.equal(gMultiRes.completed, true);
    assert.equal(gMultiTurns, 0, 'Bellman DP eliminates infeasible B1 branch at Hub in 0 planner turns');

    const mMultiSite = createSite({ branchA: 'a1', branchB: 'b2', multiExitHub: true, inputs: partialInputs });
    let mMultiTurns = 0;
    const mMultiSkill = createAttestedSkillPlanner({
      book: AttestedSkillBook.restore(multiBook.export()),
      planner: { identity: { model: 'stub' }, next: async (...a) => { mMultiTurns += 1; return mMultiSite.planner.next(...a); } },
      allowSafeJumps: true,
      allowCallableSharedSuffixes: true,
      attestPrerequisites: mMultiSite.attestPrerequisites,
      recordId: partialInputs.hubLot,
    });
    const emId = mkProj('em');
    const mMultiRes = await runWorkflow({
      dag: new TraceDag(LIMITS),
      mode: 'fresh',
      service: mMultiSite.service,
      owner: OWNER,
      pageId: emId,
      intent: 'fab-multi',
      template: 'fab-multi-v1',
      goal: 'review',
      accountScope: 'acct-fab',
      recordId: partialInputs.hubLot,
      inputs: partialInputs,
      intermediateClicks,
      observationLocators,
      task: 'fab',
      planner: mMultiSkill,
      config: CONFIG,
      store,
      projectId: emId,
      verifyReview: mMultiSite.verifyReview,
      signal: new AbortController().signal,
      includeFormState: true,
    });
    assert.equal(mMultiRes.completed, true);
    assert.equal(mMultiTurns, 1, 'Without backward DP, modular skill hands back once at multi-exit Hub then resumes B2->D');
    assert.ok(mMultiSkill.stats().guardRefusals['ambiguous-callable-branch'] >= 1);
    assert.equal(mMultiSite.writes().some(w => w.handle === 'h-b1'), false, 'Never clicks infeasible Track B1');

    // Symmetric check when only `b1Recipe` is supplied (`b2Split` omitted):
    const partialInputsB1 = makeInputs('ONLY-B1');
    delete partialInputsB1.b2Split;
    const gB1Site = createSite({ branchA: 'a2', branchB: 'b1', multiExitHub: true, inputs: partialInputsB1 });
    let gB1Turns = 0;
    const egB1Id = mkProj('egb1');
    const gB1Res = await runWorkflow({
      dag: TraceDag.restore(multiDag.export(), LIMITS),
      mode: 'reuse',
      service: gB1Site.service,
      owner: OWNER,
      pageId: egB1Id,
      intent: 'fab-multi',
      template: 'fab-multi-v1',
      goal: 'review',
      accountScope: 'acct-fab',
      recordId: partialInputsB1.hubLot,
      inputs: partialInputsB1,
      intermediateClicks,
      observationLocators,
      task: 'fab',
      planner: { identity: { model: 'stub' }, next: async (...a) => { gB1Turns += 1; return gB1Site.planner.next(...a); } },
      config: CONFIG,
      store,
      projectId: egB1Id,
      verifyReview: gB1Site.verifyReview,
      signal: new AbortController().signal,
      suffixIndex: SuffixIndex.restore(multiIdx.export()).freeze(),
      crossScreenRule: true,
      includeFormState: true,
      reconvergeMidRepair: true,
      attestPrerequisites: gB1Site.attestPrerequisites,
    });
    assert.equal(gB1Res.completed, true);
    assert.equal(gB1Turns, 0, 'Bellman DP eliminates infeasible B2 branch at Hub in 0 planner turns');

    const mB1Site = createSite({ branchA: 'a2', branchB: 'b1', multiExitHub: true, inputs: partialInputsB1 });
    let mB1Turns = 0;
    const mB1Skill = createAttestedSkillPlanner({
      book: AttestedSkillBook.restore(multiBook.export()),
      planner: { identity: { model: 'stub' }, next: async (...a) => { mB1Turns += 1; return mB1Site.planner.next(...a); } },
      allowSafeJumps: true,
      allowCallableSharedSuffixes: true,
      attestPrerequisites: mB1Site.attestPrerequisites,
      recordId: partialInputsB1.hubLot,
    });
    const emB1Id = mkProj('emb1');
    const mB1Res = await runWorkflow({
      dag: new TraceDag(LIMITS),
      mode: 'fresh',
      service: mB1Site.service,
      owner: OWNER,
      pageId: emB1Id,
      intent: 'fab-multi',
      template: 'fab-multi-v1',
      goal: 'review',
      accountScope: 'acct-fab',
      recordId: partialInputsB1.hubLot,
      inputs: partialInputsB1,
      intermediateClicks,
      observationLocators,
      task: 'fab',
      planner: mB1Skill,
      config: CONFIG,
      store,
      projectId: emB1Id,
      verifyReview: mB1Site.verifyReview,
      signal: new AbortController().signal,
      includeFormState: true,
    });
    assert.equal(mB1Res.completed, true);
    assert.equal(mB1Turns, 1);
    assert.equal(mB1Site.writes().some(w => w.handle === 'h-b2'), false, 'Never clicks infeasible Track B2');
  } finally {
    store.close();
    rmSync(root, { recursive: true, force: true });
  }
}

console.log('modular-skill-and-hub-reasoning: ok');
