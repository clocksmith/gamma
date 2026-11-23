#!/usr/bin/env node
// The MCP server one ERPNext arm session talks to (clocksmith/deco#88). DRAFT.
// The application door from erp-surface.mjs plus the few tools that arm needs:
//
//   agent-written-guard, discovery or maintenance   erp_request, try_guard
//   repair-boundary, discovery or maintenance       erp_request, set_read_plan, add_example, learn
//   always-replan, decision                         erp_get
//
// Started by the model CLI through --mcp-config; configured by GAMMATRON_ARM_SERVER (JSON).
import { appendFileSync, readFileSync, writeFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { createToolHandler, serveStdio } from '../three-arm/app-surface.mjs';
import { runGuard } from '../three-arm/guard-sandbox.mjs';
import { erpRequester, readErpState } from './erp-app.mjs';
import { createTeacher } from './erp-learner.mjs';
import { createErpSurface, ERP_LIMITS, ERP_TOOL_DEFINITIONS } from './erp-surface.mjs';

const ORDER = { familyId: { type: 'string' }, name: { type: 'string', description: 'Name of the Purchase Order, for example PUR-ORD-2026-00003.' } };
export const ERP_ARM_TOOL_DEFINITIONS = Object.freeze({
  try_guard: {
    name: 'try_guard',
    description: 'Run guard.mjs from your working directory on one Purchase Order, exactly as it will be run later: no network, and get() limited to '
      + 'reading documents as the approver, at most 8 per order. Returns its decision or its error.',
    inputSchema: { type: 'object', additionalProperties: false, required: ['familyId', 'name'],
      properties: { ...ORDER, reference: { type: 'string', description: 'The reference the write would add. Optional.' } } },
  },
  set_read_plan: {
    name: 'set_read_plan',
    description: 'Choose the reads the learner makes on every order of one family, at most three. Each read has a role and either target: true, or '
      + 'follow: { role, field, doctype } to read the document named in a field of an earlier read. Clears that family\'s examples.',
    inputSchema: { type: 'object', additionalProperties: false, required: ['familyId', 'reads'], properties: {
      familyId: { type: 'string' },
      reads: { type: 'array', minItems: 1, maxItems: 3, items: { type: 'object', additionalProperties: false, required: ['role'], properties: {
        role: { type: 'string' }, target: { type: 'boolean' },
        follow: { type: 'object', additionalProperties: false, required: ['role', 'field', 'doctype'],
          properties: { role: { type: 'string' }, field: { type: 'string' }, doctype: { type: 'string' } } },
      } } },
    } },
  },
  add_example: {
    name: 'add_example',
    description: 'Label one Purchase Order you built as valid or invalid for a family. The reads in the plan are made as the approver and the facts the learner can see are returned.',
    inputSchema: { type: 'object', additionalProperties: false, required: ['familyId', 'label', 'name'],
      properties: { ...ORDER, label: { type: 'string', enum: ['valid', 'invalid'] } } },
  },
  learn: {
    name: 'learn',
    description: 'Derive the guard for one family from its examples. Returns the guard, or the reason none was found.',
    inputSchema: { type: 'object', additionalProperties: false, required: ['familyId'], properties: { familyId: { type: 'string' } } },
  },
});

const orderFrom = input => {
  const name = String(input?.name ?? '');
  if (!/^[A-Za-z0-9_-]{1,64}$/.test(name)) throw Error('name must be the name of a Purchase Order');
  return { familyId: String(input?.familyId ?? ''), doctype: 'Purchase Order', name,
    reference: typeof input?.reference === 'string' ? input.reference.slice(0, 24) : 'CONF-TRY' };
};

export function createErpArmTools({ arm, phase, request, log = () => {}, trace = () => {}, limits = ERP_LIMITS, workDir, familyIds = [],
  saveArtifact = () => {}, restore = null, guardRunner = runGuard }) {
  const reader = () => createErpSurface({ mode: 'decision', request, log, limits }).tools.erp_get;
  const note = (tool, detail) => log({ at: new Date().toISOString(), tool, ...detail });
  if (phase === 'decision') {
    if (arm !== 'always-replan') throw Error('only always-replan uses a model session to decide a route');
    return { tools: createErpSurface({ mode: 'decision', request, log, limits }).tools, definitions: [ERP_TOOL_DEFINITIONS.erp_get] };
  }
  if (!['discovery', 'maintenance'].includes(phase)) throw Error('phase must be discovery, maintenance or decision');
  const tools = { ...createErpSurface({ mode: 'discovery', request, log, trace, limits }).tools };
  const definitions = [ERP_TOOL_DEFINITIONS.erp_request];
  if (arm === 'agent-written-guard') {
    tools.try_guard = async input => {
      const route = orderFrom(input);
      const result = await guardRunner({ guardDir: workDir, route, get: path => reader()({ path }) });
      note('try_guard', { name: route.name, decision: result.decision, reads: result.reads });
      return { ok: true, decision: result.decision, reason: result.reason, error: result.error, reads: result.reads };
    };
    definitions.push(ERP_ARM_TOOL_DEFINITIONS.try_guard);
  } else if (arm === 'repair-boundary') {
    const teacher = createTeacher(familyIds, restore);
    const save = () => saveArtifact(teacher.freeze().text);
    save();
    tools.set_read_plan = async input => { const r = teacher.setReadPlan(input?.familyId, input?.reads); note('set_read_plan', { familyId: input?.familyId, ok: r.ok }); save(); return r; };
    tools.add_example = async input => {
      const route = orderFrom(input);
      const r = await teacher.addExample(route.familyId, input?.label, route, path => reader()({ path }));
      note('add_example', { familyId: route.familyId, label: input?.label, name: route.name, ok: r.ok });
      save();
      return r;
    };
    tools.learn = async input => { const b = teacher.learn(input?.familyId); note('learn', { familyId: input?.familyId, status: b.status, reason: b.reason ?? null }); save(); return { ok: true, ...b }; };
    definitions.push(ERP_ARM_TOOL_DEFINITIONS.set_read_plan, ERP_ARM_TOOL_DEFINITIONS.add_example, ERP_ARM_TOOL_DEFINITIONS.learn);
  } else {
    throw Error('always-replan has no discovery or maintenance phase');
  }
  return { tools, definitions };
}

async function main() {
  const config = JSON.parse(process.env.GAMMATRON_ARM_SERVER ?? 'null');
  if (!config?.arm || !config.phase || !config.surfaceLog) throw Error('GAMMATRON_ARM_SERVER must name arm, phase and surfaceLog');
  const state = readErpState(config.stateFile);
  const set = createErpArmTools({
    arm: config.arm, phase: config.phase, workDir: config.workDir, familyIds: config.familyIds ?? [],
    restore: config.restoreArtifact ? JSON.parse(readFileSync(config.restoreArtifact, 'utf8')) : null,
    request: erpRequester(state[config.side ?? 'new']),
    limits: { ...ERP_LIMITS, ...(config.limits ?? {}) },
    log: entry => appendFileSync(config.surfaceLog, JSON.stringify({ arm: config.arm, ...entry }) + '\n', { mode: 0o600 }),
    trace: entry => { if (config.traceFile) appendFileSync(config.traceFile, JSON.stringify(entry) + '\n', { mode: 0o600 }); },
    saveArtifact: text => { if (config.artifactFile) writeFileSync(config.artifactFile, text, { mode: 0o600 }); },
  });
  serveStdio(createToolHandler(set, message => process.stdout.write(JSON.stringify(message) + '\n')));
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) await main();
