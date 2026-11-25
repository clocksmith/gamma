#!/usr/bin/env node
// Application-neutral Equal-Arms Next-Freeze Runner (clocksmith/deco#88).
//
// Leaves Stage A's voided freeze (`../three-arm/runner.mjs` at gamma 776462de7,
// hash 306e6171...) completely untouched while fixing every validity defect
// documented in `stage-a-decision-sheet.md` and `gammatron-holdout-kit-20261124/`:
//   1. Strips `routeId`, `entryBranch`, and `steps` from per-route inputs on BOTH
//      OpenProject and ERPNext (`forArm(application, route)`).
//   2. Loads `families.json` + `training-examples.json` (tolerating custodian
//      `about` canary GUIDs), builds the exact same labelled positive/negative
//      contrast examples on each arm's disposable instance, and records
//      `trainingReleaseSha256` on every discovery phase record.
//   3. Measures real `authoringMinutes` and exact source adapter/guard LOC
//      (never uncharged, never substituted constants).
//   4. Unconditionally re-verifies ERPNext `termsHoldsReference` on the final
//      settle read before instance teardown.
//   5. Captures setup 403 / permission blocks as `notTestable: true` with exact
//      request + status + response body, never bypassing permissions.
import { execFileSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import {
  appendFileSync, cpSync, existsSync, mkdirSync, mkdtempSync,
  readdirSync, readFileSync, realpathSync, writeFileSync,
} from 'node:fs';
import { tmpdir } from 'node:os';
import { dirname, join, relative, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { auditSessionLog, createAppSurface, DEFAULT_LIMITS } from '../three-arm/app-surface.mjs';
import { hoursPhrase, openProjectDuration } from '../three-arm/durations.mjs';
import { runGuard } from '../three-arm/guard-sandbox.mjs';
import * as opInstructions from '../three-arm/instructions.mjs';
import {
  builtins as opBuiltins, durationHours, openProjectRequester,
  substitute, validateRecipe as validateOpRecipe, validateRecipeFile as validateOpRecipeFile,
} from '../three-arm/provision.mjs';
import { createTeacher as createOpTeacher, decide as decideOpBoundary } from '../three-arm/repair-boundary-arm.mjs';
import { FILE_TOOLS, runSession, sessionArgs } from '../three-arm/session.mjs';
import {
  erpRequester, readErpState, validateErpRecipe, validateErpRecipeFile,
} from '../three-arm-erpnext/erp-app.mjs';
import * as erpInstructions from '../three-arm-erpnext/erp-instructions.mjs';
import { createTeacher as createErpTeacher, decide as decideErpBoundary } from '../three-arm-erpnext/erp-learner.mjs';
import { createErpSurface, ERP_LIMITS } from '../three-arm-erpnext/erp-surface.mjs';

const HERE = dirname(fileURLToPath(import.meta.url));
const QUALIFICATION = resolve(HERE, '..');

export const APPLICATIONS = Object.freeze(['openproject', 'erpnext']);
export const NEXT_ARMS = Object.freeze([
  'expert-guard',
  'agent-written-guard',
  'rule-selector',
  'repair-boundary',
  'always-replan',
]);

export const DEFAULT_STAGE_CONFIG = Object.freeze({
  model: 'claude-sonnet-5-5',
  stageCapUsd: 4.0,
  discovery: Object.freeze({ budgetUsd: 0.6, timeoutMs: 20 * 60 * 1000 }),
  route: Object.freeze({ budgetUsd: 0.08, timeoutMs: 3 * 60 * 1000 }),
});

const sha256 = data => createHash('sha256').update(data).digest('hex');

const countCodeLines = text => String(text ?? '')
  .split('\n')
  .map(line => line.trim())
  .filter(line => line.length > 0 && !line.startsWith('//') && !line.startsWith('/*') && !line.startsWith('*'))
  .length;

/** Count actual source lines in the per-application scalar projection adapter. */
export function measureAdapterLoc(application) {
  const qualSource = readFileSync(join(QUALIFICATION, 'repair-boundary-qualification.mjs'), 'utf8');
  const fnName = application === 'openproject' ? 'projectOpenProjectHalScalars' : 'projectFrappeResourceScalars';
  const start = qualSource.indexOf(`export function ${fnName}`);
  if (start < 0) return 0;
  let depth = 0;
  let begun = false;
  let end = qualSource.length;
  for (let i = start; i < qualSource.length; i += 1) {
    if (qualSource[i] === '{') { depth += 1; begun = true; }
    else if (qualSource[i] === '}') {
      depth -= 1;
      if (begun && depth === 0) { end = i + 1; break; }
    }
  }
  return countCodeLines(qualSource.slice(start, end));
}

/**
 * Strict per-case input projection: strips `routeId`, `entryBranch`, `steps`, and
 * any setup provenance so every arm receives identical target + write intent only.
 */
export function forArm(application, route) {
  if (application === 'openproject') {
    return Object.freeze({
      familyId: String(route.familyId),
      project: String(route.project),
      workPackageId: Number(route.workPackageId),
      workHours: Number(route.workHours),
      workDuration: openProjectDuration(Number(route.workHours)),
    });
  }
  if (application === 'erpnext') {
    return Object.freeze({
      familyId: String(route.familyId),
      doctype: String(route.doctype ?? 'Purchase Order'),
      name: String(route.name),
      reference: String(route.reference),
    });
  }
  throw Error(`unsupported application: ${application}`);
}

const listFiles = dir => readdirSync(dir, { withFileTypes: true }).flatMap(entry => {
  const path = join(dir, entry.name);
  return entry.isDirectory() ? listFiles(path) : entry.isFile() ? [path] : [];
}).sort();

export function hashDirectory(dir) {
  const hash = createHash('sha256');
  for (const file of listFiles(dir)) {
    hash.update(relative(dir, file)).update('\0').update(readFileSync(file)).update('\0');
  }
  return hash.digest('hex');
}

export function frozenNextFileSet() {
  const files = [
    fileURLToPath(import.meta.url),
    join(HERE, 'scorer', 'score_after_fallback.py'),
    join(HERE, 'scorer', 'cost_report.py'),
    join(HERE, 'scorer', 'custody.py'),
    join(QUALIFICATION, 'repair-boundary-qualification.mjs'),
    resolve(QUALIFICATION, '../../src/client/repair-boundary.js'),
    resolve(QUALIFICATION, '../../src/client/branch-verifier.js'),
    resolve(QUALIFICATION, '../../src/client/live-lookahead.js'),
  ].filter(existsSync).sort();
  const root = resolve(QUALIFICATION, '../..');
  const entries = files.map(f => ({ file: relative(root, f), sha256: sha256(readFileSync(f)) }));
  return { entries, sha256: sha256(entries.map(e => `${e.sha256}  ${e.file}\n`).join('')) };
}

/** Validates and loads `families.json` + `training-examples.json`, ignoring custodian `about` fields. */
export function loadEqualTrainingRelease({ application, familiesFile, trainingExamplesFile }) {
  if (!APPLICATIONS.includes(application)) throw Error(`application must be one of ${APPLICATIONS.join(', ')}`);
  const rawFamiliesBytes = readFileSync(familiesFile);
  const rawTrainingBytes = readFileSync(trainingExamplesFile);
  const familiesDoc = JSON.parse(rawFamiliesBytes.toString('utf8'));
  const trainingDoc = JSON.parse(rawTrainingBytes.toString('utf8'));
  const validateRec = application === 'openproject' ? validateOpRecipe : validateErpRecipe;

  if (!Array.isArray(familiesDoc?.families) || !familiesDoc.families.length) {
    throw Error('families.json must hold a non-empty families array');
  }
  const appFamilies = familiesDoc.families.filter(f => !f.application || f.application === application);
  if (!appFamilies.length) throw Error(`no families declared for application ${application}`);

  for (const fam of appFamilies) {
    if (typeof fam.familyId !== 'string' || typeof fam.policy !== 'string') {
      throw Error('each family requires familyId and policy');
    }
    const probs = validateRec(fam.disclosedExample);
    if (probs.length) throw Error(`disclosedExample of ${fam.familyId}: ${probs.join('; ')}`);
  }

  const byFamilyExamples = new Map();
  for (const item of trainingDoc?.families ?? []) {
    if (!appFamilies.some(f => f.familyId === item.familyId)) continue;
    if (!Array.isArray(item.examples)) throw Error(`training-examples ${item.familyId}: examples must be an array`);
    const pos = item.examples.filter(e => e.valid === true);
    const neg = item.examples.filter(e => e.valid === false);
    if (pos.length < 2 || neg.length < 2) {
      throw Error(`training-examples ${item.familyId} requires >=2 valid and >=2 invalid contrast examples`);
    }
    for (const ex of item.examples) {
      const probs = validateRec(ex.recipe);
      if (probs.length) throw Error(`training example in ${item.familyId}: ${probs.join('; ')}`);
    }
    byFamilyExamples.set(item.familyId, item.examples);
  }
  for (const fam of appFamilies) {
    if (!byFamilyExamples.has(fam.familyId)) {
      throw Error(`family ${fam.familyId} missing from training-examples.json`);
    }
  }

  const trainingReleaseSha256 = sha256(
    Buffer.concat([rawFamiliesBytes, Buffer.from('\0'), rawTrainingBytes]),
  );
  return { families: appFamilies, byFamilyExamples, trainingReleaseSha256 };
}

const pick = (body, path) => path.split('.').reduce((v, key) => (v == null ? undefined : v[key]), body);

/**
 * Provisions one recipe while capturing any 403 or setup refusal with exact request
 * and response (`benchmark-spec.md:62-72`) instead of bypassing permissions.
 */
export async function provisionWithRefusalCapture({ application, recipe, request, seed = null, tag = '' }) {
  const validate = application === 'openproject' ? validateOpRecipe : validateErpRecipe;
  const problems = validate(recipe);
  if (problems.length) throw Error(problems.join('; '));

  const scope = application === 'openproject' ? { ...opBuiltins(seed), tag } : { tag };
  for (const [index, step] of recipe.setup.entries()) {
    const path = substitute(step.path, scope);
    let body = step.body === undefined ? undefined : substitute(step.body, scope);
    if (application === 'openproject' && step.method === 'PATCH' && /^\/api\/v3\/work_packages\/\d+$/.test(path) && body && !('lockVersion' in body)) {
      const current = await request(step.as, 'GET', path);
      if (current.status !== 200) {
        return {
          notTestable: true,
          refusal: { stepIndex: index, as: step.as, method: 'GET', path, status: current.status, response: current.body },
        };
      }
      body = { lockVersion: current.body.lockVersion, ...body };
    }
    const response = await request(step.as, step.method, path, body);
    const expected = step.expectStatus;
    const ok = expected === undefined ? response.status >= 200 && response.status < 300 : response.status === expected;
    if (!ok) {
      return {
        notTestable: true,
        refusal: { stepIndex: index, as: step.as, method: step.method, path, status: response.status, response: response.body },
      };
    }
    for (const [name, from] of Object.entries(step.save ?? {})) {
      const val = pick(response.body, from);
      if (val === undefined) throw Error(`${recipe.routeId} setup[${index}]: response lacks ${from}`);
      scope[name] = val;
    }
  }

  if (application === 'openproject') {
    const workPackageId = Number(substitute(recipe.target.workPackage, scope));
    const target = await request('approver', 'GET', `/api/v3/work_packages/${workPackageId}`);
    if (target.status !== 200) {
      return {
        notTestable: true,
        refusal: { stepIndex: recipe.setup.length, as: 'approver', method: 'GET', path: `/api/v3/work_packages/${workPackageId}`, status: target.status, response: target.body },
      };
    }
    if (durationHours(target.body.estimatedTime) === recipe.write.workHours) {
      throw Error(`${recipe.routeId}: target already holds ${recipe.write.workHours}h`);
    }
    return {
      notTestable: false,
      route: Object.freeze({
        routeId: recipe.routeId,
        familyId: recipe.familyId,
        entryBranch: recipe.entryBranch,
        project: substitute(recipe.target.project, scope),
        workPackageId,
        workHours: recipe.write.workHours,
      }),
    };
  }

  const name = String(substitute(recipe.target.name, scope));
  const targetPath = `/api/resource/Purchase%20Order/${encodeURIComponent(name)}`;
  const target = await request('approver', 'GET', targetPath);
  if (target.status !== 200) {
    return {
      notTestable: true,
      refusal: { stepIndex: recipe.setup.length, as: 'approver', method: 'GET', path: targetPath, status: target.status, response: target.body },
    };
  }
  if (target.body?.data?.docstatus !== 0) throw Error(`${recipe.routeId}: target order must be draft`);
  return {
    notTestable: false,
    route: Object.freeze({
      routeId: recipe.routeId,
      familyId: recipe.familyId,
      entryBranch: recipe.entryBranch,
      doctype: 'Purchase Order',
      name,
      reference: recipe.write.reference,
    }),
  };
}

/** Builds identical disclosed + contrast examples on an instance and formats the shared prompt brief. */
export async function buildEqualContrastBundle({ application, release, request, seed, tagPrefix }) {
  const bundle = [];
  for (const fam of release.families) {
    const disc = await provisionWithRefusalCapture({
      application, recipe: fam.disclosedExample, request, seed, tag: `${tagPrefix}-disc-${fam.familyId}`,
    });
    if (disc.notTestable) {
      throw Error(`disclosedExample of ${fam.familyId} hit setup refusal (${disc.refusal.status} on ${disc.refusal.path})`);
    }
    const builtExamples = [];
    for (const [idx, ex] of release.byFamilyExamples.get(fam.familyId).entries()) {
      const built = await provisionWithRefusalCapture({
        application, recipe: ex.recipe, request, seed, tag: `${tagPrefix}-tr-${fam.familyId}-${idx}`,
      });
      if (built.notTestable) {
        throw Error(`training example ${idx} of ${fam.familyId} hit setup refusal (${built.refusal.status} on ${built.refusal.path})`);
      }
      builtExamples.push({
        label: ex.valid ? 'valid' : 'invalid',
        valid: Boolean(ex.valid),
        why: String(ex.why ?? ''),
        target: forArm(application, built.route),
      });
    }
    bundle.push({
      familyId: fam.familyId,
      policy: fam.policy,
      disclosed: forArm(application, disc.route),
      contrastExamples: builtExamples,
    });
  }
  return bundle;
}

export function formatEqualContrastBrief(application, bundle) {
  const describe = item => application === 'openproject'
    ? `work package number ${item.workPackageId} in project "${item.project}", saving Work as ${hoursPhrase(item.workHours)}`
    : `Purchase Order "${item.name}", adding the reference "${item.reference}"`;

  return [
    'Equal-arms training release (identical across learned policy and authored guards):',
    '',
    ...bundle.flatMap(f => [
      `Family "${f.familyId}"`,
      `  Policy: ${f.policy}`,
      `  Disclosed valid example: ${describe(f.disclosed)}.`,
      '  Labelled contrast examples:',
      ...f.contrastExamples.map((ex, idx) => `    ${idx + 1}. [${ex.label.toUpperCase()}] ${describe(ex.target)} — ${ex.why}`),
      '',
    ]),
  ].join('\n');
}

function appendJsonl(dir, name, obj) {
  appendFileSync(join(dir, name), `${JSON.stringify(obj)}\n`);
}

function prepareRunDir(runDir) {
  for (const sub of ['logs', 'artifacts', 'work']) {
    mkdirSync(join(runDir, sub), { recursive: true, mode: 0o700 });
  }
}

function readPhaseRecords(runDir) {
  const p = join(runDir, 'phase-records.jsonl');
  if (!existsSync(p)) return [];
  return readFileSync(p, 'utf8').trim().split('\n').filter(Boolean).map(line => JSON.parse(line));
}

/**
 * Records an audited model-driven adapter authoring or maintenance phase
 * (`adapter-discovery` or `adapter-maintenance`) so `costUsd` and `wallMs`
 * are charged automatically when `repair-boundary` uses `adapterSource: 'model-phase'`.
 */
export function recordAuditedAdapterPhase({
  application,
  upgrade,
  phase = 'adapter-discovery',
  runDir,
  startedAt,
  endedAt,
  costUsd,
  budgetUsd = 0,
  modelCalls = 0,
  modelTurns = 0,
  outOfSurfaceCalls = 0,
  adapterLoc = 0,
  artifactSha256,
}) {
  if (!APPLICATIONS.includes(application)) throw Error(`unsupported application: ${application}`);
  if (!['adapter-discovery', 'adapter-maintenance'].includes(phase)) {
    throw Error(`phase must be adapter-discovery or adapter-maintenance (got ${phase})`);
  }
  if (!Number.isFinite(costUsd) || costUsd < 0) throw Error('recordAuditedAdapterPhase requires finite costUsd >= 0');
  if (!artifactSha256 || typeof artifactSha256 !== 'string') {
    throw Error('recordAuditedAdapterPhase requires artifactSha256');
  }
  prepareRunDir(runDir);
  const startDate = startedAt instanceof Date ? startedAt : new Date(startedAt);
  const endDate = endedAt instanceof Date ? endedAt : new Date(endedAt);
  const wallMs = Math.max(0, endDate - startDate);
  const learnerWallMinutes = Number((wallMs / 60000).toFixed(6));
  const record = {
    schema: 'gammatron-three-arm-phase-record/v1',
    runId: `next-${resolve(runDir).split('/').pop()}`,
    application,
    upgrade,
    arm: 'repair-boundary',
    phase,
    adapterSource: 'model-phase',
    startedAt: startDate.toISOString(),
    endedAt: endDate.toISOString(),
    wallMs,
    adapterAuthoringMinutes: 0,
    adapterMaintenanceMinutes: 0,
    guardAuthoringMinutes: 0,
    guardMaintenanceMinutes: 0,
    learnerWallMinutes,
    authoringMinutes: learnerWallMinutes,
    adapterOrGuardLoc: Number(adapterLoc) || 0,
    trainingReleaseSha256: null,
    modelCalls: Number(modelCalls) || 0,
    modelTurns: Number(modelTurns) || 0,
    costUsd: Number(Number(costUsd).toFixed(6)),
    budgetUsd: Number(budgetUsd) || 0,
    recordsCreated: 0,
    outOfSurfaceCalls: Number(outOfSurfaceCalls) || 0,
    artifactSha256,
    completed: true,
  };
  appendJsonl(runDir, 'phase-records.jsonl', record);
  return record;
}

/**
 * Deterministic ($0) discovery/maintenance for `repair-boundary` from `training-examples.json`
 * + explicit read plans, or registration of a pre-authored `expert-guard` / `rule-selector`
 * with measured authoring/maintenance minutes.
 *
 * Closes the Stage A uncharged-adapter loophole: `repair-boundary` can no longer omit
 * adapter effort and fall back to `wallMs / 60000` (~0.1 min script runtime) when a
 * human wrote the scalar adapter or `readPlansByFamily`.
 */
export async function freezeDeterministicArm({
  application,
  upgrade,
  arm,
  phase = 'discovery',
  familiesFile,
  trainingExamplesFile,
  runDir,
  readPlansByFamily = null,
  adapterSource = 'human',
  adapterAuthoringMinutes = null,
  adapterMaintenanceMinutes = null,
  guardSourceFile = null,
  measuredAuthoringMinutes = null,
  measuredMaintenanceMinutes = null,
  deps,
}) {
  if (!['repair-boundary', 'expert-guard', 'rule-selector'].includes(arm)) {
    throw Error(`freezeDeterministicArm supports repair-boundary, expert-guard, rule-selector (got ${arm})`);
  }
  if (!['discovery', 'maintenance'].includes(phase)) {
    throw Error(`freezeDeterministicArm phase must be discovery or maintenance (got ${phase})`);
  }
  prepareRunDir(runDir);
  const existingPhases = readPhaseRecords(runDir);

  let resolvedAdapterSource = 'none';
  let resolvedAdapterAuthMin = 0;
  let resolvedAdapterMaintMin = 0;
  let resolvedGuardAuthMin = 0;
  let resolvedGuardMaintMin = 0;

  if (arm === 'repair-boundary') {
    if (!readPlansByFamily) throw Error('repair-boundary deterministic freeze requires readPlansByFamily');
    if (!['human', 'model-phase', 'reused-prior-stage'].includes(adapterSource)) {
      throw Error(`repair-boundary adapterSource must be human, model-phase, or reused-prior-stage (got ${adapterSource})`);
    }
    resolvedAdapterSource = adapterSource;
    if (adapterSource === 'human') {
      if (phase === 'discovery') {
        if (!Number.isFinite(adapterAuthoringMinutes) || adapterAuthoringMinutes <= 0) {
          throw Error(
            'repair-boundary discovery with adapterSource="human" requires positive finite adapterAuthoringMinutes '
            + '(never uncharged or substituted with script wallMs)',
          );
        }
        if (adapterMaintenanceMinutes !== null && (!Number.isFinite(adapterMaintenanceMinutes) || adapterMaintenanceMinutes < 0)) {
          throw Error('repair-boundary adapterMaintenanceMinutes must be finite and >= 0');
        }
        resolvedAdapterAuthMin = Number(adapterAuthoringMinutes);
        resolvedAdapterMaintMin = adapterMaintenanceMinutes !== null ? Number(adapterMaintenanceMinutes) : 0;
      } else {
        if (!Number.isFinite(adapterMaintenanceMinutes) || adapterMaintenanceMinutes < 0) {
          throw Error('repair-boundary maintenance with adapterSource="human" requires finite adapterMaintenanceMinutes >= 0');
        }
        if (adapterAuthoringMinutes !== null && (!Number.isFinite(adapterAuthoringMinutes) || adapterAuthoringMinutes < 0)) {
          throw Error('repair-boundary adapterAuthoringMinutes must be finite and >= 0');
        }
        resolvedAdapterAuthMin = adapterAuthoringMinutes !== null ? Number(adapterAuthoringMinutes) : 0;
        resolvedAdapterMaintMin = Number(adapterMaintenanceMinutes);
      }
    } else if (adapterSource === 'model-phase') {
      const expectedAdapterPhase = phase === 'discovery' ? 'adapter-discovery' : 'adapter-maintenance';
      const audited = existingPhases.findLast(
        p => p.arm === 'repair-boundary'
          && p.application === application
          && p.upgrade === upgrade
          && p.phase === expectedAdapterPhase
          && p.completed === true,
      );
      if (!audited) {
        throw Error(
          `repair-boundary with adapterSource="model-phase" requires a completed ${expectedAdapterPhase} phase record `
          + `for ${application} ${upgrade} in ${runDir}`,
        );
      }
      resolvedAdapterAuthMin = adapterAuthoringMinutes !== null ? Number(adapterAuthoringMinutes) : 0;
      resolvedAdapterMaintMin = adapterMaintenanceMinutes !== null ? Number(adapterMaintenanceMinutes) : 0;
    } else if (adapterSource === 'reused-prior-stage') {
      if (phase !== 'maintenance') {
        throw Error('adapterSource="reused-prior-stage" is only valid on phase="maintenance"');
      }
      const priorCharged = existingPhases.findLast(
        p => p.arm === 'repair-boundary'
          && p.application === application
          && p.phase === 'discovery'
          && p.completed === true,
      );
      if (!priorCharged) {
        throw Error(`adapterSource="reused-prior-stage" requires a prior completed discovery phase for ${application}`);
      }
      if (adapterMaintenanceMinutes !== null && Number(adapterMaintenanceMinutes) !== 0) {
        throw Error('adapterSource="reused-prior-stage" requires 0 adapterMaintenanceMinutes (use adapterSource="human" when edited)');
      }
      resolvedAdapterAuthMin = 0;
      resolvedAdapterMaintMin = 0;
    }
  } else {
    if (!guardSourceFile || !existsSync(guardSourceFile)) {
      throw Error(`${arm} requires an existing guardSourceFile`);
    }
    if (phase === 'discovery') {
      if (!Number.isFinite(measuredAuthoringMinutes) || measuredAuthoringMinutes < 0) {
        throw Error(`${arm} discovery requires non-negative measuredAuthoringMinutes`);
      }
      resolvedGuardAuthMin = Number(measuredAuthoringMinutes);
      resolvedGuardMaintMin = measuredMaintenanceMinutes !== null ? Number(measuredMaintenanceMinutes) : 0;
    } else {
      if (!Number.isFinite(measuredMaintenanceMinutes) || measuredMaintenanceMinutes < 0) {
        throw Error(`${arm} maintenance requires non-negative measuredMaintenanceMinutes`);
      }
      resolvedGuardAuthMin = measuredAuthoringMinutes !== null ? Number(measuredAuthoringMinutes) : 0;
      resolvedGuardMaintMin = Number(measuredMaintenanceMinutes);
    }
  }

  const release = loadEqualTrainingRelease({ application, familiesFile, trainingExamplesFile });
  const startedAt = new Date();
  deps.freshInstance();
  try {
    const state = deps.readState();
    const request = deps.requester(state.new);
    const builtBundle = await buildEqualContrastBundle({
      application, release, request, seed: state.new.seed, tagPrefix: `det-${arm}`,
    });

    let artifactSha256 = null;
    let integrationLoc = 0;
    if (arm === 'repair-boundary') {
      const teacher = application === 'openproject'
        ? createOpTeacher(release.families.map(f => f.familyId))
        : createErpTeacher(release.families.map(f => f.familyId));
      const get = application === 'openproject'
        ? path => createAppSurface({ mode: 'decision', request, limits: DEFAULT_LIMITS }).tools.app_get({ path })
        : path => createErpSurface({ mode: 'decision', request, limits: ERP_LIMITS }).tools.erp_get({ path });

      for (const fam of builtBundle) {
        const plan = readPlansByFamily[fam.familyId];
        if (!plan) throw Error(`missing read plan for family ${fam.familyId}`);
        const setRes = teacher.setReadPlan(fam.familyId, plan);
        if (!setRes.ok) throw Error(`invalid read plan for ${fam.familyId}: ${setRes.problems.join('; ')}`);
        for (const ex of fam.contrastExamples) {
          const added = await teacher.addExample(fam.familyId, ex.label, ex.target, get);
          if (!added.ok) throw Error(`addExample failed on ${fam.familyId}: ${added.problems.join('; ')}`);
        }
        const boundary = teacher.learn(fam.familyId);
        if (boundary.status !== 'learned') {
          throw Error(`repair-boundary failed to learn ${fam.familyId}: ${boundary.reason}`);
        }
      }
      const frozen = teacher.freeze();
      const outPath = join(runDir, 'artifacts', 'repair-boundary.json');
      writeFileSync(outPath, frozen.text, { mode: 0o600 });
      artifactSha256 = frozen.sha256;
      integrationLoc = measureAdapterLoc(application);
    } else {
      const outDir = join(runDir, 'artifacts', arm);
      mkdirSync(outDir, { recursive: true, mode: 0o700 });
      const srcText = readFileSync(guardSourceFile, 'utf8');
      writeFileSync(join(outDir, 'guard.mjs'), srcText, { mode: 0o600 });
      artifactSha256 = hashDirectory(outDir);
      integrationLoc = countCodeLines(srcText);
    }

    const endedAt = new Date();
    const wallMs = endedAt - startedAt;
    const learnerWallMinutes = arm === 'repair-boundary'
      ? Number((wallMs / 60000).toFixed(6))
      : 0;
    const authoringMinutes = Number((
      resolvedAdapterAuthMin
      + resolvedAdapterMaintMin
      + resolvedGuardAuthMin
      + resolvedGuardMaintMin
      + learnerWallMinutes
    ).toFixed(6));

    const record = {
      schema: 'gammatron-three-arm-phase-record/v1',
      runId: `next-${resolve(runDir).split('/').pop()}`,
      application,
      upgrade,
      arm,
      phase,
      adapterSource: resolvedAdapterSource,
      startedAt: startedAt.toISOString(),
      endedAt: endedAt.toISOString(),
      wallMs,
      adapterAuthoringMinutes: resolvedAdapterAuthMin,
      adapterMaintenanceMinutes: resolvedAdapterMaintMin,
      guardAuthoringMinutes: resolvedGuardAuthMin,
      guardMaintenanceMinutes: resolvedGuardMaintMin,
      learnerWallMinutes,
      authoringMinutes,
      adapterOrGuardLoc: integrationLoc,
      trainingReleaseSha256: release.trainingReleaseSha256,
      modelCalls: 0,
      modelTurns: 0,
      costUsd: 0,
      budgetUsd: 0,
      recordsCreated: builtBundle.reduce((acc, f) => acc + 1 + f.contrastExamples.length, 0),
      outOfSurfaceCalls: 0,
      artifactSha256,
      completed: artifactSha256 !== null,
    };
    appendJsonl(runDir, 'phase-records.jsonl', record);
    return record;
  } finally {
    deps.stopInstance();
  }
}

/** Registers `always-replan` phase record at $0 before blind route execution. */
export function registerAlwaysReplanPhase({ application, upgrade, runDir }) {
  prepareRunDir(runDir);
  const inst = application === 'openproject' ? opInstructions : erpInstructions;
  const at = new Date().toISOString();
  const record = {
    schema: 'gammatron-three-arm-phase-record/v1',
    runId: `next-${resolve(runDir).split('/').pop()}`,
    application,
    upgrade,
    arm: 'always-replan',
    phase: 'discovery',
    adapterSource: 'none',
    startedAt: at,
    endedAt: at,
    wallMs: 0,
    adapterAuthoringMinutes: 0,
    adapterMaintenanceMinutes: 0,
    guardAuthoringMinutes: 0,
    guardMaintenanceMinutes: 0,
    learnerWallMinutes: 0,
    authoringMinutes: 0,
    adapterOrGuardLoc: 0,
    trainingReleaseSha256: null,
    modelCalls: 0,
    modelTurns: 0,
    costUsd: 0,
    budgetUsd: 0,
    recordsCreated: 0,
    outOfSurfaceCalls: 0,
    artifactSha256: sha256(inst.ALWAYS_REPLAN + JSON.stringify(inst.DECISION_SCHEMA)),
    completed: true,
  };
  appendJsonl(runDir, 'phase-records.jsonl', record);
  return record;
}

/**
 * Evaluates unseen recipes for one arm on a fresh instance, enforcing:
 *   - stripped `forArm(application, route)` input (never `routeId`, `entryBranch`, `steps`);
 *   - frozen SHA-256 verification before any route runs;
 *   - setup 403 / refusal capture as `notTestable: true` without bypassing permissions;
 *   - final settle re-read on BOTH OpenProject and ERPNext (including `termsHoldsReference`).
 */
export async function runBlindArm({
  application,
  upgrade,
  arm,
  familiesFile,
  trainingExamplesFile,
  recipesFile,
  runDir,
  approvePaid = false,
  deps,
}) {
  if (!NEXT_ARMS.includes(arm)) throw Error(`arm must be one of ${NEXT_ARMS.join(', ')}`);
  prepareRunDir(runDir);
  const release = loadEqualTrainingRelease({ application, familiesFile, trainingExamplesFile });
  const rawRecipesDoc = JSON.parse(readFileSync(recipesFile, 'utf8'));
  const validateFile = application === 'openproject' ? validateOpRecipeFile : validateErpRecipeFile;
  const problems = validateFile(rawRecipesDoc);
  if (problems.length) throw Error(`recipesFile invalid: ${problems.join('; ')}`);

  const phases = existsSync(join(runDir, 'phase-records.jsonl'))
    ? readFileSync(join(runDir, 'phase-records.jsonl'), 'utf8').trim().split('\n').filter(Boolean).map(l => JSON.parse(l))
    : [];
  const frozen = phases.findLast(p => p.arm === arm && ['discovery', 'maintenance'].includes(p.phase) && p.application === application);
  if (!frozen?.completed) throw Error(`${arm} has no frozen artifact for ${application} in ${runDir}`);

  if (arm === 'always-replan' && !approvePaid && !deps.replanDecider) {
    throw Error('always-replan requires --approve-paid unless deps.replanDecider is supplied in tests');
  }

  const guardArms = ['expert-guard', 'agent-written-guard', 'rule-selector'];
  const guardDir = guardArms.includes(arm) ? join(runDir, 'artifacts', arm) : null;
  if (guardDir && hashDirectory(guardDir) !== frozen.artifactSha256) {
    throw Error(`${arm} artifact changed after freeze`);
  }
  const boundaryPath = arm === 'repair-boundary' ? join(runDir, 'artifacts', 'repair-boundary.json') : null;
  const boundaryText = boundaryPath ? readFileSync(boundaryPath, 'utf8') : null;
  if (boundaryText !== null && sha256(boundaryText) !== frozen.artifactSha256) {
    throw Error('repair-boundary artifact changed after freeze');
  }

  const startedAt = new Date();
  let costUsd = 0;
  let modelCalls = 0;
  let modelTurns = 0;
  let outOfSurfaceCalls = 0;
  const held = [];

  deps.freshInstance();
  let writer = null;
  try {
    const state = deps.readState();
    const request = deps.requester(state.new);
    const contrastBundle = arm === 'always-replan'
      ? await buildEqualContrastBundle({ application, release, request, seed: state.new.seed, tagPrefix: 'replan' })
      : null;
    writer = await deps.openWriter(state);

    for (const recipe of rawRecipesDoc.recipes) {
      const provisioned = await provisionWithRefusalCapture({
        application, recipe, request, seed: state.new.seed, tag: `b-${recipe.routeId}`,
      });
      if (provisioned.notTestable) {
        appendJsonl(runDir, 'route-records.jsonl', {
          schema: 'gammatron-next-not-testable-record/v1',
          runId: `next-${resolve(runDir).split('/').pop()}`,
          application,
          upgrade,
          release: state.new.tag ?? null,
          arm,
          routeId: recipe.routeId,
          notTestable: true,
          refusal: provisioned.refusal,
        });
        continue;
      }

      const route = provisioned.route;
      const armInput = forArm(application, route);
      const targetKey = application === 'openproject' ? route.workPackageId : route.name;
      const before = writer.readRow(targetKey);
      const began = Date.now();
      let answer = { decision: 'stop', reason: null, reads: 0, modelCalls: 0, costUsd: 0, error: null };

      try {
        const get = application === 'openproject'
          ? path => createAppSurface({ mode: 'decision', request, limits: DEFAULT_LIMITS }).tools.app_get({ path })
          : path => createErpSurface({ mode: 'decision', request, limits: ERP_LIMITS }).tools.erp_get({ path });

        if (guardDir) {
          const res = await deps.guardRunner({ guardDir, route: armInput, get });
          answer = { ...answer, decision: res.decision, reason: res.reason, reads: res.reads, error: res.error };
        } else if (arm === 'repair-boundary') {
          const artifact = JSON.parse(boundaryText);
          const res = application === 'openproject'
            ? await decideOpBoundary(artifact, armInput, get)
            : await decideErpBoundary(artifact, armInput, get);
          answer = { ...answer, ...res };
        } else if (deps.replanDecider) {
          const fam = contrastBundle.find(f => f.familyId === route.familyId);
          const res = await deps.replanDecider({ family: fam, route: armInput, get });
          answer = { ...answer, ...res };
        } else {
          throw Error('live model session requires CLI configuration');
        }
      } catch (error) {
        answer = { ...answer, decision: 'stop', error: String(error?.message ?? error).slice(0, 240) };
      }

      const decisionWallMs = Date.now() - began;
      const wrote = answer.decision === 'write' ? await writer.write(route) : null;
      const after = wrote ? structuredClone(wrote.after) : structuredClone(writer.readRow(targetKey));
      if (application === 'erpnext' && typeof writer.holdsReference === 'function') {
        after.termsHoldsReference = Boolean(writer.holdsReference(route.name, route.reference));
      }

      costUsd += answer.costUsd;
      modelCalls += answer.modelCalls;

      const committed = application === 'openproject'
        ? after.lockVersion !== before.lockVersion
        : after.modified !== before.modified;
      const effectMatches = application === 'openproject'
        ? committed && Number(after.estimatedHours) === Number(route.workHours)
        : committed && (typeof after.terms === 'string'
          ? after.terms.includes(route.reference)
          : Boolean(after.termsHoldsReference));

      held.push({
        targetKey,
        route,
        record: {
          schema: 'gammatron-next-route-record/v1',
          runId: `next-${resolve(runDir).split('/').pop()}`,
          application,
          upgrade,
          arm,
          routeId: route.routeId,
          decision: answer.decision,
          stopReason: answer.decision === 'stop' ? (answer.reason ?? null) : null,
          writeAttempted: wrote !== null,
          httpStatus: wrote?.httpStatus ?? null,
          before,
          after,
          committed,
          effectMatches,
          ...(application === 'openproject' ? { workHours: route.workHours } : { reference: route.reference }),
          reads: answer.reads,
          modelCalls: answer.modelCalls,
          costUsd: answer.costUsd,
          decisionWallMs,
          artifactSha256: frozen.artifactSha256,
          error: answer.error ?? wrote?.error ?? null,
        },
      });
    }

    // Final settle re-read on every route before instance teardown (fixes ERPNext holdsReference settle check)
    for (const { targetKey, route, record } of held) {
      try {
        const final = structuredClone(writer.readRow(targetKey));
        if (application === 'erpnext' && typeof writer.holdsReference === 'function') {
          final.termsHoldsReference = Boolean(writer.holdsReference(route.name, route.reference));
        }
        const changed = application === 'openproject'
          ? (final.lockVersion !== record.after.lockVersion || Number(final.estimatedHours) !== Number(record.after.estimatedHours))
          : (final.modified !== record.after.modified || final.termsHoldsReference !== record.after.termsHoldsReference || final.terms !== record.after.terms);
        if (changed) {
          record.after = final;
          record.committed = application === 'openproject'
            ? final.lockVersion !== record.before.lockVersion
            : final.modified !== record.before.modified;
          record.effectMatches = application === 'openproject'
            ? record.committed && Number(final.estimatedHours) === Number(record.workHours)
            : record.committed && (typeof final.terms === 'string'
              ? final.terms.includes(record.reference)
              : Boolean(final.termsHoldsReference));
          record.error = [record.error, 'the row changed after its first reading; the final reading is recorded'].filter(Boolean).join('; ');
        }
      } catch (error) {
        record.error = [record.error, `final reading failed: ${String(error?.message ?? error).slice(0, 160)}`].filter(Boolean).join('; ');
      }
      appendJsonl(runDir, 'route-records.jsonl', record);
    }
  } finally {
    await writer?.close();
    deps.stopInstance();
  }

  const endedAt = new Date();
  const phaseRecord = {
    schema: 'gammatron-three-arm-phase-record/v1',
    runId: `next-${resolve(runDir).split('/').pop()}`,
    application,
    upgrade,
    arm,
    phase: 'blind-routes',
    adapterSource: 'none',
    startedAt: startedAt.toISOString(),
    endedAt: endedAt.toISOString(),
    wallMs: endedAt - startedAt,
    adapterAuthoringMinutes: 0,
    adapterMaintenanceMinutes: 0,
    guardAuthoringMinutes: 0,
    guardMaintenanceMinutes: 0,
    learnerWallMinutes: 0,
    authoringMinutes: 0,
    adapterOrGuardLoc: 0,
    trainingReleaseSha256: release.trainingReleaseSha256,
    modelCalls,
    modelTurns,
    costUsd: Number(costUsd.toFixed(6)),
    budgetUsd: arm === 'always-replan' ? DEFAULT_STAGE_CONFIG.route.budgetUsd * rawRecipesDoc.recipes.length : 0,
    recordsCreated: 0,
    outOfSurfaceCalls,
    artifactSha256: null,
    completed: true,
  };
  appendJsonl(runDir, 'phase-records.jsonl', phaseRecord);
  return phaseRecord;
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const [cmd] = process.argv.slice(2);
  if (cmd === 'hash') {
    const frozen = frozenNextFileSet();
    for (const e of frozen.entries) console.log(`${e.sha256}  ${e.file}`);
    console.log(`\nnext-runner sha256: ${frozen.sha256}`);
  } else {
    console.error('usage: three-arm-next/runner.mjs hash');
    process.exit(2);
  }
}
