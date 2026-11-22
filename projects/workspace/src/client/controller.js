// Human and agent clients compose the supported service; only the service dispatches effects.
import { completionContract } from './completion-contract.js';
import { randomUUID } from 'node:crypto';
import { mkdirSync, readFileSync, writeFileSync, renameSync, existsSync, chmodSync, openSync, fsyncSync, closeSync } from 'node:fs';
import { join } from 'node:path';
import { realpath } from 'node:fs/promises';
import { InvestigationStore } from './investigation.js';
import { repositoryEvidence, repositoryFiles } from './repository.js';
import { startAgent, investigationContext } from './agent.js';
import { handoffBrief } from './handoff.js';
import { validityBrief, describeChange, unfinishedRecords } from './validity.js';
import { unreadMentions, claimsAbsence } from './unread-mentions.js';
import { readArtifact } from './artifact-read.js';
import { listArtifacts } from './artifact-memory.js';
import { REJECTION_CODES } from '../errors.js';
import { createOwnerSession } from '../workflows/owner-session.js';
import { sha256Hex } from '../journal.js';
import { driveReviewBatch, prepareReviewBatch, ReviewBatches } from './review-batch.js';

const CORRECTABLE_PROPOSALS = new Set([
  REJECTION_CODES.INVALID_COMMAND, REJECTION_CODES.UNSUPPORTED_CONDITION,
  REJECTION_CODES.UNSUPPORTED_ACTION_KIND, REJECTION_CODES.UNKNOWN_TARGET,
  REJECTION_CODES.TARGET_CHANGED, REJECTION_CODES.STALE_OBSERVATION,
  REJECTION_CODES.EXPIRED_OBSERVATION, REJECTION_CODES.UNKNOWN_OBSERVATION,
  // Raised by this client before anything reaches the service: an action on a page the planner has not read.
  'observation-required',
  // Raised by this client before a record is saved: an absence claim whose deciding code was never shown.
  'unread-definition',
]);

/**
 * A navigation that reaches its URL is recorded as completed even when the site answers with an error
 * page. Say so where the planner will read it: an unreachable page is often a lost sign-in.
 */
export function navigationNotice(input, result) {
  const status = result?.evidence?.effect?.status;
  if (input?.kind !== 'navigate' || !Number.isInteger(status) || status < 400) return result;
  return { ...result, notice: `The site answered HTTP ${status} for this address. The page may not exist, or it may need a sign-in that is missing or has expired; observe it before relying on it.` };
}

/** What the planner needs from an observation. Admission tables and digests stay in the service. */
export function plannerView(observation, pageId) {
  return { pageId, url: observation.url, title: observation.title, observationVersion: observation.observationVersion,
    isTruncated: observation.isTruncated, text: observation.text,
    elements: (observation.elements ?? []).filter(element => element.handle).map(({ handle, selector, role, label, value, inputType, href, formAction, actionability }) =>
      ({ handle, selector, role, label, ...(value ? { value } : {}), ...(inputType ? { inputType } : {}), ...(href ? { href } : {}),
        // Admission rejects a click on a control that submits a form; say so before the planner spends a turn finding out.
        ...(formAction ? { submitsForm: true } : {}), ...(actionability ? { actionability } : {}) })) };
}

