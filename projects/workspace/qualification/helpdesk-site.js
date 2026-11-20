// Fawn workspace differentiation — frozen helpdesk fixture with independent oracles.
//
// A live support queue whose claim status updates in place, an optional incoming-ticket feed
// that changes continuously, ticket pages with a reply draft, sent confirmations, reply lists and
// transcripts. A supervisor is simulated inside the page from queued edits. The server's own
// tickets, replies and mutation log decide success and incorrect actions.

import { createHash } from 'node:crypto';
import { createServer } from 'node:http';

const LOOPBACK = '127.0.0.1';
const SEE_OTHER = 303;
const NOT_FOUND = 404;
const POLL_MS = 100;
const FEED_ROWS = 40;
const TRANSIENT_CONFIRMATION_MS = 1000;

const TICKETS = Object.freeze([
  { id: 101, subject: 'Refund not received', product: 'Billing', ageMinutes: 58, claimant: 'agent-2' },
  { id: 102, subject: 'Card declined twice', product: 'Billing', ageMinutes: 52, claimant: null },
  { id: 103, subject: 'Parcel stuck in transit', product: 'Shipping', ageMinutes: 70, claimant: null },
  { id: 104, subject: 'Invoice address wrong', product: 'Billing', ageMinutes: 47, claimant: null },
  { id: 105, subject: 'Password reset loop', product: 'Accounts', ageMinutes: 65, claimant: null },
  { id: 106, subject: 'Double charge on renewal', product: 'Billing', ageMinutes: 30, claimant: null },
  { id: 107, subject: 'Wrong item delivered', product: 'Shipping', ageMinutes: 44, claimant: 'agent-3' },
  { id: 108, subject: 'Two-factor codes delayed', product: 'Accounts', ageMinutes: 21, claimant: null },
  { id: 109, subject: 'Tax missing on receipt', product: 'Billing', ageMinutes: 12, claimant: null },
  { id: 110, subject: 'Return label expired', product: 'Shipping', ageMinutes: 9, claimant: null },
]);

const claimText = (claimant) => (claimant ? `claimed by ${claimant}` : 'unclaimed');

