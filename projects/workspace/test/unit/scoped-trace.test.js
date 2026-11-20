import assert from 'node:assert/strict';
import { TraceDag } from '../../src/client/trace-dag.js';
import { structuralLocator } from '../../src/adapters/page-query.js';

const limits = { maxNodes: 32, maxEdges: 32, maxSteps: 8 };
const input = label => ({ role: 'textbox', tag: 'input', inputType: 'text', label });
const button = label => ({ role: 'button', tag: 'button', inputType: '', label });
const email = input('Email'), next = button('Continue'), city = input('City'), review = button('Review');
const step = (element, slot) => ({ kind: slot ? 'fill' : 'click', locator: structuralLocator(element), ...(slot ? { slot } : {}) });
const fieldGroups = [{ id: 'contact', steps: [
  { kind: 'fill', slot: 'email', locators: [structuralLocator(email), structuralLocator(input('Email address'))] },
  { kind: 'click', locators: [structuralLocator(next)] },
] }, { id: 'location', steps: [
  { kind: 'fill', slot: 'city', locators: [structuralLocator(city)] },
  { kind: 'click', locators: [structuralLocator(review)] },
] }];
function serviceFixture({ variant = '', outcome = 'completed' } = {}) {
  let stage = 0, version = 0;
  const calls = [], values = {};
  return { calls, values, outstanding: async () => outcome === 'unknown' && calls.length ? [{ isUncertain: true }] : [],
    observe: async () => {
      let elements = stage === 0 ? [{ ...email, ...(variant === 'alias' ? { label: 'Email address' } : {}) }, next]
        : stage === 1 ? [city, review] : [button('Submit')];
      if (!stage && variant === 'extra') elements.push(input('New question'));
      if (!stage && variant === 'ambiguous') elements.push(input('Email address'));
      if (variant === 'reordered') elements.reverse();
      elements = elements.map(element => ({ ...element, value: values[element.label] ?? '',
        handle: element.label, selector: `#${element.label}`, digest: `digest-${element.label}` }));
      return { url: 'https://fixture.invalid/heldout', isTruncated: false, observationVersion: ++version, elements };
    },
    submitAction: async command => {
      assert.equal(command.observationVersion, version);
      calls.push(command);
      if (outcome === 'completed') {
        if (command.kind === 'click') stage++;
        else values[command.target.handle] = command.params.value;
      }
      return { result: Promise.resolve({ outcome, isUncertain: outcome === 'unknown' }) };
    },
  };
}
const options = service => ({ service, owner: {}, pageId: 'main', intent: 'form', template: 'scoped-unit',
  inputs: { email: 'person@example.test', city: 'Albany' }, accountScope: 'account-a', fieldGroups,
  intermediateClicks: [next, review].map(structuralLocator), assertContext: async () => {}, authorizeStep: async () => {} });
const dag = new TraceDag(limits), learning = dag.session(options(serviceFixture()));
for (const spec of [step(email, 'email'), step(next), step(city, 'city'), step(review)]) {
  assert.equal((await learning.record(spec)).status, 'completed');
}
await learning.finish();
const frozen = JSON.stringify(dag.export());
for (const variant of ['', 'alias', 'reordered']) {
  const service = serviceFixture({ variant });
  const replay = await TraceDag.restore(dag.export(), limits).session(options(service)).replay();
  assert.equal(replay.reason, 'submit-boundary'); assert.equal(replay.steps, 4);
  assert.deepEqual(service.calls.map(command => command.kind), ['fill', 'click', 'fill', 'click']);
}
const extra = serviceFixture({ variant: 'extra' });
const miss = await dag.session(options(extra)).replay();
assert.equal(miss.reason, 'unseen-branch'); assert.equal(miss.steps, 1);
assert.equal(extra.calls.length, 1, 'Never cross an unverified new question dependency');
const ambiguous = serviceFixture({ variant: 'ambiguous' });
await assert.rejects(dag.session(options(ambiguous)).replay(), /Ambiguous/);
assert.equal(ambiguous.calls.length, 0);
const otherAccount = serviceFixture();
assert.equal((await dag.session({ ...options(otherAccount), accountScope: 'account-b' }).replay()).steps, 0);
assert.equal(otherAccount.calls.length, 0);
const unknown = serviceFixture({ outcome: 'unknown' });
assert.equal((await dag.session(options(unknown)).replay()).reason, 'action-not-completed');
assert.equal(unknown.calls.length, 1);
const denied = serviceFixture();
await assert.rejects(dag.session({ ...options(denied), authorizeStep: async () => { throw Error('Disclosure denied'); } }).replay(), /Disclosure/);
assert.equal(denied.calls.length, 0);
assert.throws(() => dag.session({ ...options(serviceFixture()), accountScope: null }), /verifiers/);
assert.equal(JSON.stringify(dag.export()), frozen, 'Evaluation must not learn from repairs or safe stops');
console.log('ok: scoped session replay, aliases, ordering, added controls, account/disclosure isolation and unknown stops');
