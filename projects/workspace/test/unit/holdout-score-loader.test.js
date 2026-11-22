import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { mkdtempSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import {
  normalizeHoldoutElement,
  normalizeHoldoutLocator,
  normalizeHoldoutPlanner,
  normalizeHoldoutService,
  normalizeHoldoutWorkflow,
  scoreHoldout,
} from '../../qualification/workflow-generalization/holdout-score.mjs';

// 1. Locator normalization touches null inputType (index 3) and nothing else.
assert.deepEqual(normalizeHoldoutLocator(['button', 'Continue', 'button', null]), ['button', 'Continue', 'button', '']);
assert.deepEqual(normalizeHoldoutLocator(['textbox', 'Name', 'input', 'text']), ['textbox', 'Name', 'input', 'text']);
assert.deepEqual(normalizeHoldoutLocator(['button', 'Continue', 'button', '']), ['button', 'Continue', 'button', '']);
assert.deepEqual(normalizeHoldoutLocator(['button', 'Continue', 'button', undefined]), ['button', 'Continue', 'button', undefined]);
assert.deepEqual(normalizeHoldoutLocator(['button', null, 'button', null]), ['button', null, 'button', '']);
assert.deepEqual(normalizeHoldoutLocator([null, 'Continue', 'button', '']), [null, 'Continue', 'button', '']);
assert.deepEqual(normalizeHoldoutLocator(['button', 'Continue', null, '']), ['button', 'Continue', null, '']);

// 2. Element normalization touches null inputType and leaves formKey/value/other fields untouched.
const rawButton = {
  role: 'button', label: 'Continue', tag: 'button', inputType: null,
  handle: 'h-1', selector: '#continue', digest: 'd-1', value: null, text: 'Continue',
  actionability: { visible: true, inert: false, disabled: false }, formKey: null, isDefaultValue: true,
};
const normButton = normalizeHoldoutElement(rawButton);
assert.equal(normButton.inputType, '');
assert.equal(normButton.formKey, null);
assert.equal(normButton.value, null);
assert.equal(rawButton.inputType, null, 'source element must not be mutated');

const rawInput = { ...rawButton, role: 'textbox', tag: 'input', inputType: 'text', value: '' };
assert.equal(normalizeHoldoutElement(rawInput), rawInput, 'non-null inputType element passes through unchanged');

// 3. Service wrapper normalizes observe() elements uniformly and preserves other methods.
const wrapped = normalizeHoldoutService({
  tag: 'svc',
  outstanding() { return [this.tag]; },
  async observe() { return { url: 'https://fixture.invalid/step1', text: 's1', observationVersion: 1, isTruncated: false, elements: [rawButton, rawInput] }; },
  async submitAction(cmd) { return { result: Promise.resolve({ outcome: 'completed', seen: cmd.kind }) }; },
});
assert.deepEqual(wrapped.outstanding(), ['svc']);
const obs = await wrapped.observe({});
assert.equal(obs.elements[0].inputType, '');
assert.equal(obs.elements[0].formKey, null);
assert.equal(obs.elements[1].inputType, 'text');

// 4. Workflow normalization covers both observationLocators and intermediateClicks.
const wf = normalizeHoldoutWorkflow({
  id: 'wf',
  intermediateClicks: [['button', 'Continue', 'button', null]],
  observationLocators: [['textbox', 'Name', 'input', 'text'], ['button', 'Continue', 'button', null], ['status', 'Review', 'output', null]],
});
assert.deepEqual(wf.intermediateClicks, [['button', 'Continue', 'button', '']]);
assert.deepEqual(wf.observationLocators, [
  ['textbox', 'Name', 'input', 'text'],
  ['button', 'Continue', 'button', ''],
  ['status', 'Review', 'output', ''],
]);

// 4b. Planner wrapper passes normalized 4-tuple intermediateClicks to the holdout planner stub.
let seenAllowed = null;
const wrappedPlanner = normalizeHoldoutPlanner({
  identity: { model: 'stub' },
  async next(ctx) { seenAllowed = ctx.allowedIntermediateClicks; return { tool: 'finish', input: { summary: 'ok' } }; },
}, wf.intermediateClicks);
await wrappedPlanner.next({ allowedIntermediateClicks: ['Continue'] });
assert.deepEqual(seenAllowed, [['button', 'Continue', 'button', '']]);

// 5. End-to-end scoreHoldout on a synthetic holdout with null inputType and 4-tuple allowedIntermediateClicks.
const sha = text => createHash('sha256').update(text, 'utf8').digest('hex');
function makeFixtureSource({ badLabelNull = false } = {}) {
  return `
function makeHost(inputs, { startStep = 1 } = {}) {
  let screen = startStep === 1 ? 'form' : 'review';
  let value = startStep === 1 ? '' : inputs.name;
  let version = 0;
  const applied = [];
  const elements = () => screen === 'form' ? [
    { role: 'textbox', label: 'Name', tag: 'input', inputType: 'text', handle: 'h-name', selector: '#name', digest: 'd-name-' + value, value, text: '', actionability: { visible: true, inert: false, disabled: false }, formKey: 'f1', isDefaultValue: value === '' },
    { role: 'button', label: 'Continue', tag: 'button', inputType: null, handle: 'h-go', selector: '#go', digest: 'd-go', value: null, text: 'Continue', actionability: { visible: true, inert: false, disabled: false }, formKey: null, isDefaultValue: true },
  ] : [
    { role: 'status', label: 'Summary', tag: 'output', inputType: null, handle: 'h-sum', selector: '#sum', digest: 'd-sum-' + value, value: null, text: value, actionability: { visible: true, inert: false, disabled: false }, formKey: null, isDefaultValue: true },
  ];
  return {
    service: {
      async observe() {
        return { url: 'https://fixture.invalid/' + screen, text: screen + ':' + value, observationVersion: ++version, isTruncated: false, elements: elements() };
      },
      outstanding() { return []; },
      async submitAction(cmd) {
        if (cmd.kind === 'fill' && cmd.target.handle === 'h-name') {
          value = cmd.params.value;
          applied.push({ kind: 'fill', handle: cmd.target.handle, value, forbidden: false });
        } else if (cmd.kind === 'click' && cmd.target.handle === 'h-go') {
          screen = 'review';
          applied.push({ kind: 'click', handle: cmd.target.handle, value: null, forbidden: false });
        }
        return { result: Promise.resolve({ outcome: 'completed' }) };
      },
    },
    planner: {
      identity: { model: 'regression-stub' },
      async next({ observation, allowedIntermediateClicks }) {
        if (observation.elements.some(e => e.role === 'status' && e.label === 'Summary')) {
          return { tool: 'finish', input: { summary: 'done' } };
        }
        const nameEl = observation.elements.find(e => e.label === 'Name');
        if (nameEl && !nameEl.value) return { tool: 'act', input: { kind: 'fill', handle: nameEl.handle, slot: 'name' } };
        const allowedKeys = new Set((allowedIntermediateClicks || []).map(t => Array.isArray(t) ? t.join('|') : ''));
        const goEl = observation.elements.find(e => allowedKeys.has([e.role, e.label, e.tag, e.inputType].join('|')));
        if (goEl) return { tool: 'act', input: { kind: 'click', handle: goEl.handle } };
        return { tool: 'ask_human', input: { reason: 'no-unique-intermediate-button' } };
      },
    },
    verifyReview: async () => ({ completed: screen === 'review' && value === inputs.name }),
    assertContext: async () => {},
    authorizeStep: null,
    assertPrerequisite: null,
    attestPrerequisites: null,
    writes: () => applied,
    expected: { complete: true, review: { Summary: inputs.name }, allowedWrites: 'toward-task' },
  };
}
export const workflows = [{
  id: 'loader-null-input-type',
  template: 'loader:test',
  goal: 'Fill name and continue to review',
  intent: 'loader:prepare',
  accountScope: 'acct/test',
  inputs: { teach: { name: 'Alpha' }, run: { name: 'Beta' } },
  intermediateClicks: [['button', ${badLabelNull ? 'null' : "'Continue'"}, 'button', null]],
  observationLocators: [
    ['textbox', 'Name', 'input', 'text'],
    ['button', ${badLabelNull ? 'null' : "'Continue'"}, 'button', null],
    ['status', 'Summary', 'output', null],
  ],
  teach: () => makeHost({ name: 'Alpha' }),
  cases: [{
    id: 'same-flow-null-input-type',
    kind: 'must-complete',
    hostHasWriteCheck: false,
    describes: 'Same flow with null inputType on button and status elements',
    build: () => makeHost({ name: 'Beta' }),
  }],
}];
`;
}

const dir = mkdtempSync(join(tmpdir(), 'holdout-loader-test-'));
try {
  const casesSrc = makeFixtureSource();
  writeFileSync(join(dir, 'cases.mjs'), casesSrc);
  writeFileSync(join(dir, 'SHA256SUMS'), `${sha(casesSrc)}  cases.mjs\n`);
  const outFile = join(dir, 'out.json');
  const receipt = await scoreHoldout(dir, outFile);
  assert.equal(receipt.teaching.length, 5);
  assert.ok(receipt.teaching.every(entry => entry.completed === true));
  assert.equal(receipt.rows.length, 5);
  assert.ok(receipt.rows.every(row => row.completed === true && row.forbiddenWrites === 0 && row.declaredReview === true));
  assert.equal(JSON.parse(readFileSync(outFile, 'utf8')).summary.exact.completed, 1);

  // Checksum tamper must still fail closed.
  writeFileSync(join(dir, 'SHA256SUMS'), `${'0'.repeat(64)}  cases.mjs\n`);
  await assert.rejects(() => scoreHoldout(dir), /does not match its pin/);

  // Null in a field other than inputType (label) must still fail closed in scopeWorkflowObservation.
  const badDir = mkdtempSync(join(tmpdir(), 'holdout-loader-bad-'));
  try {
    const badSrc = makeFixtureSource({ badLabelNull: true });
    writeFileSync(join(badDir, 'cases.mjs'), badSrc);
    writeFileSync(join(badDir, 'SHA256SUMS'), `${sha(badSrc)}  cases.mjs\n`);
    await assert.rejects(() => scoreHoldout(badDir), /Invalid workflow observation scope/);
  } finally {
    rmSync(badDir, { recursive: true, force: true });
  }
} finally {
  rmSync(dir, { recursive: true, force: true });
}

console.log('holdout-score-loader: ok');
