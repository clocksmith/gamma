// Fawn workspace — shared observation, action and recovery service
//
// The only holder of the workspace browser. Owners observe and submit intent; the trusted
// dispatcher re-checks authority at dispatch, and the journal keeps outcomes across restart.

import { join } from 'node:path';
import { randomUUID } from 'node:crypto';
import { MAIN_PAGE, pageView, readGrant, scopedRead } from './page-scope.js';
import {
  REGIONS_SCOPE,
  authenticateAdmin,
  authenticateOwner,
  checkAdmission,
  checkDispatchAuthority,
  validateRegionSelectors,
} from './admission.js';
import { issueCredential } from './authority.js';
import { evaluateConditions, validateConditions } from './conditions.js';
import { REJECTION_CODES, isWorkspaceError, workspaceError } from './errors.js';
import { Journal } from './journal.js';
import { requireChromiumSurfaceV1 } from './surface-contract.js';
import { UploadStore, checkUploadTarget } from './uploads.js';
import {
  ACTION_STATUS,
  OUTCOMES,
  RECORD_TYPES,
  applyRecord,
  describeAction,
  replay,
} from './state.js';

const NONATOMIC_BOUNDARY = Object.freeze({
  isAtomic: false,
  statement: 'Dispatch-time checks and the browser effect are separate steps; page, human or '
    + 'external changes can intervene, and effects already underway cannot be undone.',
});

const KIND_COMPLETION_BASIS = Object.freeze({
  navigate: 'navigation-committed',
  click: 'input-delivered',
  fill: 'value-verified',
  select: 'value-verified',
  download: 'artifact-saved',
  upload: 'files-attached',
});

// The live-page condition that shows a fill or select took effect.
const VALUE_CONDITIONS = Object.freeze({ fill: 'input-value-equals', select: 'choice-equals' });

const RESTART_RULES = Object.freeze([
  {
    matches: (action) => action.status === ACTION_STATUS.QUEUED,
    type: RECORD_TYPES.ACTION_NOT_DISPATCHED,
    body: { stage: 'restart', code: 'restart-invalidated-queue', detail: 'queued before restart' },
  },
  {
    matches: (action) => action.status === ACTION_STATUS.DISPATCHED && !action.outcome,
    type: RECORD_TYPES.ACTION_OUTCOME,
    body: {
      outcome: OUTCOMES.UNKNOWN,
      basis: 'restart-after-dispatch-start',
      evidence: { detail: 'dispatch began before restart and no outcome was recorded' },
      boundary: NONATOMIC_BOUNDARY,
    },
  },
]);

const NO_HOOKS = Object.freeze({});
const FULL_VIEW = 'full';
const OUTLINE_VIEW = 'outline';

/** Validate an observe command's read options against config. */
function validateObservationRead(command, config) {
  const read = {
    regions: command.regions ?? [],
    regionGroups: command.regionGroups ?? [],
    view: command.view ?? FULL_VIEW,
    sinceVersion: command.sinceVersion,
    ifCurrentVersion: command.ifCurrentVersion,
    includeFormState: command.includeFormState === true,
    autoControlRegions: command.autoControlRegions === true,
  };
  if (command.regions !== undefined) validateRegionSelectors(read.regions, config, 'regions');
  if (command.regionGroups !== undefined) validateRegionSelectors(read.regionGroups, config, 'regionGroups');
  if (!config.observationViews.includes(read.view)) {
    throw workspaceError(REJECTION_CODES.INVALID_COMMAND, 'view', { path: 'view', expected: config.observationViews, received: read.view });
  }
  if (read.sinceVersion !== undefined && !Number.isInteger(read.sinceVersion)) {
    throw workspaceError(REJECTION_CODES.INVALID_COMMAND, 'sinceVersion: expected integer', { path: 'sinceVersion' });
  }
  if (read.ifCurrentVersion !== undefined && !Number.isInteger(read.ifCurrentVersion)) {
    throw workspaceError(REJECTION_CODES.INVALID_COMMAND, 'ifCurrentVersion: expected integer', { path: 'ifCurrentVersion' });
  }
  if (command.includeFormState !== undefined && typeof command.includeFormState !== 'boolean') {
    throw workspaceError(REJECTION_CODES.INVALID_COMMAND, 'includeFormState: expected boolean', { path: 'includeFormState' });
  }
  if (command.autoControlRegions !== undefined && typeof command.autoControlRegions !== 'boolean') {
    throw workspaceError(REJECTION_CODES.INVALID_COMMAND, 'autoControlRegions: expected boolean', { path: 'autoControlRegions' });
  }
  return read;
}

/**
 * Compact view for agents: each requested region's outline, or `unchanged` when its digest
 * matches the base version from the same owner generation. A missing base yields full outlines.
 * Digests, handle tables and element lists stay in the journal for admission.
 */
function outlineView(workspace, recorded, snapshot, sinceVersion) {
  const base = sinceVersion === undefined ? null : workspace.observations.get(sinceVersion) ?? null;
  const regions = Object.fromEntries(Object.entries(snapshot.regionDigests).map(([selector, digest]) => {
    if (digest === null) return [selector, { missing: true }];
    if (base?.regions?.[selector] === digest) return [selector, { unchanged: true }];
    return [selector, { outline: snapshot.regionOutlines[selector] ?? '' }];
  }));
  return {
    observationVersion: recorded.observationVersion,
    url: recorded.url,
    baseVersion: base ? sinceVersion : null,
    regions,
    regionGroups: snapshot.regionGroups ?? {},
    boundary: { isAtomic: false },
  };
}
const PROFILE_DIRECTORY = 'profiles';
const ARTIFACT_DIRECTORY = 'artifacts';

class Mutex {
  constructor() {
    this._tail = Promise.resolve();
  }

  run(task) {
    const result = this._tail.then(task);
    this._tail = result.then(() => {}, () => {});
    return result;
  }
}

function deferred() {
  let settle;
  const promise = new Promise((resolve) => {
    settle = resolve;
  });
  return { promise, settle };
}

function withTimeout(promise, timeoutMs) {
  let timer;
  const timeout = new Promise((_, rejectTimeout) => {
    timer = setTimeout(() => rejectTimeout(Object.assign(new Error('effect timed out'), { isTimeout: true })),
      timeoutMs);
  });
  return Promise.race([promise, timeout]).finally(() => clearTimeout(timer));
}

