#!/usr/bin/env node
// Fawn workspace qualification — service host process driven over stdin/stdout JSON lines.
//
// Lets the runner and tests kill the real service process at declared points, reopen its state
// directory, and issue commands concurrently so handoff can race admission and dispatch.
// Usage: node service-host.js '{"stateDir": "...", "adapter": "fake"|"playwright"|"cdp", ...}'

import { createInterface } from 'node:readline';
import { writeSync } from 'node:fs';
import { loadServiceConfig } from '../src/config.js';
import { WorkspaceService } from '../src/service.js';
import { createOwnerSession } from '../src/workflows/owner-session.js';
import { recoverArtifactExport, runArtifactExport } from '../src/workflows/artifact-export.js';
import { runDocumentResearch } from '../src/workflows/document-research.js';
import { recoverFormSubmission, runFormSubmission } from '../src/workflows/form-submission.js';

const options = JSON.parse(process.argv[2]);

function emit(message) {
  process.stdout.write(`${JSON.stringify(message)}\n`);
}

function errorFields(error) {
  return { code: error.code ?? null, message: error.message };
}

const ADAPTERS = Object.freeze({
  fake: async () => {
    const { FakeAdapter } = await import('../test/support/fake-adapter.js');
    return () => new FakeAdapter({ receiptsPath: options.receiptsPath });
  },
  playwright: async () => (await import('../src/adapters/playwright-adapter.js')).createPlaywrightAdapter,
  cdp: async () => (await import('../src/adapters/cdp-adapter.js')).createCdpAdapter,
});

const WORKFLOWS = Object.freeze({
  research: runDocumentResearch,
  form: runFormSubmission,
  'form-recovery': recoverFormSubmission,
  export: runArtifactExport,
  'export-recovery': recoverArtifactExport,
});

// Hooks: a declared crash point kills this process; race arrangements register one-shot hooks.
const raceHooks = {};
function serviceHooks(crash) {
  const hook = (name) => (request) => {
    if (crash?.hook === name && request.actionId.endsWith(crash.actionIdSuffix)) {
      // Synchronous pipe publication survives the immediate process kill.
      writeSync(1, `${JSON.stringify({ event: 'termination-requested', pid: process.pid, signal: 'SIGKILL' })}\n`);
      process.kill(process.pid, 'SIGKILL');
    }
    const raced = raceHooks[name];
    if (raced && request.actionId.endsWith(raced.actionIdSuffix)) {
      delete raceHooks[name];
      raceHooks.lastDispatched = request;
      raced.run();
    }
  };
  return {
    afterIntentPersisted: hook('afterIntentPersisted'),
    afterDispatchStarted: hook('afterDispatchStarted'),
    afterEffect: hook('afterEffect'),
    afterOutcome: hook('afterOutcome'),
  };
}

const loadAdapter = ADAPTERS[options.adapter];
if (!loadAdapter) {
  emit({ event: 'open-failed', error: { code: null, message: `unknown adapter ${options.adapter}` } });
  process.exit(1);
}

let service;
try {
  service = await WorkspaceService.open({
    stateDir: options.stateDir,
    config: loadServiceConfig(options.browserConfig ?? undefined, { browserChannel: options.browserChannel, headless: options.headless }),
    createAdapter: await loadAdapter(),
    hooks: serviceHooks(options.crash),
  });
} catch (error) {
  emit({ event: 'open-failed', error: errorFields(error) });
  process.exit(1);
}

const isEffect = (spec, fault) => spec.actionId.endsWith(fault.actionIdSuffix);
const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

// Test-only command faults: the workflow observes normally but selected mutations are altered.
const SESSION_FAULTS = Object.freeze({
  'stale-observation': (session) => ({
    ...session,
    submit: (observation, spec) => session.submit({ ...observation, observationVersion: observation.observationVersion - 1 }, spec),
  }),
  'stale-owner': (session, fault) => ({ ...session, submit: createOwnerSession(service, fault.owner).submit }),
  'effect-precondition': (session, fault) => ({
    ...session,
    submit: (observation, spec) => session.submit(observation, isEffect(spec, fault)
      ? { ...spec, preconditions: [...(spec.preconditions ?? []), fault.precondition] }
      : spec),
  }),
  'effect-kind': (session, fault) => ({
    ...session,
    submit: (observation, spec) => session.submit(observation, isEffect(spec, fault) ? { ...spec, kind: fault.actionKind } : spec),
  }),
  // The page changes after the workflow observed it and before the effect is submitted.
  'before-effect-control': (session, fault) => ({
    ...session,
    async submit(observation, spec) {
      if (isEffect(spec, fault)) {
        if (fault.controlUrl) await fetch(fault.controlUrl);
        await sleep(fault.settleMs);
      }
      return session.submit(observation, spec);
    },
  }),
});

function sessionFor(owner, fault, sessionOptions = {}) {
  const session = createOwnerSession(service, owner, sessionOptions);
  return fault ? SESSION_FAULTS[fault.kind](session, fault) : session;
}

function settle(promise) {
  return promise.then((value) => ({ value }), (error) => ({ error: errorFields(error) }));
}

