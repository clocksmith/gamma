// Fawn workspace differentiation — the helpdesk as each arm sees it.

import { completedUrl } from './fawn-agent.js';
import { controls } from './outline.js';

const AGE = /opened (\d+) min ago/;
const CLAIM = /(unclaimed|claimed by ([\w-]+))/;
const replyIdOf = (url) => Number(/[?&]reply=(\d+)/.exec(url)?.[1]) || null;

function ticketFields(text) {
  const claim = CLAIM.exec(text);
  return {
    product: ['Billing', 'Shipping', 'Accounts'].find((product) => text.includes(` ${product} `) || text.includes(`| ${product} |`)) ?? null,
    ageMinutes: Number(AGE.exec(text)?.[1] ?? 0),
    claimant: claim?.[2] ?? null,
  };
}

// The workspace service's outline view.
const FAWN_VIEWS = Object.freeze({
  queue: { regionGroups: ['.ticket-row'] },
  ticket: { regions: ['h1', '#reply-form', '#draft', '#reference', '#transcript'] },
});

const FAWN_PARSERS = Object.freeze({
  queue: (regions, version) => ({
    tickets: Object.entries(regions).filter(([selector]) => selector.startsWith('#ticket-')).map(([selector, outline]) => ({
      id: Number(selector.slice('#ticket-'.length)),
      subject: outline.split(' | ').find((part) => !part.startsWith('[')),
      ...ticketFields(outline),
      handle: controls(outline).find((control) => control.name === 'Claim')?.handle,
      region: selector,
      version,
    })),
  }),
  ticket: (regions, version) => {
    const field = (region, name) => {
      const control = controls(regions[region] ?? '').find((candidate) => candidate.name === name);
      return control ? { handle: control.handle, value: control.value ?? '', region, version } : null;
    };
    const send = controls(regions['#reply-form'] ?? '').find((control) => control.name === 'Send reply');
    const transcript = controls(regions['#transcript'] ?? '').find((control) => control.name === 'Download transcript');
    return {
      draft: field('#draft', 'body'),
      reference: field('#reference', 'reference'),
      send: send ? { handle: send.handle, version } : null,
      transcript: transcript ? { handle: transcript.handle, version } : null,
    };
  },
});

const FAWN_ACTIONS = Object.freeze({
  claim: (target, options, { base, actionId, scoped, task, sequence }) => ({
    ...base,
    actionId: actionId('claim'),
    kind: 'click',
    ...scoped([target.region]),
    effect: { external: true, effectKey: `claim:${task.id}:${target.id}:${sequence()}` },
    completion: { completedWhen: [{ kind: 'element-text-includes', selector: target.region, value: `claimed by ${task.agentName}` }] },
  }),
  fill: (target, { value }, { base, actionId, scoped }) => ({ ...base, actionId: actionId('fill'), kind: 'fill', ...scoped([target.region]), params: { value } }),
  send: (target, { ticketId, reference }, { base, actionId, scoped, task }) => ({
    ...base,
    actionId: actionId('send'),
    kind: 'submit',
    ...scoped(['#reply-form']),
    effect: { external: true, effectKey: `reply:${task.id}`, ...(reference ? { externalIdempotencyKey: reference } : {}) },
    completion: { completedWhen: [{ kind: 'url-prefix', value: `${task.origin}/tickets/${ticketId}/sent` }] },
  }),
  download: (target, options, { base, actionId, scoped }) => ({ ...base, actionId: actionId('download'), kind: 'download', ...scoped(['#transcript']) }),
});

const helpdeskFawnProfile = Object.freeze({
  views: FAWN_VIEWS,
  parsers: FAWN_PARSERS,
  actions: FAWN_ACTIONS,
  results: {
    send: (record) => ({ replyId: replyIdOf(completedUrl(record)) }),
    download: (record) => ({ sha256: record.evidence.effect.sha256 }),
  },
  interrupted: (task) => ({ effectKey: `reply:${task.id}`, idFrom: (record) => replyIdOf(completedUrl(record)) }),
});

