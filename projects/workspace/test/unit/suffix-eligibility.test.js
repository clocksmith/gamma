import assert from 'node:assert/strict';
import { TraceDag } from '../../src/client/trace-dag.js';
import { SuffixIndex, certifySuffix, labelsCompete } from '../../src/client/suffix-eligibility.js';
import { scopeWorkflowObservation } from '../../src/client/workflow-agent.js';
import { structuralLocator } from '../../src/adapters/page-query.js';

const limits = { maxNodes: 32, maxEdges: 32, maxSteps: 8 };
const control = (label, id, extra = {}) => ({ label, role: 'textbox', tag: 'input', inputType: 'text',
  selector: `#${id}`, handle: id, digest: `digest-${id}`, value: '', ...extra });
const button = (label, id) => ({ label, role: 'button', tag: 'button', inputType: '', selector: `#${id}`,
  handle: id, digest: `digest-${id}`, value: null });
const name = () => control('Name', 'name'), city = () => control('City', 'city');
const inputs = { name: 'PRIVATE_NAME', city: 'PRIVATE_CITY' };
const base = { owner: { workspaceId: 'test' }, pageId: 'main', intent: 'form', template: 'unit-form', inputs };
const fill = (element, slot) => ({ kind: 'fill', locator: structuralLocator(element), slot });

/** What a host adds to a control when an observation is requested with form state. */
const withFormState = (element, command) => (command?.includeFormState ? { ...structuredClone(element),
  formKey: element.formKey === undefined ? '#form' : element.formKey,
  isDefaultValue: element.isDefaultValue ?? !element.value } : structuredClone(element));

/** Stateful page: fills settle their value, so a later observation shows them. Form state is
 * returned only when the command asks for it, unless the host is told never to return it. */
function page(elements, { formState = true } = {}) {
  let version = 0;
  const calls = [], commands = [];
  return { calls, commands, elements, outstanding: async () => [],
    observe: async command => {
      commands.push(command);
      return { url: 'https://fixture.invalid/form', observationVersion: ++version, isTruncated: false,
        elements: elements.map(element => withFormState(element, formState ? command : null)) };
    },
    submitAction: async action => {
      calls.push(action);
      const target = elements.find(element => element.handle === action.target.handle);
      if (action.kind !== 'click') target.value = action.params.value;
      return { result: Promise.resolve({ outcome: 'completed' }) };
    } };
}
async function learn(extra = []) {
  const dag = new TraceDag(limits), index = new SuffixIndex();
  const session = dag.session({ ...base, service: page([name(), city(), ...extra]), suffixIndex: index });
  assert.equal((await session.record(fill(name(), 'name'))).status, 'completed');
  assert.equal((await session.record(fill(city(), 'city'))).status, 'completed');
  assert.equal((await session.finish()).reason, 'recorded-submit-boundary');
  return { dag, index: SuffixIndex.restore(index.export()).freeze() };
}
const replay = (dag, service, options = {}) => dag.session({ ...base, service, ...options }).replay();
const handles = service => service.calls.map(call => call.target.handle);

assert.equal(labelsCompete('Email', 'Confirm email'), true);
assert.equal(labelsCompete('Email', 'Email address'), true);
assert.equal(labelsCompete('First name', 'Last name'), false);
assert.equal(labelsCompete('Current city', 'Name'), false);
assert.equal(labelsCompete('', 'Name'), true, 'An unlabelled control is never assumed unrelated');

const { dag, index } = await learn();
const frozenGraph = JSON.stringify(dag.export()), frozenIndex = JSON.stringify(index.export());
assert.ok(!frozenIndex.includes('PRIVATE_') && !frozenIndex.includes('Name'), 'The index holds no labels or values');

// Unchanged page: identical with and without the index.
for (const suffixIndex of [null, index]) {
  const service = page([name(), city()]);
  assert.equal((await replay(dag, service, { suffixIndex })).reason, 'submit-boundary');
  assert.deepEqual(handles(service), ['name', 'city']);
}

