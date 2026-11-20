// Bounded shopping adapter. The caller supplies a site reader, grants, planner and
// quote-specific approval. Final purchase never enters a TraceDag.
import { randomUUID } from 'node:crypto';
import { structuralLocator } from '../adapters/page-query.js';
import { TraceDag } from './trace-dag.js';
import { eligibleOffer, quoteHash, selectShoppingOffer, validateShoppingRequest, verifyShoppingQuote, verifyShoppingReceipt } from './shopping-contract.js';

export function createShoppingDriver({ service, owner, intent = 'shopping', pageId = 'main' }) {
  const identity = { ...owner, pageId };
  const trace = [];
  let latest;
  const observed = {
    outstanding: command => service.outstanding(command),
    async observe(command) { latest = await service.observe(command); return latest; },
    async submitAction(command) {
      const element = latest?.elements.find(value => value.handle === command.target?.handle);
      const step = { kind: command.kind, label: element?.label ?? null,
        value: command.params?.value ?? null, purchase: command.effect?.external === true };
      try {
        const admitted = await service.submitAction(command);
        return { ...admitted, result: admitted.result.then(result => { trace.push({ ...step, outcome: result.outcome }); return result; }) };
      } catch (error) { trace.push({ ...step, outcome: 'rejected' }); throw error; }
    },
  };
  return {
    service: observed, identity, intent, trace,
    observe: () => observed.observe(identity),
    outstanding: () => service.outstanding(identity),
    async act(observation, spec) {
      const admitted = await observed.submitAction({ ...identity, actionId: randomUUID(), authorizedIntent: intent,
        observationVersion: observation.observationVersion, ...spec });
      return admitted.result;
    },
    reconcile: spec => service.reconcile({ ...identity, method: 'application-state', ...spec }),
    action: actionId => service.action({ ...identity, actionId }),
  };
}

