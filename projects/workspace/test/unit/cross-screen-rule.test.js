// cross-screen-rule.md: a run may continue past steps it did not take only when each is carried,
// settled, or attested by the host. These tests drive TraceSession directly.
import assert from 'node:assert/strict';
import { TraceDag } from '../../src/client/trace-dag.js';
import { SuffixIndex } from '../../src/client/suffix-eligibility.js';
import { structuralLocator } from '../../src/adapters/page-query.js';

const limits = { maxNodes: 32, maxEdges: 32, maxSteps: 8 };
const field = (label, id, extra = {}) => ({ label, role: 'textbox', tag: 'input', inputType: 'text', selector: `#${id}`,
  handle: id, digest: `digest-${id}`, value: '', ...extra });
const button = (label, id) => ({ label, role: 'button', tag: 'button', inputType: '', selector: `#${id}`, handle: id,
  digest: `digest-${id}`, value: null });
const name = () => field('Name', 'name'), city = () => field('City', 'city'), zip = () => field('Postcode', 'zip');
const next = () => button('Continue', 'continue'), help = () => button('Help', 'help');
// The second screen needs enough familiar controls for an added one to stay within the overlap policy.
const chrome = () => [button('Terms', 'terms'), button('Privacy', 'privacy')];
const inputs = { name: 'PRIVATE_NAME', city: 'PRIVATE_CITY', zip: 'PRIVATE_ZIP' };
const base = { owner: { workspaceId: 'test' }, pageId: 'main', intent: 'form', template: 'cross-unit', inputs,
  accountScope: 'account-a', intermediateClicks: [structuralLocator(next())] };
const fill = (element, slot) => ({ kind: 'fill', locator: structuralLocator(element), slot });
const withFormState = (element, command) => (command?.includeFormState
  ? { formKey: '#form', isDefaultValue: !element.value, ...structuredClone(element) } : structuredClone(element));

/** Screens are lists of controls; a click moves to the next screen. */
function site(screens, start = 0) {
  let stage = start, version = 0;
  const calls = [];
  return { calls, outstanding: async () => [],
    observe: async command => ({ url: `https://fixture.invalid/step-${stage}`, observationVersion: ++version, isTruncated: false,
      elements: screens[stage].map(element => withFormState(element, command)) }),
    submitAction: async action => {
      calls.push(action);
      if (action.kind === 'click') stage += 1;
      else screens[stage].find(element => element.handle === action.target.handle).value = action.params.value;
      return { result: Promise.resolve({ outcome: 'completed' }) };
    } };
}
const handles = service => service.calls.map(call => call.target.handle);
const certified = session => session.traceEvents.filter(event => event.phase === 'suffix-certified');
const refusedFor = (session, reason) => session.traceEvents.some(event => event.phase === 'suffix-refused'
  && (event.reason === reason || event.refusals?.[reason] > 0));

// Teach two screens: fill Name, Continue, then fill City.
const dag = new TraceDag(limits), built = new SuffixIndex();
{
  const session = dag.session({ ...base, service: site([[name(), next()], [city(), ...chrome()]]), suffixIndex: built });
  await session.record(fill(name(), 'name'));
  await session.record({ kind: 'click', locator: structuralLocator(next()) });
  await session.record(fill(city(), 'city'));
  assert.equal((await session.finish()).reason, 'recorded-submit-boundary');
}
const index = SuffixIndex.restore(built.export()).freeze();
// A run that starts on the second screen, with an extra control so the exact hash misses.
const laterScreen = () => site([[name(), next()], [city(), ...chrome(), help()]], 1);
const run = async (options, service = laterScreen()) => {
  const session = dag.session({ ...base, service, suffixIndex: index, ...options });
  const outcome = await session.replay();
  return { session, service, outcome };
};
const both = async ({ skipped }) => skipped.map(() => true);

// Without the rule, or with the rule and no host attestation, the later screen is refused.
for (const options of [{}, { crossScreenRule: true }, { attestPrerequisites: both }]) {
  const { session, service, outcome } = await run(options);
  assert.equal(outcome.reason, 'unseen-branch');
  assert.equal(service.calls.length, 0);
  assert.ok(refusedFor(session, 'prefix-unaccounted'));
}

// With the rule and a host that attests both skipped steps, the run continues and says so.
{
  const seen = [];
  const { session, service, outcome } = await run({ crossScreenRule: true,
    attestPrerequisites: async request => { seen.push(structuredClone(request)); return request.skipped.map(() => true); } });
  assert.equal(outcome.reason, 'submit-boundary');
  assert.deepEqual(handles(service), ['city']);
  // The entry state and the review state are each certified, and each rests on attestation.
  assert.ok(certified(session).length >= 1);
  assert.ok(certified(session).every(event => event.attested === true), 'A certification records that it rests on attestation');
  // Asked in the host's terms: slot names and the host's own click locator, never page content.
  assert.ok(seen.length >= 1);
  for (const request of seen) {
    assert.deepEqual(Object.keys(request).sort(), ['origin', 'skipped', 'url']);
    assert.equal(request.origin, 'https://fixture.invalid');
    assert.ok(request.skipped.some(step => step.kind === 'fill' && step.slot === 'name' && step.locator === null));
    assert.ok(request.skipped.some(step => step.kind === 'click' && step.slot === null
      && JSON.stringify(step.locator) === JSON.stringify(structuralLocator(next()))));
    assert.ok(!JSON.stringify(request).includes('PRIVATE_'), 'No input value is sent to the host');
  }
}

