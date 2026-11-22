// Fawn workspace — admission and dispatch-time checks
//
// The same checks run when intent is admitted and again immediately before dispatch, so every
// workflow adapter receives identical rejections for stale or unauthorized commands.

import { generationForCredential, credentialMatches } from './authority.js';
import { validateConditions } from './conditions.js';
import { REJECTION_CODES, workspaceError } from './errors.js';
import { ACTION_STATUS, OUTCOMES, latestReconciliation } from './state.js';
import { validateUploadParams } from './uploads.js';

const URL_TARGET_KINDS = Object.freeze(['navigate']);
const VALUE_KINDS = Object.freeze(['fill', 'select']);
const COMPLETION_REQUIRED_KINDS = Object.freeze(['submit']);
const FORM_CONTROL_KINDS = Object.freeze(['submit']);
const LINK_FOLLOWING_KINDS = Object.freeze(['click', 'download']);
const PAGE_SCOPE = Object.freeze({ kind: 'page' });
const REGIONS_SCOPE = 'regions';

function reject(code, message, details) {
  throw workspaceError(code, message, details);
}

function requireString(value, path) {
  if (typeof value !== 'string' || value.length === 0) {
    reject(REJECTION_CODES.INVALID_COMMAND, `${path}: expected non-empty string`, {
      path,
      expected: 'non-empty string',
      received: value,
    });
  }
}

function originOf(url, path) {
  try {
    return new URL(url).origin;
  } catch {
    return reject(REJECTION_CODES.INVALID_COMMAND, `${path}: expected absolute URL`, { path, received: url });
  }
}

/**
 * Validate a list of region selectors against config.observation.maxRegions. An empty regions
 * scope means the action depends on no page content beyond the cited URL and target identity.
 */
function validateRegionSelectors(selectors, config, path, { allowEmpty = false } = {}) {
  if (!Array.isArray(selectors) || (selectors.length === 0 && !allowEmpty)
    || selectors.some((selector) => typeof selector !== 'string' || selector.length === 0)) {
    reject(REJECTION_CODES.INVALID_COMMAND, `${path}: expected array of selectors`, { path, received: selectors });
  }
  if (selectors.length > config.observation.maxRegions || new Set(selectors).size !== selectors.length) {
    reject(REJECTION_CODES.INVALID_COMMAND, `${path}: expected at most ${config.observation.maxRegions} distinct selectors`, {
      path,
      received: selectors,
    });
  }
}

function validatePredicateVersions(list, path) {
  if (!Array.isArray(list) || list.length === 0 || list.length > 32) {
    reject(REJECTION_CODES.INVALID_COMMAND, `${path}: expected 1..32 predicate version bindings`, { path, received: list });
  }
  for (let i = 0; i < list.length; i += 1) {
    const item = list[i];
    if (!item || typeof item !== 'object') {
      reject(REJECTION_CODES.INVALID_COMMAND, `${path}[${i}]: expected object`, { path: `${path}[${i}]` });
    }
    if (item.account !== undefined) requireString(item.account, `${path}[${i}].account`);
    requireString(item.record, `${path}[${i}].record`);
    requireString(item.predicate, `${path}[${i}].predicate`);
    const validVersion = (typeof item.version === 'string' && item.version.length > 0) || Number.isInteger(item.version);
    if (!validVersion) {
      reject(REJECTION_CODES.INVALID_COMMAND, `${path}[${i}].version: expected non-empty string or integer`, {
        path: `${path}[${i}].version`,
        received: item.version,
      });
    }
  }
}

function validateObservationScope(scope, config) {
  if (scope === undefined) return;
  if (!config.observationScopes.includes(scope?.kind)) {
    reject(REJECTION_CODES.INVALID_COMMAND, 'observationScope.kind', {
      path: 'observationScope.kind',
      expected: config.observationScopes,
      received: scope?.kind,
    });
  }
  if (scope.kind === REGIONS_SCOPE) {
    validateRegionSelectors(scope.selectors, config, 'observationScope.selectors', { allowEmpty: true });
  }
}

function authenticateAdmin(workspace, adminCredential) {
  if (!credentialMatches(adminCredential, workspace.adminCredentialHash)) {
    reject(REJECTION_CODES.UNAUTHENTICATED, 'admin credential rejected', { workspaceId: workspace.workspaceId });
  }
}

