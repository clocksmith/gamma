import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { test } from 'node:test';
import {
  builtins, durationHours, provisionRecipe, substitute, validateRecipe, validateRecipeFile,
} from '../../qualification/workflow-generalization/three-arm/provision.mjs';

const examples = JSON.parse(readFileSync(
  new URL('../../qualification/workflow-generalization/three-arm/example-recipes.json', import.meta.url), 'utf8'));
const seed = {
  newStatusHref: '/api/v3/statuses/1', approvedStatusHref: '/api/v3/statuses/2', holdStatusHref: '/api/v3/statuses/3',
  disallowedStatusHref: '/api/v3/statuses/4', authorUserId: 5, approverUserId: 6,
};

test('the committed examples are well formed', () => {
  assert.deepEqual(validateRecipeFile(examples), []);
});

test('a recipe may not carry its own label', () => {
  const problems = validateRecipe({ ...examples.recipes[0], valid: true });
  assert.equal(problems.length, 1);
  assert.match(problems[0], /must not carry its label/);
});

test('shape problems are reported, not thrown', () => {
  const recipe = structuredClone(examples.recipes[0]);
  recipe.entryBranch = 'somewhere';
  recipe.setup[1].path = '/work_packages/{approval}';
  recipe.setup[0].save = undefined;
  recipe.write.workHours = 0;
  const problems = validateRecipe(recipe).join('\n');
  assert.match(problems, /entryBranch/);
  assert.match(problems, /must start with \/api\/v3\//);
  assert.match(problems, /uses \{approval\} before a step saves it/);
  assert.match(problems, /workHours/);
  assert.deepEqual(validateRecipeFile({ recipes: [examples.recipes[0], examples.recipes[0]] }), ['example-valid: routeId is used twice']);
});

test('a whole-string placeholder keeps its type and an embedded one becomes text', () => {
  const scope = { ...builtins(seed), order: 41, tag: 't1' };
  assert.equal(substitute('{order}', scope), 41);
  assert.equal(substitute('/api/v3/work_packages/{order}', scope), '/api/v3/work_packages/41');
  assert.deepEqual(substitute({ a: ['{status.hold}', 'Order {tag}'] }, scope), { a: ['/api/v3/statuses/3', 'Order t1'] });
  assert.throws(() => substitute('{missing}', scope), /unknown placeholder/);
});

test('durations are read in hours', () => {
  assert.equal(durationHours('PT20H'), 20);
  assert.equal(durationHours('P1DT4H30M'), 28.5);
  assert.equal(durationHours(null), null);
});

function fakeServer({ storedHours = 'PT20H' } = {}) {
  const calls = [];
  let next = 100;
  const request = async (account, method, path, body) => {
    calls.push({ account, method, path, body });
    if (method === 'POST') return { status: 201, body: { id: next++, lockVersion: 0 } };
    if (method === 'GET') return { status: 200, body: { lockVersion: 7, estimatedTime: storedHours } };
    if (account === 'author' && body?._links?.status) return { status: 422, body: { message: 'Status is invalid' } };
    return { status: 200, body: { lockVersion: 8 } };
  };
  return { calls, request };
}

test('provisioning threads saved ids, fills the lock version and honours an expected refusal', async () => {
  const { calls, request } = fakeServer();
  const route = await provisionRecipe(examples.recipes[1], { request, seed, tag: 'x' });
  assert.equal(route.workPackageId, 101);
  assert.equal(route.workHours, 24);
  assert.equal(route.project, 'stage2-qual-proj');
  assert.deepEqual(route.steps.map(s => s.status), [201, 200, 201, 200, 422]);
  const patch = calls.find(c => c.method === 'PATCH');
  assert.equal(patch.path, '/api/v3/work_packages/100');
  assert.equal(patch.body.lockVersion, 7);
  assert.equal(patch.body._links.status.href, '/api/v3/statuses/2');
  assert.equal(calls.find(c => c.method === 'POST' && c.account === 'author').body._links.parent.href, '/api/v3/work_packages/100');
  assert.ok(!('valid' in route));
});

test('a step that fails stops provisioning with the server message', async () => {
  const { request } = fakeServer();
  const recipe = structuredClone(examples.recipes[1]);
  delete recipe.setup[4].expectStatus;
  await assert.rejects(provisionRecipe(recipe, { request, seed }), /setup\[4\]: PATCH .* returned 422: Status is invalid/);
});

test('a write that would change nothing is refused', async () => {
  const { request } = fakeServer({ storedHours: 'PT24H' });
  await assert.rejects(provisionRecipe(examples.recipes[0], { request, seed }), /already holds 24 hours/);
});