// An unrelated new control or a reordering misses the exact hash; suffix eligibility replays every step.
for (const elements of [[name(), city(), control('Referral code', 'referral')], [city(), name()],
  [button('Help', 'help'), name(), city()]]) {
  const without = page(structuredClone(elements));
  assert.equal((await replay(dag, without)).reason, 'unseen-branch');
  assert.equal(without.calls.length, 0);
  const service = page(structuredClone(elements));
  const session = dag.session({ ...base, service, suffixIndex: index });
  assert.equal((await session.replay()).reason, 'submit-boundary');
  assert.deepEqual(handles(service), ['name', 'city']);
  assert.equal(service.calls[0].params.value, 'PRIVATE_NAME');
  assert.ok(session.traceEvents.some(event => event.phase === 'suffix-certified'));
  assert.ok(session.traceEvents.every(event => event.phase !== 'suffix-refused'));
}

// Refusals: nothing is dispatched and the caller sees an ordinary cache miss.
const refusals = {
  'lookalike-added-control': [name(), city(), control('Confirm name', 'confirm')],
  'ambiguous-target': [name(), city(), control('Name', 'decoy')],
  'blocking-dialog': [name(), city(), { ...button('Session expired', 'modal'), role: 'dialog' }],
  'unlabelled-added-control': [name(), city(), control('', 'mystery')],
  'page-mismatch': [name(), button('A', 'a'), button('B', 'b'), button('C', 'c'), button('D', 'd')],
};
for (const [reason, elements] of Object.entries(refusals)) {
  const service = page(elements);
  const session = dag.session({ ...base, service, suffixIndex: index });
  assert.equal((await session.replay()).reason, 'unseen-branch', reason);
  assert.equal(service.calls.length, 0, `${reason} must dispatch nothing`);
  const refused = session.traceEvents.find(event => event.phase === 'suffix-refused');
  assert.ok(refused.reason === reason || refused.refusals[reason] > 0, `${reason}: ${JSON.stringify(refused)}`);
}

// A renamed target on an otherwise familiar page is a miss, not a guess.
const chrome = () => [button('Help', 'help'), button('Terms', 'terms'), button('Privacy', 'privacy')];
const larger = await learn(chrome());
const renamed = page([control('Legal name', 'name'), city(), ...chrome()]);
const renamedSession = larger.dag.session({ ...base, service: renamed, suffixIndex: larger.index });
assert.equal((await renamedSession.replay()).reason, 'unseen-branch');
assert.equal(renamed.calls.length, 0);
assert.ok(renamedSession.traceEvents.some(event => event.refusals?.['missing-target'] > 0));

// A different account never borrows another account's graph.
const other = page([name(), city(), control('Referral code', 'referral')]);
assert.equal((await replay(dag, other, { suffixIndex: index, accountScope: 'account-b' })).reason, 'unseen-branch');
assert.equal(other.calls.length, 0);

// A value already settled on the page is not written again; replay resumes after it.
const prefilled = page([name(), city(), control('Referral code', 'referral')]);
prefilled.elements[0].value = 'PRIVATE_NAME';
assert.equal((await replay(dag, prefilled, { suffixIndex: index })).reason, 'submit-boundary');
assert.deepEqual(handles(prefilled), ['city']);

// A wrong pre-existing value is not treated as settled, and it is not silently overwritten past the learned state.
const conflicting = page([name(), city(), control('Referral code', 'referral')]);
conflicting.elements[1].value = 'SOMEONE_ELSE';
const conflict = dag.session({ ...base, service: conflicting, suffixIndex: index });
assert.equal((await conflict.replay()).reason, 'submit-boundary');
assert.deepEqual(handles(conflicting), ['name', 'city'], 'Both learned fills still run from the learned start state');

// A missing input slot stops before any write.
const missing = page([name(), city(), control('Referral code', 'referral')]);
const noCity = dag.session({ ...base, inputs: { name: 'PRIVATE_NAME' }, service: missing, suffixIndex: index });
assert.notEqual((await noCity.replay()).reason, 'submit-boundary');
assert.ok(handles(missing).every(handle => handle !== 'city'));