function escapeHtml(text) {
  return String(text).replace(/[&<>"]/g, (char) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' })[char]);
}

function page(title, body) {
  return `<!doctype html><html><head><title>${title}</title></head><body>${body}</body></html>`;
}

function queuePage(state) {
  const rows = state.tickets.map((ticket) => `
    <li class="ticket-row" id="ticket-${ticket.id}"><a class="open" href="/tickets/${ticket.id}">#${ticket.id}</a>
      <span class="subject">${ticket.subject}</span>
      <span class="product">${ticket.product}</span> <span class="age">opened ${ticket.ageMinutes} min ago</span>
      <span class="claim">${claimText(ticket.claimant)}</span>
      <button class="claim-button" data-ticket="${ticket.id}">Claim</button></li>`).join('');
  const feed = state.setup.churn
    ? `<section id="incoming"><h2>Incoming</h2><ol>${Array.from({ length: FEED_ROWS }, (_, index) => `<li id="incoming-${index}">Message ${index}: waiting</li>`).join('')}</ol></section>`
    : '';
  return page('Support queue', `
  <h1>Support queue</h1>
  <p id="clock">tick 0</p>
  <ul id="tickets">${rows}</ul>
  ${feed}
  <script>
    (() => {
      let tick = 0;
      document.querySelectorAll('button.claim-button').forEach((button) => button.addEventListener('click', async () => {
        const response = await fetch('/tickets/' + button.dataset.ticket + '/claim', { method: 'POST', body: 'agent' });
        button.closest('li').querySelector('.claim').textContent = await response.text();
      }));
      setInterval(async () => {
        tick += 1;
        document.getElementById('clock').textContent = 'tick ' + tick;
        const state = await (await fetch('/queue/state')).json();
        for (const ticket of state.tickets) {
          const claim = document.querySelector('#ticket-' + ticket.id + ' .claim');
          const text = ticket.claimant ? 'claimed by ' + ticket.claimant : 'unclaimed';
          if (claim.textContent !== text) claim.textContent = text;
        }
        if (state.churn) {
          document.querySelectorAll('#incoming li').forEach((row, index) => {
            row.textContent = 'Message ' + index + ': ' + ((index * 6151 + tick * 92821) % 7919) + ' new at tick ' + tick;
          });
        }
      }, ${POLL_MS});
    })();
  </script>`);
}

function ticketPage(state, ticket) {
  const reference = state.setup.idempotency ? '<label>Reference <input id="reference" name="reference"></label>' : '';
  return page(`Ticket ${ticket.id}`, `
  <h1>Ticket ${ticket.id}: ${ticket.subject}</h1>
  <p id="claim-status">${claimText(ticket.claimant)}</p>
  <form id="reply-form" method="post" action="/tickets/${ticket.id}/reply">
    <label>Reply <textarea id="draft" name="body"></textarea></label>
    ${reference}
    <button id="send" type="submit">Send reply</button>
  </form>
  <a id="transcript" href="/tickets/${ticket.id}/transcript.txt">Download transcript</a>
  <script>
    // A supervisor at the same browser: edits arrive from the human queue, not an automation channel.
    setInterval(async () => {
      const next = await (await fetch('/human/next')).json();
      if (!next) return;
      const draft = document.getElementById('draft');
      draft.value = next.fill;
      draft.dispatchEvent(new Event('input', { bubbles: true }));
      await fetch('/human/done', { method: 'POST', body: next.fill });
    }, ${POLL_MS});
  </script>`);
}

function sentPage(state, ticket, reply) {
  const redirect = state.setup.transientConfirmation && !reply.viewed
    ? `<script>setTimeout(() => { location.href = '/queue'; }, ${TRANSIENT_CONFIRMATION_MS});</script>`
    : '';
  reply.viewed = true;
  return page('Reply sent', `
  <h1>Reply ${reply.id} sent</h1>
  <p id="sent-detail">Ticket ${ticket.id}; reference ${escapeHtml(reply.reference || 'none')}</p>
  <a id="transcript" href="/tickets/${ticket.id}/transcript.txt">Download transcript</a>
  ${redirect}`);
}

function transcriptBytes(state, ticket) {
  const replies = state.replies.filter((reply) => reply.ticket === ticket.id);
  return Buffer.from(`ticket,${ticket.id},${ticket.subject}\n${replies.map((reply) => `reply,${reply.id},${reply.body}`).join('\n')}\n`);
}

function sha256Hex(bytes) {
  return createHash('sha256').update(bytes).digest('hex');
}

async function readBody(request) {
  let raw = '';
  for await (const chunk of request) raw += chunk;
  return raw;
}

/**
 * Start the helpdesk. `setup` flags: churn, sentList, idempotency, transientConfirmation.
 * `hold({method, pathPattern})` holds the next matching response after its effect is recorded.
 */
async function startHelpdeskSite() {
  const state = {
    setup: { churn: false, sentList: true, idempotency: true, transientConfirmation: false },
    tickets: TICKETS.map((ticket) => ({ ...ticket })),
    replies: [],
    mutations: [],
    humanQueue: [],
    requests: [],
  };
  const holds = [];
  const mutate = (kind, details) => {
    const entry = { seq: state.mutations.length + 1, at: new Date().toISOString(), kind, ...details };
    state.mutations.push(entry);
    return entry;
  };
  const ticketOf = (id) => state.tickets.find((ticket) => ticket.id === Number(id));
  const holdIfRequested = async (method, path, entry) => {
    const index = holds.findIndex((held) => held.method === method && new RegExp(held.pathPattern).test(path));
    if (index === -1) return;
    const [held] = holds.splice(index, 1);
    held.reach(entry);
    await held.released;
  };
  const respond = (response, status, body, headers = {}) => {
    try {
      response.writeHead(status, { 'content-type': 'text/html; charset=utf-8', ...headers });
      response.end(body);
    } catch {
      // The browser that asked is gone; the application state already changed.
    }
  };
  const json = (response, value) => respond(response, 200, JSON.stringify(value), { 'content-type': 'application/json' });
  const missing = (response) => respond(response, NOT_FOUND, page('Not found', '<h1>Not found</h1>'));

  const ROUTES = [
    ['GET', /^\/queue$/, (request, response) => respond(response, 200, queuePage(state))],
    ['GET', /^\/queue\/state$/, (request, response) => json(response, {
      churn: state.setup.churn,
      tickets: state.tickets.map(({ id, claimant }) => ({ id, claimant })),
    })],
    ['POST', /^\/tickets\/(\d+)\/claim$/, async (request, response, url, match) => {
      const ticket = ticketOf(match[1]);
      if (!ticket) return missing(response);
      const claimant = await readBody(request);
      mutate('claim', {
        ticket: ticket.id,
        by: claimant,
        previousClaimant: ticket.claimant,
        queueAtClaim: state.tickets.map((candidate) => ({ ...candidate })),
      });
      ticket.claimant = claimant;
      return respond(response, 200, claimText(claimant), { 'content-type': 'text/plain' });
    }],
    ['GET', /^\/tickets\/(\d+)$/, (request, response, url, match) => {
      const ticket = ticketOf(match[1]);
      return ticket ? respond(response, 200, ticketPage(state, ticket)) : missing(response);
    }],
    ['GET', /^\/human\/next$/, (request, response) => json(response, state.humanQueue.shift() ?? null)],
    ['POST', /^\/human\/done$/, async (request, response) => {
      mutate('human-fill', { value: await readBody(request) });
      return json(response, true);
    }],
    ['POST', /^\/tickets\/(\d+)\/reply$/, async (request, response, url, match) => {
      const ticket = ticketOf(match[1]);
      if (!ticket) return missing(response);
      const fields = Object.fromEntries(new URLSearchParams(await readBody(request)));
      const reference = state.setup.idempotency ? (fields.reference ?? '') : '';
      const duplicateOf = reference ? state.replies.find((reply) => reply.reference === reference) : null;
      let reply = duplicateOf;
      if (!reply) {
        reply = { id: state.replies.length + 1, ticket: ticket.id, body: fields.body ?? '', reference, viewed: false };
        state.replies.push(reply);
      }
      const entry = mutate('reply', { replyId: reply.id, ticket: ticket.id, body: reply.body, duplicateOf: duplicateOf?.id ?? null });
      await holdIfRequested('POST', url.pathname, entry);
      return respond(response, SEE_OTHER, '', { location: `/tickets/${ticket.id}/sent?reply=${reply.id}` });
    }],
    ['GET', /^\/tickets\/(\d+)\/sent$/, (request, response, url, match) => {
      const ticket = ticketOf(match[1]);
      const reply = state.replies.find((candidate) => candidate.id === Number(url.searchParams.get('reply')));
      return ticket && reply ? respond(response, 200, sentPage(state, ticket, reply)) : missing(response);
    }],
    ['GET', /^\/tickets\/(\d+)\/replies$/, (request, response, url, match) => {
      const ticket = ticketOf(match[1]);
      if (!ticket || !state.setup.sentList) return missing(response);
      const rows = state.replies.filter((reply) => reply.ticket === ticket.id)
        .map((reply) => `<li id="reply-${reply.id}">Reply ${reply.id}; reference ${escapeHtml(reply.reference || 'none')}</li>`).join('');
      return respond(response, 200, page('Replies', `<h1>Replies to ticket ${ticket.id}</h1><ul id="replies">${rows}</ul>`));
    }],
    ['GET', /^\/tickets\/(\d+)\/transcript\.txt$/, (request, response, url, match) => {
      const ticket = ticketOf(match[1]);
      if (!ticket) return missing(response);
      const bytes = transcriptBytes(state, ticket);
      mutate('transcript', { ticket: ticket.id, sha256: sha256Hex(bytes) });
      return respond(response, 200, bytes, {
        'content-type': 'text/plain',
        'content-disposition': `attachment; filename="ticket-${ticket.id}.txt"`,
      });
    }],
    ['GET', /^\/control\/setup$/, (request, response, url) => {
      for (const flag of Object.keys(state.setup)) {
        if (url.searchParams.has(flag)) state.setup[flag] = url.searchParams.get(flag) === '1';
      }
      return json(response, state.setup);
    }],
    ['GET', /^\/control\/claim$/, (request, response, url) => {
      const ticket = ticketOf(url.searchParams.get('ticket'));
      ticket.claimant = url.searchParams.get('by');
      mutate('claim-by-other', { ticket: ticket.id, by: ticket.claimant });
      return json(response, ticket);
    }],
    ['GET', /^\/control\/human$/, (request, response, url) => {
      state.humanQueue.push({ fill: url.searchParams.get('fill') });
      return json(response, true);
    }],
  ];

  const server = createServer(async (request, response) => {
    const url = new URL(request.url, `http://${request.headers.host}`);
    state.requests.push({ at: new Date().toISOString(), method: request.method, path: url.pathname, search: url.search });
    for (const [method, pattern, handler] of ROUTES) {
      const match = pattern.exec(url.pathname);
      if (match && request.method === method) return handler(request, response, url, match);
    }
    return missing(response);
  });
  const origin = await new Promise((resolve) => {
    server.listen(0, LOOPBACK, () => resolve(`http://${LOOPBACK}:${server.address().port}`));
  });
  return {
    origin,
    state,
    transcriptSha256: (ticketId) => sha256Hex(transcriptBytes(state, ticketOf(ticketId))),
    hold({ method, pathPattern }) {
      let reach;
      let release;
      const reached = new Promise((resolve) => {
        reach = resolve;
      });
      const released = new Promise((resolve) => {
        release = resolve;
      });
      holds.push({ method, pathPattern, reach, released });
      return { reached, release };
    },
    close: () => new Promise((done) => {
      server.closeAllConnections();
      server.close(done);
    }),
  };
}

export { TICKETS, startHelpdeskSite };