// Playwright agent tooling: the page-wide agent snapshot.
const ROW_TEXT = /^\s*- text: (.+)$/;
const BUTTON = /^\s*- button "([^"]+)" (?:\[[^\]]+\] )*\[ref=(e\d+)\]/;
const TEXTBOX = /^\s*- textbox "([^"]+)" (?:\[[^\]]+\] )*\[ref=(e\d+)\](?:: (.*))?$/;
const LINK = /^\s*- link "([^"]+)" \[ref=(e\d+)\]/;
const HEADING = /^\s*- '?heading "([^"]+)"/;

const PLAYWRIGHT_PARSERS = Object.freeze({
  queue: (lines) => ({
    tickets: lines.flatMap((line, index) => {
      const text = ROW_TEXT.exec(line)?.[1];
      const button = BUTTON.exec(lines[index + 1] ?? '');
      if (!text || button?.[1] !== 'Claim') return [];
      const link = lines.slice(Math.max(0, index - 3), index).map((candidate) => LINK.exec(candidate)).filter(Boolean).at(-1);
      return [{ id: Number(/#(\d+)/.exec(link?.[1] ?? '')?.[1]) || null, subjectLine: text, ...ticketFields(` ${text} `), ref: button[2] }];
    }),
  }),
  ticket: (lines) => {
    const field = (name) => {
      const match = lines.map((line) => TEXTBOX.exec(line)).find((candidate) => candidate?.[1] === name);
      return match ? { ref: match[2], value: match[3] ?? '' } : null;
    };
    const send = lines.map((line) => BUTTON.exec(line)).find((match) => match?.[1] === 'Send reply');
    const transcript = lines.map((line) => LINK.exec(line)).find((match) => match?.[1] === 'Download transcript');
    return {
      draft: field('Reply'),
      reference: field('Reference'),
      send: send ? { ref: send[2] } : null,
      transcript: transcript ? { ref: transcript[2] } : null,
    };
  },
  sent: (lines) => {
    const heading = lines.map((line) => HEADING.exec(line)).find(Boolean)?.[1] ?? '';
    return { replyId: Number(/Reply (\d+) sent/.exec(heading)?.[1]) || null, lines };
  },
  replies: (lines) => ({
    found: lines.some((line) => /Replies to ticket/.test(HEADING.exec(line)?.[1] ?? '')),
    replies: lines.map((line) => /Reply (\d+); reference (\S+?)"?$/.exec(line)).filter(Boolean)
      .map(([, id, reference]) => ({ id: Number(id), reference })),
  }),
});

/**
 * The send call began but its result was lost. Check the page the browser is on, then the
 * ticket's reply list; with an idempotency reference a resend is safe; otherwise the outcome
 * is unknown and goes to human review.
 */
async function resolveInterruptedSend(agent, task, progress) {
  const current = PLAYWRIGHT_PARSERS.sent((await agent.snapshot()).full.split('\n'));
  if (current.replyId && current.lines.some((line) => line.includes(`Ticket ${progress.ticketId};`))) return { id: current.replyId };
  await agent.navigate(`${task.origin}/tickets/${progress.ticketId}/replies`);
  const list = await agent.view('replies');
  if (list.found) {
    const match = list.replies.find((reply) => reply.reference === (progress.reference ?? 'none'));
    return match ? { id: match.id } : { retry: true };
  }
  if (progress.reference) return { retry: true };
  return { humanReview: true, reason: 'reply outcome unknown: no confirmation on the page, no reply list, no idempotency' };
}

const PLAYWRIGHT_ACTS = Object.freeze({
  claim: (agent, target) => agent.tool('click', { ref: target.ref }, { consequential: true }),
  fill: (agent, target, { value }) => agent.tool('fill', { ref: target.ref, value }, { consequential: true }),
  download: (agent, target) => agent.tool('download', { ref: target.ref }, { consequential: true }),
  async send(agent, target) {
    agent.requireAllowed((await agent.tool('formAction')).action);
    const sent = await agent.tool('click', { ref: target.ref }, { consequential: true });
    return { replyId: replyIdOf(sent.url) };
  },
});

const helpdeskPlaywrightProfile = Object.freeze({
  parsers: PLAYWRIGHT_PARSERS,
  act: PLAYWRIGHT_ACTS,
  resolveInterrupted: resolveInterruptedSend,
});

export { helpdeskFawnProfile, helpdeskPlaywrightProfile };