// One skipped step not attested is enough to refuse. So is any answer that is not one boolean per step.
const refusing = [
  async ({ skipped }) => skipped.map(step => step.kind === 'click'),
  async ({ skipped }) => skipped.map(step => step.kind !== 'click'),
  async () => true,
  async ({ skipped }) => skipped.map(() => 'yes'),
  async ({ skipped }) => skipped.slice(1).map(() => true),
  async () => { throw Error('host read failed'); },
];
for (const attestPrerequisites of refusing) {
  const { session, service, outcome } = await run({ crossScreenRule: true, attestPrerequisites });
  assert.equal(outcome.reason, 'unseen-branch');
  assert.equal(service.calls.length, 0, 'Nothing is written without a full attestation');
  assert.equal(certified(session).length, 0);
}

// A click the host did not list cannot be asked about, so it is never attested.
{
  const { service, outcome } = await run({ crossScreenRule: true, attestPrerequisites: both, intermediateClicks: [] });
  assert.equal(outcome.reason, 'unseen-branch');
  assert.equal(service.calls.length, 0);
}

// Attestation accounts for skipped steps only. Scope, form state and the dirty-field guard still refuse.
{
  const other = await run({ crossScreenRule: true, attestPrerequisites: both, accountScope: 'account-b' });
  assert.equal(other.outcome.reason, 'unseen-branch');
  assert.equal(other.service.calls.length, 0, 'Another account never borrows the graph, attested or not');

  const dirty = site([[name(), next()], [city(), ...chrome(), help(), field('Promo code', 'promo', { value: 'VIP99', isDefaultValue: false })]], 1);
  const dirtyRun = await run({ crossScreenRule: true, attestPrerequisites: both }, dirty);
  assert.equal(dirtyRun.outcome.reason, 'unseen-branch');
  assert.equal(dirty.calls.length, 0);
  assert.ok(refusedFor(dirtyRun.session, 'dirty-untracked-form-field'));

  const blind = laterScreen();
  blind.observe = (inner => async () => inner(null))(blind.observe);
  const blindRun = await run({ crossScreenRule: true, attestPrerequisites: both }, blind);
  assert.equal(blind.calls.length, 0);
  assert.ok(refusedFor(blindRun.session, 'form-state-unavailable'));
}

// Asked afresh for every frame it judges.
{
  let asked = 0;
  const { session } = await run({ crossScreenRule: true, attestPrerequisites: async ({ skipped }) => { asked += 1; return skipped.map(() => true); } });
  assert.equal(asked, session.traceEvents.filter(event => event.phase.startsWith('suffix-')).length);
}

// Clause 4. Teach Name, Continue, then City and Postcode. On a changed second screen where City is
// already present, the run stops after the click without the rule and finishes with it.
const flat = new TraceDag(limits), flatBuilt = new SuffixIndex();
{
  const session = flat.session({ ...base, service: site([[name(), next()], [city(), zip(), ...chrome()]]), suffixIndex: flatBuilt });
  await session.record(fill(name(), 'name'));
  await session.record({ kind: 'click', locator: structuralLocator(next()) });
  await session.record(fill(city(), 'city'));
  await session.record(fill(zip(), 'zip'));
  assert.equal((await session.finish()).reason, 'recorded-submit-boundary');
}
const flatIndex = SuffixIndex.restore(flatBuilt.export()).freeze();
const prefilled = value => site([[name(), next()], [field('City', 'city', { value }), zip(), ...chrome(), help()]]);
{
  const without = prefilled('PRIVATE_CITY');
  const stopped = flat.session({ ...base, service: without, suffixIndex: flatIndex });
  assert.equal((await stopped.replay()).reason, 'unseen-branch');
  assert.deepEqual(handles(without), ['name', 'continue'], 'Without the rule the run stops at the field that is already filled');
  assert.ok(refusedFor(stopped, 'pending-fill-already-done'));

  const withRule = prefilled('PRIVATE_CITY');
  const finished = flat.session({ ...base, service: withRule, suffixIndex: flatIndex, crossScreenRule: true });
  assert.equal((await finished.replay()).reason, 'submit-boundary');
  assert.deepEqual(handles(withRule), ['name', 'continue', 'zip'], 'The settled field is not written again');
  assert.ok(certified(finished).length >= 1 && certified(finished).every(event => !event.attested), 'No attestation was needed or used');
}
// A field holding another value is not settled, so clause 4 does not skip it: the learned fill runs.
{
  const wrong = prefilled('SOMEONE_ELSE');
  const session = flat.session({ ...base, service: wrong, suffixIndex: flatIndex, crossScreenRule: true });
  assert.equal((await session.replay()).reason, 'submit-boundary');
  assert.deepEqual(handles(wrong), ['name', 'continue', 'city', 'zip']);
}
console.log('cross-screen-rule: ok');