function stripCredentials(command) {
  const { ownerCredential, adminCredential, ...request } = command;
  return request;
}

class WorkspaceService {
  #journal;
  #state;
  #config;
  #adapter;
  #hooks;
  #clock;
  #uploads;
  #runtime = new Map();
  #ready = false;

  constructor({ journal, state, config, adapter, hooks, clock, uploads }) {
    this.#journal = journal;
    this.#state = state;
    this.#config = config;
    this.#adapter = adapter;
    this.#hooks = hooks;
    this.#clock = clock;
    this.#uploads = uploads;
  }

  /**
   * Restore durable authority, settle interrupted actions, then accept commands.
   * @param {{stateDir: string, config: object, createAdapter: Function, hooks?: object,
   *   clock?: () => number}} options
   */
  static async open({ stateDir, config, createAdapter, hooks = NO_HOOKS, clock = Date.now }) {
    const journal = Journal.open({
      directory: stateDir,
      fileName: config.journal.fileName,
      lockFileName: config.journal.lockFileName,
    });
    try {
      const state = replay(journal.records);
      const adapter = requireChromiumSurfaceV1(createAdapter({
        config,
        profileRoot: join(stateDir, PROFILE_DIRECTORY),
        artifactRoot: join(stateDir, ARTIFACT_DIRECTORY),
      }));
      const uploads = new UploadStore(join(stateDir, 'uploads'), config.uploads);
      const service = new WorkspaceService({ journal, state, config, adapter, hooks, clock, uploads });
      service.#restore();
      return service;
    } catch (error) {
      journal.close();
      throw error;
    }
  }

  #append(type, body) {
    const record = this.#journal.append(type, body);
    applyRecord(this.#state, record);
    return record;
  }

