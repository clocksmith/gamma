// Fawn workspace qualification — plain summaries shared by the runner and the validator.
//
// The runner summarizes what callers saw; the validator summarizes the same actions from the
// journal it replays. Both use these shapes so expectations compare one form.

function summarizeAction(action) {
  if (!action) return null;
  return {
    dispatchStatus: action.dispatchStatus,
    outcome: action.outcome,
    outcomeBasis: action.outcomeBasis,
    isUncertain: action.isUncertain,
    neverDispatchedCode: action.neverDispatched?.code ?? null,
    neverDispatchedStage: action.neverDispatched?.stage ?? null,
    reconciliationResult: action.reconciliation?.result ?? null,
    acknowledged: action.acknowledgedGeneration !== null,
    ownerGeneration: action.ownerGeneration,
  };
}

const WORKFLOW_SUMMARIES = Object.freeze({
  research: (result) => ({
    findingTitles: result.findings.map((finding) => finding.title),
    skipped: result.skipped.length,
  }),
  form: (result) => ({ recovered: result.recovered ?? null }),
  export: (result) => ({ artifactSha256: result.artifact?.sha256 ?? null, recovered: result.recovered ?? null }),
});

function summarizeWorkflow(workflow, result) {
  return { status: result.status, ...WORKFLOW_SUMMARIES[workflow](result) };
}

/** A rejected call keeps its code; a host that died keeps its exit signal. */
function summarizeError(error) {
  return { rejection: error.code ?? null, message: error.message, ...(error.exit ? { exit: error.exit } : {}) };
}

export { summarizeAction, summarizeError, summarizeWorkflow };