// A click may not leave the page while a new question is unanswered.
const next = () => button('Continue', 'continue');
async function learnWithClick() {
  const graph = new TraceDag(limits), built = new SuffixIndex();
  let stage = 0;
  const first = [name(), next()], second = [city()];
  const service = { outstanding: async () => [], calls: [],
    observe: async command => ({ url: 'https://fixture.invalid/form', observationVersion: Date.now() + Math.random(),
      isTruncated: false, elements: (stage ? second : first).map(element => withFormState(element, command)) }),
    submitAction: async action => {
      const elements = stage ? second : first;
      if (action.kind === 'click') stage = 1;
      else elements.find(element => element.handle === action.target.handle).value = action.params.value;
      return { result: Promise.resolve({ outcome: 'completed' }) };
    } };
  const session = graph.session({ ...base, service, suffixIndex: built, intermediateClicks: [structuralLocator(next())] });
  await session.record(fill(name(), 'name'));
  await session.record({ kind: 'click', locator: structuralLocator(next()) });
  await session.record(fill(city(), 'city'));
  assert.equal((await session.finish()).reason, 'recorded-submit-boundary');
  return { graph, built: built.freeze() };
}
const { graph, built } = await learnWithClick();
const unanswered = page([name(), next(), control('Referral code', 'referral')]);
const stopped = graph.session({ ...base, service: unanswered, suffixIndex: built,
  intermediateClicks: [structuralLocator(next())] });
assert.equal((await stopped.replay()).reason, 'unseen-branch');
assert.deepEqual(handles(unanswered), ['name'], 'The fill is reused; the click waits for the planner');
assert.ok(stopped.traceEvents.some(event => event.refusals?.['unanswered-added-control'] > 0));

// Hidden state: the matcher cannot see a server-side prerequisite, so it may propose a step.
// The step-authorization gate runs after the proposal and before dispatch, and nothing is written.
for (const elements of [[name(), city()], [city(), name()]]) {
  const service = page(elements);
  const session = dag.session({ ...base, service, suffixIndex: index,
    authorizeStep: async () => { throw Error('Server prerequisite not met'); } });
  await assert.rejects(session.replay(), /prerequisite/);
  assert.equal(service.calls.length, 0, 'A refused prerequisite dispatches nothing');
  await assert.rejects(session.replay(), /stopped/, 'No implicit resume after a refusal');
  assert.equal(session.traceEvents.some(event => event.phase === 'suffix-certified'), elements[0].label === 'City',
    'On the reordered page the suffix matcher had proposed the step');
}

// Rule 1 (suffix-repair-rules.md). The index matcher asks for form state itself, with the profile
// matcher off, on every observation it judges.
const asked = page([city(), name()]);
assert.equal((await replay(dag, asked, { suffixIndex: index })).reason, 'submit-boundary');
assert.ok(asked.commands.length > 0 && asked.commands.every(command => command.includeFormState === true),
  'Every observation of an index session requests form state');
const plain = page([name(), city()]);
await replay(dag, plain);
assert.ok(plain.commands.every(command => command.includeFormState === undefined), 'No matcher, no form-state request');

// A host that returns no form state: the matcher refuses before any candidate, and nothing is dispatched.
const blind = page([city(), name()], { formState: false });
const blindSession = dag.session({ ...base, service: blind, suffixIndex: index });
assert.equal((await blindSession.replay()).reason, 'unseen-branch');
assert.equal(blind.calls.length, 0, 'No form state, no suffix write');
const blindRefusal = blindSession.traceEvents.find(event => event.phase === 'suffix-refused');
assert.equal(blindRefusal.reason, 'form-state-unavailable');
assert.deepEqual(blindRefusal.refusals, {}, 'Refused before any candidate was considered');
assert.ok(blindSession.traceEvents.every(event => event.phase !== 'suffix-certified'));