/**
 * Authenticate an owner and require the claimed generation to be the current one.
 */
function authenticateOwner(workspace, { ownerCredential, ownerId, ownerGeneration }) {
  if (workspace.ownerGeneration === 0) {
    reject(REJECTION_CODES.NO_OWNER, 'workspace has no owner', { workspaceId: workspace.workspaceId });
  }
  const issuedGeneration = generationForCredential(ownerCredential, workspace.ownerCredentialHashes);
  if (issuedGeneration === null || issuedGeneration !== ownerGeneration) {
    reject(REJECTION_CODES.UNAUTHENTICATED, 'owner credential rejected', {
      workspaceId: workspace.workspaceId,
      claimedGeneration: ownerGeneration,
    });
  }
  if (ownerGeneration !== workspace.ownerGeneration || ownerId !== workspace.ownerId) {
    reject(REJECTION_CODES.STALE_OWNER_GENERATION, 'owner generation is no longer current', {
      workspaceId: workspace.workspaceId,
      claimed: { ownerId, ownerGeneration },
      current: { ownerId: workspace.ownerId, ownerGeneration: workspace.ownerGeneration },
    });
  }
}

function validateActionShape(command, config) {
  requireString(command.actionId, 'actionId');
  requireString(command.authorizedIntent, 'authorizedIntent');
  if (!config.actionKinds.includes(command.kind)) {
    reject(REJECTION_CODES.UNSUPPORTED_ACTION_KIND, `kind ${command.kind}`, {
      path: 'kind',
      expected: config.actionKinds,
      received: command.kind,
    });
  }
  if (URL_TARGET_KINDS.includes(command.kind)) {
    requireString(command.target?.url, 'target.url');
  } else if (command.target?.handle !== undefined) {
    requireString(command.target.handle, 'target.handle');
  } else {
    requireString(command.target?.selector, 'target.selector');
    requireString(command.target?.digest, 'target.digest');
  }
  if (VALUE_KINDS.includes(command.kind)) requireString(command.params?.value, 'params.value');
  if (command.kind === 'upload') {
    validateUploadParams(command.params, config);
    if (command.effect?.external !== true) reject(REJECTION_CODES.INVALID_COMMAND, 'Upload discloses file bytes; declare an external effect and effectKey');
  }
  if (!Number.isInteger(command.observationVersion)) {
    reject(REJECTION_CODES.INVALID_COMMAND, 'observationVersion: expected integer', {
      path: 'observationVersion',
      received: command.observationVersion,
    });
  }
  validateObservationScope(command.observationScope, config);
  validateConditions(command.preconditions ?? [], config.conditionKinds, 'preconditions');
  const effect = command.effect ?? { external: false };
  if (typeof effect.external !== 'boolean') {
    reject(REJECTION_CODES.INVALID_COMMAND, 'effect.external: expected boolean', { path: 'effect.external' });
  }
  const completedWhen = command.completion?.completedWhen ?? [];
  validateConditions(completedWhen, config.conditionKinds, 'completion.completedWhen');
  validateConditions(command.completion?.failedWhen ?? [], config.conditionKinds, 'completion.failedWhen');
  const needsCompletion = effect.external || COMPLETION_REQUIRED_KINDS.includes(command.kind);
  if (needsCompletion && completedWhen.length === 0) {
    reject(REJECTION_CODES.INVALID_COMMAND, 'completion.completedWhen: required for external effects', {
      path: 'completion.completedWhen',
    });
  }
  if (effect.external) requireString(effect.effectKey, 'effect.effectKey');
  if (effect.externalIdempotencyKey !== undefined) {
    requireString(effect.externalIdempotencyKey, 'effect.externalIdempotencyKey');
    if (effect.externalIdempotencyKey === command.actionId) {
      reject(REJECTION_CODES.INVALID_IDEMPOTENCY_KEY, 'a local action id is not an external idempotency key', {
        path: 'effect.externalIdempotencyKey',
      });
    }
  }
  if (command.writeCondition?.predicateVersions !== undefined) {
    validatePredicateVersions(command.writeCondition.predicateVersions, 'writeCondition.predicateVersions');
  }
}

