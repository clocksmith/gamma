// Fawn workspace model-driven comparison — the two backends behind the identical tool interface.
//
// The model sees the same tools on both sides (tools.json). The treatment backs them with the
// workspace service; the control with Playwright agent tooling plus revalidation before every
// mutation and cancellation after human takeover, as frozen. Refusals use the same words on
// both sides, so only backend behavior differs.

import { loadServiceConfig } from '../../src/config.js';
import { controls } from '../agents/outline.js';

const OWNERSHIP_POLL_MS = 50;
const OWNERSHIP_WAIT_MS = 60000;
const OWNERSHIP_CODES = Object.freeze(['stale-owner-generation', 'unauthenticated']);
const STALE_CODES = Object.freeze(['stale-observation', 'target-changed', 'precondition-unestablished', 'expired-observation']);
const DEFAULT_REGIONS = Object.freeze(['body']);
const SELECT_ROLES = Object.freeze(['combobox', 'select']);
const MAX_SCOPE_REGIONS = loadServiceConfig().observation.maxRegions;

const MESSAGES = Object.freeze({
  stale: 'Refused: the page changed in a part your decision depended on, or the element changed, since your latest observation. Observe again and decide again.',
  takeover: 'Refused: a person took control of the browser while you were deciding; control has returned to you. Observe again before acting.',
  unknownElement: 'Refused: that element id is not in your latest observation. Observe again.',
  notObserved: (missing) => `Refused: depends_on names ${missing.join(', ')}, which your latest observation did not include. Observe those parts first.`,
  tooManyParts: (count, limit) => `Refused: depends_on covers ${count} page parts; at most ${limit} can be named. Name the parts your decision used.`,
  origin: 'Refused: only the application\'s own origin is allowed.',
  unauthorized: 'Refused: this task is not authorized for that action on this page.',
});

const ok = (text) => ({ text, isError: false });
const refused = (text) => ({ text, isError: true });

/** The treatment: the workspace service through its outline view, handles and observation scope. */
class FawnModelBackend {
  constructor({ host, identity, task, hooks }) {
    this.host = host;
    this.identity = identity;
    this.task = task;
    this.hooks = hooks;
    this.latest = null;
    this.citable = null;
    this.cache = new Map();
    this.sequence = 0;
  }

  /** The workspace records every outcome itself, so an ended agent process abandons nothing here. */
  kill() {}

  _actionId(label) {
    this.sequence += 1;
    return `${this.task.id}-${this.task.incarnation}-${this.sequence}-${label}`;
  }

  /** Wait until the workspace is handed back under a generation newer than the one used. */
  async _awaitOwnership(used) {
    const deadline = Date.now() + OWNERSHIP_WAIT_MS;
    while (this.identity.current().ownerGeneration <= used) {
      if (Date.now() > deadline) throw new Error('ownership did not return to the agent');
      await new Promise((resolve) => setTimeout(resolve, OWNERSHIP_POLL_MS));
    }
  }

  /** Like the control, every action decided before a handoff is cancelled until the agent observes again. */
  _decidedBeforeHandoff() {
    return Boolean(this.latest) && this.identity.current().ownerGeneration > this.latest.generation;
  }