export class ShoppingSession {
  constructor({ driver, site, request, cache, planner, mode, limits, attempts, operationId,
    approvePurchase = async () => null, signal = new AbortController().signal }) {
    if (!['learn', 'reuse', 'script'].includes(mode)) throw Error('Unknown shopping execution mode');
    validateShoppingRequest(request);
    if (!/^[a-zA-Z0-9-]{1,100}$/.test(operationId)) throw Error('Invalid purchase operation identity');
    Object.assign(this, { driver, site, request, cache, planner, mode, limits, attempts, operationId, approvePurchase, signal });
    this.stats = { plannerCalls: 0, cachedSteps: 0, actions: [], misses: [] };
  }
  async read() {
    this.signal.throwIfAborted();
    const observation = await this.driver.observe();
    if (observation.isTruncated !== false || new URL(observation.url).origin !== this.site.origin) throw Error('Incomplete or out-of-scope storefront');
    const state = this.site.read(observation);
    if (state.accountId !== this.request.accountId) throw Error('Shopping account changed');
    return { observation, state };
  }
  async settled() {
    if ((await this.driver.outstanding()).some(action => action.isUncertain || action.dispatchStatus === 'queued'
      || (action.dispatchStatus === 'dispatched' && !action.outcome))) throw Error('Unresolved action; use recovery without repeating the purchase');
  }
  async act(label, kind = 'click', extra = {}) {
    await this.settled();
    const { observation } = await this.read();
    const matches = observation.elements.filter(element => element.label === label);
    if (matches.length !== 1) throw Error(`Expected one current control: ${label}`);
    const transition = this.site.transitions?.[label] ?? {};
    kind = transition.kind ?? kind;
    const result = await this.driver.act(observation, { kind, target: { handle: matches[0].handle }, ...transition, ...extra });
    this.stats.actions.push({ label, kind, outcome: result.outcome });
    if (result.outcome !== 'completed') throw Error(`Action ${label} requires attention`);
    return result;
  }
  async fields(phase) {
    const bindings = this.site.fields[phase];
    const inputs = Object.fromEntries(bindings.map(field => [field.slot, this.request[field.slot]]));
    const matches = (observation, field) => observation.elements.filter(el => field.labels.includes(el.label)
      && el.tag === (field.kind === 'select' ? 'select' : 'input'));
    const verified = observation => bindings.every(field => {
      const elements = matches(observation, field);
      return elements.length === 1 && elements[0].value === inputs[field.slot];
    });
    const context = async () => {
      await this.settled();
      const current = await this.read();
      if (current.state.phase !== phase) throw Error('Unexpected shopping phase');
      return current.observation;
    };
    const key = `${this.site.id}:${this.request.accountId}:${phase}`;
    const dag = this.cache.get(key) ?? new TraceDag(this.limits);
    const traceService = this.driver.service ? {
      outstanding: command => this.driver.service.outstanding(command),
      submitAction: command => this.driver.service.submitAction(command),
      observe: async command => {
        const observation = await this.driver.service.observe(command);
        const state = this.site.read(observation);
        if (observation.isTruncated !== false || new URL(observation.url).origin !== this.site.origin
          || state.accountId !== this.request.accountId || state.phase !== phase) throw Error('Shopping context changed');
        return observation;
      },
    } : null;
    const options = { service: traceService, owner: this.driver.identity, pageId: 'main', intent: this.driver.intent,
      template: key, inputs, signal: this.signal, accountScope: this.request.accountId,
      assertContext: () => this.settled(), authorizeStep: ({ slot, locator }) => {
        const field = bindings.find(value => value.slot === slot);
        if (!field || !field.labels.includes(locator[1])) throw Error('Unapproved field disclosure');
      } };
    let recorder = this.mode === 'learn' ? dag.session(options) : null;
    if (this.mode === 'reuse') {
      const replay = await dag.session(options).replay();
      this.stats.cachedSteps += replay.steps;
      if (replay.reason === 'submit-boundary' && verified(await context())) return;
      if (!['unseen-branch', 'missing-locator', 'ambiguous-locator', 'ambiguous-branch'].includes(replay.reason)) throw Error(`Replay stopped: ${replay.reason}`);
      this.stats.misses.push({ phase, reason: replay.reason });
    }
    for (let turn = 0; turn < this.limits.maxSteps; turn++) {
      const observation = await context();
      if (verified(observation)) {
        if (recorder) {
          const result = await recorder.finish();
          if (result.reason !== 'recorded-submit-boundary') throw Error('Shopping trace did not verify');
          this.cache.set(key, dag);
        }
        return;
      }
      const proposal = await this.planner.next({ phase, inputs, bindings, observation }, { signal: this.signal });
      if (this.mode !== 'script') this.stats.plannerCalls++;
      const field = bindings.find(value => value.slot === proposal.slot);
      if (!field) throw Error('Planner requested an unauthorized input slot');
      const elements = matches(observation, field);
      if (elements.length !== 1 || elements[0].handle !== proposal.handle) throw Error('Planner target is missing or ambiguous');
      let result;
      if (recorder) result = await recorder.record({ kind: field.kind, locator: structuralLocator(elements[0]), slot: field.slot }, observation);
      else result = await this.driver.act(observation, { kind: field.kind, target: { handle: elements[0].handle }, params: { value: inputs[field.slot] } });
      this.stats.actions.push({ kind: field.kind, label: elements[0].label, outcome: result.outcome ?? result.status });
      if (result.outcome !== 'completed' && result.status !== 'completed') throw Error('Input did not settle');
    }
    throw Error('Shopping planner step limit');
  }
  async run() {
    return this.attempts.transaction(async () => {
      if (this.attempts.read(null)) throw Error('Purchase operation already exists; recover it, never replay checkout');
      try {
        await this.fields('search');
        await this.act('Search');
        const results = await this.read();
        const offer = selectShoppingOffer(results.state.offers, this.request);
        await this.act(`View ${offer.sku}`);
        const detail = await this.read();
        if (quoteHash(detail.state.offers?.[0]) !== quoteHash(offer)) throw Error('Product changed after search');
        await this.act('Add to cart');
        await this.fields('shipping');
        await this.act('Review order');
        const review = await this.read();
        if (!eligibleOffer(review.state.offers?.find(value => value.sku === offer.sku), this.request)) throw Error('Stock or price changed before checkout');
        const hash = verifyShoppingQuote(review.state.quote, offer, this.request);
        const approval = await this.approvePurchase({ quote: review.state.quote, quoteHash: hash, operationId: this.operationId });
        if (approval?.quoteHash !== hash) return { status: 'review-ready', completed: false, stats: this.stats };
        const current = await this.read();
        if (!eligibleOffer(current.state.offers?.find(value => value.sku === offer.sku), this.request)) throw Error('Stock or price changed during approval');
        if (verifyShoppingQuote(current.state.quote, offer, this.request) !== hash) throw Error('Quote changed during approval');
        const controls = current.observation.elements.filter(el => el.label === 'Place order');
        if (controls.length !== 1) throw Error('Missing unique final order control');
        const attempt = { version: 1, operationId: this.operationId, request: this.request,
          origin: this.site.origin, siteId: this.site.id, workspaceId: this.driver.identity.workspaceId,
          actionId: randomUUID(), quote: current.state.quote, quoteHash: hash, status: 'prepared' };
        this.attempts.write(attempt);
        const result = await this.driver.act(current.observation, { actionId: attempt.actionId, kind: 'submit',
          target: { handle: controls[0].handle }, effect: { external: true, effectKey: this.operationId },
          completion: { completedWhen: this.site.receiptConditions(this.operationId) } });
        this.attempts.write({ ...attempt, status: result.outcome === 'completed' ? 'acknowledged' : 'unknown' });
        this.stats.actions.push({ kind: 'submit', outcome: result.outcome });
        if (result.outcome !== 'completed') return { status: 'unknown', completed: false, stats: this.stats };
        return await this.confirm(attempt);
      } catch (error) {
        return { status: 'needs-attention', completed: false, reason: error.message, stats: this.stats };
      }
    });
  }
  async confirm(attempt) {
    const { state } = await this.read();
    if (!verifyShoppingReceipt(state.receipt, attempt)) throw Error('Order receipt does not match the authorized purchase');
    this.attempts.write({ ...attempt, status: 'completed', orderId: state.receipt.orderId });
    return { status: 'completed', completed: true, orderId: state.receipt.orderId, stats: this.stats };
  }
  async recover() {
    return this.attempts.transaction(async () => {
      const attempt = this.attempts.read(null);
      if (!attempt || attempt.version !== 1 || attempt.operationId !== this.operationId
        || attempt.siteId !== this.site.id || attempt.origin !== this.site.origin
        || attempt.workspaceId !== this.driver.identity.workspaceId || quoteHash(attempt.request) !== quoteHash(this.request)
        || quoteHash(attempt.quote) !== attempt.quoteHash) throw Error('Purchase recovery identity differs');
      // Caller explicitly navigates to the merchant's receipt/lookup page. No effect is repeated here.
      const { state } = await this.read();
      if (!verifyShoppingReceipt(state.receipt, attempt)) return { status: 'unknown', completed: false, stats: this.stats };
      const action = await this.driver.action(attempt.actionId);
      if (action.isUncertain) {
        const reconciled = await this.driver.reconcile({ actionId: attempt.actionId,
          effectPresentWhen: this.site.receiptConditions(this.operationId), effectAbsentWhen: [] });
        if (reconciled.isUncertain) return { status: 'unknown', completed: false, stats: this.stats };
      } else if (action.outcome !== 'completed') return { status: 'needs-attention', completed: false, stats: this.stats };
      return this.confirm(attempt);
    });
  }
}
