// Planner input is paid for on every turn. Only the newest observation of each page is sent in full;
// saved evidence keeps its hash and identity but sends a bounded excerpt of its bytes.
import { artifactMemory } from './artifact-memory.js';
import { completionContract, completionProgress, incompleteDeliverables } from './completion-contract.js';
// A page observation can be most of a request (text plus every addressable element), and it is paid
// for again on every later turn. It stays in full while the planner is working on that page; once
// this many later results have followed it, it is reduced to where the page was and how it began.
// The planner observes again to act there, and anything it saved as evidence is still on record.
const FULL_OBSERVATION_RESULTS = 3, AGED_EXCERPT_CHARS = 1200;
// The same holds for any other large result, such as a slice of saved evidence: after the same number
// of later results its long fields are dropped. What identifies it stays, so it can be read again.
const AGED_RESULT_BYTES = 3000, AGED_FIELD_CHARS = 200;
function ageResult(output) {
  if (!output || typeof output !== 'object' || Array.isArray(output) || JSON.stringify(output).length <= AGED_RESULT_BYTES) return output;
  const kept = Object.fromEntries(Object.entries(output).filter(([, value]) => value === null || ['number', 'boolean'].includes(typeof value)
    || (typeof value === 'string' && value.length <= AGED_FIELD_CHARS)));
  return { ...kept, omitted: Object.keys(output).filter(key => !Object.hasOwn(kept, key)), aged: 'Sent in full earlier. Request it again if it is still needed.' };
}
export function investigationContext(project, { task, permissions, initialArtifacts, startSequence, shareRecords, visibleArtifacts = null, handoff = null }) {
  const shared = visibleArtifacts ?? new Set(Object.keys(project.artifacts).filter(key => shareRecords || !initialArtifacts.has(key)));
  const { artifacts, artifactCatalog } = artifactMemory(project, shared);
  const events = project.activity.filter(event => event.seq > startSequence && ['tool-requested', 'tool-result', 'tool-failed'].includes(event.event));
  const latestObservation = new Map();
  for (const event of events) {
    if (event.event === 'tool-result' && event.output?.observationVersion !== undefined && typeof event.output?.text === 'string') {
      latestObservation.set(event.output.pageId ?? 'main', event.seq);
    }
  }
  const results = events.filter(event => event.event !== 'tool-requested');
  const resultsAfter = new Map(results.map((event, index) => [event.seq, results.length - 1 - index]));
  const history = events
    .map(event => {
      if (event.event === 'tool-result' && event.output?.observationVersion !== undefined && typeof event.output?.text === 'string'
        && latestObservation.get(event.output.pageId ?? 'main') !== event.seq) {
        const { pageId, url, title, observationVersion } = event.output;
        return { event: event.event, callId: event.callId, output: { pageId, url, title, observationVersion, superseded: 'a newer observation of this page follows' } };
      }
      if (event.event === 'tool-result' && event.output?.observationVersion !== undefined && typeof event.output?.text === 'string'
        && resultsAfter.get(event.seq) >= FULL_OBSERVATION_RESULTS) {
        const { pageId, url, title, observationVersion, isTruncated, text, elements } = event.output;
        return { event: event.event, callId: event.callId, output: { pageId, url, title, observationVersion, isTruncated,
          textExcerpt: text.slice(0, AGED_EXCERPT_CHARS), textChars: text.length, elementCount: elements?.length ?? 0,
          aged: 'Sent in full earlier. Observe this page again before acting on its elements.' } };
      }
      if (event.event === 'tool-requested') return { event: event.event, callId: event.callId, tool: event.tool, input: event.input };
      if (event.event === 'tool-failed') return { event: event.event, callId: event.callId,
        error: event.error, code: event.code, details: event.details, recoverable: event.recoverable };
      const output = event.output?.id && event.output?.kind
        ? shared.has(event.output.id) ? { artifactId: event.output.id, kind: event.output.kind,
          revision: event.output.revision, status: event.output.status,
          // Advice attached to a saved conclusion stays in view for as long as other full results do.
          ...(event.output.unreadMentions && resultsAfter.get(event.seq) < FULL_OBSERVATION_RESULTS ? { unreadMentions: event.output.unreadMentions } : {}) }
          : { omitted: 'Source record was not shared with this task' }
        : resultsAfter.get(event.seq) >= FULL_OBSERVATION_RESULTS ? ageResult(event.output) : event.output;
      return { event: event.event, callId: event.callId, output };
    });
  return { goal: project.goal, task, permissions, repositoryAvailable: !!project.repositoryRoot, artifacts, artifactCatalog, history,
    ...(handoff ? { handoff } : {}) };
}

// A bounded product agent. It owns planning, never browser authority or outcome truth.
import { randomUUID } from 'node:crypto';