  async observe({ regions = [], since_last: sinceLast = false } = {}) {
    const requested = regions.length ? regions : [...DEFAULT_REGIONS];
    const read = { view: 'outline', regionGroups: requested };
    if (sinceLast && this.latest) read.sinceVersion = this.latest.version;
    let observed;
    const identity = this.identity.current();
    try {
      observed = await this.host.call('observe', { ...identity, ...read });
    } catch (error) {
      if (!OWNERSHIP_CODES.includes(error.code)) throw error;
      await this._awaitOwnership(identity.ownerGeneration);
      return this.observe({ regions });
    }
    const resolved = {};
    const lines = [`URL: ${observed.url}`];
    for (const [selector, entry] of Object.entries(observed.regions)) {
      if (entry.missing) {
        lines.push(`[${selector}] not on this page`);
        continue;
      }
      if (entry.outline !== undefined) this.cache.set(selector, entry.outline);
      resolved[selector] = this.cache.get(selector) ?? '';
      lines.push(entry.unchanged ? `[${selector}] unchanged` : `[${selector}] ${entry.outline}`);
    }
    const groups = observed.regionGroups;
    for (const group of requested) if (!groups[group]?.length) lines.push(`[${group}] not on this page`);
    this.latest = { version: observed.observationVersion, url: observed.url, regions: resolved, groups, generation: identity.ownerGeneration };
    this.citable = observed.observationVersion;
    return ok(lines.join('\n'));
  }

  /** Role and name of an element in the latest observation, for perturbation hooks. */
  describe(element) {
    for (const [selector, outline] of Object.entries(this.latest?.regions ?? {})) {
      const control = controls(outline).find((candidate) => candidate.handle === element);
      if (control) return { ...control, region: selector };
    }
    return null;
  }

  /** A refusal after a handoff since the agent's observation reads as a takeover on both sides. */
  _staleOrTakeover() {
    return refused(this._decidedBeforeHandoff() ? MESSAGES.takeover : MESSAGES.stale);
  }

  async _submit(spec) {
    let record;
    const identity = this.identity.current();
    try {
      record = await this.host.submitAndWait({ ...identity, ...spec });
    } catch (error) {
      if (OWNERSHIP_CODES.includes(error.code)) {
        await this._awaitOwnership(identity.ownerGeneration);
        return refused(MESSAGES.takeover);
      }
      if (error.code === 'unknown-target') return refused(MESSAGES.unknownElement);
      if (STALE_CODES.includes(error.code)) return this._staleOrTakeover();
      if (error.code === 'unauthorized-target') return refused(MESSAGES.unauthorized);
      return refused(`Refused: ${error.message}`);
    }
    if (record.postObservationVersion) this.citable = record.postObservationVersion;
    if (record.dispatchStatus === 'never-dispatched') {
      if (OWNERSHIP_CODES.includes(record.neverDispatched.code)) {
        await this._awaitOwnership(identity.ownerGeneration);
        return refused(MESSAGES.takeover);
      }
      return STALE_CODES.includes(record.neverDispatched.code) ? this._staleOrTakeover() : refused(`Refused: ${record.neverDispatched.code}`);
    }
    return record;
  }

  /** A cited part is a region of the latest observation, or a requested selector naming its members. */
  _scoped(dependsOn) {
    const { regions, groups } = this.latest;
    const missing = dependsOn.filter((selector) => !(selector in regions) && !groups[selector]?.length);
    if (missing.length) return { error: refused(MESSAGES.notObserved(missing)) };
    const selectors = [...new Set(dependsOn.flatMap((selector) => (selector in regions ? [selector] : groups[selector])))];
    if (selectors.length > MAX_SCOPE_REGIONS) return { error: refused(MESSAGES.tooManyParts(selectors.length, MAX_SCOPE_REGIONS)) };
    return { observationVersion: this.latest.version, observationScope: { kind: 'regions', selectors } };
  }

  async navigate({ url }) {
    if (new URL(url).origin !== this.task.origin) return refused(MESSAGES.origin);
    if (this.citable === null) await this.observe({ regions: ['h1'] });
    const spec = () => ({
      actionId: this._actionId('navigate'),
      authorizedIntent: this.task.intent,
      kind: 'navigate',
      target: { url },
      observationVersion: this.citable,
      observationScope: { kind: 'regions', selectors: [] },
    });
    let record = await this._submit(spec());
    if (record.isError && record.text === MESSAGES.stale) {
      await this.observe({ regions: ['h1'] });
      record = await this._submit(spec());
    }
    if (record.isError) return record;
    return ok(`Opened ${record.evidence?.effect?.finalUrl ?? url}.`);
  }