// One writable control without form state is enough to refuse.
const partial = page([city(), name(), control('Referral code', 'referral', { formKey: undefined, isDefaultValue: undefined })]);
partial.observe = (inner => async command => {
  const observation = await inner(command);
  for (const key of ['formKey', 'isDefaultValue']) delete observation.elements[2][key];
  return observation;
})(partial.observe);
const partialSession = dag.session({ ...base, service: partial, suffixIndex: index });
assert.equal((await partialSession.replay()).reason, 'unseen-branch');
assert.equal(partial.calls.length, 0);
assert.equal(partialSession.traceEvents.find(event => event.phase === 'suffix-refused').reason, 'form-state-unavailable');

// With form state established the dirty-field guard works with the index option alone: an untouched
// non-default control in the target form refuses, the same control in another form does not.
const dirty = page([city(), name(), control('Promo code', 'promo', { value: 'VIP99', isDefaultValue: false })]);
const dirtySession = dag.session({ ...base, service: dirty, suffixIndex: index });
assert.equal((await dirtySession.replay()).reason, 'unseen-branch');
assert.equal(dirty.calls.length, 0, 'A dirty untracked field in the target form dispatches nothing');
assert.ok(dirtySession.traceEvents.some(event => event.refusals?.['dirty-untracked-form-field'] > 0));
const elsewhere = page([city(), name(), control('Saved search', 'search', { value: 'old', isDefaultValue: false, formKey: '#header' })]);
assert.equal((await replay(dag, elsewhere, { suffixIndex: index })).reason, 'submit-boundary');
assert.deepEqual(handles(elsewhere), ['name', 'city']);

// The same guard when a host policy hides the dirty control from the planner: it is judged on the
// unfiltered view that the observation policy passes through.
{
  const hidden = page([city(), name(), control('Promo code', 'promo', { value: 'VIP99', isDefaultValue: false })]);
  const scoped = scopeWorkflowObservation(hidden, base.template, [structuralLocator(name()), structuralLocator(city())]);
  const taught = new TraceDag(limits), taughtIndex = new SuffixIndex();
  const teachPage = scopeWorkflowObservation(page([name(), city()]), base.template,
    [structuralLocator(name()), structuralLocator(city())]);
  const teacher = taught.session({ ...base, template: teachPage.template, service: teachPage.service, suffixIndex: taughtIndex });
  await teacher.record(fill(name(), 'name'));
  await teacher.record(fill(city(), 'city'));
  assert.equal((await teacher.finish()).reason, 'recorded-submit-boundary');
  const session = taught.session({ ...base, template: scoped.template, service: scoped.service,
    suffixIndex: SuffixIndex.restore(taughtIndex.export()).freeze() });
  assert.equal((await session.replay()).reason, 'unseen-branch');
  assert.equal(hidden.calls.length, 0, 'A dirty field the planner cannot see still refuses');
  assert.ok(session.traceEvents.some(event => event.refusals?.['dirty-untracked-form-field'] > 0));
}

// Fresh: a frame that is not the session's latest observation is refused.
{
  const service = page([city(), name()]);
  const session = dag.session({ ...base, service, suffixIndex: index });
  const frame = await session.observe();
  const args = { dag, index, dp: dag.solve({ inputs }), frame,
    session: { inputs: session.inputs, clicks: session.clicks, executedSteps: [], sameOutlineClicks: 0,
      isGoalTerminal: (id, node) => Boolean(node?.terminal) } };
  assert.equal(certifySuffix({ ...args, session: { ...args.session, formStateFresh: true } }).status, 'certified');
  const stale = certifySuffix({ ...args, session: { ...args.session, formStateFresh: false } });
  assert.equal(stale.status, 'refused');
  assert.equal(stale.reason, 'form-state-unavailable');
}

// The frozen graph and index never change during reuse.
assert.equal(JSON.stringify(dag.export()), frozenGraph);
assert.equal(JSON.stringify(index.export()), frozenIndex);
assert.throws(() => SuffixIndex.restore({ version: 1, nodes: [['not-a-hash', {}]] }), /Invalid suffix index/);
assert.throws(() => SuffixIndex.restore({ version: 2, nodes: [] }), /Invalid suffix index/);
console.log('suffix-eligibility: ok');
