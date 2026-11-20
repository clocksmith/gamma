// Fawn workspace differentiation — treatment tools: the agent as a client of the workspace service.
//
// Observations use the outline view with deltas against the agent's previous version; unchanged
// regions come from the agent's own cache. Each action cites the observation its decision used
// and binds staleness to the regions that decision read. A handoff makes the agent wait for
// ownership and observe again before acting. A profile supplies each application's views,
// actions and interrupted-effect resolution.

const OWNERSHIP_POLL_MS = 50;
const OWNERSHIP_WAIT_MS = 30000;
const OUTCOME_POLL_MS = 50;
const OUTCOME_WAIT_MS = 20000;
const REDECIDE_CODES = Object.freeze(['stale-observation', 'target-changed', 'precondition-unestablished', 'expired-observation']);
const OWNERSHIP_CODES = Object.freeze(['stale-owner-generation', 'unauthenticated']);

class AgentKilled extends Error {
  constructor() {
    super('agent process ended');
    this.code = 'agent-killed';
  }
}

class Redecide extends Error {
  constructor(code) {
    super(`refused: ${code}`);
    this.code = code;
    this.redecide = true;
  }
}

class FawnAgent {
  constructor({ host, identity, checkpoint, thinkTimeMs, task, profile }) {
    this.host = host;
    this.profile = profile;
    this.identity = identity;
    this.checkpoint = checkpoint;
    this.thinkTimeMs = thinkTimeMs;
    this.task = task;
    this.observationBytes = 0;
    this.dead = false;
    this._base = null;
    this._citable = null;
    this._cache = new Map();
    this._sequence = 0;
  }

  kill() {
    this.dead = true;
  }

  _live() {
    if (this.dead) throw new AgentKilled();
  }

  async _call(method, args) {
    this._live();
    const result = await this.host.call(method, { ...this.identity.current(), ...args });
    this._live();
    return result;
  }

  /** Wait until the workspace is handed back to this agent under a newer generation. */
  async _awaitOwnership() {
    const stale = this.identity.current().ownerGeneration;
    const deadline = Date.now() + OWNERSHIP_WAIT_MS;
    while (this.identity.current().ownerGeneration <= stale) {
      if (Date.now() > deadline) throw new Error('ownership did not return to the agent');
      await new Promise((resolve) => setTimeout(resolve, OWNERSHIP_POLL_MS));
      this._live();
    }
    this._base = null;
  }

  async _observe(read) {
    let observed;
    try {
      observed = await this._call('observe', { view: 'outline', ...read, ...(this._base ? { sinceVersion: this._base } : {}) });
    } catch (error) {
      if (!OWNERSHIP_CODES.includes(error.code)) throw error;
      await this._awaitOwnership();
      return this._observe(read);
    }
    this.observationBytes += Buffer.byteLength(JSON.stringify(observed));
    const regions = {};
    for (const [selector, entry] of Object.entries(observed.regions)) {
      if (entry.missing) continue;
      if (entry.outline !== undefined) this._cache.set(selector, entry.outline);
      regions[selector] = this._cache.get(selector) ?? '';
    }
    this._base = observed.observationVersion;
    this._citable = observed.observationVersion;
    return { version: observed.observationVersion, url: observed.url, regions };
  }

  async view(kind) {
    const observed = await this._observe(this.profile.views[kind]);
    return this.profile.parsers[kind](observed.regions, observed.version);
  }

  /** Submit one action; refusals that call for a fresh decision become Redecide. */
  async _submit(spec) {
    let record;
    try {
      this._live();
      record = await this.host.submitAndWait({ ...this.identity.current(), ...spec });
      this._live();
    } catch (error) {
      if (error.code === 'agent-killed') throw error;
      if (OWNERSHIP_CODES.includes(error.code)) {
        await this._awaitOwnership();
        throw new Redecide(error.code);
      }
      if (REDECIDE_CODES.includes(error.code)) throw new Redecide(error.code);
      throw error;
    }
    if (record.postObservationVersion) this._citable = record.postObservationVersion;
    if (record.dispatchStatus === 'never-dispatched') {
      if (OWNERSHIP_CODES.includes(record.neverDispatched.code)) await this._awaitOwnership();
      throw new Redecide(record.neverDispatched.code);
    }
    if (record.outcome !== 'completed') throw new Error(`${spec.actionId}: ${record.outcome} (${record.outcomeBasis})`);
    return record;
  }

  _actionId(label) {
    this._sequence += 1;
    return `${this.task.id}-${this.checkpoint.get().incarnation ?? 0}-${this._sequence}-${label}`;
  }

  async navigate(url) {
    if (this._citable === null) await this._observe({ regions: ['h1'] });
    const spec = (version) => ({
      actionId: this._actionId('navigate'),
      authorizedIntent: this.task.intent,
      kind: 'navigate',
      target: { url },
      observationVersion: version,
      observationScope: { kind: 'regions', selectors: [] },
    });
    try {
      await this._submit(spec(this._citable));
    } catch (error) {
      if (!error.redecide) throw error;
      await this._observe({ regions: ['h1'] });
      await this._submit(spec(this._citable));
    }
  }

  async act(kind, target, options = {}) {
    const helpers = {
      task: this.task,
      sequence: () => this._sequence,
      actionId: (label) => this._actionId(label),
      scoped: (selectors) => ({ observationVersion: target.version, observationScope: { kind: 'regions', selectors } }),
      base: { authorizedIntent: this.task.intent, target: { handle: target.handle } },
    };
    const record = await this._submit(this.profile.actions[kind](target, options, helpers));
    return this.profile.results[kind]?.(record) ?? record;
  }

  outstanding() {
    return this._call('outstanding', {});
  }

  acknowledge(actionId) {
    return this._call('acknowledge', { actionId });
  }

  /** The workspace kept dispatching while the agent was gone; its record says what happened. */
  async resolveInterrupted() {
    const { effectKey, idFrom } = this.profile.interrupted(this.task);
    const deadline = Date.now() + OUTCOME_WAIT_MS;
    for (;;) {
      const effect = (await this.outstanding()).filter((entry) => entry.effectKey === effectKey).at(-1);
      if (!effect || effect.dispatchStatus === 'never-dispatched') return { retry: true };
      if (effect.outcome === 'completed') {
        await this.acknowledge(effect.actionId);
        return { id: idFrom(effect) };
      }
      if (effect.outcome !== null) return { humanReview: true, reason: `effect outcome ${effect.outcome}` };
      if (Date.now() > deadline) return { humanReview: true, reason: 'effect dispatch has not settled' };
      await new Promise((resolve) => setTimeout(resolve, OUTCOME_POLL_MS));
    }
  }
}

/** The URL a completed navigation-style effect ended on, from its completion evidence. */
function completedUrl(record) {
  return record.evidence?.conditions?.results?.[0]?.observed ?? '';
}

export { FawnAgent, Redecide, completedUrl };