  async mutate(tool, { element, value, depends_on: dependsOn = [], external_effect: externalEffect = false }) {
    if (!this.latest) return refused(MESSAGES.unknownElement);
    const target = this.describe(element);
    if (!target) return refused(MESSAGES.unknownElement);
    if (this._decidedBeforeHandoff()) return refused(MESSAGES.takeover);
    await this.hooks.beforeAction({ tool, target, externalEffect });
    const scoped = this._scoped(dependsOn);
    if (scoped.error) return scoped.error;
    const base = { authorizedIntent: this.task.intent, target: { handle: element }, ...scoped };
    const SPECS = {
      click: () => ({ ...base, actionId: this._actionId('click'), kind: 'click' }),
      fill: () => ({ ...base, actionId: this._actionId('fill'), kind: SELECT_ROLES.includes(target.role) ? 'select' : 'fill', params: { value } }),
      submit: () => ({
        ...base,
        actionId: this._actionId('submit'),
        kind: 'submit',
        effect: { external: true, effectKey: `${this.task.id}:submit:${this.sequence + 1}` },
        completion: { completedWhen: [{ kind: 'url-not-equals', value: this.latest.url }] },
      }),
    };
    const record = await this._submit(SPECS[tool]());
    if (record.isError) return record;
    if (record.outcome === 'completed') {
      return ok(tool === 'submit' ? `Done. The page is now ${record.evidence?.conditions?.results?.[0]?.observed}.` : 'Done.');
    }
    return refused(`The outcome is ${record.outcome} (${record.outcomeBasis}).`);
  }

  async download({ element }) {
    if (!this.describe(element)) return refused(MESSAGES.unknownElement);
    if (this._decidedBeforeHandoff()) return refused(MESSAGES.takeover);
    const record = await this._submit({
      actionId: this._actionId('download'),
      authorizedIntent: this.task.intent,
      kind: 'download',
      target: { handle: element },
      observationVersion: this.latest.version,
      observationScope: { kind: 'regions', selectors: [] },
    });
    if (record.isError) return record;
    return record.outcome === 'completed'
      ? ok(`Saved artifact ${record.evidence.effect.sha256}.`)
      : refused(`The download outcome is ${record.outcome} (${record.outcomeBasis}).`);
  }

  /** The workspace's own records of this task's external effects. */
  async pendingEffects() {
    const outstanding = await this.host.call('outstanding', this.identity.current());
    const effects = outstanding.filter((entry) => entry.effectKey?.startsWith(`${this.task.id}:submit:`));
    if (!effects.length) return ok('No external effects are outstanding.');
    return ok(effects.map((entry) => {
      const ended = entry.evidence?.conditions?.results?.[0]?.observed;
      return `${entry.actionId}: dispatch ${entry.dispatchStatus}; outcome ${entry.outcome ?? 'not yet recorded'}`
        + `${entry.outcomeBasis ? ` (${entry.outcomeBasis})` : ''}${ended ? `; the page then showed ${ended}` : ''}`;
    }).join('\n'));
  }

  execute(name, input) {
    const TOOLS = {
      observe: () => this.observe(input),
      navigate: () => this.navigate(input),
      click: () => this.mutate('click', input),
      fill: () => this.mutate('fill', input),
      submit: () => this.mutate('submit', input),
      download: () => this.download(input),
      pending_effects: () => this.pendingEffects(),
    };
    return TOOLS[name]();
  }
}

const ROLE_LINE = (ref) => new RegExp(`^\\s*- '?(\\w+)(?: "([^"]*)")?[^\\n]*\\[ref=${ref}\\]`, 'm');