/**
 * Every origin an action touches: the navigation URL, or the cited page plus the destination of
 * a followed link or submitted form.
 */
function touchedOrigins(command, cited) {
  if (URL_TARGET_KINDS.includes(command.kind)) return [originOf(command.target.url, 'target.url')];
  if (!cited) return [null];
  const origins = [originOf(cited.url, 'observation.url')];
  const selector = command.target?.selector;
  const formAction = cited.targetFormActions?.[selector];
  if (command.kind === 'submit' && formAction) origins.push(originOf(formAction, 'target.formAction'));
  if (LINK_FOLLOWING_KINDS.includes(command.kind)) {
    // Protocol 1 observations did not record link destinations; they cannot authorize one.
    if (!cited.targetNavigations) return [...origins, null];
    const destination = cited.targetNavigations[selector];
    if (destination) origins.push(originOf(destination, 'target.href'));
  }
  return origins;
}

/**
 * Require at least one current, unexpired grant for the owner and intent. Checked before the
 * observation, so a revoked or expired grant is reported as such whatever the page did.
 */
function grantsForIntent(workspace, command, nowMs) {
  const forIntent = [...workspace.grants.values()].filter(
    (grant) => grant.ownerId === command.ownerId
      && (grant.expiresAt === null || Date.parse(grant.expiresAt) > nowMs)
      && grant.intents.includes(command.authorizedIntent),
  );
  if (forIntent.length === 0) {
    reject(REJECTION_CODES.UNAUTHORIZED_INTENT, `intent ${command.authorizedIntent}`, {
      ownerId: command.ownerId,
      authorizedIntent: command.authorizedIntent,
    });
  }
  return forIntent;
}

/**
 * Require one of the intent's grants to cover the action kind and every target origin.
 */
function authorize(forIntent, command, cited) {
  const origins = touchedOrigins(command, cited);
  const grant = forIntent.find((candidate) => candidate.actionKinds.includes(command.kind)
    && (!command.grantId || command.grantId === candidate.grantId)
    && (!candidate.pageIds || candidate.pageIds.includes(command.pageId ?? 'main'))
    && (command.kind !== 'upload' || command.params.fileIds.every(id => candidate.uploadFiles?.some(file => file.fileId === id)))
    && origins.every((origin) => origin !== null && candidate.targetOrigins.includes(origin)));
  if (!grant) {
    reject(REJECTION_CODES.UNAUTHORIZED_TARGET, `${command.kind} on ${origins.join(', ')}`, {
      kind: command.kind,
      origins,
    });
  }
  return grant.grantId;
}

/**
 * A regions-scoped action stays current while its URL and every scoped region are unchanged
 * since the cited observation. Later recorded observations are compared at admission; the live
 * page is compared at dispatch.
 */
function checkRegions(workspace, cited, scope, live) {
  const missing = scope.selectors.filter((selector) => !cited.regions?.[selector]);
  if (missing.length > 0) {
    reject(REJECTION_CODES.INVALID_COMMAND, `observation ${cited.observationVersion} has no unique region ${missing.join(', ')}`, {
      path: 'observationScope.selectors',
      missing,
    });
  }
  const changes = [];
  const compare = (url, regions, source) => {
    if (url !== cited.url) changes.push({ source, url });
    for (const selector of scope.selectors) {
      if (regions && selector in regions && regions[selector] !== cited.regions[selector]) {
        changes.push({ source, selector });
      }
    }
  };
  for (const [version, observation] of workspace.observations) {
    if (version > cited.observationVersion) compare(observation.url, observation.regions, `observation ${version}`);
  }
  if (live) {
    compare(live.url, live.regions, 'dispatch');
    const unread = scope.selectors.filter((selector) => !(selector in (live.regions ?? {})));
    if (unread.length > 0) changes.push({ source: 'dispatch', unread });
  }
  if (changes.length > 0) {
    reject(REJECTION_CODES.STALE_OBSERVATION, `scoped regions of observation ${cited.observationVersion} changed`, {
      observationVersion: cited.observationVersion,
      scope: REGIONS_SCOPE,
      changes,
    });
  }
}