  #restore() {
    const settled = [];
    for (const workspace of this.#state.workspaces.values()) {
      for (const action of workspace.actions.values()) {
        const rule = RESTART_RULES.find((candidate) => candidate.matches(action));
        if (!rule) continue;
        this.#append(rule.type, { workspaceId: workspace.workspaceId, actionId: action.request.actionId, ...rule.body });
        settled.push(action.request.actionId);
      }
    }
    this.#append(RECORD_TYPES.SERVICE_RESTORED, {
      recordCount: this.#journal.records.length,
      recovery: this.#journal.recovery,
      settledActionIds: settled,
      protocolVersion: this.#config.protocolVersion,
      configVersion: this.#config.configVersion,
    });
    this.#ready = true;
  }

  #workspace(workspaceId) {
    if (!this.#ready) throw workspaceError(REJECTION_CODES.AUTHORITY_UNAVAILABLE, 'service is not restored');
    const workspace = this.#state.workspaces.get(workspaceId);
    if (!workspace) throw workspaceError(REJECTION_CODES.UNKNOWN_WORKSPACE, String(workspaceId), { workspaceId });
    return workspace;
  }

  #runtimeFor(workspaceId) {
    if (!this.#runtime.has(workspaceId)) {
      this.#runtime.set(workspaceId, { mutex: new Mutex(), queue: [], pumping: false, opened: null, latestObservations: new Map() });
    }
    return this.#runtime.get(workspaceId);
  }

  async #page(workspaceId) {
    const runtime = this.#runtimeFor(workspaceId);
    runtime.opened ??= this.#bounded(this.#adapter.openWorkspace(workspaceId, { pages: [...this.#workspace(workspaceId).pages.values()].filter(page => !page.closed) })).catch((error) => {
      runtime.opened = null;
      throw error;
    });
    await runtime.opened;
  }

  /** Browser reads are bounded so a stuck page cannot hold the dispatch/handoff lock. */
  #bounded(promise) {
    return withTimeout(promise, this.#config.dispatch.actionTimeoutMs);
  }

  #snapshot(workspaceId, read = {}, pageId = MAIN_PAGE) {
    return this.#bounded(this.#adapter.snapshot(workspaceId, { ...read, pageId }));
  }

  #nowMs() {
    return this.#clock();
  }

  #probe(workspaceId, pageId = MAIN_PAGE, command = null, knownUrl = null) {
    // The resource being probed owns the page identity, including reconciliation of an
    // earlier action. A caller's omitted/different pageId cannot select another tab's grant.
    const readCommand = command ? { ...command, pageId } : null;
    const url = async () => {
      const value = knownUrl ?? await this.#bounded(this.#adapter.probeUrl(workspaceId, pageId));
      if (readCommand) readGrant(this.#workspace(workspaceId), readCommand, value, this.#nowMs());
      return value;
    };
    return { url, validate: async condition => {
      const grant = readCommand ? readGrant(this.#workspace(workspaceId), readCommand, await url(), this.#nowMs()) : null;
      if (grant?.readRegions && condition.kind === 'element-absent') {
        throw workspaceError(REJECTION_CODES.UNSUPPORTED_CONDITION, 'A regional grant cannot establish whole-page absence');
      }
    }, element: async selector => {
      const grant = readCommand ? readGrant(this.#workspace(workspaceId), readCommand, await url(), this.#nowMs()) : null;
      return this.#bounded(this.#adapter.probeElement(workspaceId, selector, pageId, grant?.readRegions ?? null));
    } };
  }

  /** Record a new observation version from a live snapshot. */
  #recordObservation(workspace, snapshot, reason, pageId = MAIN_PAGE, meta = {}) {
    const issuedMs = this.#nowMs();
    const targetDigests = Object.fromEntries(snapshot.elements.map((element) => [element.selector, element.digest]));
    const targetFormActions = Object.fromEntries(snapshot.elements
      .filter((element) => element.formAction)
      .map((element) => [element.selector, element.formAction]));
    // Selectors of password fields. Admission refuses to fill one: an admitted action's value is journaled.
    const passwordTargets = snapshot.elements.filter((element) => element.inputType === 'password').map((element) => element.selector);
    const targetNavigations = Object.fromEntries(snapshot.elements
      .filter((element) => element.href)
      .map((element) => [element.selector, element.href]));
    const handles = Object.fromEntries(snapshot.elements
      .filter((element) => element.handle)
      .map((element) => [element.handle, element.selector]));
    this.#append(RECORD_TYPES.OBSERVATION_RECORDED, {
      workspaceId: workspace.workspaceId,
      pageId,
      observationVersion: workspace.observationVersion + 1,
      ownerGeneration: workspace.ownerGeneration,
      reason,
      url: snapshot.url,
      contentHash: snapshot.contentHash,
      issuedAt: new Date(issuedMs).toISOString(),
      expiresAt: new Date(issuedMs + this.#config.observation.maxAgeMs).toISOString(),
      targetDigests,
      targetFormActions,
      targetNavigations,
      ...(passwordTargets.length ? { passwordTargets } : {}),
      handles,
      regions: snapshot.regionDigests,
    });
    const recorded = { ...workspace.observation, title: snapshot.title, text: snapshot.text, elements: snapshot.elements,
      structuralHash: snapshot.structuralHash, isTruncated: snapshot.isTruncated };
    this.#runtimeFor(workspace.workspaceId).latestObservations.set(pageId, {
      ownerGeneration: workspace.ownerGeneration,
      observationVersion: workspace.observationVersion,
      recorded,
      snapshot,
      readRoots: meta.readRoots ?? null,
      includeFormState: Boolean(meta.includeFormState),
      autoControlRegions: Boolean(meta.autoControlRegions),
    });
    return recorded;
  }

  /**
   * Create a durable workspace; the admin credential is returned once.
   */
  async createWorkspace({ workspaceId, scopedReads = false }) {
    if (!this.#ready) throw workspaceError(REJECTION_CODES.AUTHORITY_UNAVAILABLE, 'service is not restored');
    if (typeof workspaceId !== 'string' || !/^[a-z0-9-]+$/.test(workspaceId)) {
      throw workspaceError(REJECTION_CODES.INVALID_COMMAND, 'workspaceId: expected [a-z0-9-]+', {
        path: 'workspaceId',
        received: workspaceId,
      });
    }
    if (this.#state.workspaces.has(workspaceId)) {
      throw workspaceError(REJECTION_CODES.DUPLICATE_WORKSPACE, workspaceId, { workspaceId });
    }
    const { credential, credentialHash } = issueCredential(this.#config.credentials.secretBytes);
    if (scopedReads && this.#config.protocolVersion < 4) throw workspaceError(REJECTION_CODES.INVALID_COMMAND, 'Scoped reads require protocol 4');
    if (typeof scopedReads !== 'boolean') throw workspaceError(REJECTION_CODES.INVALID_COMMAND, 'scopedReads must be boolean');
    this.#append(RECORD_TYPES.WORKSPACE_CREATED, { workspaceId, scopedReads, adminCredentialHash: credentialHash });
    return { workspaceId, adminCredential: credential };
  }

  async grantAuthorization({ workspaceId, adminCredential, grantId, ownerId, intents, actionKinds,
    targetOrigins, expiresAt = null, pageIds, readRegions, uploadFiles }) {
    const workspace = this.#workspace(workspaceId);
    authenticateAdmin(workspace, adminCredential);
    for (const [path, list] of [['intents', intents], ['actionKinds', actionKinds], ['targetOrigins', targetOrigins]]) {
      if (!Array.isArray(list) || list.length === 0 || list.some((item) => typeof item !== 'string')) {
        throw workspaceError(REJECTION_CODES.INVALID_COMMAND, `${path}: expected non-empty string array`, { path });
      }
    }
    const unsupported = actionKinds.filter((kind) => !this.#config.actionKinds.includes(kind));
    if (unsupported.length > 0) {
      throw workspaceError(REJECTION_CODES.UNSUPPORTED_ACTION_KIND, unsupported.join(', '), { received: unsupported });
    }
    if (typeof grantId !== 'string' || typeof ownerId !== 'string' || !grantId || !ownerId) {
      throw workspaceError(REJECTION_CODES.INVALID_COMMAND, 'grantId and ownerId: expected non-empty strings', {
        received: { grantId, ownerId },
      });
    }
    if (expiresAt !== null && Number.isNaN(Date.parse(expiresAt))) {
      throw workspaceError(REJECTION_CODES.INVALID_COMMAND, 'expiresAt: expected ISO time or null', { path: 'expiresAt' });
    }
    const origins = targetOrigins.map((origin, index) => {
      try {
        return new URL(origin).origin;
      } catch {
        throw workspaceError(REJECTION_CODES.INVALID_COMMAND, `targetOrigins[${index}]: expected URL origin`, {
          path: `targetOrigins[${index}]`,
          received: origin,
        });
      }
    });
    if (pageIds !== undefined && (!Array.isArray(pageIds) || !pageIds.length
      || pageIds.some(id => !workspace.pages.has(id) || workspace.pages.get(id).closed))) {
      throw workspaceError(REJECTION_CODES.INVALID_COMMAND, 'pageIds must name open workspace pages');
    }
    if (readRegions !== undefined && readRegions !== null) validateRegionSelectors(readRegions, this.#config, 'readRegions');
    if (workspace.scopedReads && (!pageIds || readRegions === undefined)) {
      throw workspaceError(REJECTION_CODES.INVALID_COMMAND, 'Scoped workspaces require pageIds and readRegions (null means whole page)');
    }
    if (actionKinds.includes('upload') !== (uploadFiles !== undefined)) {
      throw workspaceError(REJECTION_CODES.INVALID_COMMAND, 'Upload grants require explicitly selected uploadFiles; other grants cannot select files');
    }
    return this.#runtimeFor(workspaceId).mutex.run(() => {
      const files = uploadFiles === undefined ? [] : this.#uploads.stage(uploadFiles);
      try {
        this.#append(RECORD_TYPES.AUTHORIZATION_GRANTED, {
          workspaceId,
          grantId,
          grant: { ownerId, intents, actionKinds, targetOrigins: origins, expiresAt, ...(pageIds ? { pageIds } : {}),
            ...(readRegions !== undefined ? { readRegions } : {}), ...(files.length ? { uploadFiles: files } : {}) },
        });
      } catch (error) {
        this.#uploads.discard(files);
        throw error;
      }
      return { grantId, ...(files.length ? { uploadFiles: files } : {}) };
    });
  }

  async revokeAuthorization({ workspaceId, adminCredential, grantId }) {
    const workspace = this.#workspace(workspaceId);
    authenticateAdmin(workspace, adminCredential);
    return this.#runtimeFor(workspaceId).mutex.run(() => {
      this.#append(RECORD_TYPES.AUTHORIZATION_REVOKED, { workspaceId, grantId });
      return { grantId };
    });
  }

  /**
   * Hand the workspace to a new owner. The generation advances durably before the new owner can
   * act; queued commands of earlier generations are ended undispatched. Effects already underway
   * are not undone and are returned among the outstanding records.
   */
  async assignOwner({ workspaceId, adminCredential, ownerId }) {
    const workspace = this.#workspace(workspaceId);
    authenticateAdmin(workspace, adminCredential);
    if (typeof ownerId !== 'string' || ownerId.length === 0) {
      throw workspaceError(REJECTION_CODES.INVALID_COMMAND, 'ownerId: expected non-empty string', { path: 'ownerId' });
    }
    const runtime = this.#runtimeFor(workspaceId);
    return runtime.mutex.run(() => {
      runtime.latestObservations.clear();
      const previous = { ownerId: workspace.ownerId, ownerGeneration: workspace.ownerGeneration };
      const { credential, credentialHash } = issueCredential(this.#config.credentials.secretBytes);
      this.#append(RECORD_TYPES.OWNERSHIP_ADVANCED, {
        workspaceId,
        ownerId,
        ownerGeneration: previous.ownerGeneration + 1,
        ownerCredentialHash: credentialHash,
        previous,
      });
      for (const action of workspace.actions.values()) {
        if (action.status !== ACTION_STATUS.QUEUED) continue;
        this.#append(RECORD_TYPES.ACTION_NOT_DISPATCHED, {
          workspaceId,
          actionId: action.request.actionId,
          stage: 'handoff',
          code: REJECTION_CODES.STALE_OWNER_GENERATION,
          detail: `owner generation advanced to ${workspace.ownerGeneration}`,
        });
      }
      for (const entry of runtime.queue.splice(0)) entry.settle(this.#describe(workspace, entry.actionId));
      return {
        workspaceId,
        ownerId,
        ownerGeneration: workspace.ownerGeneration,
        ownerCredential: credential,
        outstanding: this.#outstanding(workspace),
        boundary: NONATOMIC_BOUNDARY,
      };
    });
  }

  /**
   * Observe the workspace page under the current owner generation; returns a new version.
   * `regions` names page regions whose digests the observation records, so a later action can
   * bind its staleness to them instead of to the whole page.
   */
  async observe(command) {
    const workspace = this.#workspace(command.workspaceId);
    authenticateOwner(workspace, command);
    if (this.#config.protocolVersion < 4 && command.pageId && command.pageId !== MAIN_PAGE) throw workspaceError(REJECTION_CODES.INVALID_COMMAND, 'Additional pages require protocol 4');
    const requested = validateObservationRead(command, this.#config);
    const pageId = command.pageId ?? MAIN_PAGE;
    pageView(workspace, pageId);
    await this.#page(command.workspaceId);
    return this.#runtimeFor(command.workspaceId).mutex.run(async () => {
      authenticateOwner(workspace, command);
      const url = await this.#probe(command.workspaceId, pageId).url();
      const read = scopedRead(workspace, command, url, requested, this.#config, this.#nowMs());
      const currentPageObs = pageView(workspace, pageId).observation;
      const cached = this.#runtimeFor(command.workspaceId).latestObservations.get(pageId);
      if (read.ifCurrentVersion !== undefined
        && currentPageObs?.observationVersion === read.ifCurrentVersion
        && cached?.observationVersion === read.ifCurrentVersion
        && cached.ownerGeneration === workspace.ownerGeneration
        && Date.parse(currentPageObs.expiresAt) > this.#nowMs()
        && cached.recorded.url === url
        && (read.regionGroups ?? []).length === 0
        && (read.regions ?? []).every(sel => sel in (cached.snapshot.regionDigests ?? {}))
        && (!read.includeFormState || cached.includeFormState)
        && JSON.stringify(cached.readRoots ?? null) === JSON.stringify(read.readRoots ?? null)) {
        readGrant(workspace, command, cached.recorded.url, this.#nowMs());
        if (read.view === OUTLINE_VIEW) {
          return { ...outlineView(workspace, cached.recorded, cached.snapshot, read.sinceVersion), reusedCurrentRevision: true, ...(command.pageId ? { pageId } : {}) };
        }
        return structuredClone({ ...cached.recorded, ...(workspace.scopedReads ? { readScope: { pageId, regions: read.readRoots ?? null } } : {}), boundary: NONATOMIC_BOUNDARY });
      }
      const snapshot = await this.#snapshot(command.workspaceId, {
        ...read, outline: read.view === OUTLINE_VIEW || (read.regions?.length ?? 0) > 0,
      }, pageId);
      readGrant(workspace, command, snapshot.url, this.#nowMs());
      const recorded = this.#recordObservation(workspace, snapshot, 'observe', pageId, {
        readRoots: read.readRoots ?? null,
        includeFormState: read.includeFormState,
        autoControlRegions: read.autoControlRegions || (read.regions?.length ?? 0) > 0,
      });
      if (read.view === OUTLINE_VIEW) return { ...outlineView(workspace, recorded, snapshot, read.sinceVersion), ...(command.pageId ? { pageId } : {}) };
      return structuredClone({ ...recorded, ...(workspace.scopedReads ? { readScope: { pageId, regions: read.readRoots ?? null } } : {}), boundary: NONATOMIC_BOUNDARY });
    });
  }

  /**
   * Admit an action. Intent is durable before this resolves; `result` resolves with the action
   * record once it is dispatched, rejected before dispatch, or ended by handoff.
   */
  async submitAction(command) {
    const workspace = this.#workspace(command.workspaceId);
    const runtime = this.#runtimeFor(command.workspaceId);
    const admitted = await runtime.mutex.run(() => {
      let grantId;
      let resolved;
      try {
        ({ grantId, command: resolved } = checkAdmission(pageView(workspace, command.pageId), { ...command, pageId: command.pageId ?? MAIN_PAGE }, this.#config, this.#nowMs()));
      } catch (error) {
        if (isWorkspaceError(error)) {
          this.#append(RECORD_TYPES.COMMAND_REJECTED, {
            workspaceId: command.workspaceId,
            actionId: typeof command.actionId === 'string' ? command.actionId : null,
            stage: 'admission',
            code: error.code,
          });
          // Only admission can attest this before an action was admitted or dispatched.
          error.details = { ...error.details, neverDispatched: { code: error.code } };
        }
        throw error;
      }
      const request = { ...stripCredentials(resolved), grantId, effect: resolved.effect ?? { external: false } };
      const admitT0 = performance.now();
      this.#append(RECORD_TYPES.ACTION_ADMITTED, request);
      const admitJournalMs = Number((performance.now() - admitT0).toFixed(3));
      this.#hooks.afterIntentPersisted?.(request);
      const settlement = deferred();
      runtime.queue.push({ actionId: request.actionId, settle: settlement.settle, admitJournalMs });
      return { actionId: request.actionId, result: settlement.promise };
    });
    this.#pump(command.workspaceId);
    return admitted;
  }

  async #pump(workspaceId) {
    const runtime = this.#runtimeFor(workspaceId);
    if (runtime.pumping) return;
    runtime.pumping = true;
    try {
      while (runtime.queue.length > 0) {
        const entry = runtime.queue.shift();
        try {
          entry.settle(await this.#dispatchOne(workspaceId, entry.actionId, entry.admitJournalMs ?? 0));
        } catch (error) {
          // The journal or service closed mid-dispatch; the durable record, not this reply, is authoritative.
          entry.settle({ actionId: entry.actionId, serviceError: { code: error.code ?? null, message: error.message } });
        }
      }
    } finally {
      runtime.pumping = false;
    }
  }

  async #checkLiveDispatch(workspace, action) {
    const { workspaceId } = workspace;
    const request = action.request;
    checkDispatchAuthority(pageView(workspace, request.pageId), request, this.#nowMs());
    const scope = request.observationScope;
    const regions = scope?.kind === REGIONS_SCOPE ? scope.selectors : [];
    const current = pageView(workspace, request.pageId);
    const permission = readGrant(workspace, request, await this.#probe(workspaceId, request.pageId).url(), this.#nowMs());
    const snapshot = await this.#snapshot(workspaceId, { regions, readRoots: permission?.readRegions ?? null }, request.pageId);
    readGrant(workspace, request, snapshot.url, this.#nowMs());
    if (snapshot.contentHash !== current.observation?.contentHash || snapshot.url !== current.observation?.url) {
      this.#recordObservation(workspace, snapshot, 'page-change', request.pageId);
    }
    const live = { url: snapshot.url, regions: snapshot.regionDigests };
    checkDispatchAuthority(pageView(workspace, request.pageId), request, this.#nowMs(), live);
    const probe = this.#probe(workspaceId, request.pageId, request, snapshot.url);
    let targetDigest = null;
    if (request.target.selector) {
      const element = await probe.element(request.target.selector);
      if (element.count !== 1 || element.digest !== request.target.digest) {
        throw workspaceError(REJECTION_CODES.TARGET_CHANGED, `target ${request.target.selector}`, {
          count: element.count,
        });
      }
      if (request.kind === 'upload') {
        const grant = workspace.grants.get(request.grantId);
        checkUploadTarget(element, this.#uploads.resolve(grant, request.params.fileIds));
      }
      targetDigest = element.digest;
    }
    const preconditions = await evaluateConditions(request.preconditions ?? [], probe);
    if (!preconditions.allEstablished) {
      throw workspaceError(REJECTION_CODES.PRECONDITION_UNESTABLISHED, 'dispatch preconditions', {
        results: preconditions.results,
      });
    }
    return {
      targetDigest,
      preconditionResults: preconditions.results,
      observationScope: scope ?? { kind: 'page' },
      liveRegions: regions.length > 0 ? live.regions : null,
    };
  }

  async #dispatchOne(workspaceId, actionId, admitJournalMs = 0) {
    const dispatchT0 = performance.now();
    let dispatchCheckMs = 0;
    let journalMs = admitJournalMs;
    const workspace = this.#workspace(workspaceId);
    const runtime = this.#runtimeFor(workspaceId);
    const begun = await runtime.mutex.run(async () => {
      const action = workspace.actions.get(actionId);
      if (action.status !== ACTION_STATUS.QUEUED) return { settled: this.#describe(workspace, actionId) };
      let checks;
      const checkT0 = performance.now();
      try {
        await this.#page(workspaceId);
        checks = await this.#checkLiveDispatch(workspace, action);
      } catch (error) {
        this.#append(RECORD_TYPES.ACTION_NOT_DISPATCHED, {
          workspaceId,
          actionId,
          stage: 'dispatch',
          code: isWorkspaceError(error) ? error.code : REJECTION_CODES.PRECONDITION_UNESTABLISHED,
          detail: error.message,
        });
        return { settled: this.#describe(workspace, actionId) };
      } finally {
        dispatchCheckMs = Number((performance.now() - checkT0).toFixed(3));
      }
      const startJ0 = performance.now();
      this.#append(RECORD_TYPES.ACTION_DISPATCH_STARTED, {
        workspaceId,
        actionId,
        ownerGeneration: workspace.ownerGeneration,
        observationVersion: workspace.observationVersion,
        ...checks,
      });
      journalMs += performance.now() - startJ0;
      this.#hooks.afterDispatchStarted?.(action.request);
      return { action };
    });
    if (begun.settled) return begun.settled;
    const outcome = await this.#performEffect(workspaceId, begun.action.request);
    return runtime.mutex.run(async () => {
      let postObservationVersion = null;
      let postObsJournalMs = 0;
      const postSnapT0 = performance.now();
      try {
        const current = pageView(workspace, begun.action.request.pageId);
        const request = begun.action.request;
        const permission = readGrant(workspace, request, await this.#probe(workspaceId, request.pageId).url(), this.#nowMs());
        const priorCached = runtime.latestObservations.get(request.pageId ?? MAIN_PAGE);
        const autoControlRegions = Boolean(priorCached?.autoControlRegions);
        const carryRegions = request.kind === 'click' || request.kind === 'navigate'
          ? []
          : [...new Set([
              ...Object.keys(current.observation?.regions ?? {}),
              ...(request.observationScope?.kind === REGIONS_SCOPE ? request.observationScope.selectors : []),
            ])].slice(0, this.#config.observation.maxRegions);
        const includeFormState = Boolean(priorCached?.includeFormState);
        const snapshot = await this.#snapshot(workspaceId, {
          regions: carryRegions,
          autoControlRegions: autoControlRegions && carryRegions.length === 0,
          outline: carryRegions.length > 0 || autoControlRegions,
          includeFormState,
          readRoots: permission?.readRegions ?? null,
        }, request.pageId);
        readGrant(workspace, request, snapshot.url, this.#nowMs());
        if (snapshot.contentHash !== current.observation?.contentHash || snapshot.url !== current.observation?.url) {
          const obsJ0 = performance.now();
          this.#recordObservation(workspace, snapshot, 'post-action', begun.action.request.pageId, {
            readRoots: permission?.readRegions ?? null,
            includeFormState,
            autoControlRegions,
          });
          postObsJournalMs = performance.now() - obsJ0;
        } else if (current.observation) {
          runtime.latestObservations.set(request.pageId ?? MAIN_PAGE, {
            ownerGeneration: workspace.ownerGeneration,
            observationVersion: workspace.observationVersion,
            recorded: {
              ...current.observation,
              title: snapshot.title,
              text: snapshot.text,
              elements: snapshot.elements,
              structuralHash: snapshot.structuralHash,
              isTruncated: snapshot.isTruncated,
            },
            snapshot,
            readRoots: permission?.readRegions ?? null,
            includeFormState,
            autoControlRegions,
          });
        }
        postObservationVersion = workspace.observationVersion;
      } catch (error) {
        outcome.evidence = { ...outcome.evidence, postObservationError: error.message };
      }
      const postSnapshotTotalMs = performance.now() - postSnapT0;
      const postSnapshotMs = Number(Math.max(0, postSnapshotTotalMs - postObsJournalMs).toFixed(3));
      journalMs += postObsJournalMs;
      outcome.evidence = {
        ...outcome.evidence,
        dispatchProfileMs: {
          dispatchCheckMs,
          browserExecuteMs: outcome.evidence?.effectExecuteMs ?? 0,
          valueSettleMs: outcome.evidence?.valueSettleElapsedMs ?? 0,
          postSnapshotMs,
          journalBeforeOutcomeMs: Number(journalMs.toFixed(3)),
          totalDispatchMs: Number((performance.now() - dispatchT0).toFixed(3)),
        },
      };
      this.#append(RECORD_TYPES.ACTION_OUTCOME, {
        workspaceId,
        actionId,
        ...outcome,
        postObservationVersion,
        boundary: NONATOMIC_BOUNDARY,
      });
      this.#hooks.afterOutcome?.(begun.action.request);
      return this.#describe(workspace, actionId);
    });
  }

  async #performEffect(workspaceId, request) {
    let effect;
    const execT0 = performance.now();
    try {
      const uploadFiles = request.kind === 'upload'
        ? this.#uploads.resolve(this.#workspace(workspaceId).grants.get(request.grantId), request.params.fileIds) : null;
      effect = await withTimeout(this.#adapter.execute(workspaceId, request, uploadFiles), this.#config.dispatch.actionTimeoutMs);
    } catch (error) {
      return {
        outcome: OUTCOMES.UNKNOWN,
        basis: error.isTimeout ? 'effect-timeout' : 'effect-exception',
        evidence: { message: error.message, effectExecuteMs: Number((performance.now() - execT0).toFixed(3)) },
      };
    }
    const effectExecuteMs = Number((performance.now() - execT0).toFixed(3));
    this.#hooks.afterEffect?.(request);
    if (request.kind === 'upload') {
      const attached = await this.#awaitValue(workspaceId, request, effect, effectExecuteMs);
      if (attached.outcome !== OUTCOMES.COMPLETED || !request.completion?.completedWhen?.length) return attached;
    }
    const completion = request.completion;
    if (completion?.completedWhen?.length) return this.#awaitCompletion(workspaceId, completion, effect, request, effectExecuteMs);
    if (VALUE_CONDITIONS[request.kind]) return this.#awaitValue(workspaceId, request, effect, effectExecuteMs);
    return { outcome: OUTCOMES.COMPLETED, basis: KIND_COMPLETION_BASIS[request.kind], evidence: { effect, effectExecuteMs, valueSettleElapsedMs: 0 } };
  }

  /**
   * A filled or chosen value counts only once the page shows it and still shows it after
   * dispatch.valueSettleMs, so a page that resets the value (late hydration, a re-render) is
   * caught. Never shown: value-unverified. Shown, then lost: value-reverted. Both stay unknown.
   * Waits count poll intervals rather than clock time, so an injected clock cannot stall them.
   */
  async #awaitValue(workspaceId, request, effect, effectExecuteMs = 0) {
    const settleT0 = performance.now();
    const conditions = request.kind === 'upload'
      ? [{ kind: 'input-files-equal', selector: request.target.selector,
        files: effect.files.map(({ name, byteLength }) => ({ name, byteLength })) }]
      : [{ kind: VALUE_CONDITIONS[request.kind], selector: request.target.selector, value: request.params.value }];
    const probe = this.#probe(workspaceId, request.pageId, request);
    const { completionTimeoutMs, completionPollMs, valueSettleMs } = this.#config.dispatch;
    const pause = () => new Promise((resolve) => setTimeout(resolve, completionPollMs));
    let check = await evaluateConditions(conditions, probe);
    for (let waitedMs = 0; !check.allEstablished && waitedMs < completionTimeoutMs; waitedMs += completionPollMs) {
      await pause();
      check = await evaluateConditions(conditions, probe);
    }
    if (!check.allEstablished) {
      return { outcome: OUTCOMES.UNKNOWN, basis: 'value-unverified', evidence: { effect, check, effectExecuteMs, valueSettleElapsedMs: Number((performance.now() - settleT0).toFixed(3)) } };
    }
    const settleIntervals = valueSettleMs >= completionPollMs * 2
      ? [Math.floor(valueSettleMs / 2), valueSettleMs - Math.floor(valueSettleMs / 2)]
      : [valueSettleMs];
    for (const waitMs of settleIntervals) {
      await new Promise((resolve) => setTimeout(resolve, waitMs));
      const recheck = await evaluateConditions(conditions, probe);
      if (!recheck.allEstablished) {
        return { outcome: OUTCOMES.UNKNOWN, basis: 'value-reverted', evidence: { effect, check, recheck, effectExecuteMs, valueSettleElapsedMs: Number((performance.now() - settleT0).toFixed(3)) } };
      }
    }
    return {
      outcome: OUTCOMES.COMPLETED,
      basis: KIND_COMPLETION_BASIS[request.kind],
      evidence: { effect, check, effectExecuteMs, valueSettleElapsedMs: Number((performance.now() - settleT0).toFixed(3)) },
    };
  }

  async #awaitCompletion(workspaceId, completion, effect, request, effectExecuteMs = 0) {
    const probe = this.#probe(workspaceId, request.pageId, request);
    const deadline = this.#nowMs() + this.#config.dispatch.completionTimeoutMs;
    let last = null;
    for (;;) {
      if (completion.failedWhen?.length) {
        const failed = await evaluateConditions(completion.failedWhen, probe);
        if (failed.allEstablished) {
          return { outcome: OUTCOMES.FAILED, basis: 'failure-condition', evidence: { effect, conditions: failed } };
        }
      }
      last = await evaluateConditions(completion.completedWhen, probe);
      if (last.allEstablished) {
        return { outcome: OUTCOMES.COMPLETED, basis: 'completion-condition', evidence: { effect, conditions: last } };
      }
      if (this.#nowMs() >= deadline) break;
      await new Promise((resolve) => setTimeout(resolve, this.#config.dispatch.completionPollMs));
    }
    return { outcome: OUTCOMES.UNKNOWN, basis: 'completion-unestablished', evidence: { effect, conditions: last } };
  }

  #describe(workspace, actionId) {
    return structuredClone({ ...describeAction(workspace.actions.get(actionId)), boundary: NONATOMIC_BOUNDARY });
  }

  #outstanding(workspace) {
    return [...workspace.actions.values()]
      .map(action => structuredClone(describeAction(action)))
      .filter((action) => action.isUncertain
        || action.dispatchStatus === ACTION_STATUS.QUEUED
        || (action.dispatchStatus === ACTION_STATUS.DISPATCHED && action.outcome === null)
        || action.acknowledgedGeneration === null);
  }

  async outstanding(command) {
    const workspace = this.#workspace(command.workspaceId);
    authenticateOwner(workspace, command);
    return this.#outstanding(workspace);
  }

  async action(command) {
    const workspace = this.#workspace(command.workspaceId);
    authenticateOwner(workspace, command);
    if (!workspace.actions.has(command.actionId)) {
      throw workspaceError(REJECTION_CODES.UNKNOWN_ACTION, String(command.actionId), { actionId: command.actionId });
    }
    return this.#describe(workspace, command.actionId);
  }

  /** Record that the current owner received an action's settled state. */
  async acknowledge(command) {
    const workspace = this.#workspace(command.workspaceId);
    return this.#runtimeFor(command.workspaceId).mutex.run(() => {
      authenticateOwner(workspace, command);
      const action = workspace.actions.get(command.actionId);
      if (!action) {
        throw workspaceError(REJECTION_CODES.UNKNOWN_ACTION, String(command.actionId), { actionId: command.actionId });
      }
      if (action.status === ACTION_STATUS.QUEUED || (action.status === ACTION_STATUS.DISPATCHED && !action.outcome)) {
        throw workspaceError(REJECTION_CODES.INVALID_COMMAND, 'action has not settled', { actionId: command.actionId });
      }
      this.#append(RECORD_TYPES.ACTION_ACKNOWLEDGED, {
        workspaceId: command.workspaceId,
        actionId: command.actionId,
        ownerGeneration: workspace.ownerGeneration,
      });
      return this.#describe(workspace, command.actionId);
    });
  }

  #requireUnknown(workspace, actionId) {
    const action = workspace.actions.get(actionId);
    if (!action) throw workspaceError(REJECTION_CODES.UNKNOWN_ACTION, String(actionId), { actionId });
    if (action.outcome?.outcome !== OUTCOMES.UNKNOWN || describeAction(action).isUncertain === false) {
      throw workspaceError(REJECTION_CODES.RECONCILIATION_NOT_APPLICABLE, `${actionId} is not uncertain`, { actionId });
    }
    return action;
  }

  /**
   * Resolve or route an unknown outcome. Application-state reconciliation reads the live page;
   * external idempotency permits a resubmission reusing the original key; human review defers
   * to the workspace administrator. The unknown outcome record itself is never rewritten.
   */
  async reconcile(command) {
    const workspace = this.#workspace(command.workspaceId);
    if (!this.#config.reconciliationMethods.includes(command.method)) {
      throw workspaceError(REJECTION_CODES.UNSUPPORTED_RECONCILIATION, String(command.method), {
        expected: this.#config.reconciliationMethods,
        received: command.method,
      });
    }
    if (command.method === 'application-state') {
      validateConditions(command.effectPresentWhen ?? [], this.#config.conditionKinds, 'effectPresentWhen');
      validateConditions(command.effectAbsentWhen ?? [], this.#config.conditionKinds, 'effectAbsentWhen');
      await this.#page(command.workspaceId);
    }
    return this.#runtimeFor(command.workspaceId).mutex.run(async () => {
      authenticateOwner(workspace, command);
      const action = this.#requireUnknown(workspace, command.actionId);
      const body = await this.#reconciliationBody(workspace, action, command);
      this.#append(RECORD_TYPES.ACTION_RECONCILED, {
        workspaceId: command.workspaceId,
        actionId: command.actionId,
        method: command.method,
        ownerGeneration: workspace.ownerGeneration,
        decidedBy: { ownerId: workspace.ownerId },
        ...body,
      });
      return this.#describe(workspace, command.actionId);
    });
  }

  async #reconciliationBody(workspace, action, command) {
    if (command.method === 'external-idempotency') {
      const key = action.request.effect?.externalIdempotencyKey;
      if (!key) {
        throw workspaceError(REJECTION_CODES.RECONCILIATION_NOT_APPLICABLE, 'action carried no external idempotency key', {
          actionId: command.actionId,
        });
      }
      return {
        result: 'idempotent-resubmission-permitted',
        resolvesUncertainty: false,
        permitsResubmission: true,
        requiredIdempotencyKey: key,
        basis: { externalIdempotencyKey: key },
      };
    }
    if (command.method === 'human-review') {
      return { result: 'human-review-requested', resolvesUncertainty: false, permitsResubmission: false, basis: {} };
    }
    const probe = this.#probe(workspace.workspaceId, action.request.pageId, command);
    const present = await evaluateConditions(command.effectPresentWhen ?? [], probe);
    const absent = await evaluateConditions(command.effectAbsentWhen ?? [], probe);
    const isPresent = (command.effectPresentWhen ?? []).length > 0 && present.allEstablished;
    const isAbsent = (command.effectAbsentWhen ?? []).length > 0 && absent.allEstablished;
    const result = isPresent === isAbsent ? 'inconclusive' : (isPresent ? 'effect-present' : 'effect-absent');
    return {
      result,
      resolvesUncertainty: result !== 'inconclusive',
      permitsResubmission: result === 'effect-absent',
      basis: { url: await probe.url(), effectPresent: present, effectAbsent: absent },
    };
  }

  /** Administrator decision on a human-review request. */
  async decideHumanReview({ workspaceId, adminCredential, actionId, decision, note = '' }) {
    const workspace = this.#workspace(workspaceId);
    authenticateAdmin(workspace, adminCredential);
    const decisions = { 'effect-present': false, 'effect-absent': true };
    if (!(decision in decisions)) {
      throw workspaceError(REJECTION_CODES.INVALID_COMMAND, 'decision: expected effect-present or effect-absent', {
        path: 'decision',
        received: decision,
      });
    }
    return this.#runtimeFor(workspaceId).mutex.run(() => {
      const action = this.#requireUnknown(workspace, actionId);
      if (action.reconciliations.at(-1)?.result !== 'human-review-requested') {
        throw workspaceError(REJECTION_CODES.RECONCILIATION_NOT_APPLICABLE, 'no pending human review', { actionId });
      }
      this.#append(RECORD_TYPES.ACTION_RECONCILED, {
        workspaceId,
        actionId,
        method: 'human-review',
        ownerGeneration: workspace.ownerGeneration,
        decidedBy: { role: 'workspace-admin' },
        result: decision,
        resolvesUncertainty: true,
        permitsResubmission: decisions[decision],
        basis: { note },
      });
      return this.#describe(workspace, actionId);
    });
  }

  /** Supported client boundary: metadata contains no control credentials or browser handles. */
  async inspect({ workspaceId, adminCredential }) {
    const workspace = this.#workspace(workspaceId);
    authenticateAdmin(workspace, adminCredential);
    await this.#page(workspaceId);
    return this.#runtimeFor(workspaceId).mutex.run(async () => {
      const pages = this.#adapter.listPages ? await this.#bounded(this.#adapter.listPages(workspaceId))
        : [{ pageId: MAIN_PAGE, url: await this.#probe(workspaceId).url(), closed: false }];
      for (const page of pages) {
        const previous = workspace.pages.get(page.pageId);
        const needsReopen = page.url === 'about:blank' && !!previous?.lastKnownUrl;
        const value = { workspaceId, ...page, lastKnownUrl: page.url.startsWith('http') ? page.url : previous?.lastKnownUrl ?? null, needsReopen };
        if (JSON.stringify(previous) !== JSON.stringify(value)) {
          this.#append(RECORD_TYPES.PAGE_REGISTERED, value);
        }
      }
      return structuredClone({ workspaceId, scopedReads: workspace.scopedReads, ownerId: workspace.ownerId,
        ownerGeneration: workspace.ownerGeneration, pages: [...workspace.pages.values()],
        grants: [...workspace.grants.values()], actions: [...workspace.actions.values()].map(describeAction),
        boundary: NONATOMIC_BOUNDARY });
    });
  }

  async openPage({ workspaceId, adminCredential, pageId = `page-${randomUUID()}` }) {
    if (this.#config.protocolVersion < 4) throw workspaceError(REJECTION_CODES.INVALID_COMMAND, 'Additional pages require protocol 4');
    const workspace = this.#workspace(workspaceId);
    authenticateAdmin(workspace, adminCredential);
    await this.#page(workspaceId);
    if (!this.#adapter.openPage) throw workspaceError(REJECTION_CODES.INVALID_COMMAND, 'Adapter does not support additional pages');
    return this.#runtimeFor(workspaceId).mutex.run(async () => {
      if (typeof pageId !== 'string' || !/^[a-z0-9-]{1,128}$/i.test(pageId) || workspace.pages.has(pageId)) {
        throw workspaceError(REJECTION_CODES.INVALID_COMMAND, 'pageId must be unique, including closed page identities');
      }
      await this.#bounded(this.#adapter.openPage(workspaceId, pageId));
      this.#append(RECORD_TYPES.PAGE_REGISTERED, { workspaceId, pageId, url: 'about:blank', closed: false });
      return { pageId };
    });
  }

  async selectRegion({ workspaceId, adminCredential, pageId }) {
    const workspace = this.#workspace(workspaceId);
    authenticateAdmin(workspace, adminCredential);
    if (workspace.ownerId !== 'human') throw workspaceError(REJECTION_CODES.INVALID_COMMAND, 'Take over before selecting a page region');
    pageView(workspace, pageId);
    await this.#page(workspaceId);
    return this.#bounded(this.#adapter.selectRegion(workspaceId, pageId));
  }

  async focusPage({ workspaceId, adminCredential, pageId }) {
    const workspace = this.#workspace(workspaceId);
    authenticateAdmin(workspace, adminCredential);
    pageView(workspace, pageId);
    await this.#page(workspaceId);
    await this.#adapter.focusPage(workspaceId, pageId);
    return { pageId };
  }

  /** Stop accepting commands and release the browser and journal. Reports how each browser was released. */
  async close() {
    this.#ready = false;
    const released = await this.#adapter.close();
    const releases = Array.isArray(released) ? released.filter(value => value?.workspaceId && value.release) : [];
    const retained = new Set([...this.#state.workspaces.values()].flatMap(workspace => [...workspace.grants.values()]
      .filter(grant => grant.expiresAt === null || Date.parse(grant.expiresAt) > this.#nowMs())
      .flatMap(grant => (grant.uploadFiles ?? []).map(file => file.fileId))));
    try { this.#uploads.retireUnused(retained); }
    finally { this.#journal.close(); }
    return { releases };
  }
}

export { NONATOMIC_BOUNDARY, WorkspaceService };
