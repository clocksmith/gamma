// Fawn workspace differentiation — control tools: the agent over Playwright agent tooling.
//
// Each view takes a page-wide agent snapshot; the agent pays for the incremental text when there
// is one, and parses the full snapshot it is given alongside. Actions target aria refs from the
// latest snapshot. Consequential calls are checkpointed before and after, and every call waits
// while a human holds control. Two frozen control variants add behavior:
// - revalidate: before a mutation, take a fresh snapshot and re-check the decision's inputs
// - cancelOnTakeover: a call decided before a human takeover is cancelled and the agent observes
//   again, instead of resuming it
// A profile supplies each application's parsers, actions and interrupted-call resolution.

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

class PlaywrightAgent {
  constructor({ host, pause, checkpoint, thinkTimeMs, task, profile, revalidate = false, cancelOnTakeover = false }) {
    this.host = host;
    this.pause = pause;
    this.checkpoint = checkpoint;
    this.thinkTimeMs = thinkTimeMs;
    this.task = task;
    this.profile = profile;
    this.revalidate = revalidate;
    this.cancelOnTakeover = cancelOnTakeover;
    this.observationBytes = 0;
    this.dead = false;
    this._takeoversSeen = pause.takeovers();
  }

  kill() {
    this.dead = true;
  }

  _live() {
    if (this.dead) throw new AgentKilled();
  }

  async tool(op, args = {}, { consequential = false } = {}) {
    this._live();
    await this.pause.whileHeld();
    this._live();
    if (consequential && this.cancelOnTakeover && this.pause.takeovers() > this._takeoversSeen) {
      throw new Redecide('human-took-control');
    }
    if (consequential) this.checkpoint.update({ lastCall: { op, args, phase: 'calling' } });
    const result = await this.host.request(op, args);
    this._live();
    if (consequential) this.checkpoint.update({ lastCall: { op, args, phase: 'done' } });
    return result;
  }

  async snapshot() {
    const snapshot = await this.tool('snapshot');
    this._takeoversSeen = this.pause.takeovers();
    this.observationBytes += Buffer.byteLength(JSON.stringify({ url: snapshot.url, snapshot: snapshot.incremental ?? snapshot.full }));
    return snapshot;
  }

  async view(kind) {
    const snapshot = await this.snapshot();
    return this.profile.parsers[kind](snapshot.full.split('\n'));
  }

  requireAllowed(url) {
    if (new URL(url).origin !== this.task.origin) throw new Error(`origin of ${url} is not allowed`);
  }

  async navigate(url) {
    this.requireAllowed(url);
    await this.tool('navigate', { url });
  }

  /**
   * With revalidation, `options.revalidate` names the view to read again and a function that
   * returns the decision's target from the fresh view, or null when the decision no longer holds.
   */
  async act(kind, target, options = {}) {
    let current = target;
    if (this.revalidate && options.revalidate) {
      current = options.revalidate.find(await this.view(options.revalidate.view));
      if (!current) throw new Redecide('revalidation-failed');
    }
    return this.profile.act[kind](this, current, options);
  }

  resolveInterrupted(task, progress) {
    return this.profile.resolveInterrupted(this, task, progress);
  }
}

export { PlaywrightAgent, Redecide };