/**
 * Require the cited observation to be current under the current owner generation and unexpired,
 * and its element target to appear in it. Page scope requires the latest version; regions scope
 * requires the scoped regions to be unchanged. Returns the cited observation.
 */
function checkObservation(workspace, command, nowMs, live = null) {
  const version = command.observationVersion;
  if (!workspace.observation || version > workspace.observationVersion || version < 1) {
    reject(REJECTION_CODES.UNKNOWN_OBSERVATION, `observation ${version}`, { observationVersion: version });
  }
  const cited = workspace.observations.get(version);
  if (!cited || cited.ownerGeneration !== workspace.ownerGeneration) {
    reject(REJECTION_CODES.STALE_OBSERVATION, `observation ${version} is from an earlier owner generation`, {
      observationVersion: version,
      currentVersion: workspace.observationVersion,
    });
  }
  if (Date.parse(cited.expiresAt) <= nowMs) {
    reject(REJECTION_CODES.EXPIRED_OBSERVATION, `observation ${version} expired`, { expiresAt: cited.expiresAt });
  }
  const scope = command.observationScope ?? PAGE_SCOPE;
  if (scope.kind === REGIONS_SCOPE) {
    checkRegions(workspace, cited, scope, live);
  } else if (version !== workspace.observationVersion) {
    reject(REJECTION_CODES.STALE_OBSERVATION, `observation ${version} is not current`, {
      observationVersion: version,
      currentVersion: workspace.observationVersion,
    });
  }
  if (!URL_TARGET_KINDS.includes(command.kind)) {
    if (cited.targetFormActions?.[command.target.selector] && !FORM_CONTROL_KINDS.includes(command.kind)) {
      reject(REJECTION_CODES.INVALID_COMMAND, `${command.target.selector} submits a form; use kind submit`, {
        selector: command.target.selector,
        expected: FORM_CONTROL_KINDS,
        received: command.kind,
      });
    }
    // Every admitted action is journaled with its value, so a password is never accepted as one,
    // from any owner. A person types it directly into the browser.
    if (command.kind === 'fill' && cited.passwordTargets?.includes(command.target.selector)) {
      reject(REJECTION_CODES.INVALID_COMMAND, `${command.target.selector} is a password field; credentials are typed directly in the browser, never sent through the workspace`, {
        selector: command.target.selector,
      });
    }
    const digest = cited.targetDigests?.[command.target.selector];
    if (!digest) {
      reject(REJECTION_CODES.UNKNOWN_TARGET, `target ${command.target.selector} not in observation`, {
        selector: command.target.selector,
      });
    }
    if (digest !== command.target.digest) {
      reject(REJECTION_CODES.TARGET_CHANGED, `target ${command.target.selector} digest differs`, {
        selector: command.target.selector,
      });
    }
  }
  return cited;
}

function priorsForEffect(workspace, effectKey, excludeActionId) {
  return [...workspace.actions.values()].filter((action) => action.request.effect?.effectKey === effectKey
    && action.request.actionId !== excludeActionId);
}

function effectDisposition(action) {
  const reconciliation = latestReconciliation(action);
  if (action.status === ACTION_STATUS.QUEUED || (action.status === ACTION_STATUS.DISPATCHED && !action.outcome)) {
    return { blocking: REJECTION_CODES.EFFECT_UNRESOLVED };
  }
  if (action.status === ACTION_STATUS.NEVER_DISPATCHED) return { resubmittable: true };
  if (action.outcome.outcome === OUTCOMES.COMPLETED) return { blocking: REJECTION_CODES.EFFECT_ALREADY_COMPLETED };
  if (action.outcome.outcome === OUTCOMES.FAILED) return { resubmittable: true };
  if (reconciliation?.result === 'effect-present') return { blocking: REJECTION_CODES.EFFECT_ALREADY_COMPLETED };
  if (reconciliation?.permitsResubmission) {
    return { resubmittable: true, requiredIdempotencyKey: reconciliation.requiredIdempotencyKey ?? null };
  }
  return { blocking: REJECTION_CODES.EFFECT_UNRESOLVED };
}

/**
 * Missing completion never authorizes another submission: a command for an external effect
 * that already has an uncertain, in-flight or completed attempt is refused, and any permitted
 * resubmission must name the prior attempt explicitly.
 */
