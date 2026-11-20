// Zero-trust Fawn client for the Managed Recipe Graph Service.
// Remote recipes act strictly as routing hints: local account checks, slot-to-field
// disclosure rules, click allowlists, service admission and review verification stay mandatory.
import { createHash, randomUUID } from 'node:crypto';
import { canonicalJson } from './trace-graph-dp.js';
import { TraceDag } from './trace-dag.js';
import { PinnedRecipeGenerationCache } from './pinned-recipe-cache.js';
import { MAX_RECIPE_SNAPSHOT_BYTES } from './recipe-generation-format.js';
import { runWorkflow, scopeWorkflowObservation } from './workflow-agent.js';
import { structuralLocator, structuralOutlineHash } from '../adapters/page-query.js';

const HASH_RE = /^[a-f0-9]{64}$/;

function sha256Hex(text) {
  return createHash('sha256').update(text).digest('hex');
}

function exactKeys(value, keys) {
  return value && typeof value === 'object' && !Array.isArray(value)
    && Object.keys(value).sort().join() === [...keys].sort().join();
}

async function boundedResponse(response, maximum) {
  if (!response.body) return '';
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let length = 0, text = '';
  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) return text + decoder.decode();
      length += value.byteLength;
      if (length > maximum) {
        await reader.cancel().catch(() => {});
        throw Object.assign(Error('Recipe publication response exceeds the byte limit'),
          { code: 'generation-response-too-large' });
      }
      text += decoder.decode(value, { stream: true });
    }
  } finally { reader.releaseLock(); }
}

function locatorValid(value) {
  return Array.isArray(value) && value.length === 4
    && value.every(part => typeof part === 'string');
}

/** Observe PII-free structural transitions on a scoped service without recording input values. */
export function createStructuralTraceCapture(service, { resolveSlot }) {
  let latestObservation = null;
  const capturedSteps = [];

  const wrappedService = {
    async observe(identity) {
      const obs = await service.observe(identity);
      latestObservation = obs;
      return obs;
    },
    outstanding: (...args) => service.outstanding(...args),
    async submitAction(request) {
      const beforeObs = latestObservation ?? await service.observe({
        workspaceId: request.workspaceId,
        ownerId: request.ownerId,
        ownerToken: request.ownerToken,
        ownerGeneration: request.ownerGeneration,
        pageId: request.pageId,
      });
      if (!['fill', 'select', 'click'].includes(request.kind)) {
        return service.submitAction(request);
      }
      const element = beforeObs.elements?.find(el => el.handle === request.target?.handle);
      const beforeOutline = structuralOutlineHash(beforeObs.elements ?? []);
      const locator = element ? structuralLocator(element) : null;
      const slot = request.kind === 'click' ? null : resolveSlot(element, request.params?.value);
      const started = performance.now();
      const admitted = await service.submitAction(request);
      const result = await admitted.result;
      const elapsedMs = Math.max(0, Math.round(performance.now() - started));
      if (locator && (request.kind === 'click' || slot)) {
        const afterObs = await service.observe({
          workspaceId: request.workspaceId,
          ownerId: request.ownerId,
          ownerToken: request.ownerToken,
          ownerGeneration: request.ownerGeneration,
          pageId: request.pageId,
        });
        latestObservation = afterObs;
        const afterOutline = structuralOutlineHash(afterObs.elements ?? []);
        capturedSteps.push({
          beforeOutline,
          afterOutline,
          kind: request.kind,
          locator,
          ...(slot ? { slot } : {}),
          elapsedMs,
          outcome: result.outcome === 'completed' ? 'completed' : 'miss',
        });
      }
      return { ...admitted, result: Promise.resolve(result) };
    },
  };

  return {
    service: wrappedService,
    steps: () => structuredClone(capturedSteps),
  };
}

export class ManagedRecipeClient {
  constructor({
    url,
    token,
    accessClientId = null,
    accessClientSecret = null,
    timeoutMs = 10000,
    fetchImpl = globalThis.fetch,
  }) {
    const endpoint = new URL(url);
    if (endpoint.protocol !== 'https:' && !(endpoint.protocol === 'http:' && ['127.0.0.1', '[::1]', 'localhost'].includes(endpoint.hostname))) {
      throw Error('Managed recipe client requires HTTPS or loopback');
    }
    if (typeof token !== 'string' || token.length < 32) {
      throw Error('Client bearer token (>=32 chars) is required');
    }
    this.baseUrl = endpoint.origin;
    this.timeoutMs = timeoutMs;
    this.fetchImpl = fetchImpl;
    this.headers = {
      authorization: `Bearer ${token}`,
      'content-type': 'application/json',
      ...(accessClientId && accessClientSecret
        ? { 'cf-access-client-id': accessClientId, 'cf-access-client-secret': accessClientSecret }
        : {}),
    };
  }

