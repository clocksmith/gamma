#!/usr/bin/env node
// Route-recipe interpreter for the same-model three-arm test (clocksmith/deco#88).
//
// A recipe is a list of API calls that puts an OpenProject instance into the
// state one route needs, plus the work package the write is aimed at and the
// hours to write. This file turns a recipe into records. It knows nothing about
// any arm, and it never sees whether a route is valid: labels live in a separate
// answer key that this file does not read.
//
//   node provision.mjs check <recipes.json>            # shape only, no network
//   node provision.mjs run <recipes.json> [--only id]  # provision on the upgraded release
//   node provision.mjs run <recipes.json> --try-write  # also make the write, to prove the server accepts it
//
// `run` reads the bring-up state file written by ../bringup/openproject-up.sh.
import { readFileSync } from 'node:fs';
import { homedir } from 'node:os';
import { join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

export const ENTRY_BRANCHES = Object.freeze(['direct', 'project-table', 'project-overview', 'relations-tab']);
export const ACCOUNTS = Object.freeze(['author', 'approver']);
export const LIMITS = Object.freeze({ setupSteps: 24, bodyBytes: 8192, recipes: 64 });
const METHODS = new Set(['GET', 'POST', 'PATCH', 'DELETE']);
const NAME = /^[a-z][A-Za-z0-9]{0,31}$/;
const ID = /^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$/;
const PLACEHOLDER = /\{([A-Za-z][A-Za-z0-9.]{0,47})\}/g;

const isObject = v => v !== null && typeof v === 'object' && !Array.isArray(v);

/** Shape check only. Returns a list of problems; an empty list means well formed. */
export function validateRecipe(recipe) {
  const problems = [];
  const bad = message => problems.push(`${recipe?.routeId ?? '<no routeId>'}: ${message}`);
  if (!isObject(recipe)) return ['recipe is not an object'];
  if (typeof recipe.routeId !== 'string' || !ID.test(recipe.routeId)) bad('routeId must match ' + ID);
  if (typeof recipe.familyId !== 'string' || !ID.test(recipe.familyId)) bad('familyId must match ' + ID);
  if (!ENTRY_BRANCHES.includes(recipe.entryBranch)) bad(`entryBranch must be one of ${ENTRY_BRANCHES.join(', ')}`);
  if (!Array.isArray(recipe.setup) || !recipe.setup.length || recipe.setup.length > LIMITS.setupSteps) {
    bad(`setup must hold 1 to ${LIMITS.setupSteps} steps`);
  } else {
    const saved = new Set(['tag']);
    recipe.setup.forEach((step, index) => {
      const at = `setup[${index}]`;
      if (!isObject(step)) return bad(`${at} is not an object`);
      if (!ACCOUNTS.includes(step.as)) bad(`${at}.as must be author or approver`);
      if (!METHODS.has(step.method)) bad(`${at}.method must be GET, POST, PATCH or DELETE`);
      if (typeof step.path !== 'string' || !step.path.startsWith('/api/v3/')) bad(`${at}.path must start with /api/v3/`);
      if (step.body !== undefined && (!isObject(step.body) || JSON.stringify(step.body).length > LIMITS.bodyBytes)) {
        bad(`${at}.body must be an object of at most ${LIMITS.bodyBytes} bytes`);
      }
      if (step.expectStatus !== undefined && !Number.isInteger(step.expectStatus)) bad(`${at}.expectStatus must be an integer`);
      for (const used of placeholders(step)) {
        if (!used.includes('.') && !saved.has(used)) bad(`${at} uses {${used}} before a step saves it`);
      }
      if (step.save !== undefined) {
        if (!isObject(step.save)) bad(`${at}.save must map a name to a response path`);
        else for (const [name, path] of Object.entries(step.save)) {
          if (!NAME.test(name)) bad(`${at}.save name ${name} must match ${NAME}`);
          if (typeof path !== 'string' || !path) bad(`${at}.save.${name} must be a dotted response path`);
          saved.add(name);
        }
      }
    });
    if (isObject(recipe.target)) {
      for (const used of placeholders(recipe.target)) {
        if (!used.includes('.') && !saved.has(used)) bad(`target uses {${used}}, which no step saves`);
      }
    }
  }
  if (!isObject(recipe.target) || typeof recipe.target.workPackage !== 'string' || typeof recipe.target.project !== 'string') {
    bad('target needs workPackage and project');
  }
  if (!isObject(recipe.write) || !Number.isInteger(recipe.write.workHours)
      || recipe.write.workHours < 1 || recipe.write.workHours > 999) bad('write.workHours must be an integer from 1 to 999');
  if ('valid' in recipe || 'label' in recipe || 'reason' in recipe) bad('a recipe must not carry its label; put it in the answer key');
  return problems;
}

export function validateRecipeFile(document) {
  if (!isObject(document) || !Array.isArray(document.recipes)) return ['file must be { "recipes": [...] }'];
  if (document.recipes.length > LIMITS.recipes) return [`at most ${LIMITS.recipes} recipes per file`];
  const problems = document.recipes.flatMap(validateRecipe);
  const ids = document.recipes.map(r => r?.routeId);
  for (const id of new Set(ids)) if (ids.filter(x => x === id).length > 1) problems.push(`${id}: routeId is used twice`);
  return problems;
}

function placeholders(value) {
  const found = [];
  const visit = v => {
    if (typeof v === 'string') for (const m of v.matchAll(PLACEHOLDER)) found.push(m[1]);
    else if (Array.isArray(v)) v.forEach(visit);
    else if (isObject(v)) Object.values(v).forEach(visit);
  };
  visit(isObject(value) && 'path' in value ? { path: value.path, body: value.body } : value);
  return found;
}

/** A whole-string placeholder keeps the saved value's type; an embedded one is spliced in as text. */
export function substitute(value, scope) {
  const lookup = name => {
    if (!Object.hasOwn(scope, name)) throw Error(`unknown placeholder {${name}}`);
    return scope[name];
  };
  if (typeof value === 'string') {
    const whole = value.match(/^\{([A-Za-z][A-Za-z0-9.]{0,47})\}$/);
    if (whole) return lookup(whole[1]);
    return value.replace(PLACEHOLDER, (_, name) => String(lookup(name)));
  }
  if (Array.isArray(value)) return value.map(v => substitute(v, scope));
  if (isObject(value)) return Object.fromEntries(Object.entries(value).map(([k, v]) => [k, substitute(v, scope)]));
  return value;
}

/** Hours in an ISO 8601 duration such as PT20H or P1DT4H30M; null when there is none. */
export function durationHours(value) {
  const m = typeof value === 'string' && value.match(/^P(?:(\d+)D)?(?:T(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?)?$/);
  if (!m) return null;
  return Number(m[1] ?? 0) * 24 + Number(m[2] ?? 0) + Number(m[3] ?? 0) / 60 + Number(m[4] ?? 0) / 3600;
}

const pick = (body, path) => path.split('.').reduce((v, key) => (v == null ? undefined : v[key]), body);

/** Names every recipe may use without saving them: they differ between instances. */
export function builtins(seed) {
  return {
    'status.new': seed.newStatusHref,
    'status.approved': seed.approvedStatusHref,
    'status.hold': seed.holdStatusHref,
    'status.disallowed': seed.disallowedStatusHref,
    'user.author': `/api/v3/users/${seed.authorUserId}`,
    'user.approver': `/api/v3/users/${seed.approverUserId}`,
  };
}

/**
 * Runs one recipe. `request(account, method, path, body)` performs the call and
 * resolves to { status, body }. A PATCH to a work package that carries no
 * lockVersion gets the current one, so recipes need not thread it through.
 */
export async function provisionRecipe(recipe, { request, seed, tag = '' }) {
  const problems = validateRecipe(recipe);
  if (problems.length) throw Error(problems.join('; '));
  const scope = { ...builtins(seed), tag };
  const steps = [];
  for (const [index, step] of recipe.setup.entries()) {
    const path = substitute(step.path, scope);
    let body = step.body === undefined ? undefined : substitute(step.body, scope);
    if (step.method === 'PATCH' && /^\/api\/v3\/work_packages\/\d+$/.test(path) && body && !('lockVersion' in body)) {
      const current = await request(step.as, 'GET', path);
      if (current.status !== 200) throw Error(`${recipe.routeId} setup[${index}]: cannot read ${path} (${current.status})`);
      body = { lockVersion: current.body.lockVersion, ...body };
    }
    const response = await request(step.as, step.method, path, body);
    const expected = step.expectStatus;
    const ok = expected === undefined ? response.status >= 200 && response.status < 300 : response.status === expected;
    steps.push({ index, as: step.as, method: step.method, path, status: response.status });
    if (!ok) {
      const detail = response.body?.message ?? response.body?._embedded?.errors?.map(e => e.message).join(' | ') ?? '';
      throw Error(`${recipe.routeId} setup[${index}]: ${step.method} ${path} returned ${response.status}`
        + (expected === undefined ? '' : `, expected ${expected}`) + (detail ? `: ${String(detail).slice(0, 300)}` : ''));
    }
    for (const [name, from] of Object.entries(step.save ?? {})) {
      const value = pick(response.body, from);
      if (value === undefined) throw Error(`${recipe.routeId} setup[${index}]: response has no ${from}`);
      scope[name] = value;
    }
  }
  const workPackageId = Number(substitute(recipe.target.workPackage, scope));
  if (!Number.isSafeInteger(workPackageId) || workPackageId < 1) throw Error(`${recipe.routeId}: target.workPackage did not resolve to an id`);
  // Saving the value a work package already holds returns 200 and changes no row,
  // so a completed write could not be told from a skipped one.
  const target = await request('approver', 'GET', `/api/v3/work_packages/${workPackageId}`);
  if (target.status !== 200) throw Error(`${recipe.routeId}: the approver cannot read the target (${target.status})`);
  if (durationHours(target.body.estimatedTime) === recipe.write.workHours) {
    throw Error(`${recipe.routeId}: the target already holds ${recipe.write.workHours} hours of Work; write.workHours must differ`);
  }
  return Object.freeze({
    routeId: recipe.routeId,
    familyId: recipe.familyId,
    entryBranch: recipe.entryBranch,
    project: substitute(recipe.target.project, scope),
    workPackageId,
    workHours: recipe.write.workHours,
    steps,
  });
}

export function openProjectRequester({ url, seed }) {
  const tokens = { author: seed.authorToken, approver: seed.approverToken };
  return async (account, method, path, body) => {
    const response = await fetch(url + path, {
      method,
      headers: {
        Accept: 'application/json',
        'Content-Type': 'application/json',
        Authorization: `Basic ${Buffer.from(`apikey:${tokens[account]}`).toString('base64')}`,
      },
      body: body === undefined ? undefined : JSON.stringify(body),
    });
    const text = await response.text();
    let parsed = null;
    try { parsed = text ? JSON.parse(text) : null; } catch { parsed = { message: text.slice(0, 300) }; }
    return { status: response.status, body: parsed };
  };
}

export function readState(file = join(process.env.GAMMATRON_QUAL_STATE ?? join(homedir(), '.local/state/gammatron-qual'), 'openproject.json')) {
  return JSON.parse(readFileSync(file, 'utf8'));
}

async function main(argv) {
  const [mode, file, ...rest] = argv;
  if (!['check', 'run'].includes(mode) || !file) {
    console.error('usage: provision.mjs check <recipes.json> | run <recipes.json> [--only <routeId>] [--side old|new] [--try-write]');
    process.exit(2);
  }
  const document = JSON.parse(readFileSync(file, 'utf8'));
  const problems = validateRecipeFile(document);
  if (problems.length) {
    console.log(JSON.stringify({ ok: false, problems }, null, 2));
    process.exit(1);
  }
  if (mode === 'check') {
    console.log(JSON.stringify({ ok: true, recipes: document.recipes.length }));
    return;
  }
  const tryWrite = rest.includes('--try-write');
  const only = rest.includes('--only') ? rest[rest.indexOf('--only') + 1] : null;
  const side = rest.includes('--side') ? rest[rest.indexOf('--side') + 1] : 'new';
  const state = readState();
  const request = openProjectRequester(state[side]);
  const results = [];
  let failed = false;
  for (const recipe of document.recipes) {
    if (only && recipe.routeId !== only) continue;
    try {
      const route = await provisionRecipe(recipe, { request, seed: state[side].seed, tag: `check-${Date.now()}` });
      const result = { ok: true, ...route };
      if (tryWrite) {
        // Uses up this copy of the route: the same request the page sends, made as the approver.
        const path = `/api/v3/work_packages/${route.workPackageId}`;
        const current = await request('approver', 'GET', path);
        const written = await request('approver', 'PATCH', path,
          { lockVersion: current.body.lockVersion, estimatedTime: `PT${route.workHours}H` });
        result.serverAcceptsWrite = written.status === 200;
        result.writeStatus = written.status;
        if (!result.serverAcceptsWrite) { result.ok = false; failed = true; }
      }
      results.push(result);
    } catch (error) {
      failed = true;
      results.push({ ok: false, routeId: recipe.routeId, error: error.message });
    }
  }
  console.log(JSON.stringify({ ok: !failed, release: state[side].tag, results }, null, 2));
  if (failed) process.exit(1);
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) await main(process.argv.slice(2));
