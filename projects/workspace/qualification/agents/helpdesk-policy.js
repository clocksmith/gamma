// Fawn workspace differentiation — the shared helpdesk agent policy.
//
// One deterministic triage procedure drives both sides: claim the oldest open, unclaimed ticket
// for the agent's product, send one reply (the template unless a supervisor edited the draft),
// and save the transcript. Every mutation names what its decision depended on; the revalidating
// control re-checks that against a fresh view, and the treatment binds it to the regions read.

const MAX_DECISIONS = 4;
const VERIFY_ATTEMPTS = 20;
const VERIFY_POLL_MS = 50;

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

/** Observe until the effect shows, as careful automation waits for a page update. */
async function viewUntil(agent, kind, predicate) {
  for (let attempt = 1; attempt <= VERIFY_ATTEMPTS; attempt += 1) {
    const view = await agent.view(kind);
    if (predicate(view)) return view;
    await sleep(VERIFY_POLL_MS);
  }
  return null;
}

function oldestOpen(tickets, product) {
  return tickets.filter((ticket) => ticket.product === product && ticket.claimant === null)
    .sort((a, b) => b.ageMinutes - a.ageMinutes || a.id - b.id)[0] ?? null;
}

const urls = (task) => ({
  queue: `${task.origin}/queue`,
  ticket: (id) => `${task.origin}/tickets/${id}`,
});

async function claimTicket(agent, task, hooks) {
  for (let decision = 1; decision <= MAX_DECISIONS; decision += 1) {
    await agent.navigate(urls(task).queue);
    const choice = oldestOpen((await agent.view('queue')).tickets, task.product);
    if (!choice) throw new Error(`no open ${task.product} ticket`);
    await hooks.decision('claim', { ticket: choice, decision });
    await sleep(agent.thinkTimeMs);
    try {
      await agent.act('claim', choice, {
        revalidate: { view: 'queue', find: (view) => view.tickets.find((ticket) => ticket.id === choice.id && ticket.claimant === null) ?? null },
      });
    } catch (error) {
      if (error.redecide) continue;
      throw error;
    }
    const claimed = await viewUntil(agent, 'queue',
      (view) => view.tickets.find((ticket) => ticket.id === choice.id)?.claimant === task.agentName);
    if (claimed) return choice.id;
  }
  throw new Error('no ticket could be claimed within the decision bound');
}

/** Write the template into an empty draft, then send whatever draft the ticket holds. */
async function sendReply(agent, task, hooks, ticketId) {
  await agent.navigate(urls(task).ticket(ticketId));
  let ticket = await agent.view('ticket');
  for (let attempt = 1; attempt <= MAX_DECISIONS; attempt += 1) {
    try {
      if (ticket.draft.value === '') {
        await sleep(agent.thinkTimeMs);
        await agent.act('fill', ticket.draft, {
          value: task.template,
          revalidate: { view: 'ticket', find: (view) => (view.draft.value === '' ? view.draft : null) },
        });
        ticket = await agent.view('ticket');
      }
      if (ticket.reference && ticket.reference.value !== task.reference) {
        await agent.act('fill', ticket.reference, { value: task.reference });
        ticket = await agent.view('ticket');
      }
      const decided = ticket.draft.value;
      if (attempt === 1) await hooks.decision('send', { ticketId });
      await sleep(agent.thinkTimeMs);
      agent.checkpoint.update({ reply: 'calling', ticketId, reference: ticket.reference ? task.reference : null });
      const sent = await agent.act('send', ticket.send, {
        ticketId,
        reference: ticket.reference ? task.reference : null,
        revalidate: { view: 'ticket', find: (view) => (view.draft.value === decided ? view.send : null) },
      });
      agent.checkpoint.update({ reply: 'done', replyId: sent.replyId });
      return sent.replyId;
    } catch (error) {
      if (!error.redecide) throw error;
      agent.checkpoint.update({ reply: null });
      ticket = await agent.view('ticket');
    }
  }
  throw new Error('the reply could not be sent within the decision bound');
}

async function saveTranscript(agent, task, ticketId) {
  await agent.navigate(urls(task).ticket(ticketId));
  return agent.act('download', (await agent.view('ticket')).transcript);
}

/**
 * Run the triage task, resuming from the checkpoint after an interruption.
 * @returns {Promise<{status: string, ticketId?: number, replyId?: number, transcriptSha256?: string, reason?: string}>}
 */
async function runTriage(agent, task, hooks) {
  const progress = agent.checkpoint.get();
  let ticketId = progress.ticketId ?? null;
  let replyId = progress.replyId ?? null;
  if (!replyId && progress.reply === 'calling') {
    const resolved = await agent.resolveInterrupted(task, progress);
    if (resolved.humanReview) return { status: 'human-review', reason: resolved.reason };
    replyId = resolved.id ?? null;
    agent.checkpoint.update({ reply: replyId ? 'done' : null, replyId });
  }
  if (!ticketId) {
    ticketId = await claimTicket(agent, task, hooks);
    agent.checkpoint.update({ ticketId });
  }
  if (!replyId) replyId = await sendReply(agent, task, hooks, ticketId);
  const transcript = await saveTranscript(agent, task, ticketId);
  return { status: 'completed', ticketId, replyId, transcriptSha256: transcript.sha256 };
}

export { oldestOpen, runTriage };
