import assert from 'node:assert/strict';
import { TraceDag } from '../../src/client/trace-dag.js';
import { runWorkflow } from '../../src/client/workflow-agent.js';
import { skillPlanner, skillRecorder, validateSkill } from '../../src/client/skill-exec.js';
import { structuralLocator } from '../../src/adapters/page-query.js';

const limits = { maxNodes: 32, maxEdges: 32, maxSteps: 12 };
const field = (label, id) => ({ label, role: 'textbox', tag: 'input', inputType: 'text', selector: `#${id}`, handle: id,
  digest: `digest-${id}`, value: '' });
const button = (label, id) => ({ label, role: 'button', tag: 'button', inputType: '', selector: `#${id}`, handle: id,
  digest: `digest-${id}`, value: null });
const next = () => button('Continue', 'continue');
const inputs = { name: 'PRIVATE_NAME', city: 'PRIVATE_CITY', referral: 'PRIVATE_REFERRAL' };
const slotOf = { Name: 'name', 'Legal name': 'name', City: 'city', 'Referral code': 'referral' };

/** Two screens: a form with a Continue button, then an empty review screen. */
function site(first, { staleOnce = false } = {}) {
  let stage = 0, version = 0, stale = staleOnce;
  const calls = [];
  return { calls, stage: () => stage, fields: first,
    outstanding: async () => [],
    observe: async () => ({ url: 'https://fixture.invalid/form', observationVersion: ++version, isTruncated: false,
      text: stage ? 'review' : 'form', elements: structuredClone(stage ? [] : first) }),
    submitAction: async action => {
      if (stale) {
        stale = false;
        throw Object.assign(Error('stale'), { details: { neverDispatched: { code: 'stale-observation' } } });
      }
      calls.push(action);
      const target = first.find(element => element.handle === action.target.handle);
      if (action.kind === 'click') stage = 1;
      else target.value = action.params.value;
      return { result: Promise.resolve({ outcome: 'completed' }) };
    } };
}
const store = () => {
  const runs = new Map();
  return { run: (id, state) => runs.set(id, state), get: id => ({ run: runs.get(id) ?? null }), activity: () => {} };
};
/** A planner that fills any empty field it knows a slot for, then continues, then finishes. */
function stubPlanner({ refuseDuplicates = false } = {}) {
  const seen = [];
  return { seen, identity: { model: 'stub' }, next: async context => {
    seen.push(context.observation.elements.map(element => element.label));
    const elements = context.observation.elements;
    if (refuseDuplicates && new Set(elements.map(element => element.label)).size !== elements.length) {
      return { tool: 'ask_human', input: { reason: 'Two controls share a label' } };
    }
    const empty = elements.find(element => slotOf[element.label] && element.value !== context.inputs[slotOf[element.label]]);
    if (empty) return { tool: 'act', input: { kind: 'fill', handle: empty.handle, slot: slotOf[empty.label] } };
    const click = elements.find(element => element.label === 'Continue');
    if (click) return { tool: 'act', input: { kind: 'click', handle: click.handle } };
    return { tool: 'finish', input: { summary: 'review' } };
  } };
}
const common = service => ({ dag: new TraceDag(limits), service, owner: { workspaceId: 'w' }, pageId: 'main', intent: 'form',
  template: 'skill-unit', inputs, intermediateClicks: [structuralLocator(next())], task: 'Fill the form to review',
  config: { maxTurns: 12, maxInputBytes: 50000 }, store: store(), projectId: 'p',
  verifyReview: async () => ({ completed: service.stage() === 1 }), signal: new AbortController().signal });

// Teach once. The skill holds slots and locators, never values.
const taughtSite = site([field('Name', 'name'), field('City', 'city'), next()]);
const teacher = skillRecorder(stubPlanner());
const taught = await runWorkflow({ ...common(taughtSite), mode: 'learn', planner: teacher.planner });
assert.equal(taught.completed, true);
const skill = validateSkill(teacher.skill());
assert.deepEqual(skill.steps.map(step => [step.kind, step.locator[1], step.slot ?? null]),
  [['fill', 'Name', 'name'], ['fill', 'City', 'city'], ['click', 'Continue', null]]);
