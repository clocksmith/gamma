// Fawn workspace — durable state projection
//
// Pure reduction of journal records into workspace authority and action state. Replay of the
// same journal always yields the same state; nothing here touches the browser or the disk.

const RECORD_TYPES = Object.freeze({
  SERVICE_RESTORED: 'service-restored',
  WORKSPACE_CREATED: 'workspace-created',
  PAGE_REGISTERED: 'page-registered',
  AUTHORIZATION_GRANTED: 'authorization-granted',
  AUTHORIZATION_REVOKED: 'authorization-revoked',
  OWNERSHIP_ADVANCED: 'ownership-advanced',
  OBSERVATION_RECORDED: 'observation-recorded',
  COMMAND_REJECTED: 'command-rejected',
  ACTION_ADMITTED: 'action-admitted',
  ACTION_NOT_DISPATCHED: 'action-not-dispatched',
  ACTION_DISPATCH_STARTED: 'action-dispatch-started',
  ACTION_OUTCOME: 'action-outcome',
  ACTION_ACKNOWLEDGED: 'action-acknowledged',
  ACTION_RECONCILED: 'action-reconciled',
});

const ACTION_STATUS = Object.freeze({
  QUEUED: 'queued',
  NEVER_DISPATCHED: 'never-dispatched',
  DISPATCHED: 'dispatched',
});

const OUTCOMES = Object.freeze({
  COMPLETED: 'completed',
  FAILED: 'failed',
  UNKNOWN: 'unknown',
});

function createState() {
  return { workspaces: new Map() };
}

function requireWorkspace(state, workspaceId, record) {
  const workspace = state.workspaces.get(workspaceId);
  if (!workspace) throw new Error(`journal seq ${record.seq}: unknown workspace ${workspaceId}`);
  return workspace;
}

function requireAction(workspace, actionId, record) {
  const action = workspace.actions.get(actionId);
  if (!action) throw new Error(`journal seq ${record.seq}: unknown action ${actionId}`);
  return action;
}

