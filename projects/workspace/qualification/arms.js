// Fawn workspace differentiation — the two arms' hosts, shared by every differentiation runner.
//
// The treatment arm hosts the workspace service with an agent grant; the control arm hosts
// Playwright agent tooling. Both start fresh per run, take human control the same way, and
// release their browsers before the next run.

import { mkdtempSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { loadServiceConfig } from '../src/config.js';
import { Checkpoint } from './agents/checkpoint.js';
import { FawnAgent } from './agents/fawn-agent.js';
import { PlaywrightAgent } from './agents/playwright-agent.js';
import { inspectBrowserProcesses, waitForProfileRelease } from './identity.js';
import { startHost } from './service-client.js';

const TOOL_HOST = fileURLToPath(new URL('./agents/playwright-tool-host.js', import.meta.url));
const WORKSPACE_ID = 'ws-differentiation';
const AGENT_ID = 'agent';
const HUMAN_ID = 'human-operator';
const AGENT_ACTION_KINDS = Object.freeze(['navigate', 'click', 'fill', 'submit', 'download']);
const POLL_MS = 25;
// Perturbation timing shared by both arms and every differentiation runner: how long a person
// keeps control after typing (a multiple of the agent's think time), and how long a killed agent
// takes to come back.
const HUMAN_HOLD_FACTOR = 2;
const AGENT_RESTART_DELAY_MS = 1500;

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

function median(values) {
  const sorted = [...values].sort((a, b) => a - b);
  if (sorted.length === 0) return null;
  const middle = Math.floor(sorted.length / 2);
  return sorted.length % 2 ? sorted[middle] : (sorted[middle - 1] + sorted[middle]) / 2;
}

async function until(predicate, limitMs, description) {
  const deadline = Date.now() + limitMs;
  while (!predicate()) {
    if (Date.now() > deadline) throw new Error(`timed out waiting for ${description}`);
    await sleep(POLL_MS);
  }
}

/** Shared by the control's tools: every call waits while a human holds the browser. */
function createPause() {
  let held = false;
  let takeovers = 0;
  const waiters = [];
  return {
    hold() {
      held = true;
      takeovers += 1;
    },
    takeovers: () => takeovers,
    release() {
      held = false;
      for (const resolve of waiters.splice(0)) resolve();
    },
    whileHeld: () => (held ? new Promise((resolve) => waiters.push(resolve)) : Promise.resolve()),
  };
}

class Arm {
  constructor({ name, site, scenario, definition, browserChannel = null, browserConfig = null }) {
    this.name = name;
    this.site = site;
    this.scenario = scenario;
    this.definition = definition;
    this.browserChannel = browserChannel;
    this.browserConfig = browserConfig;
    this.root = mkdtempSync(join(tmpdir(), `fawn-differentiation-${name}-`));
    this.stateDir = join(this.root, 'state');
    this.checkpointPath = join(this.root, 'checkpoint.json');
    this.inspections = [];
    this.pause = createPause();
    this.owner = null;
  }

  async start() {
    if (this.name === 'treatment') {
      this.host = await startHost({ stateDir: this.stateDir, adapter: 'playwright', browserChannel: this.browserChannel, browserConfig: this.browserConfig });
      const { adminCredential } = await this.host.call('createWorkspace', { workspaceId: WORKSPACE_ID });
      this.adminCredential = adminCredential;
      await this.host.call('grantAuthorization', {
        workspaceId: WORKSPACE_ID,
        adminCredential,
        grantId: 'agent-task',
        ownerId: AGENT_ID,
        intents: [this.definition.intent],
        actionKinds: this.definition.actionKinds ?? AGENT_ACTION_KINDS,
        targetOrigins: [this.site.origin],
      });
      await this.assign(AGENT_ID);
    } else {
      this.host = await startHost({ stateDir: this.stateDir, actionTimeoutMs: loadServiceConfig().dispatch.actionTimeoutMs,
        headless: true, browserChannel: this.browserChannel, browserConfig: this.browserConfig }, TOOL_HOST);
    }
  }

  async assign(ownerId) {
    const assigned = await this.host.call('assignOwner', { workspaceId: WORKSPACE_ID, adminCredential: this.adminCredential, ownerId });
    if (ownerId === AGENT_ID) {
      this.owner = { workspaceId: WORKSPACE_ID, ownerId, ownerGeneration: assigned.ownerGeneration, ownerCredential: assigned.ownerCredential };
    }
    return assigned;
  }

  createAgent(task, thinkTimeMs, incarnation) {
    const checkpoint = new Checkpoint(this.checkpointPath);
    checkpoint.update({ incarnation });
    if (this.name === 'treatment') {
      return new FawnAgent({ host: this.host, identity: { current: () => this.owner }, checkpoint, thinkTimeMs, task, profile: this.definition.profiles.treatment });
    }
    return new PlaywrightAgent({
      host: this.host,
      pause: this.pause,
      checkpoint,
      thinkTimeMs,
      task,
      profile: this.definition.profiles.control,
      ...this.definition.controlOptions,
    });
  }

  /** A human takes the browser, types an address, keeps control for a while, and hands back. */
  async humanTakesControl(window, holdMs) {
    window.start = new Date().toISOString();
    if (this.name === 'treatment') await this.assign(HUMAN_ID);
    else this.pause.hold();
    const before = this.site.state.mutations.filter((entry) => entry.kind === 'human-fill').length;
    await fetch(`${this.site.origin}/control/human?fill=${encodeURIComponent(this.definition.humanFill)}`);
    await until(() => this.site.state.mutations.filter((entry) => entry.kind === 'human-fill').length > before, 10000, 'the human to type');
    await sleep(holdMs);
    window.end = new Date().toISOString();
    if (this.name === 'treatment') await this.assign(AGENT_ID);
    else this.pause.release();
  }

  inspect() {
    this.inspections.push(inspectBrowserProcesses(this.host.pid, this.stateDir));
  }

  async close() {
    await this.host.request('close', {}).catch(() => {});
    await this.host.exited;
    await waitForProfileRelease(this.stateDir);
    rmSync(this.root, { recursive: true, force: true });
  }
}


export { AGENT_ACTION_KINDS, AGENT_ID, AGENT_RESTART_DELAY_MS, Arm, createPause, HUMAN_HOLD_FACTOR, median, sleep, until };
