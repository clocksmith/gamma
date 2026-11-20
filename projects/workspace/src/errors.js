// Fawn workspace — rejection taxonomy
//
// Every refusal carries a stable code so all workflow adapters observe identical rejections.

const REJECTION_CODES = Object.freeze({
  AUTHORITY_UNAVAILABLE: 'authority-unavailable',
  UNKNOWN_WORKSPACE: 'unknown-workspace',
  DUPLICATE_WORKSPACE: 'duplicate-workspace',
  UNAUTHENTICATED: 'unauthenticated',
  STALE_OWNER_GENERATION: 'stale-owner-generation',
  NO_OWNER: 'no-owner',
  DUPLICATE_ACTION_ID: 'duplicate-action-id',
  UNKNOWN_ACTION: 'unknown-action',
  UNSUPPORTED_ACTION_KIND: 'unsupported-action-kind',
  UNAUTHORIZED_INTENT: 'unauthorized-intent',
  UNAUTHORIZED_TARGET: 'unauthorized-target',
  UNKNOWN_OBSERVATION: 'unknown-observation',
  STALE_OBSERVATION: 'stale-observation',
  EXPIRED_OBSERVATION: 'expired-observation',
  UNKNOWN_TARGET: 'unknown-target',
  TARGET_CHANGED: 'target-changed',
  UNSUPPORTED_CONDITION: 'unsupported-condition',
  PRECONDITION_UNESTABLISHED: 'precondition-unestablished',
  EFFECT_UNRESOLVED: 'effect-unresolved',
  EFFECT_ALREADY_COMPLETED: 'effect-already-completed',
  RESUBMISSION_NOT_PERMITTED: 'resubmission-not-permitted',
  INVALID_IDEMPOTENCY_KEY: 'invalid-idempotency-key',
  UNSUPPORTED_RECONCILIATION: 'unsupported-reconciliation',
  RECONCILIATION_NOT_APPLICABLE: 'reconciliation-not-applicable',
  INVALID_COMMAND: 'invalid-command',
  JOURNAL_LOCKED: 'journal-locked',
  JOURNAL_CORRUPT: 'journal-corrupt',
  INVALID_CONFIG: 'invalid-config',
});

/**
 * Build a rejection with stable machine-readable fields.
 * @param {string} code one of REJECTION_CODES
 * @param {string} message
 * @param {object} [details]
 */
function workspaceError(code, message, details = {}) {
  const error = new Error(`${code}: ${message}`);
  error.code = code;
  error.details = details;
  return error;
}

function isWorkspaceError(error) {
  return error instanceof Error && Object.values(REJECTION_CODES).includes(error.code);
}

export { REJECTION_CODES, workspaceError, isWorkspaceError };