function checkEffect(workspace, command) {
  const effectKey = command.effect?.effectKey;
  if (!effectKey) {
    if (command.resubmissionOf) {
      reject(REJECTION_CODES.RESUBMISSION_NOT_PERMITTED, 'resubmission requires an effect key', {
        resubmissionOf: command.resubmissionOf,
      });
    }
    return;
  }
  const priors = priorsForEffect(workspace, effectKey, command.actionId);
  for (const prior of priors) {
    const disposition = effectDisposition(prior);
    if (disposition.blocking) {
      reject(disposition.blocking, `effect ${effectKey} has attempt ${prior.request.actionId}`, {
        effectKey,
        priorActionId: prior.request.actionId,
      });
    }
  }
  if (priors.length === 0) {
    if (command.resubmissionOf) {
      reject(REJECTION_CODES.RESUBMISSION_NOT_PERMITTED, 'no prior attempt for this effect', {
        resubmissionOf: command.resubmissionOf,
      });
    }
    return;
  }
  const latest = priors.reduce((a, b) => (a.admittedSeq > b.admittedSeq ? a : b));
  if (command.resubmissionOf !== latest.request.actionId) {
    reject(REJECTION_CODES.RESUBMISSION_NOT_PERMITTED, `name prior attempt ${latest.request.actionId}`, {
      effectKey,
      priorActionId: latest.request.actionId,
      received: command.resubmissionOf ?? null,
    });
  }
  const required = effectDisposition(latest).requiredIdempotencyKey;
  if (required && command.effect.externalIdempotencyKey !== required) {
    reject(REJECTION_CODES.RESUBMISSION_NOT_PERMITTED, 'resubmission must reuse the external idempotency key', {
      effectKey,
    });
  }
}

/**
 * A handle names an element in the cited observation; it resolves to that observation's
 * selector and digest, so dispatch checks the same target identity as an explicit target.
 */
function resolveHandle(workspace, command) {
  if (URL_TARGET_KINDS.includes(command.kind) || command.target?.handle === undefined) return command;
  const cited = workspace.observations.get(command.observationVersion);
  const selector = cited?.handles?.[command.target.handle];
  if (!cited) return command;
  if (!selector) {
    reject(REJECTION_CODES.UNKNOWN_TARGET, `handle ${command.target.handle} not in observation ${command.observationVersion}`, {
      handle: command.target.handle,
    });
  }
  return { ...command, target: { handle: command.target.handle, selector, digest: cited.targetDigests[selector] } };
}

/**
 * Admission: shape, owner authority, authorization, observation binding and effect safety.
 * Returns the command with any handle target resolved.
 */
function checkAdmission(workspace, submitted, config, nowMs) {
  validateActionShape(submitted, config);
  authenticateOwner(workspace, submitted);
  if (workspace.actions.has(submitted.actionId)) {
    reject(REJECTION_CODES.DUPLICATE_ACTION_ID, submitted.actionId, { actionId: submitted.actionId });
  }
  const forIntent = grantsForIntent(workspace, submitted, nowMs);
  const command = resolveHandle(workspace, submitted);
  const cited = checkObservation(workspace, command, nowMs);
  const grantId = authorize(forIntent, command, cited);
  checkEffect(workspace, command);
  return { grantId, command };
}

/**
 * Dispatch-time authority: generation, owner, observation currency and grant must still hold for
 * the admitted request. `live` is the dispatch-time page read (URL and scoped region digests).
 */
function checkDispatchAuthority(workspace, request, nowMs, live = null) {
  if (request.ownerGeneration !== workspace.ownerGeneration || request.ownerId !== workspace.ownerId) {
    reject(REJECTION_CODES.STALE_OWNER_GENERATION, 'owner generation advanced before dispatch', {
      admittedGeneration: request.ownerGeneration,
      currentGeneration: workspace.ownerGeneration,
    });
  }
  const forIntent = grantsForIntent(workspace, request, nowMs);
  const cited = checkObservation(workspace, request, nowMs, live);
  authorize(forIntent, request, cited);
}

export {
  REGIONS_SCOPE,
  authenticateAdmin,
  authenticateOwner,
  checkAdmission,
  checkDispatchAuthority,
  validateRegionSelectors,
};