/**
 * Run a workflow whose effect submission races a handoff. Orders:
 * - handoff-first: assignOwner is issued, then the effect is submitted in the same turn
 * - submit-first: the effect is submitted, then assignOwner after delayMs
 * - at-dispatch-start: assignOwner is issued when the effect's dispatch has been journaled
 */
async function raceWorkflow({ name, owner, task, race, sessionOptions }) {
  let handoff = null;
  const assign = () => {
    handoff = settle(service.assignOwner({
      workspaceId: owner.workspaceId,
      adminCredential: race.adminCredential,
      ownerId: race.nextOwnerId,
    }));
  };
  const session = createOwnerSession(service, owner, sessionOptions);
  let reached = false;
  const raced = {
    ...session,
    submit(observation, spec) {
      if (!isEffect(spec, race)) return session.submit(observation, spec);
      reached = true;
      if (race.order === 'handoff-first') {
        assign();
        return session.submit(observation, spec);
      }
      if (race.order === 'at-dispatch-start') {
        raceHooks.afterDispatchStarted = { actionIdSuffix: race.actionIdSuffix, run: assign };
        return session.submit(observation, spec);
      }
      const submitted = session.submit(observation, spec);
      if (race.delayMs === 0) assign();
      else setTimeout(assign, race.delayMs);
      return submitted;
    },
  };
  const outcome = await settle(WORKFLOWS[name](raced, task));
  // An effect that never reached dispatch leaves the hook unfired; hand off afterwards instead.
  const handoffAfterWorkflow = !reached || Boolean(raceHooks.afterDispatchStarted);
  delete raceHooks.afterDispatchStarted;
  if (handoffAfterWorkflow && !handoff) assign();
  while (!handoff) await sleep(race.delayMs || 1);
  return { outcome, handoff: await handoff, effectReached: reached, handoffAfterWorkflow };
}

const pendingResults = new Map();
const pendingAdmissions = new Map();

/**
 * When the effect's dispatch is journaled, admit `queued` citing the effect's own observation,
 * so it waits behind the in-flight effect. Page reads are unavailable while Chromium holds a
 * pending navigation, so the queued command cannot observe for itself.
 */
function queueBehindEffect({ actionIdSuffix, queued }) {
  let admit;
  pendingAdmissions.set(queued.actionId, new Promise((resolve) => {
    admit = resolve;
  }));
  raceHooks.afterDispatchStarted = {
    actionIdSuffix,
    run: () => {
      const effect = raceHooks.lastDispatched;
      const admitted = service.submitAction({ ...queued, observationVersion: effect.observationVersion });
      admit(admitted.then((entry) => {
        pendingResults.set(entry.actionId, entry.result);
        return { actionId: entry.actionId };
      }));
    },
  };
  return { registered: queued.actionId };
}

const OPERATIONS = Object.freeze({
  call: ({ method, args }) => service[method](args),
  submitAndWait: async (args) => (await service.submitAction(args)).result,
  // Admit without waiting for dispatch; `awaitAction` returns the settled record later.
  submit: async (args) => {
    const admitted = await service.submitAction(args);
    pendingResults.set(admitted.actionId, admitted.result);
    return { actionId: admitted.actionId };
  },
  awaitAction: ({ actionId }) => pendingResults.get(actionId),
  queueBehindEffect,
  awaitAdmission: ({ actionId }) => pendingAdmissions.get(actionId),
  workflow: ({ name, owner, task, fault, sessionOptions }) => WORKFLOWS[name](sessionFor(owner, fault, sessionOptions), task),
  // Counts the observation bytes returned to workflow logic, for the baseline comparison.
  async measuredWorkflow({ name, owner, task, fault, sessionOptions }) {
    let observationBytes = 0;
    const session = sessionFor(owner, fault, sessionOptions);
    const counted = {
      ...session,
      async observe() {
        const observation = await session.observe();
        observationBytes += Buffer.byteLength(JSON.stringify(observation));
        return observation;
      },
      act: session.act,
    };
    const result = await WORKFLOWS[name](counted, task);
    return { result, observationBytes };
  },
  raceWorkflow,
  // What workflow code can reach: the service exposes no fields and the session no browser handle.
  surface: ({ owner }) => {
    const session = createOwnerSession(service, owner);
    return {
      serviceOwnKeys: Reflect.ownKeys(service).map(String),
      serviceExposesAdapter: 'adapter' in service || '_adapter' in service,
      sessionKeys: Object.keys(session).sort(),
    };
  },
  close: async () => {
    await service.close();
    setImmediate(() => process.exit(0));
    return null;
  },
});

emit({ event: 'ready', pid: process.pid });
for await (const line of createInterface({ input: process.stdin })) {
  const { id, op, args } = JSON.parse(line);
  // Operations run concurrently; the service's own serialization decides their order.
  Promise.resolve()
    .then(() => OPERATIONS[op](args))
    .then((result) => emit({ id, ok: true, result }), (error) => emit({ id, ok: false, error: errorFields(error) }));
}

// The parent closed stdin (it exited or crashed): release the browser and journal.
await service.close();
process.exit(0);