assert.ok(!JSON.stringify(skill).includes('PRIVATE_'), 'A skill stores no input values');
assert.throws(() => validateSkill({ version: 1, steps: [] }), /Invalid skill/);

async function attempt(service, options = {}, plannerOptions = {}) {
  const planner = stubPlanner(plannerOptions);
  const run = skillPlanner({ skill, planner });
  const result = await runWorkflow({ ...common(service), mode: 'fresh', planner: run, ...options });
  return { result, planner, stats: run.stats(), handles: service.calls.map(call => call.target.handle) };
}

// Unchanged and reordered pages: the script runs alone and finishes without a planner turn.
for (const elements of [[field('Name', 'name'), field('City', 'city'), next()], [field('City', 'city'), next(), field('Name', 'name')]]) {
  const { result, planner, stats, handles } = await attempt(site(elements));
  assert.equal(result.completed, true);
  assert.equal(planner.seen.length, 0, 'No planner turn on a page the script can ground');
  assert.deepEqual(handles, ['name', 'city', 'continue']);
  assert.deepEqual([stats.scriptSteps, stats.handBacks], [3, 0]);
}

// A renamed field: the planner fills it, the script does the rest, and the planner decides the finish.
{
  const { result, planner, stats, handles } = await attempt(site([field('Legal name', 'name'), field('City', 'city'), next()]));
  assert.equal(result.completed, true);
  assert.deepEqual(handles, ['name', 'city', 'continue']);
  assert.deepEqual(stats.reasons, { 'missing-target': 1, 'script-finished-after-recovery': 1 });
  assert.equal(planner.seen.length, 2);
  assert.equal(stats.scriptSteps, 2);
}

// A new empty control: the script fills what it knows, then hands the click's turn to the planner.
{
  const { result, stats, handles } = await attempt(site([field('Name', 'name'), field('City', 'city'), field('Referral code', 'referral'), next()]));
  assert.equal(result.completed, true);
  assert.deepEqual(handles, ['name', 'city', 'referral', 'continue']);
  assert.equal(stats.reasons['new-empty-control-before-click'], 1);
  assert.equal(stats.scriptSteps, 3, 'The script still clicks once the new control is answered');
}

// Two controls with the taught locator: the script does not choose, and the planner stops the run.
{
  const service = site([field('Name', 'name'), field('Name', 'decoy'), field('City', 'city'), next()]);
  const { result, stats } = await attempt(service, {}, { refuseDuplicates: true });
  assert.equal(result.completed, false);
  assert.equal(service.calls.length, 0, 'Nothing is written while the target is ambiguous');
  assert.equal(stats.reasons['ambiguous-target'], 1);
}

// A step refused as stale before dispatch is proposed again; no planner turn is spent.
{
  const { result, planner, stats, handles } = await attempt(site([field('Name', 'name'), field('City', 'city'), next()], { staleOnce: true }));
  assert.equal(result.completed, true);
  assert.equal(planner.seen.length, 0);
  assert.equal(stats.retries, 1);
  assert.deepEqual(handles, ['name', 'city', 'continue']);
}

// The script goes through the same guards as a planner action: a refused step writes nothing.
for (const guard of [{ authorizeStep: async () => { throw Error('Step not authorized'); } },
  { requirePrerequisiteCheck: true, assertPrerequisite: async () => ({ ok: false, reason: 'Record is locked' }) },
  { assertContext: async () => { throw Error('Wrong account'); } }]) {
  const service = site([field('Name', 'name'), field('City', 'city'), next()]);
  const { result } = await attempt(service, guard);
  assert.equal(result.completed, false);
  assert.equal(service.calls.length, 0, 'A refused guard dispatches nothing');
}

// An unauthorized click is refused by the session, not performed by the script.
{
  const service = site([field('Name', 'name'), field('City', 'city'), next()]);
  const { result, handles } = await attempt(service, { intermediateClicks: [] });
  assert.equal(result.completed, false);
  assert.deepEqual(handles, ['name', 'city']);
}
console.log('skill-exec: ok');