export function startAgent({ projectId, store, planner, execute, config, signal, assertCurrent, context: getContext,
  runId = randomUUID(), verifyCompletion = null, recoverToolError = null, reviewFinish = null, requiredCompletion = null, completionRecords = null }) {
  const contract = completionContract(requiredCompletion);
  const progress = () => completionProgress(completionRecords ? completionRecords() : store.get(projectId).artifacts, contract);
  const id = runId, usage = [];
  let turns = 0, finishReturned = false;
  const save = (status, detail) => {
    if (store.get(projectId).run?.id !== id) return;
    store.run(projectId, { id, status, detail, turns, usage, planner: planner.identity });
  };
  store.run(projectId, { id, status: 'running', turns, usage, planner: planner.identity });
  const done = (async () => {
    try {
      while (turns < config.maxTurns) {
        assertCurrent(); signal.throwIfAborted();
        const context = { ...getContext(), ...(contract ? { completion: progress() } : {}), budget: { maxRequests: config.maxTurns, remainingRequests: config.maxTurns - turns } };
        if (Buffer.byteLength(JSON.stringify(context)) > config.maxInputBytes) throw Error('Investigation input budget reached');
        const requestId = randomUUID();
        turns += 1; usage.push(null);
        save('running', 'Waiting for the planner');
        store.activity(projectId, { event: 'planner-requested', requestId, planner: planner.identity });
        let proposal;
        try { proposal = await planner.next(context, { signal }); }
        catch (error) {
          usage[usage.length - 1] = error.usage ?? null;
          store.activity(projectId, { event: 'planner-failed', requestId, error: error.message, usage: error.usage ?? null });
          const current = store.get(projectId).run;
          if (current?.id === id) store.run(projectId, { ...current, turns, usage });
          throw error;
        }
        usage[usage.length - 1] = proposal.usage ?? null;
        store.activity(projectId, { event: 'planner-result', requestId, usage: proposal.usage ?? null });
        const current = store.get(projectId).run;
        if (current?.id === id) store.run(projectId, { ...current, turns, usage });
        assertCurrent(); signal.throwIfAborted();
        const callId = randomUUID();
        // Persist the call before execution. Restart never automatically replays a pending call.
        store.activity(projectId, { event: 'tool-requested', callId, tool: proposal.tool, input: proposal.input });
        // A finish that leaves saved work visibly incomplete is returned once, while requests remain,
        // with what is missing. A second finish is accepted as the agent's decision.
        const objection = proposal.tool === 'finish' && !finishReturned && turns < config.maxTurns
          ? (reviewFinish?.() || incompleteDeliverables(progress())) : null;
        if (objection) {
          finishReturned = true;
          store.activity(projectId, { event: 'tool-failed', callId, error: objection, code: 'finish-incomplete', recoverable: true,
            details: { neverDispatched: { code: 'finish-incomplete' } } });
          save('running', 'Finish returned: required work remains');
          continue;
        }
        if (proposal.tool === 'finish' || proposal.tool === 'ask_human') {
          store.activity(projectId, { event: proposal.tool, text: proposal.input.summary ?? proposal.input.reason ?? '' });
          if (proposal.tool === 'finish') {
            const missing = incompleteDeliverables(progress());
            if (missing) { save('needs-attention', missing); return; }
          }
          if (proposal.tool === 'finish' && verifyCompletion) {
            save('running', 'Checking the completed work');
            const verified = await verifyCompletion();
            assertCurrent(); signal.throwIfAborted();
            // The verifier may yield while sources or saved records change. Check the live contract again.
            const missingAfterVerification = incompleteDeliverables(progress());
            if (missingAfterVerification) { save('needs-attention', missingAfterVerification); return; }
            save(verified.completed === true ? 'completed' : 'needs-attention', verified.detail);
            return;
          }
          save(proposal.tool === 'finish' ? 'completed' : 'needs-attention', proposal.input.summary ?? proposal.input.reason);
          return;
        }
        let output;
        try { output = await execute(proposal.tool, proposal.input, { callId }); }
        catch (error) {
          assertCurrent(); signal.throwIfAborted();
          const recoverable = recoverToolError?.(error) === true;
          store.activity(projectId, { event: 'tool-failed', callId, error: error.message,
            code: error.code ?? null, recoverable,
            details: { path: error.details?.path, expected: error.details?.expected,
              neverDispatched: error.details?.neverDispatched } });
          if (!recoverable) throw error;
          // Only a trusted caller can attest a correctable, never-dispatched
          // proposal. A new planner decision consumes the ordinary turn budget.
          save('running', `Proposal rejected: ${error.code}`);
          continue;
        }
        store.activity(projectId, { event: 'tool-result', callId, output });
        assertCurrent(); signal.throwIfAborted();
        if (output?.isUncertain || output?.outcome === 'failed' || output?.serviceError) {
          save('needs-attention', 'The last action needs review. No retry was attempted.'); return;
        }
        save('running', `Finished ${proposal.tool}`);
      }
      save('needs-attention', 'Task turn budget reached');
    } catch (error) {
      save(signal.aborted ? 'stopped' : 'needs-attention', signal.aborted ? 'Human control requested; dispatched effects may still settle.' : error.message);
    }
  })();
  return { id, done };
}