/** The control: Playwright agent tooling with revalidation and takeover cancellation. */
class PlaywrightModelBackend {
  constructor({ host, pause, task, checkpoint, hooks }) {
    this.host = host;
    this.pause = pause;
    this.task = task;
    this.checkpoint = checkpoint;
    this.hooks = hooks;
    this.latestFull = null;
    this.takeoversSeen = pause.takeovers();
    this.dead = false;
  }

  /** The agent process ended: a call still in flight can no longer record its result. */
  kill() {
    this.dead = true;
  }

  async observe({ since_last: sinceLast = false } = {}) {
    await this.pause.whileHeld();
    const snapshot = await this.host.request('observeForModel', {});
    const hadObservation = this.latestFull !== null;
    this.latestFull = snapshot.full;
    this.takeoversSeen = this.pause.takeovers();
    const body = sinceLast && hadObservation && snapshot.incremental !== null ? snapshot.incremental : snapshot.full;
    return ok(`URL: ${snapshot.url}\n${body}`);
  }

  describe(element) {
    const match = ROLE_LINE(element).exec(this.latestFull ?? '');
    return match ? { role: match[1], name: match[2] ?? '', handle: element } : null;
  }

  async navigate({ url }) {
    if (new URL(url).origin !== this.task.origin) return refused(MESSAGES.origin);
    await this.pause.whileHeld();
    const navigated = await this.host.request('navigate', { url });
    return ok(`Opened ${navigated.url}.`);
  }

  _pending() {
    return this.checkpoint.get().pendingCalls ?? [];
  }

  async mutate(tool, { element, value, depends_on: dependsOn = [], external_effect: externalEffect = false }) {
    const target = this.describe(element);
    if (!target) return refused(MESSAGES.unknownElement);
    await this.hooks.beforeAction({ tool, target, externalEffect });
    await this.pause.whileHeld();
    if (this.pause.takeovers() > this.takeoversSeen) return refused(MESSAGES.takeover);
    const check = await this.host.request('revalidate', { regions: dependsOn, ref: element });
    if (check.stale) return refused(MESSAGES.stale);
    const recorded = tool === 'submit' || (tool === 'click' && externalEffect);
    const call = { tool, element, issuedAt: new Date().toISOString() };
    if (recorded) this.checkpoint.update({ pendingCalls: [...this._pending(), call] });
    let result;
    if (tool === 'fill') {
      result = await this.host.request(SELECT_ROLES.includes(target.role) ? 'select' : 'fill', { ref: element, value });
    } else {
      if (tool === 'submit' && new URL((await this.host.request('formAction', {})).action).origin !== this.task.origin) {
        return refused(MESSAGES.origin);
      }
      result = await this.host.request('click', { ref: element });
    }
    if (recorded && !this.dead) {
      this.checkpoint.update({ pendingCalls: this._pending().filter((entry) => entry.issuedAt !== call.issuedAt) });
    }
    return ok(tool === 'submit' ? `Done. The page is now ${result.url}.` : 'Done.');
  }

  async download({ element }) {
    if (!this.describe(element)) return refused(MESSAGES.unknownElement);
    await this.pause.whileHeld();
    const saved = await this.host.request('download', { ref: element });
    return ok(`Saved artifact ${saved.sha256}.`);
  }

  /** The harness checkpoint: calls issued before the agent process ended whose result was not recorded. */
  async pendingEffects() {
    const pending = this._pending();
    if (!pending.length) return ok('No external effects are outstanding.');
    return ok(pending.map((call) => `${call.tool} on ${call.element}: issued ${call.issuedAt}; its result was not recorded`).join('\n'));
  }

  execute(name, input) {
    const TOOLS = {
      observe: () => this.observe(input),
      navigate: () => this.navigate(input),
      click: () => this.mutate('click', input),
      fill: () => this.mutate('fill', input),
      submit: () => this.mutate('submit', input),
      download: () => this.download(input),
      pending_effects: () => this.pendingEffects(),
    };
    return TOOLS[name]();
  }
}

export { FawnModelBackend, MESSAGES, PlaywrightModelBackend };
