// Fawn workspace differentiation — shared engineering-investigation agent policy.
//
// Both arms execute the identical procedure and think time: claim the longest-running unassigned
// incident for the target service, inspect its runbook guidance, file one mitigation disposition
// (preserving any human incident-commander edit), and export the postmortem bundle.

const MAX_DECISIONS = 4;
const VERIFY_ATTEMPTS = 20;
const VERIFY_POLL_MS = 50;

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

async function viewUntil(agent, kind, predicate) {
  for (let attempt = 1; attempt <= VERIFY_ATTEMPTS; attempt += 1) {
    const view = await agent.view(kind);
    if (predicate(view)) return view;
    await sleep(VERIFY_POLL_MS);
  }
  return null;
}

function longestUnassigned(incidents, service) {
  return incidents.filter((incident) => incident.service === service && incident.investigator === null)
    .sort((a, b) => b.durationMinutes - a.durationMinutes || a.id - b.id)[0] ?? null;
}

const urls = (task) => ({
  queue: `${task.origin}/incidents`,
  incident: (id) => `${task.origin}/incidents/${id}`,
});

async function claimIncident(agent, task, hooks) {
  for (let decision = 1; decision <= MAX_DECISIONS; decision += 1) {
    await agent.navigate(urls(task).queue);
    const choice = longestUnassigned((await agent.view('queue')).incidents, task.service);
    if (!choice) throw new Error(`no unassigned ${task.service} incident`);
    await hooks.decision('claim', { incident: choice, decision });
    await sleep(agent.thinkTimeMs);
    try {
      await agent.act('claim', choice, {
        revalidate: {
          view: 'queue',
          find: (view) => view.incidents.find((incident) => incident.id === choice.id && incident.investigator === null) ?? null,
        },
      });
    } catch (error) {
      if (error.redecide) continue;
      throw error;
    }
    const claimed = await viewUntil(agent, 'queue',
      (view) => view.incidents.find((incident) => incident.id === choice.id)?.investigator === task.agentName);
    if (claimed) return choice.id;
  }
  throw new Error('no incident could be claimed within the decision bound');
}

async function recordMitigation(agent, task, hooks, incidentId) {
  await agent.navigate(urls(task).incident(incidentId));
  let detail = await agent.view('incident');
  for (let attempt = 1; attempt <= MAX_DECISIONS; attempt += 1) {
    try {
      const drafted = `${task.summaryPrefix}: ${detail.runbook}`;
      if (detail.summary.value === '') {
        await sleep(agent.thinkTimeMs);
        await agent.act('fill', detail.summary, {
          value: drafted,
          revalidate: { view: 'incident', find: (view) => (view.summary.value === '' ? view.summary : null) },
        });
        detail = await agent.view('incident');
      }
      if (detail.reference && detail.reference.value !== task.reference) {
        await agent.act('fill', detail.reference, { value: task.reference });
        detail = await agent.view('incident');
      }
      const decided = detail.summary.value;
      if (attempt === 1) await hooks.decision('mitigate', { incidentId });
      await sleep(agent.thinkTimeMs);
      agent.checkpoint.update({ mitigation: 'calling', incidentId, reference: detail.reference ? task.reference : null });
      const recorded = await agent.act('mitigate', detail.mitigate, {
        incidentId,
        reference: detail.reference ? task.reference : null,
        revalidate: { view: 'incident', find: (view) => (view.summary.value === decided ? view.mitigate : null) },
      });
      agent.checkpoint.update({ mitigation: 'done', mitigationId: recorded.mitigationId });
      return recorded.mitigationId;
    } catch (error) {
      if (!error.redecide) throw error;
      agent.checkpoint.update({ mitigation: null });
      detail = await agent.view('incident');
    }
  }
  throw new Error('mitigation could not be recorded within the decision bound');
}

async function exportPostmortem(agent, task, incidentId) {
  await agent.navigate(urls(task).incident(incidentId));
  return agent.act('download', (await agent.view('incident')).postmortem);
}

async function runInvestigation(agent, task, hooks) {
  const progress = agent.checkpoint.get();
  let incidentId = progress.incidentId ?? null;
  let mitigationId = progress.mitigationId ?? null;
  if (!mitigationId && progress.mitigation === 'calling') {
    const resolved = await agent.resolveInterrupted(task, progress);
    if (resolved.humanReview) return { status: 'human-review', reason: resolved.reason };
    mitigationId = resolved.id ?? null;
    agent.checkpoint.update({ mitigation: mitigationId ? 'done' : null, mitigationId });
  }
  if (!incidentId) {
    incidentId = await claimIncident(agent, task, hooks);
    agent.checkpoint.update({ incidentId });
  }
  if (!mitigationId) mitigationId = await recordMitigation(agent, task, hooks, incidentId);
  const postmortem = await exportPostmortem(agent, task, incidentId);
  return { status: 'completed', incidentId, mitigationId, postmortemSha256: postmortem.sha256 };
}

export { longestUnassigned, runInvestigation };