export class WorkspaceController {
  constructor({ service, stateDir, config, planner = null, workflowStore = null, workflowTasks = new Map() }) {
    this.service = service; this.config = config; this.planner = planner; this.active = new Map(); this.owners = new Map(); this.operations = new Map();
    this.workflowStore = workflowStore;
    this.workflowTasks = new Map(workflowTasks);
    this.reviewBatches = new ReviewBatches(join(stateDir, 'review-batches'));
    this.batchRuns = new Map();
    mkdirSync(stateDir, { recursive: true, mode: 0o700 }); chmodSync(stateDir, 0o700);
    this.credentialsPath = join(stateDir, 'client-credentials.json');
    this.credentials = existsSync(this.credentialsPath) ? JSON.parse(readFileSync(this.credentialsPath, 'utf8')) : {};
    this.store = new InvestigationStore(join(stateDir, 'investigations'));
  }
  saveCredentials() {
    const temporary = `${this.credentialsPath}.new`;
    writeFileSync(temporary, `${JSON.stringify(this.credentials)}\n`, { mode: 0o600 });
    chmodSync(temporary, 0o600);
    const fd = openSync(temporary, 'r');
    try { fsyncSync(fd); } finally { closeSync(fd); }
    renameSync(temporary, this.credentialsPath);
  }
  admin(id) { const value = this.credentials[id]; if (!value) throw Error('Missing investigation admin credential'); return { workspaceId: id, adminCredential: value }; }
  async restore() {
    for (const id of this.store.projects.keys()) {
      await this.exclusive(id, async () => {
        const interrupted = this.store.get(id).run;
        const prior = await this.service.inspect(this.admin(id));
        // Fence the dead operator before removing its task grants. A crash skips
        // the normal delegation finalizer; those grants must not survive restore.
        await this.takeOverNow(id);
        for (const grant of prior.grants.filter(value => value.ownerId === 'agent')) {
          await this.service.revokeAuthorization({ ...this.admin(id), grantId: grant.grantId });
        }
        await this.reviewBatches.finish(id, null, 'interrupted', 'batch-restart-review-required');
        if (interrupted?.status === 'running') this.store.run(id, { ...interrupted,
          status: 'needs-attention', detail: 'Service restarted. Review recorded outcomes before explicitly resuming.' });
      });
    }
  }
  async create({ goal, repositoryRoot = null }) {
    if (typeof goal !== 'string' || !goal.trim() || Buffer.byteLength(goal) > this.config.maxInputBytes) throw Error('Provide a non-empty goal within the investigation input budget');
    const root = repositoryRoot ? await realpath(repositoryRoot) : null;
    const id = `investigation-${randomUUID()}`;
    const { adminCredential } = await this.service.createWorkspace({ workspaceId: id, scopedReads: true });
    this.credentials[id] = adminCredential; this.saveCredentials();
    this.store.create({ id, goal, repositoryRoot: root });
    await this.takeOver(id); return { id };
  }
  owner(id) { const value = this.owners.get(id); if (!value) throw Error('Investigation has no current client owner'); return { workspaceId: id, ...value }; }
  exclusive(id, task) {
    const previous = this.operations.get(id) ?? Promise.resolve();
    const result = previous.then(task);
    const settled = result.then(() => {}, () => {});
    this.operations.set(id, settled);
    settled.then(() => { if (this.operations.get(id) === settled) this.operations.delete(id); });
    return result;
  }
  takeOver(id) {
    return this.exclusive(id, async () => {
      const pending = this.batchRuns.get(id);
      if (pending) {
        await this.reviewBatches.cancel(id);
        pending.controller.abort(Object.assign(Error('Human took control'), { code: 'batch-cancelled' }));
      }
      const result = await this.takeOverNow(id);
      const blocked = this.reviewBatches.read(id);
      if (blocked?.status === 'needs-attention') {
        const inspected = await this.service.inspect(this.admin(id));
        for (const grant of inspected.grants.filter(value => value.ownerId === 'agent')) {
          await this.service.revokeAuthorization({ ...this.admin(id), grantId: grant.grantId });
        }
        await this.reviewBatches.finish(id, blocked.id, 'interrupted', 'batch-takeover-recovered');
      }
      return result;
    });
  }
  async takeOverNow(id) {
    this.active.get(id)?.controller.abort(Error('Human took control'));
    const owner = await this.service.assignOwner({ ...this.admin(id), ownerId: 'human' });
    this.owners.set(id, createOwnerSession(this.service, { workspaceId: id, ...owner }).identity);
    const run = this.store.get(id).run;
    if (run?.status === 'running') this.store.run(id, { ...run, status: 'stopped', detail: 'Human has control. Previously dispatched work may still complete.' });
    this.store.activity(id, { event: 'human-control', outstanding: owner.outstanding });
    return { outstanding: owner.outstanding, boundary: owner.boundary };
  }
  async humanPage(id, pageId, extraOrigins = []) {
    if (this.owner(id).ownerId !== 'human') throw Error('Take over before issuing a human action');
    const state = await this.service.inspect(this.admin(id));
    const page = state.pages.find(value => value.pageId === pageId && !value.closed);
    if (!page) throw Error('Select an open page');
    const origin = page.url === 'about:blank' ? [] : [new URL(page.url).origin];
    await this.service.grantAuthorization({ ...this.admin(id), grantId: `human-${pageId}`, ownerId: 'human',
      intents: ['human'], actionKinds: ['navigate', 'click', 'fill', 'select', 'submit', 'download'],
      targetOrigins: [...new Set([...origin, ...extraOrigins, ...(origin.length || extraOrigins.length ? [] : ['about:blank'])])], pageIds: [pageId], readRegions: null });
    return this.owner(id);
  }
  async navigate(id, { pageId, url }) {
    const target = new URL(url);
    if (!['http:', 'https:'].includes(target.protocol)) throw Error('Navigation requires HTTP or HTTPS');
    const owner = await this.humanPage(id, pageId, [target.origin]);
    const observation = await this.service.observe({ ...owner, pageId });
    const admitted = await this.service.submitAction({ ...owner, pageId, actionId: randomUUID(), authorizedIntent: 'human',
      kind: 'navigate', target: { url: target.href }, observationVersion: observation.observationVersion });
    return admitted.result;
  }
  async capture(id, { pageId, regions = [], artifactId, expectedRevision = 0 }, owner = null, onObservation = null) {
    const identity = owner ?? await this.humanPage(id, pageId);
    const observation = await this.service.observe({ ...identity, pageId, ...(regions.length ? { regions } : {}) });
    onObservation?.(observation);
    const content = observation.text;
    const source = { kind: 'page', pageId, url: observation.url, observationVersion: observation.observationVersion,
      capturedAt: new Date().toISOString(), regions: observation.readScope?.regions ?? null, content, sha256: sha256Hex(content) };
    const previous = artifactId ? this.store.get(id).artifacts[artifactId] : null;
    if (artifactId && (previous?.source?.kind !== 'page' || previous.source.pageId !== pageId)) throw Error('Source identity does not match this page');
    if (previous && observation.url === 'about:blank') throw Error('Reopen the source page before refreshing its evidence');
    if (previous?.source.sha256 === source.sha256 && previous.source.url === source.url) return previous;
    return this.store.revise(id, { id: artifactId, expectedRevision, kind: 'evidence', text: `Page evidence: ${observation.title || observation.url}`, source });
  }
  async readRepository(id, { path, artifactId, expectedRevision = 0 }) {
    const source = await repositoryEvidence(this.store.get(id).repositoryRoot, path, this.config.maxEvidenceBytes);
    const previous = artifactId ? this.store.get(id).artifacts[artifactId] : null;
    if (artifactId && (previous?.source?.kind !== 'repository' || previous.source.path !== source.path)) throw Error('Source identity does not match this repository file');
    if (previous?.source.sha256 === source.sha256) return previous;
    return this.store.revise(id, { id: artifactId, expectedRevision, kind: 'evidence', text: `Repository evidence: ${path}`, source });
  }
  /** A person's note for whoever continues: kept in the journal and shown in every handoff. */
  humanNote(id, text) {
    if (typeof text !== 'string' || !text.trim() || Buffer.byteLength(text) > this.config.maxInputBytes) throw Error('Provide a non-empty note within budget');
    this.store.get(id);
    return this.store.activity(id, { event: 'human-note', text: text.trim() });
  }
  /** What a returning agent or person sees: prior sessions, attempts, human notes, unknown outcomes. */
  async handoff(id, options = {}) { return handoffBrief(this.store.get(id), await this.service.inspect(this.admin(id)), options); }
  record(id, input) {
    if (input.kind === 'evidence' || (input.id && this.store.get(id).artifacts[input.id]?.kind === 'evidence')) throw Error('Capture a page or repository file to create evidence');
    return this.store.revise(id, input);
  }
  /**
   * Compare every saved repository source with the file as it is now, and say what that means for
   * the conclusions built on it. A changed file is saved as the next revision of the same evidence
   * record, which marks every record resting on it for review; the earlier bytes stay in the journal.
   * Pages are not re-read here: reopening a page is a browser action someone has to take.
   */
  async checkSources(id, { refresh = true } = {}) {
    const project = this.store.get(id), changed = [], unchecked = [];
    let unchangedCount = 0;
    for (const artifact of Object.values(project.artifacts).filter(value => value.kind === 'evidence')) {
      if (artifact.source?.kind !== 'repository') {
        unchecked.push({ artifactId: artifact.id, source: artifact.source?.url ?? null, reason: 'a page is rechecked by opening it and saving it again' });
        continue;
      }
      let live;
      try { live = await repositoryEvidence(project.repositoryRoot, artifact.source.path, this.config.maxEvidenceBytes); }
      catch (error) {
        changed.push({ artifactId: artifact.id, path: artifact.source.path, missing: true, savedRevision: artifact.revision, detail: String(error.message).slice(0, 200) });
        continue;
      }
      if (live.sha256 === artifact.source.sha256) { unchangedCount += 1; continue; }
      const revision = refresh ? this.store.revise(id, { id: artifact.id, expectedRevision: artifact.revision, kind: 'evidence', text: artifact.text, source: live }).revision : artifact.revision;
      changed.push({ artifactId: artifact.id, path: artifact.source.path, previousRevision: artifact.revision, revision, refreshed: refresh,
        previousSha256: artifact.source.sha256, sha256: live.sha256, change: describeChange(artifact.source.content, live.content) });
    }
    this.store.activity(id, { event: 'sources-checked', changed, unchecked, unchangedCount });
    const workspace = await this.service.inspect(this.admin(id));
    return validityBrief(this.store.get(id), { unresolvedActions: workspace.actions.filter(action => action.isUncertain).length });
  }
  /** Trusted host entrypoint. Task/account/disclosure/oracle definitions are installed by the
   * host, not accepted from HTTP, a model, or a downloaded graph. No final-submit permission.
   */
  #workflowFields(definition) {
    const seen = new Set(), fields = [];
    for (const field of definition.disclosurePolicy?.fields ?? []) {
      if (seen.has(field.slot)) continue;
      seen.add(field.slot);
      const options = Array.isArray(definition.slotOptions?.[field.slot]) ? [...definition.slotOptions[field.slot]] : undefined;
      fields.push({ slot: field.slot, kind: field.kind, label: definition.slotLabels?.[field.slot] ?? field.locator[1],
        inputType: field.locator[3] || 'text', ...(options ? { options } : {}) });
    }
    return fields;
  }
  #workflowSummaries() {
    if (!this.workflowStore || !this.workflowTasks.size) return [];
    return [...this.workflowTasks.entries()].map(([template, definition]) => {
      const { revision, hasLearnedGraph } = this.workflowStore.summary({ accountScope: definition.accountScope, template });
      return { template, label: definition.label ?? template, task: definition.task,
        origin: definition.disclosurePolicy.origin, plannerConfigured: Boolean(definition.planner ?? this.planner),
        learnRepairs: definition.learnRepairs ?? true, revision, hasLearnedGraph, fields: this.#workflowFields(definition) };
    });
  }
  // Trusted host API only. No browser, planner or HTTP caller supplies its own policy.
  async runPersonalWorkflowBatch(id, input) {
    const policy = this.workflowTasks.get(input?.template)?.reviewBatch;
    const planned = prepareReviewBatch(input, policy, this.config.maxInputBytes);
    return this.exclusive(id, async () => {
      this.admin(id);
      if (!this.workflowStore || this.active.has(id) || this.batchRuns.has(id)) throw Error('Workspace is not ready for a batch');
      const job = await this.reviewBatches.reserve(id, planned);
      const controller = new AbortController();
      const budget = AbortSignal.timeout(Math.max(1, job.deadline - Date.now()));
      const signal = AbortSignal.any([controller.signal, budget]);
      const done = driveReviewBatch(this.reviewBatches, job, planned.manifest, signal,
        item => this.#startPersonalWorkflow(id, { ...item, template: planned.template, mode: 'reuse' },
          { id: job.id, signal, versionId: job.versionId, recordId: item.recordId, policy: planned.policy }));
      this.batchRuns.set(id, { controller, done, id: job.id });
      const release = () => { if (this.batchRuns.get(id)?.id === job.id) this.batchRuns.delete(id); };
      done.then(release, release);
      return { batchId: job.id, done };
    });
  }
  reviewBatchStatus(id) { this.admin(id); return this.reviewBatches.read(id); }
  runPersonalWorkflow(id, input) { return this.#startPersonalWorkflow(id, input); }
  #startPersonalWorkflow(id, { template, pageId = 'main', inputs, mode } = {}, batch = null) {
    return this.exclusive(id, async () => {
      this.reviewBatches.assertAdmission(id, batch?.id ?? null);
      batch?.signal.throwIfAborted();
      const definition = typeof template === 'string' ? this.workflowTasks.get(template) : null;
      if (!this.workflowStore || !definition || !['learn', 'reuse', 'fresh'].includes(mode)) {
        throw Error('Select an installed personal workflow and explicit mode');
      }
      if (!inputs || typeof inputs !== 'object' || Array.isArray(inputs)) throw Error('Provide workflow slot values');
      const allowedSlots = new Set(definition.disclosurePolicy.fields.map(field => field.slot));
      for (const [slot, value] of Object.entries(inputs)) {
        if (!allowedSlots.has(slot)) throw Error(`Unknown workflow input slot ${slot}`);
        if (typeof value !== 'string' || Buffer.byteLength(value) > this.config.maxInputBytes) {
          throw Error(`Provide a string value within budget for workflow slot ${slot}`);
        }
      }
      const planner = batch ? null : definition.planner ?? this.planner;
      if (!planner && mode !== 'reuse') throw Error('Configure BLITZEN_MODEL (or FAWN_MODEL) and the planner API credential before delegating');
      if (this.active.has(id)) throw Error('The prior agent has not settled');
      const before = await this.service.inspect(this.admin(id));
      if (!before.pages.some(value => value.pageId === pageId && !value.closed)) throw Error('Select an open page');
      if (before.actions.some(action => action.isUncertain || action.dispatchStatus === 'queued'
        || (action.dispatchStatus === 'dispatched' && !action.outcome))) throw Error('Review unresolved actions before delegating');
      const grantId = `workflow-${randomUUID()}`, runId = randomUUID();
      const { disclosurePolicy, accountScope, verifyAccount, verifyReview, verificationId, taskSourceHashes,
        task, fieldGroups = null, learnRepairs = true } = definition;
      const profile = structuredClone(inputs);
      try {
        batch?.signal.throwIfAborted();
        await this.service.grantAuthorization({ ...this.admin(id), grantId, ownerId: 'agent',
          intents: ['personal-workflow'], targetOrigins: [disclosurePolicy.origin],
          actionKinds: ['fill', 'select', 'click'], pageIds: [pageId], readRegions: null,
          expiresAt: new Date(Date.now() + this.config.delegationMaxAgeMs).toISOString() });
        for (const grant of before.grants.filter(value => value.ownerId === 'agent')) {
          await this.service.revokeAuthorization({ ...this.admin(id), grantId: grant.grantId });
        }
        batch?.signal.throwIfAborted();
        const assigned = await this.service.assignOwner({ ...this.admin(id), ownerId: 'agent' });
        const owner = createOwnerSession(this.service, { workspaceId: id, ...assigned }).identity;
        this.owners.set(id, owner);
        const controller = new AbortController();
        const signal = batch ? AbortSignal.any([controller.signal, batch.signal]) : controller.signal;
        const reviewBatchItem = batch ? { versionId: batch.versionId, recordId: batch.recordId,
          verifyRecord: batch.policy.verifyRecord, authorizeReadOnlyStep: batch.policy.authorizeReadOnlyStep } : null;
        signal.throwIfAborted();
        this.store.activity(id, { event: 'personal-workflow-started', template, mode, grantId });
        let workflowAttempt = null;
        const done = this.workflowStore.run({ template, mode, pageId, inputs: profile,
          accountScope, verifyAccount, verificationId, taskSourceHashes, disclosurePolicy, fieldGroups, learnRepairs: batch ? false : learnRepairs, service: this.service, owner,
          intent: 'personal-workflow', task, planner, config: this.config, store: this.store,
          projectId: id, signal, reviewBatchItem,
          verifyReview: () => verifyReview({ service: this.service, owner, pageId, inputs: profile }),
        }).then(result => {
          workflowAttempt = result.attempt;
          this.store.activity(id, { event: 'personal-workflow-finished', completed: result.completed,
            persistence: result.persistence, attempt: result.attempt, modelCalls: result.modelCalls, cacheSteps: result.cacheSteps });
          return result;
        }).catch(error => {
          workflowAttempt = error.attempt ?? workflowAttempt;
          if (!controller.signal.aborted) {
            const prior = this.store.get(id).run;
            this.store.run(id, { id: prior?.id ?? runId, status: 'needs-attention',
              detail: error.message || 'Personal workflow rejected', turns: prior?.turns ?? 0,
              usage: prior?.usage ?? [], planner: planner?.identity ?? null });
          }
          this.store.activity(id, { event: 'personal-workflow-rejected', attempt: error.attempt ?? null,
            code: error.code ?? 'workflow-attempt-failed' });
          throw error;
        }).finally(() => this.exclusive(id, async () => {
          try {
            await this.#releaseWorkflowGrant(id, grantId,
              this.owners.get(id)?.ownerGeneration === owner.ownerGeneration);
          } catch (error) {
            if (!batch) throw error;
            throw Object.assign(Error('Grant cleanup did not finish', { cause: error }),
              { code: 'batch-child-cleanup-failed', attempt: workflowAttempt });
          }
        }));
        this.active.set(id, { id: runId, done, controller });
        const release = () => { if (this.active.get(id)?.id === runId) this.active.delete(id); };
        done.then(release, release);
        return { runId, done };
      } catch (error) {
        // Setup may have installed the grant or changed ownership before rejecting.
        // Fence conservatively even if the assignment's reply was never received.
        try { await this.#releaseWorkflowGrant(id, grantId, true); }
        catch (cleanupError) {
          throw Object.assign(new AggregateError([error, cleanupError], 'Workflow setup and cleanup failed'),
            { code: 'workflow-setup-cleanup-failed' });
        }
        throw error;
      }
    });
  }
  async #releaseWorkflowGrant(id, grantId, fence) {
    const errors = [];
    try { await this.service.revokeAuthorization({ ...this.admin(id), grantId }); }
    catch (error) { errors.push(error); }
    if (fence) {
      try { await this.takeOverNow(id); }
      catch (error) { errors.push(error); }
    }
    if (errors.length) throw new AggregateError(errors, 'Personal workflow grant or ownership cleanup failed');
  }
  delegate(id, input) { return this.exclusive(id, () => this.delegateNow(id, input)); }
  async delegateNow(id, { pageIds, origins, regions = null, actionKinds, task, shareRecords = false, uploadFiles, resume = false, requiredCompletion }) {
    this.reviewBatches.assertAdmission(id);
    // An omitted contract on resume keeps the trusted prior delegation contract. Explicit null clears it.
    const priorContract = resume ? this.store.get(id).activity.findLast(event => event.event === 'delegated')?.requiredCompletion : null;
    const contract = completionContract(requiredCompletion === undefined ? priorContract ?? null : requiredCompletion);
    if (!this.planner) throw Error('Configure BLITZEN_MODEL (or FAWN_MODEL) and the planner API credential before delegating');
    if (!Array.isArray(pageIds) || !pageIds.length || !Array.isArray(origins) || !origins.length) throw Error('Select pages and exact origins');
    if (!Array.isArray(actionKinds) || !actionKinds.length || typeof task !== 'string' || !task.trim()) throw Error('Select actions and provide a bounded task');
    if (this.active.has(id)) throw Error('The prior agent has not settled; take over and wait before resuming');
    const before = await this.service.inspect(this.admin(id));
    if (before.actions.some(action => action.dispatchStatus === 'dispatched' && !action.outcome)) throw Error('Wait for dispatched actions to settle before delegating');
    // A fresh task must not inherit unknown outcomes; a resumed task inherits them and must establish each one.
    if (!resume && before.actions.some(action => action.isUncertain)) throw Error('Review unresolved actions before delegating, or resume with the handoff');
    if (resume) shareRecords = true;
    // Time has passed: before a returning agent reads anything, re-read the saved repository sources so
    // its handoff says which conclusions rest on files that changed and which still hold.
    if (resume) await this.checkSources(id);
    let handoff = resume ? handoffBrief(this.store.get(id), before) : null;
    const grantId = `delegation-${randomUUID()}`;
    const approved = await this.service.grantAuthorization({ ...this.admin(id), grantId, ownerId: 'agent', intents: ['delegated-task'],
      targetOrigins: origins, actionKinds, pageIds, readRegions: regions,
      ...(uploadFiles !== undefined ? { uploadFiles } : {}),
      expiresAt: new Date(Date.now() + this.config.delegationMaxAgeMs).toISOString() });
    // A new task must not inherit an earlier delegation's wider access.
    for (const grant of before.grants.filter(value => value.ownerId === 'agent')) await this.service.revokeAuthorization({ ...this.admin(id), grantId: grant.grantId });
    const assigned = await this.service.assignOwner({ ...this.admin(id), ownerId: 'agent' });
    const owner = createOwnerSession(this.service, { workspaceId: id, ...assigned }).identity;
    this.owners.set(id, owner);
    const controller = new AbortController(), observations = new Map();
    const initialArtifacts = new Set(Object.keys(this.store.get(id).artifacts));
    const visibleArtifacts = new Set(shareRecords ? initialArtifacts : []);
    const startSequence = this.store.journal.records.at(-1)?.seq ?? 0;
    this.store.activity(id, { event: 'delegated', task, pageIds, origins, regions, actionKinds, shareRecords, grantId, resume,
      ...(contract ? { requiredCompletion: contract } : {}),
      ...(approved.uploadFiles ? { uploadFiles: approved.uploadFiles } : {}) });
    const assertCurrent = () => { if (this.owners.get(id)?.ownerGeneration !== owner.ownerGeneration) throw Error('Agent ownership changed'); };
    // An interrupted action already declared how its completion shows on the page. Before the resuming
    // planner spends a request, the trusted service checks that same condition on the live page. Only
    // effect-present settles here: a condition that does not hold proves nothing, and the planner still
    // has to establish that outcome. Each check is recorded like a planner call, marked automatic.
    if (resume) {
      for (const action of before.actions.filter(value => value.isUncertain && pageIds.includes(value.pageId)
        && Array.isArray(value.completion?.completedWhen) && value.completion.completedWhen.length > 0)) {
        const callId = randomUUID(), input = { actionId: action.actionId, effectPresentWhen: action.completion.completedWhen };
        this.store.activity(id, { event: 'tool-requested', callId, tool: 'reconcile', input, automatic: true });
        try {
          const output = await this.service.reconcile({ ...owner, ...input, method: 'application-state', effectAbsentWhen: [] });
          this.store.activity(id, { event: 'tool-result', callId, output, automatic: true });
        } catch (error) {
          this.store.activity(id, { event: 'tool-failed', callId, error: error.message, code: error.code ?? null, recoverable: true, automatic: true });
        }
      }
      handoff = handoffBrief(this.store.get(id), await this.service.inspect(this.admin(id)));
    }
    const returnedRecords = new Set();
    const execute = async (tool, input, { callId }) => {
      assertCurrent(); controller.signal.throwIfAborted();
      // Models often name a target by its bare handle or URL; normalize rather than fail the run.
      if (typeof input.target === 'string') input = { ...input, target: /^https?:/.test(input.target) ? { url: input.target } : { handle: input.target } };
      // A single condition object is a common slip; the service requires a list.
      for (const key of ['completedWhen', 'failedWhen']) {
        const value = input.completion?.[key];
        if (value && !Array.isArray(value) && typeof value === 'object') input = { ...input, completion: { ...input.completion, [key]: [value] } };
      }
      const pageId = input.pageId ?? pageIds[0];
      if (['observe', 'act', 'capture'].includes(tool) && !pageIds.includes(pageId)) throw Error('Page exceeds this delegation');
      if (tool === 'observe') {
        const observation = await this.service.observe({ ...owner, pageId }); observations.set(pageId, observation); return plannerView(observation, pageId);
      }
      if (input.artifactId && !visibleArtifacts.has(input.artifactId)) throw Error('Source record was not shared with this task');
      if (tool === 'handoff_read') {
        if (!resume) throw Error('Resume the investigation before reading prior handoff records');
        return this.handoff(id, { cursors: input.cursors ?? {} });
      }
      if (tool === 'sources_check') return this.checkSources(id);
      if (tool === 'artifact_list') return listArtifacts(this.store.get(id), input, visibleArtifacts);
      if (tool === 'artifact_read') return readArtifact(this.store.get(id), input, visibleArtifacts);
      if (tool === 'capture') {
        // Saving a page reads it again, which supersedes the observation the planner last saw. Keep the
        // newer one as current so the next action is not refused as stale; handles and digests are still
        // checked against it, so a page that changed in between is refused there instead.
        const artifact = await this.capture(id, { ...input, pageId }, owner, observation => { if (!input.regions?.length) observations.set(pageId, observation); });
        visibleArtifacts.add(artifact.id); return artifact;
      }
      if (tool === 'repository_files') return repositoryFiles(this.store.get(id).repositoryRoot, this.config.maxRepositoryFiles);
      if (tool === 'repository_read') { const artifact = await this.readRepository(id, input); visibleArtifacts.add(artifact.id); return artifact; }
      if (tool === 'record') {
        if ((input.id && !visibleArtifacts.has(input.id)) || input.dependsOn?.some(key => !visibleArtifacts.has(key))) throw Error('Reasoning depends on records not shared with this task');
        // Code this conclusion names that sits in saved sources beyond what the agents were shown.
        const unread = input.kind === 'question' || typeof input.text !== 'string' ? null : unreadMentions(this.store.get(id), input.text);
        const excerpts = (unread?.mentions ?? []).filter(mention => mention.excerpt);
        for (const { artifactId, revision, from, to } of excerpts) this.store.activity(id, { event: 'source-shown', artifactId, revision, from, to });
        // A claim that something is absent, resting on a file whose defining part was never shown, goes
        // back to the agent with that part attached, before it is saved. At most twice per session, and
        // never twice for the same text: the agent keeps the last word.
        if (excerpts.length && claimsAbsence(input.text) && returnedRecords.size < 2 && !returnedRecords.has(input.text)) {
          returnedRecords.add(input.text);
          const shown = excerpts.map(mention => `${mention.path} at offset ${mention.offset} (${mention.term}): ${JSON.stringify(mention.excerpt)}`).join(' ');
          throw Object.assign(Error(`Not saved yet. This record says something is absent or unbounded and names code that is defined in a part of a saved source no agent had been shown. Here is that part: ${shown} `
            + 'If it changes the conclusion, correct the text and cite that source in dependsOn; read more with artifact_read if needed. If the conclusion stands, send the same record again and it will be saved.'),
            { code: 'unread-definition', details: { expected: ['record', 'artifact_read'], neverDispatched: { code: 'unread-definition' } } });
        }
        const artifact = this.record(id, input); visibleArtifacts.add(artifact.id);
        return unread ? { ...artifact, unreadMentions: unread } : artifact;
      }
      if (tool === 'reconcile') {
        const state = await this.service.inspect(this.admin(id));
        const unresolved = resume && state.actions.find(value => value.actionId === input.actionId && value.isUncertain);
        if (!unresolved) throw Error('Reconcile only names an unresolved action from the handoff');
        const reconciled = await this.service.reconcile({ ...owner, actionId: input.actionId, method: 'application-state',
          effectPresentWhen: input.effectPresentWhen ?? [], effectAbsentWhen: input.effectAbsentWhen ?? [] });
        handoff = handoffBrief(this.store.get(id), await this.service.inspect(this.admin(id)));
        return reconciled;
      }
      if (tool !== 'act') throw Error(`Unsupported product tool ${tool}`);
      if ((handoff?.unresolvedActionCount ?? handoff?.unresolvedActions.length) && input.kind !== 'navigate') {
        throw Error('Establish every unresolved action with reconcile before taking a new action');
      }
      // Opening a URL does not depend on anything the planner read from the page, so the workspace takes
      // the required observation itself. Every other action names something on the page and the planner
      // must have seen it; that proposal was never sent to the browser and can be corrected.
      let observed = observations.get(pageId);
      if (!observed && input.kind === 'navigate' && input.target?.url) observed = await this.service.observe({ ...owner, pageId });
      if (!observed) {
        throw Object.assign(Error('Observe this page before proposing an action on it'),
          { code: 'observation-required', details: { expected: ['observe'], neverDispatched: { code: 'observation-required' } } });
      }
      // Credentials are a person's to enter. The run stops for attention instead of typing into the field.
      if ((observed.elements ?? []).some(element => element.handle && element.handle === input.target?.handle && element.inputType === 'password')) {
        throw Error('Passwords are entered by a person: sign in on this page, then return the task to the agent');
      }
      const admitted = await this.service.submitAction({ ...owner, pageId, actionId: callId, authorizedIntent: 'delegated-task',
        kind: input.kind, target: input.target, params: input.params, completion: input.completion, effect: input.effect,
        observationVersion: observed.observationVersion });
      observations.delete(pageId); return navigationNotice(input, await admitted.result);
    };
    const run = startAgent({ projectId: id, store: this.store, planner: this.planner, config: this.config,
      execute, signal: controller.signal, assertCurrent, requiredCompletion: contract,
      completionRecords: () => Object.fromEntries(Object.entries(this.store.get(id).artifacts).filter(([key]) => visibleArtifacts.has(key))),
      recoverToolError: error => error.details?.neverDispatched?.code === error.code && CORRECTABLE_PROPOSALS.has(error.code),
      reviewFinish: () => unfinishedRecords(this.store.get(id)),
      verifyCompletion: async () => {
        const state = await this.service.inspect(this.admin(id));
        const outstanding = state.actions.filter(action => action.isUncertain || action.dispatchStatus === 'queued'
          || (action.dispatchStatus === 'dispatched' && !action.outcome));
        if (outstanding.length) return { completed: false, detail: `${outstanding.length} unresolved browser action(s) need review; the task is not complete.` };
        const stale = Object.values(this.store.get(id).artifacts).filter(value => value.kind !== 'evidence' && value.status === 'needs-review').length;
        return { completed: stale === 0,
          detail: stale ? `${stale} saved record(s) still need rechecking against changed sources; the task is not complete.`
            : 'Task finished with no unresolved browser actions.' };
      },
      context: () => investigationContext(this.store.get(id), {
        task, permissions: { pageIds, origins, regions, actionKinds,
          ...(approved.uploadFiles ? { uploadFiles: approved.uploadFiles } : {}) }, initialArtifacts, startSequence, shareRecords, visibleArtifacts, handoff
      }) });
    const settled = run.done.then(async () => {
      await this.exclusive(id, async () => {
        await this.service.revokeAuthorization({ ...this.admin(id), grantId });
        if (this.owners.get(id)?.ownerGeneration === owner.ownerGeneration) await this.takeOverNow(id);
      });
    });
    this.active.set(id, { ...run, done: settled, controller });
    const release = () => { if (this.active.get(id)?.id === run.id) this.active.delete(id); };
    settled.then(release, release);
    return { runId: run.id };
  }
  revoke(id, { grantId }) {
    return this.exclusive(id, async () => {
      await this.service.revokeAuthorization({ ...this.admin(id), grantId });
      const pending = this.batchRuns.get(id);
      if (pending) {
        await this.reviewBatches.cancel(id);
        pending.controller.abort(Object.assign(Error('Workflow grant revoked'), { code: 'batch-cancelled' }));
      }
      return this.takeOverNow(id);
    });
  }
  async check(id, { actionId }) {
    const owner = await this.takeOver(id);
    const action = await this.service.action({ ...this.owner(id), actionId });
    await this.humanPage(id, action.pageId);
    if (!action.isUncertain) return { action, boundary: owner.boundary };
    const conditions = action.completion?.completedWhen ?? [];
    if (!conditions.length) return this.service.reconcile({ ...this.owner(id), actionId, method: 'human-review' });
    return this.service.reconcile({ ...this.owner(id), actionId, method: 'application-state', effectPresentWhen: conditions });
  }
  async status(id = null) {
    const projects = [...this.store.projects.keys()].map(key => this.store.get(key));
    const exists = id && this.store.projects.has(id);
    return { projects, missingProjectId: id && !exists ? id : null, selected: exists ? await (async () => { const workspace = await this.service.inspect(this.admin(id)), investigation = this.store.get(id);
        return { investigation, workspace, handoff: handoffBrief(investigation, workspace) }; })() : null,
      workflows: this.#workflowSummaries(), planner: this.planner?.identity ?? null, pollMs: this.config.pollMs };
  }
  /** With `release` (the service close), a browser that did not close cleanly is recorded for whoever resumes. */
  async close({ release = null } = {}) {
    const ids = new Set([...this.active.keys(), ...(this.batchRuns?.keys() ?? [])]);
    const settled = Promise.allSettled([...(this.batchRuns?.values() ?? []), ...this.active.values()].map(value => value.done));
    const errors = [];
    for (const id of ids) {
      try { await this.takeOver(id); }
      catch (error) { errors.push(error); }
    }
    for (const result of await settled) if (result.status === 'rejected') errors.push(result.reason);
    try {
      const { releases = [] } = release ? await release() ?? {} : {};
      for (const value of releases) {
        if (!this.store.projects.has(value.workspaceId)) continue;
        // An ordinary release is recorded only to clear an earlier one that was not.
        const last = this.store.get(value.workspaceId).activity.findLast(event => event.event === 'browser-released');
        const earlier = last ? (last.release ?? (last.forced ? 'forced' : 'graceful')) !== 'graceful' : false;
        if (value.release !== 'graceful' || earlier) this.store.activity(value.workspaceId, { event: 'browser-released', release: value.release,
          forced: value.release === 'forced', ...(value.survivors ? { survivors: value.survivors } : {}), ...(value.errors ? { errors: value.errors } : {}) });
      }
    } catch (error) { errors.push(error); }
    finally { this.store.close(); }
    if (errors.length) throw new AggregateError(errors, 'Workspace shutdown reported errors');
  }
}