const REDUCERS = Object.freeze({
  [RECORD_TYPES.SERVICE_RESTORED]: () => {},
  [RECORD_TYPES.COMMAND_REJECTED]: () => {},
  [RECORD_TYPES.WORKSPACE_CREATED]: (state, body) => {
    state.workspaces.set(body.workspaceId, {
      workspaceId: body.workspaceId,
      scopedReads: body.scopedReads === true,
      pages: new Map([['main', { pageId: 'main', url: 'about:blank', closed: false }]]),
      pageObservations: new Map(),
      adminCredentialHash: body.adminCredentialHash,
      ownerGeneration: 0,
      ownerId: null,
      ownerCredentialHashes: new Map(),
      grants: new Map(),
      observationVersion: 0,
      observation: null,
      observations: new Map(),
      actions: new Map(),
    });
  },
  [RECORD_TYPES.PAGE_REGISTERED]: (state, body, record) => {
    const workspace = requireWorkspace(state, body.workspaceId, record);
    workspace.pages.set(body.pageId, { ...body });
    if (body.closed) workspace.pageObservations.delete(body.pageId);
  },
  [RECORD_TYPES.AUTHORIZATION_GRANTED]: (state, body, record) => {
    const workspace = requireWorkspace(state, body.workspaceId, record);
    workspace.grants.set(body.grantId, { ...body.grant, grantId: body.grantId });
  },
  [RECORD_TYPES.AUTHORIZATION_REVOKED]: (state, body, record) => {
    requireWorkspace(state, body.workspaceId, record).grants.delete(body.grantId);
  },
  [RECORD_TYPES.OWNERSHIP_ADVANCED]: (state, body, record) => {
    const workspace = requireWorkspace(state, body.workspaceId, record);
    if (body.ownerGeneration !== workspace.ownerGeneration + 1) {
      throw new Error(`journal seq ${record.seq}: owner generation must advance by one`);
    }
    workspace.ownerGeneration = body.ownerGeneration;
    workspace.ownerId = body.ownerId;
    workspace.ownerCredentialHashes.set(body.ownerGeneration, body.ownerCredentialHash);
    // Observations from earlier generations can never be cited again.
    workspace.observations.clear();
    workspace.pageObservations.clear();
  },
  [RECORD_TYPES.OBSERVATION_RECORDED]: (state, body, record) => {
    const workspace = requireWorkspace(state, body.workspaceId, record);
    if (body.observationVersion !== workspace.observationVersion + 1) {
      throw new Error(`journal seq ${record.seq}: observation version must advance by one`);
    }
    workspace.observationVersion = body.observationVersion;
    workspace.observation = { ...body, regions: body.regions ?? {} };
    workspace.observations.set(body.observationVersion, workspace.observation);
    workspace.pageObservations.set(body.pageId ?? 'main', workspace.observation);
  },
  [RECORD_TYPES.ACTION_ADMITTED]: (state, body, record) => {
    const workspace = requireWorkspace(state, body.workspaceId, record);
    workspace.actions.set(body.actionId, {
      request: body,
      status: ACTION_STATUS.QUEUED,
      admittedSeq: record.seq,
      notDispatched: null,
      dispatch: null,
      outcome: null,
      reconciliations: [],
      acknowledgedGeneration: null,
    });
  },
  [RECORD_TYPES.ACTION_NOT_DISPATCHED]: (state, body, record) => {
    const action = requireAction(requireWorkspace(state, body.workspaceId, record), body.actionId, record);
    if (action.status !== ACTION_STATUS.QUEUED) {
      throw new Error(`journal seq ${record.seq}: only queued actions can end undispatched`);
    }
    action.status = ACTION_STATUS.NEVER_DISPATCHED;
    action.notDispatched = { stage: body.stage, code: body.code, detail: body.detail, seq: record.seq };
  },
  [RECORD_TYPES.ACTION_DISPATCH_STARTED]: (state, body, record) => {
    const action = requireAction(requireWorkspace(state, body.workspaceId, record), body.actionId, record);
    if (action.status !== ACTION_STATUS.QUEUED) {
      throw new Error(`journal seq ${record.seq}: dispatch requires a queued action`);
    }
    action.status = ACTION_STATUS.DISPATCHED;
    action.dispatch = { ...body, seq: record.seq };
  },
  [RECORD_TYPES.ACTION_OUTCOME]: (state, body, record) => {
    const action = requireAction(requireWorkspace(state, body.workspaceId, record), body.actionId, record);
    if (action.status !== ACTION_STATUS.DISPATCHED) {
      throw new Error(`journal seq ${record.seq}: outcome requires a dispatched action`);
    }
    if (action.outcome) {
      throw new Error(`journal seq ${record.seq}: an outcome is recorded once; reconciliation is separate`);
    }
    action.outcome = { ...body, seq: record.seq };
  },
  [RECORD_TYPES.ACTION_ACKNOWLEDGED]: (state, body, record) => {
    const action = requireAction(requireWorkspace(state, body.workspaceId, record), body.actionId, record);
    action.acknowledgedGeneration = body.ownerGeneration;
  },
  [RECORD_TYPES.ACTION_RECONCILED]: (state, body, record) => {
    const action = requireAction(requireWorkspace(state, body.workspaceId, record), body.actionId, record);
    action.reconciliations.push({ ...body, seq: record.seq });
  },
});

/**
 * Apply one verified journal record.
 * @param {ReturnType<typeof createState>} state
 * @param {{seq: number, type: string, body: object}} record
 */
function applyRecord(state, record) {
  const reducer = REDUCERS[record.type];
  if (!reducer) throw new Error(`journal seq ${record.seq}: unknown record type ${record.type}`);
  reducer(state, record.body, record);
  return state;
}

function replay(records) {
  return records.reduce(applyRecord, createState());
}

function latestReconciliation(action) {
  return action.reconciliations.at(-1) ?? null;
}

/**
 * Plain-data view of an action for owners: dispatch status, outcome and uncertainty kept apart.
 */
function describeAction(action) {
  const reconciliation = latestReconciliation(action);
  const outcome = action.outcome?.outcome ?? null;
  return {
    actionId: action.request.actionId,
    pageId: action.request.pageId ?? 'main',
    target: action.request.target,
    completion: action.request.completion ?? null,
    kind: action.request.kind,
    authorizedIntent: action.request.authorizedIntent,
    ownerId: action.request.ownerId,
    ownerGeneration: action.request.ownerGeneration,
    effectKey: action.request.effect?.effectKey ?? null,
    dispatchStatus: action.status,
    neverDispatched: action.notDispatched,
    outcome,
    outcomeBasis: action.outcome?.basis ?? null,
    evidence: action.outcome?.evidence ?? null,
    postObservationVersion: action.outcome?.postObservationVersion ?? null,
    isUncertain: outcome === OUTCOMES.UNKNOWN && !reconciliation?.resolvesUncertainty,
    reconciliation,
    acknowledgedGeneration: action.acknowledgedGeneration,
  };
}

export {
  ACTION_STATUS,
  OUTCOMES,
  RECORD_TYPES,
  applyRecord,
  createState,
  describeAction,
  latestReconciliation,
  replay,
};