  async #request(method, path, body = null, maxResponseBytes = null) {
    const response = await this.fetchImpl(`${this.baseUrl}${path}`, {
      method,
      headers: this.headers,
      redirect: 'error',
      signal: AbortSignal.timeout(this.timeoutMs),
      ...(body !== null ? { body: JSON.stringify(body) } : {}),
    });
    const text = maxResponseBytes === null ? await response.text() : await boundedResponse(response, maxResponseBytes);
    let parsed = null;
    try { parsed = text ? JSON.parse(text) : null; } catch {}
    if (!response.ok) {
      if (maxResponseBytes !== null) {
        // Never surface response-controlled error text for publication reads.
        throw Object.assign(Error(`Recipe publication HTTP ${response.status}`),
          { status: response.status, code: `http-${response.status}` });
      }
      throw Object.assign(
        Error(parsed?.message ?? parsed?.error ?? `Recipe service HTTP ${response.status}`),
        { status: response.status, code: parsed?.error ?? `http-${response.status}` },
      );
    }
    return parsed;
  }

  health() {
    return this.#request('GET', '/health');
  }

  registerSubrecipe(spec) {
    return this.#request('POST', '/v1/subrecipes', spec);
  }

  listSubrecipes({ scope = 'workspace', origin }) {
    const params = new URLSearchParams({ scope, origin });
    return this.#request('GET', `/v1/subrecipes?${params.toString()}`);
  }

  composeRecipe(spec) {
    return this.#request('POST', '/v1/recipes/compose', spec);
  }

  submitVerifiedTrace(spec) {
    return this.#request('POST', '/v1/traces', spec);
  }

  /** Explicit, data-only publication read. Never used by resolve or dispatch. */
  async fetchPinnedGeneration({ origin, template, readScope = null, generation, trust, cache, replayFloor = null, clock = Date.now }) {
    if (!Number.isSafeInteger(generation) || generation < 1 ||
        !trust || !HASH_RE.test(trust.namespaceId ?? '') ||
        !(cache instanceof PinnedRecipeGenerationCache) || typeof clock !== 'function' ||
        (replayFloor !== null && typeof replayFloor?.advance !== 'function')) {
      throw new TypeError('Exact generation, local namespace trust and a bounded cache are required');
    }
    const { publicKey, namespaceId, compilerVersion, limits, replanPenalty, minimumGeneration } = trust;
    const policy = { publicKey, namespaceId, compilerVersion, limits: structuredClone(limits),
      replanPenalty, minimumGeneration };
    const packet = await this.#request('POST', '/v1/recipe-generations/read', {
      origin, template, readScope, generation,
    }, MAX_RECIPE_SNAPSHOT_BYTES + 8192);
    return cache.admitSigned(packet, { ...policy, now: clock() }, generation, replayFloor);
  }

  async resolveDag({
    scope = 'workspace',
    origin,
    template,
    readScope = null,
    availableSlots = null,
    currentOutline = null,
    limits,
  }) {
    const payload = await this.#request('POST', '/v1/recipes/resolve', {
      scope,
      origin,
      template,
      readScope,
      ...(availableSlots ? { availableSlots } : {}),
      ...(currentOutline ? { currentOutline } : {}),
      limits,
    });
    if (!payload?.dag || !HASH_RE.test(payload.dagDigest ?? '')
      || sha256Hex(canonicalJson(payload.dag)) !== payload.dagDigest) {
      throw Error('Served recipe digest mismatch');
    }
    const dag = TraceDag.restore(payload.dag, limits);
    return { ...payload, restoredDag: dag };
  }

  /** Execute a workflow backed by the Managed Recipe Service under local zero-trust fences. */
  async runWorkflow({
    scope = 'workspace',
    fallbackCatalog = false,
    publishLearned = true,
    limits,
    disclosurePolicy,
    verifyAccount,
    accountScope,
    verificationId,
    reconvergeMidRepair = true,
    ...options
  }) {
    if (typeof verifyAccount !== 'function' || typeof options.verifyReview !== 'function'
      || typeof verificationId !== 'string' || !verificationId.trim()) {
      throw Error('Managed workflow execution requires local verifyAccount, verifyReview and verificationId');
    }
    const policy = structuredClone(disclosurePolicy);
    if (!exactKeys(policy, ['origin', 'fields', 'intermediateClicks'])
      || new URL(policy.origin).origin !== policy.origin
      || !Array.isArray(policy.fields) || !Array.isArray(policy.intermediateClicks)
      || !policy.intermediateClicks.every(locatorValid)
      || !policy.fields.every(f => exactKeys(f, ['kind', 'slot', 'locator'])
        && ['fill', 'select'].includes(f.kind) && typeof f.slot === 'string' && f.slot.trim() && locatorValid(f.locator))) {
      throw Error('Local slot-to-field disclosurePolicy and intermediateClicks are required');
    }

    const observationLocators = [
      ...policy.fields.map(field => field.locator),
      ...policy.intermediateClicks,
    ];
    // Compute the exact scoped template name that runWorkflow will evaluate against.
    const { template: effectiveTemplate, service: scopedService } = scopeWorkflowObservation(
      options.service,
      options.template,
      observationLocators,
    );

    const availableSlots = Object.entries(options.inputs ?? {})
      .filter(([, val]) => typeof val === 'string')
      .map(([slot]) => slot);

    let resolved = await this.resolveDag({
      scope,
      origin: policy.origin,
      template: effectiveTemplate,
      availableSlots,
      limits,
    });
    if (resolved.restoredDag.nodes.size === 0 && fallbackCatalog && scope === 'workspace') {
      const catalogResolved = await this.resolveDag({
        scope: 'catalog',
        origin: policy.origin,
        template: effectiveTemplate,
        availableSlots,
        limits,
      });
      if (catalogResolved.restoredDag.nodes.size > 0) resolved = catalogResolved;
    }

    // Resolve element -> declared slot locally without ever recording slot values in captured steps.
    const resolveSlot = (element, submittedValue) => {
      if (!element) return null;
      const loc = canonicalJson(structuralLocator(element));
      const candidates = policy.fields.filter(f => canonicalJson(f.locator) === loc);
      const exactMatch = candidates.find(f => options.inputs?.[f.slot] === submittedValue);
      return (exactMatch ?? candidates[0])?.slot ?? null;
    };
    const capture = createStructuralTraceCapture(scopedService, { resolveSlot });

    const identity = { service: options.service, owner: options.owner, pageId: options.pageId };
    const assertContext = async () => {
      options.signal.throwIfAborted();
      if (await verifyAccount(identity) !== accountScope) {
        throw Object.assign(Error('Website account does not match local workflow scope'), { code: 'workflow-account-mismatch' });
      }
    };
    await assertContext();

    const authorizeStep = async step => {
      const permitted = step.origin === policy.origin && (step.kind === 'click'
        ? policy.intermediateClicks.some(loc => canonicalJson(loc) === canonicalJson(step.locator))
        : policy.fields.some(field => field.kind === step.kind && field.slot === step.slot
          && canonicalJson(field.locator) === canonicalJson(step.locator)));
      if (!permitted) {
        throw Object.assign(Error('Served recipe step violates local slot disclosure policy'), { code: 'workflow-disclosure-denied' });
      }
    };

    const result = await runWorkflow({
      ...options,
      service: capture.service,
      template: effectiveTemplate,
      observationLocators: null,
      accountScope: null,
      dag: resolved.restoredDag,
      intermediateClicks: policy.intermediateClicks,
      learnRepairs: publishLearned,
      reconvergeMidRepair,
      assertContext,
      authorizeStep,
    });

    let remotePublication = { status: 'skipped' };
    const steps = capture.steps();
    if (publishLearned && result.completed && result.verification?.completed === true
      && (options.mode === 'learn' || result.modelCalls > 0) && steps.length > 0) {
      const ingested = await this.submitVerifiedTrace({
        submissionId: randomUUID(),
        scope,
        origin: policy.origin,
        template: effectiveTemplate,
        verificationId,
        reviewVerified: true,
        limits,
        steps,
      });
      remotePublication = { status: 'published', ...ingested };
    }

    return {
      ...result,
      resolvedRevision: resolved.revision,
      resolvedScope: resolved.scope,
      remotePublication,
    };
  }
}
