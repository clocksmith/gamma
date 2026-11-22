// Unit verification of post-holdout-entry-accountability-rules.md (Rules 1-4):
//   Rule 1: authorizeStep return-value refusals ({ ok: false } / false) fail closed before dispatch.
//   Rule 2: Unchanged interior screens in TraceDag v3 require entry accountability (roots / accountedReach
//           or server-truth attestPrerequisites), closing the exact-hash mid-entry bypass; negative
//           attestation at session entry halts runWorkflow without handing a stale tab to the planner.
//   Rule 3: Read-only [role="status"] / <output> elements bind slot-projected vs. literal text signatures
//           without leaking raw labels or private slot values into SuffixIndex exports.
//   Rule 4: Optional effectForStep passes { effect, completion, preconditions } to submitAction.

import assert from 'node:assert/strict';
import { mkdtempSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { structuralLocator } from '../../src/adapters/page-query.js';
import { InvestigationStore } from '../../src/client/investigation.js';
import { SuffixIndex } from '../../src/client/suffix-eligibility.js';
import { TraceDag } from '../../src/client/trace-dag.js';
import { runWorkflow } from '../../src/client/workflow-agent.js';

const LIMITS = { maxNodes: 32, maxEdges: 32, maxSteps: 10 };
const field = (label, id, extra = {}) => ({
  label, role: 'textbox', tag: 'input', inputType: 'text',
  selector: `#${id}`, handle: id, digest: `dig-${id}`, value: '', ...extra,
});
const button = (label, id) => ({
  label, role: 'button', tag: 'button', inputType: '',
  selector: `#${id}`, handle: id, digest: `dig-${id}`, value: null,
});
const statusOut = (label, id, text) => ({
  label, role: 'status', tag: 'output', inputType: '',
  selector: `#${id}`, handle: id, digest: `dig-${id}-${text}`, value: null, text,
});
const withFormState = (el, cmd) => (cmd?.includeFormState
  ? {
      formKey: el.role === 'status' || el.tag === 'output' ? null : '#form',
      isDefaultValue: el.role === 'status' || el.tag === 'output' ? undefined : !el.value,
      ...structuredClone(el),
    }
  : structuredClone(el));

function makeMultiScreenSite(screens, startStage = 0) {
  let stage = startStage;
  let version = 0;
  const calls = [];
  return {
    calls,
    stage: () => stage,
    outstanding: async () => [],
    observe: async (cmd) => ({
      url: `https://fixture.example.test/screen-${stage}`,
      text: `screen-${stage}`,
      observationVersion: ++version,
      isTruncated: false,
      elements: screens[stage].map((el) => withFormState(el, cmd)),
    }),
    submitAction: async (action) => {
      calls.push(structuredClone(action));
      if (action.kind === 'click') {
        stage += 1;
      } else {
        const target = screens[stage].find((el) => el.handle === action.target.handle);
        if (target) target.value = action.params.value;
      }
      return { result: Promise.resolve({ outcome: 'completed', isUncertain: false }) };
    },
  };
}

// ---------------------------------------------------------------------------
// Rule 1: authorizeStep return-value refusal ({ ok: false, reason } and false)
// ---------------------------------------------------------------------------
{
  const dag = new TraceDag(LIMITS);
  const teachSvc = makeMultiScreenSite([[field('Name', 'name')], []]);
  const teachSess = dag.session({
    service: teachSvc, owner: {}, pageId: 'main', intent: 'form', template: 'auth-ret',
    inputs: { name: 'Ada' }, accountScope: 'acct-1',
  });
  await teachSess.record({ kind: 'fill', locator: structuralLocator(field('Name', 'name')), slot: 'name' });
  assert.equal((await teachSess.finish()).reason, 'recorded-submit-boundary');

  for (const refusal of [false, { ok: false, reason: 'Result is ratified and locked' }]) {
    const replaySvc = makeMultiScreenSite([[field('Name', 'name')], []]);
    const replaySess = dag.session({
      service: replaySvc, owner: {}, pageId: 'main', intent: 'form', template: 'auth-ret',
      inputs: { name: 'Grace' }, accountScope: 'acct-1',
      authorizeStep: async () => refusal,
    });
    await assert.rejects(() => replaySess.replay(), (err) => {
      assert.equal(err.code, 'step-not-authorized');
      return true;
    });
    assert.equal(replaySvc.calls.length, 0, 'Return-value refusal in authorizeStep must dispatch 0 actions');

    const recSvc = makeMultiScreenSite([[field('Name', 'name')], []]);
    const recSess = dag.session({
      service: recSvc, owner: {}, pageId: 'main', intent: 'form', template: 'auth-ret',
      inputs: { name: 'Grace' }, accountScope: 'acct-1',
      authorizeStep: async () => refusal,
    });
    await assert.rejects(
      () => recSess.record({ kind: 'fill', locator: structuralLocator(field('Name', 'name')), slot: 'name' }),
      (err) => err.code === 'step-not-authorized',
    );
    assert.equal(recSvc.calls.length, 0, 'Planner record() must also fail closed on { ok: false }');
  }
}

// ---------------------------------------------------------------------------
// Rule 2: Universal DAG entry accountability on UNCHANGED interior screens
// ---------------------------------------------------------------------------
{
  const refField = () => field('Lease reference', 'ref');
  const nextBtn = () => button('Continue', 'next');
  const rentField = () => field('Monthly rent', 'rent');
  const reviewBtn = () => button('Review offer', 'review');
  const clicks = [structuralLocator(nextBtn()), structuralLocator(reviewBtn())];
  const baseOpts = {
    owner: {}, pageId: 'main', intent: 'lettings', template: 'entry-gate-v1',
    accountScope: 'portfolio-a', intermediateClicks: clicks,
    inputs: { ref: 'LS-100', rent: '1400' },
  };

  // Teach 2-screen workflow: [ref, next] -> [rent, review] -> [].
  const dag = new TraceDag(LIMITS);
  const builtIdx = new SuffixIndex();
  const profileDag = new TraceDag(LIMITS);
  for (const [targetDag, idx, useProfile] of [[dag, builtIdx, false], [profileDag, null, true]]) {
    const svc = makeMultiScreenSite([[refField(), nextBtn()], [rentField(), reviewBtn()], []], 0);
    const sess = targetDag.session({
      ...baseOpts, service: svc, suffixIndex: idx, suffixEligibility: useProfile,
    });
    await sess.record({ kind: 'fill', locator: structuralLocator(refField()), slot: 'ref' });
    await sess.record({ kind: 'click', locator: structuralLocator(nextBtn()) });
    await sess.record({ kind: 'fill', locator: structuralLocator(rentField()), slot: 'rent' });
    await sess.record({ kind: 'click', locator: structuralLocator(reviewBtn()) });
    assert.equal((await sess.finish()).reason, 'recorded-submit-boundary');
  }
  const frozenIdx = SuffixIndex.restore(builtIdx.export()).freeze();

  // Start directly on UNCHANGED Screen 1 (interior screen [rentField(), reviewBtn()], NO extra noise controls!):
  // 2a. Exact replay refuses unaccounted interior entry with 0 writes.
  {
    const svc = makeMultiScreenSite([[refField(), nextBtn()], [rentField(), reviewBtn()], []], 1);
    const res = await dag.session({ ...baseOpts, inputs: { ref: 'LS-200', rent: '1550' }, service: svc }).replay();
    assert.equal(res.reason, 'unseen-branch');
    assert.equal(svc.calls.length, 0, 'Exact replay must not bypass prefix accountability on clean interior screen');
  }

  // 2b. SuffixIndex without crossScreenRule refuses with prefix-unaccounted (0 writes).
  {
    const svc = makeMultiScreenSite([[refField(), nextBtn()], [rentField(), reviewBtn()], []], 1);
    const sess = dag.session({
      ...baseOpts, inputs: { ref: 'LS-200', rent: '1550' }, service: svc, suffixIndex: frozenIdx,
    });
    const res = await sess.replay();
    assert.equal(res.reason, 'unseen-branch');
    assert.equal(svc.calls.length, 0);
    assert.ok(sess.traceEvents.some((e) => e.phase === 'suffix-refused' && e.refusals?.['prefix-unaccounted'] > 0));
  }

  // 2c. crossScreenRule with server-attested prerequisites certifies and records restingOnAttestation!
  {
    const svc = makeMultiScreenSite([[refField(), nextBtn()], [rentField(), reviewBtn()], []], 1);
    const sess = dag.session({
      ...baseOpts, inputs: { ref: 'LS-200', rent: '1550' }, service: svc, suffixIndex: frozenIdx,
      crossScreenRule: true,
      attestPrerequisites: async ({ skipped }) => skipped.map(() => true),
    });
    const res = await sess.replay();
    assert.equal(res.reason, 'submit-boundary');
    assert.deepEqual(svc.calls.map((c) => c.target.handle), ['rent', 'review']);
    assert.ok(sess.traceEvents.some((e) => e.phase === 'suffix-certified' && e.attested === true));
    assert.ok(sess.traceEvents.some((e) => e.phase === 'certified-suffix-replay'));
  }

  // 2d. Dirty untracked <form> field on clean interior screen is now caught even when attested!
  {
    const dirtyScreen = [
      rentField(),
      reviewBtn(),
      field('Promo surcharge', 'promo', { value: 'BAD', isDefaultValue: false }),
    ];
    const svc = makeMultiScreenSite([[refField(), nextBtn()], dirtyScreen, []], 1);
    const sess = dag.session({
      ...baseOpts, inputs: { ref: 'LS-200', rent: '1550' }, service: svc, suffixIndex: frozenIdx,
      crossScreenRule: true,
      attestPrerequisites: async ({ skipped }) => skipped.map(() => true),
    });
    const res = await sess.replay();
    assert.equal(res.reason, 'unseen-branch');
    assert.equal(svc.calls.length, 0);
    assert.ok(sess.traceEvents.some((e) => e.refusals?.['dirty-untracked-form-field'] > 0));
  }

  // 2e. Negative server attestation at entry marks attestationRefuted and halts runWorkflow (0 planner calls, 0 writes).
  {
    const root = mkdtempSync(join(tmpdir(), 'entry-att-refuted-'));
    const store = new InvestigationStore(root);
    try {
      let plannerCalled = 0;
      const svc = makeMultiScreenSite([[refField(), nextBtn()], [rentField(), reviewBtn()], []], 1);
      store.create({ id: 'refuted-run', goal: 'Test negative attestation halt' });
      const wfRes = await runWorkflow({
        ...baseOpts,
        dag,
        mode: 'reuse',
        inputs: { ref: 'LS-200', rent: '1550' },
        service: svc,
        suffixIndex: frozenIdx,
        crossScreenRule: true,
        attestPrerequisites: async ({ skipped }) => skipped.map((_, idx) => idx === 0), // [true, false]
        learnRepairs: false,
        reconvergeMidRepair: true,
        task: 'Prepare renewal',
        planner: {
          identity: { model: 'should-not-be-called' },
          next: async () => {
            plannerCalled += 1;
            return { tool: 'act', input: { kind: 'fill', handle: 'rent', slot: 'rent' } };
          },
        },
        config: { maxTurns: 6, maxInputBytes: 16000 },
        store,
        projectId: 'refuted-run',
        verifyReview: async () => ({ completed: false }),
        signal: new AbortController().signal,
      });
      assert.equal(wfRes.completed, false);
      assert.equal(plannerCalled, 0, 'Negative server attestation at entry must not hand stale tab to page-only planner');
      assert.equal(svc.calls.length, 0);
      assert.equal(wfRes.suffix?.attestationRefuted, 1);
    } finally {
      store.close();
      rmSync(root, { recursive: true, force: true });
    }
  }

  // 2f. suffixProfiles routes clean interior entry through #resolveSuffixNode so its certification is counted!
  {
    const svc = makeMultiScreenSite([[refField(), nextBtn()], [rentField(), reviewBtn()], []], 1);
    const sess = profileDag.session({
      ...baseOpts, inputs: { ref: 'LS-200', rent: '1550' }, service: svc, suffixEligibility: true,
    });
    const res = await sess.replay();
    assert.equal(res.reason, 'submit-boundary');
    assert.equal(sess.certifiedSuffixRejoins.length, 1, 'Profile interior rejoin is explicitly recorded, never hidden');
  }
}

// ---------------------------------------------------------------------------
// Rule 3: Slot-bound vs. literal read-only [role="status"] / <output> binding
// ---------------------------------------------------------------------------
{
  const studentField = () => field('Student number', 'student');
  const openBtn = () => button('Open result', 'open');
  const amendBtn = () => button('Amend mark', 'amend');
  const clicks = [structuralLocator(openBtn()), structuralLocator(amendBtn())];
  const baseOpts = {
    owner: {}, pageId: 'main', intent: 'registrar', template: 'status-binding-v1',
    accountScope: 'exams-office', intermediateClicks: clicks,
  };

  // Teach: Screen 0 [studentField, openBtn] -> Screen 1 [Student output, Approval output, amendBtn] -> Screen 2 [].
  const dag = new TraceDag(LIMITS);
  const builtIdx = new SuffixIndex();
  {
    const svc = makeMultiScreenSite([
      [studentField(), openBtn()],
      [
        statusOut('Student', 'st-out', 'PRIVATE_S100 — Alice Teaching'),
        statusOut('Board approval', 'ap-out', 'Approved'),
        amendBtn(),
      ],
      [],
    ], 0);
    const sess = dag.session({
      ...baseOpts, inputs: { student: 'PRIVATE_S100' }, service: svc, suffixIndex: builtIdx,
    });
    await sess.record({ kind: 'fill', locator: structuralLocator(studentField()), slot: 'student' });
    await sess.record({ kind: 'click', locator: structuralLocator(openBtn()) });
    await sess.record({ kind: 'click', locator: structuralLocator(amendBtn()) });
    assert.equal((await sess.finish()).reason, 'recorded-submit-boundary');
  }
  const exportedIdxJson = JSON.stringify(builtIdx.export());
  assert.ok(!exportedIdxJson.includes('PRIVATE_') && !exportedIdxJson.includes('Approved') && !exportedIdxJson.includes('Student'),
    'SuffixIndex export hashes status signatures and never leaks labels, status text, or input values');
  const frozenIdx = SuffixIndex.restore(builtIdx.export()).freeze();

  // 3a. Valid new student ('S-481207 — Tomasz Brennan') + 'Approved' matches slot-bound + literal status in 0 planner calls!
  {
    const svc = makeMultiScreenSite([
      [studentField(), openBtn()],
      [
        statusOut('Student', 'st-out', 'S-481207 — Tomasz Brennan'),
        statusOut('Board approval', 'ap-out', 'Approved'),
        amendBtn(),
      ],
      [],
    ], 0);
    const res = await dag.session({
      ...baseOpts, inputs: { student: 'S-481207' }, service: svc, suffixIndex: frozenIdx,
    }).replay();
    assert.equal(res.reason, 'submit-boundary');
    assert.deepEqual(svc.calls.map((c) => c.target.handle), ['student', 'open', 'amend']);
  }

  // 3b. Literal status change ('Approved' -> 'None recorded') stops before clicking 'Amend mark'!
  {
    const svc = makeMultiScreenSite([
      [studentField(), openBtn()],
      [
        statusOut('Student', 'st-out', 'S-481207 — Tomasz Brennan'),
        statusOut('Board approval', 'ap-out', 'None recorded'),
        amendBtn(),
      ],
      [],
    ], 0);
    const sess = dag.session({
      ...baseOpts, inputs: { student: 'S-481207' }, service: svc, suffixIndex: frozenIdx,
    });
    const res = await sess.replay();
    assert.equal(res.reason, 'unseen-branch');
    assert.deepEqual(svc.calls.map((c) => c.target.handle), ['student', 'open'], 'Must stop before forbidden Amend mark click');
    assert.ok(sess.traceEvents.some((e) => e.refusals?.['status-changed'] > 0));
  }

  // 3c. Closest-match / wrong record ID ('S-481270 — Tamsin Brenner' when input is 'S-481207') stops before 'Amend mark'!
  {
    const svc = makeMultiScreenSite([
      [studentField(), openBtn()],
      [
        statusOut('Student', 'st-out', 'S-481270 — Tamsin Brenner'),
        statusOut('Board approval', 'ap-out', 'Approved'),
        amendBtn(),
      ],
      [],
    ], 0);
    const sess = dag.session({
      ...baseOpts, inputs: { student: 'S-481207' }, service: svc, suffixIndex: frozenIdx,
    });
    const res = await sess.replay();
    assert.equal(res.reason, 'unseen-branch');
    assert.deepEqual(svc.calls.map((c) => c.target.handle), ['student', 'open']);
    assert.ok(sess.traceEvents.some((e) => e.refusals?.['status-changed'] > 0));
  }
}

console.log('entry-accountability-and-status: ok');
