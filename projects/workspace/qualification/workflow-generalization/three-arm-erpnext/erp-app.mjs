// ERPNext side of the three-arm test (clocksmith/deco#88): state, API calls and
// route recipes. DRAFT: built while Stage A is on hold, outside the frozen runner
// hash. Nothing here has been frozen or used with a model.
//
// The workflow. A draft Purchase Order whose first line names the Supplier
// Quotation it was raised from (items[0].supplier_quotation). The one write:
// signed in as the approver, a confirmation reference is added to the order's
// Terms and the order is saved. A recipe builds the records for one route with
// REST calls made as the author or the approver; it never carries its label.
import { readFileSync } from 'node:fs';
import { homedir } from 'node:os';
import { join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { substitute } from '../three-arm/provision.mjs';

export const ENTRY_BRANCHES = Object.freeze(['direct', 'order-list', 'buying-workspace', 'more-info-tab']);
export const LIMITS = Object.freeze({ setupSteps: 24, bodyBytes: 16384, recipes: 64 });
const ACCOUNTS = Object.freeze({ author: 'authorToken', approver: 'approverToken' });
const METHODS = new Set(['GET', 'POST', 'PUT', 'DELETE']);
const ID = /^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$/;
const NAME = /^[a-z][A-Za-z0-9]{0,31}$/;
const REFERENCE = /^[A-Z0-9][A-Z0-9-]{3,23}$/;
const PLACEHOLDER = /\{([A-Za-z][A-Za-z0-9.]{0,47})\}/g;
// What a recipe or an arm may call: documents, and the two calls that submit or cancel one.
export const ALLOWED_PATH = /^\/api\/(?:resource\/[A-Za-z%0-9 _-]+(?:\/[A-Za-z0-9%._ -]+)?|method\/frappe\.client\.(?:submit|cancel))(?:\?.*)?$/;
const isObject = v => v !== null && typeof v === 'object' && !Array.isArray(v);

export function readErpState(file = join(process.env.GAMMATRON_QUAL_STATE ?? join(homedir(), '.local/state/gammatron-qual'), 'erpnext.json')) {
  return JSON.parse(readFileSync(file, 'utf8'));
}

export function erpRequester(release) {
  return async (account, method, path, body) => {
    const response = await fetch(release.url + path, {
      method,
      headers: { Accept: 'application/json', 'Content-Type': 'application/json', Authorization: `token ${release.seed[ACCOUNTS[account]]}` },
      body: body === undefined ? undefined : JSON.stringify(body),
    });
    const text = await response.text();
    let parsed = null;
    try { parsed = text ? JSON.parse(text) : null; } catch { parsed = { message: text.slice(0, 300) }; }
    return { status: response.status, body: parsed };
  };
}

const used = value => {
  const found = [];
  const visit = v => {
    if (typeof v === 'string') for (const m of v.matchAll(PLACEHOLDER)) found.push(m[1]);
    else if (Array.isArray(v)) v.forEach(visit);
    else if (isObject(v)) Object.values(v).forEach(visit);
  };
  visit(value);
  return found;
};

/** Shape check only. Returns a list of problems; an empty list means well formed. */
export function validateErpRecipe(recipe) {
  const problems = [];
  const bad = message => problems.push(`${recipe?.routeId ?? '<no routeId>'}: ${message}`);
  if (!isObject(recipe)) return ['recipe is not an object'];
  if (typeof recipe.routeId !== 'string' || !ID.test(recipe.routeId)) bad('routeId must match ' + ID);
  if (typeof recipe.familyId !== 'string' || !ID.test(recipe.familyId)) bad('familyId must match ' + ID);
  if (!ENTRY_BRANCHES.includes(recipe.entryBranch)) bad(`entryBranch must be one of ${ENTRY_BRANCHES.join(', ')}`);
  const saved = new Set(['tag']);
  if (!Array.isArray(recipe.setup) || !recipe.setup.length || recipe.setup.length > LIMITS.setupSteps) {
    bad(`setup must hold 1 to ${LIMITS.setupSteps} steps`);
  } else {
    recipe.setup.forEach((step, index) => {
      const at = `setup[${index}]`;
      if (!isObject(step)) return bad(`${at} is not an object`);
      if (!Object.hasOwn(ACCOUNTS, step.as)) bad(`${at}.as must be author or approver`);
      if (!METHODS.has(step.method)) bad(`${at}.method must be GET, POST, PUT or DELETE`);
      if (typeof step.path !== 'string' || !ALLOWED_PATH.test(step.path.replace(PLACEHOLDER, 'X'))) bad(`${at}.path must be a document path or frappe.client.submit / cancel`);
      if (step.body !== undefined && (!isObject(step.body) || JSON.stringify(step.body).length > LIMITS.bodyBytes)) bad(`${at}.body must be an object of at most ${LIMITS.bodyBytes} bytes`);
      if (step.expectStatus !== undefined && !Number.isInteger(step.expectStatus)) bad(`${at}.expectStatus must be an integer`);
      for (const name of used({ path: step.path, body: step.body })) if (!saved.has(name)) bad(`${at} uses {${name}} before a step saves it`);
      if (step.save !== undefined) {
        if (!isObject(step.save)) bad(`${at}.save must map a name to a response path`);
        else for (const [name, path] of Object.entries(step.save)) {
          if (!NAME.test(name)) bad(`${at}.save name ${name} must match ${NAME}`);
          if (typeof path !== 'string' || !path) bad(`${at}.save.${name} must be a dotted response path`);
          saved.add(name);
        }
      }
    });
  }
  if (!isObject(recipe.target) || recipe.target.doctype !== 'Purchase Order' || typeof recipe.target.name !== 'string') bad('target needs doctype "Purchase Order" and a name');
  else for (const name of used(recipe.target)) if (!saved.has(name)) bad(`target uses {${name}}, which no step saves`);
  if (!isObject(recipe.write) || typeof recipe.write.reference !== 'string' || !REFERENCE.test(recipe.write.reference)) bad('write.reference must be 4 to 24 capitals, digits or hyphens');
  if ('valid' in recipe || 'label' in recipe || 'reason' in recipe) bad('a recipe must not carry its label; put it in the answer key');
  return problems;
}

export function validateErpRecipeFile(document) {
  if (!isObject(document) || !Array.isArray(document.recipes)) return ['file must be { "recipes": [...] }'];
  if (document.recipes.length > LIMITS.recipes) return [`at most ${LIMITS.recipes} recipes per file`];
  const problems = document.recipes.flatMap(validateErpRecipe);
  const ids = document.recipes.map(r => r?.routeId);
  for (const id of new Set(ids)) if (ids.filter(x => x === id).length > 1) problems.push(`${id}: routeId is used twice`);
  return problems;
}

const pick = (body, path) => path.split('.').reduce((v, key) => (v == null ? undefined : v[key]), body);

/** Runs one recipe and returns the route an arm is asked about. `request(account, method, path, body)` performs a call. */
export async function provisionErpRecipe(recipe, { request, tag = '' }) {
  const problems = validateErpRecipe(recipe);
  if (problems.length) throw Error(problems.join('; '));
  const scope = { tag };
  const steps = [];
  for (const [index, step] of recipe.setup.entries()) {
    const path = substitute(step.path, scope);
    const body = step.body === undefined ? undefined : substitute(step.body, scope);
    const response = await request(step.as, step.method, path, body);
    const ok = step.expectStatus === undefined ? response.status >= 200 && response.status < 300 : response.status === step.expectStatus;
    steps.push({ index, as: step.as, method: step.method, path, status: response.status });
    if (!ok) {
      const detail = String(response.body?.exception ?? response.body?.message ?? '').slice(0, 240);
      throw Error(`${recipe.routeId} setup[${index}]: ${step.method} ${path} returned ${response.status}${detail ? `: ${detail}` : ''}`);
    }
    for (const [name, from] of Object.entries(step.save ?? {})) {
      const value = pick(response.body, from);
      if (value === undefined) throw Error(`${recipe.routeId} setup[${index}]: response has no ${from}`);
      scope[name] = value;
    }
  }
  const name = String(substitute(recipe.target.name, scope));
  const target = await request('approver', 'GET', `/api/resource/Purchase%20Order/${encodeURIComponent(name)}`);
  if (target.status !== 200) throw Error(`${recipe.routeId}: the approver cannot read the target (${target.status})`);
  if (target.body?.data?.docstatus !== 0) throw Error(`${recipe.routeId}: the target order must be a draft`);
  return Object.freeze({ routeId: recipe.routeId, familyId: recipe.familyId, entryBranch: recipe.entryBranch,
    doctype: 'Purchase Order', name, reference: recipe.write.reference, steps });
}

async function main(argv) {
  const [mode, file, ...rest] = argv;
  if (!['check', 'run'].includes(mode) || !file) {
    console.error('usage: erp-app.mjs check <recipes.json> | run <recipes.json> [--side old|new]');
    process.exit(2);
  }
  const document = JSON.parse(readFileSync(file, 'utf8'));
  const problems = validateErpRecipeFile(document);
  if (problems.length) { console.log(JSON.stringify({ ok: false, problems }, null, 2)); process.exit(1); }
  if (mode === 'check') { console.log(JSON.stringify({ ok: true, recipes: document.recipes.length })); return; }
  const side = rest.includes('--side') ? rest[rest.indexOf('--side') + 1] : 'new';
  const state = readErpState();
  const request = erpRequester(state[side]);
  const results = [];
  let failed = false;
  for (const recipe of document.recipes) {
    try { results.push({ ok: true, ...(await provisionErpRecipe(recipe, { request, tag: `check-${Date.now()}` })) }); }
    catch (error) { failed = true; results.push({ ok: false, routeId: recipe.routeId, error: error.message }); }
  }
  console.log(JSON.stringify({ ok: !failed, release: state[side].tag, results }, null, 2));
  if (failed) process.exit(1);
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) await main(process.argv.slice(2));
