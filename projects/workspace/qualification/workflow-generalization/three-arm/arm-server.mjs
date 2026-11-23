#!/usr/bin/env node
// The MCP server one arm session talks to (clocksmith/deco#88, same-model
// three-arm test). It is the application door from app-surface.mjs plus the
// few tools that arm needs. Which tools exist depends on the arm and the phase:
//
//   agent-written-guard, discovery   app_request, try_guard
//   repair-boundary, discovery       app_request, set_read_plan, add_example, learn
//   always-replan, decision          app_get
//
// Started by the model CLI through --mcp-config; configured by GAMMATRON_ARM_SERVER (JSON).
import { appendFileSync, writeFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { createAppSurface, createToolHandler, DEFAULT_LIMITS, serveStdio, TOOL_DEFINITIONS } from './app-surface.mjs';
import { runGuard } from './guard-sandbox.mjs';
import { openProjectRequester, readState } from './provision.mjs';
import { createTeacher } from './repair-boundary-arm.mjs';

const ROUTE_PROPERTIES = {
  familyId: { type: 'string' },
  project: { type: 'string', description: 'Project identifier of the work package.' },
  workPackageId: { type: 'integer' },
  workHours: { type: 'integer', description: 'The hours the write would save as Work.' },
};
export const ARM_TOOL_DEFINITIONS = Object.freeze({
  try_guard: {
    name: 'try_guard',
    description: 'Run guard.mjs from your working directory on one work package, exactly as it will be run later: '
      + 'no network, and get() limited to read-only API v3 calls as the approver, at most 8 per route. Returns its decision or its error.',
    inputSchema: { type: 'object', additionalProperties: false, required: ['familyId', 'project', 'workPackageId', 'workHours'], properties: ROUTE_PROPERTIES },
  },
  set_read_plan: {
    name: 'set_read_plan',
    description: 'Choose the reads the learner makes on every route of one family, at most three. Each read has a role and either '
      + 'a path that may hold {target}, or follow: { role, link } to take a link from the body of an earlier read. Clears that family\'s examples.',
    inputSchema: { type: 'object', additionalProperties: false, required: ['familyId', 'reads'], properties: {
      familyId: { type: 'string' },
      reads: { type: 'array', minItems: 1, maxItems: 3, items: { type: 'object', additionalProperties: false, required: ['role'], properties: {
        role: { type: 'string' }, path: { type: 'string' },
        follow: { type: 'object', additionalProperties: false, required: ['role', 'link'], properties: { role: { type: 'string' }, link: { type: 'string' } } },
      } } },
    } },
  },
  add_example: {
    name: 'add_example',
    description: 'Label one work package you built as valid or invalid for a family. The reads in the plan are made as the approver '
      + 'and the facts the learner can see are returned.',
    inputSchema: { type: 'object', additionalProperties: false, required: ['familyId', 'label', 'project', 'workPackageId', 'workHours'],
      properties: { ...ROUTE_PROPERTIES, label: { type: 'string', enum: ['valid', 'invalid'] } } },
  },
  learn: {
    name: 'learn',
    description: 'Derive the guard for one family from its examples. Returns the guard, or the reason none was found.',
    inputSchema: { type: 'object', additionalProperties: false, required: ['familyId'], properties: { familyId: { type: 'string' } } },
  },
});

const routeFrom = input => {
  const route = { familyId: String(input?.familyId ?? ''), project: String(input?.project ?? ''),
    workPackageId: Number(input?.workPackageId), workHours: Number(input?.workHours) };
  if (!Number.isSafeInteger(route.workPackageId) || route.workPackageId < 1) throw Error('workPackageId must be a positive integer');
  if (!Number.isSafeInteger(route.workHours) || route.workHours < 1 || route.workHours > 999) throw Error('workHours must be an integer from 1 to 999');
  return route;
};

/** Builds the tool set for one arm and phase. `request` reaches the instance; `log` receives every call. */
export function createArmTools({ arm, phase, request, log = () => {}, limits = DEFAULT_LIMITS, workDir, familyIds = [],
  saveArtifact = () => {}, guardRunner = runGuard }) {
  const reader = () => createAppSurface({ mode: 'decision', request, log, limits }).tools.app_get;
  const note = (tool, detail) => log({ at: new Date().toISOString(), tool, ...detail });
  if (phase === 'decision') {
    if (arm !== 'always-replan') throw Error('only always-replan uses a model session to decide a route');
    const surface = createAppSurface({ mode: 'decision', request, log, limits });
    return { tools: surface.tools, definitions: [TOOL_DEFINITIONS.app_get] };
  }
  if (phase !== 'discovery') throw Error('phase must be discovery or decision');
  const surface = createAppSurface({ mode: 'discovery', request, log, limits });
  const tools = { ...surface.tools };
  const definitions = [TOOL_DEFINITIONS.app_request];
  if (arm === 'agent-written-guard') {
    tools.try_guard = async input => {
      const route = routeFrom(input);
      const result = await guardRunner({ guardDir: workDir, route, get: path => reader()({ path }) });
      note('try_guard', { workPackageId: route.workPackageId, decision: result.decision, reads: result.reads });
      return { ok: true, decision: result.decision, reason: result.reason, error: result.error, reads: result.reads };
    };
    definitions.push(ARM_TOOL_DEFINITIONS.try_guard);
  } else if (arm === 'repair-boundary') {
    const teacher = createTeacher(familyIds);
    const save = () => saveArtifact(teacher.freeze().text);
    save();
    tools.set_read_plan = async input => {
      const result = teacher.setReadPlan(input?.familyId, input?.reads);
      note('set_read_plan', { familyId: input?.familyId, ok: result.ok });
      save();
      return result;
    };
    tools.add_example = async input => {
      const route = routeFrom(input);
      const result = await teacher.addExample(route.familyId, input?.label, route, path => reader()({ path }));
      note('add_example', { familyId: route.familyId, label: input?.label, workPackageId: route.workPackageId, ok: result.ok });
      save();
      return result;
    };
    tools.learn = async input => {
      const boundary = teacher.learn(input?.familyId);
      note('learn', { familyId: input?.familyId, status: boundary.status, reason: boundary.reason ?? null });
      save();
      return { ok: true, ...boundary };
    };
    definitions.push(ARM_TOOL_DEFINITIONS.set_read_plan, ARM_TOOL_DEFINITIONS.add_example, ARM_TOOL_DEFINITIONS.learn);
  } else {
    throw Error('always-replan has no discovery phase');
  }
  return { tools, definitions };
}

async function main() {
  const config = JSON.parse(process.env.GAMMATRON_ARM_SERVER ?? 'null');
  if (!config?.arm || !config.phase || !config.surfaceLog) throw Error('GAMMATRON_ARM_SERVER must name arm, phase and surfaceLog');
  const state = readState(config.stateFile);
  const set = createArmTools({
    arm: config.arm, phase: config.phase, workDir: config.workDir, familyIds: config.familyIds ?? [],
    request: openProjectRequester(state[config.side ?? 'new']),
    limits: { ...DEFAULT_LIMITS, ...(config.limits ?? {}) },
    log: entry => appendFileSync(config.surfaceLog, JSON.stringify({ arm: config.arm, ...entry }) + '\n', { mode: 0o600 }),
    saveArtifact: text => { if (config.artifactFile) writeFileSync(config.artifactFile, text, { mode: 0o600 }); },
  });
  serveStdio(createToolHandler(set, message => process.stdout.write(JSON.stringify(message) + '\n')));
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) await main();
