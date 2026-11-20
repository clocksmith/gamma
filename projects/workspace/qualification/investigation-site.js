// Fawn workspace differentiation — engineering incident investigation fixture with independent oracles.
//
// Serves a live incident queue whose assignment updates in place, an optional streaming telemetry
// feed that mutates continuously, incident detail pages with runbook context and mitigation form,
// transient or persistent mitigation confirmations, an optional mitigation audit log, and
// postmortem bundle downloads. The server's own state and mutation log are the sole oracle.

import { createHash } from 'node:crypto';
import { createServer } from 'node:http';

const LOOPBACK = '127.0.0.1';
const SEE_OTHER = 303;
const NOT_FOUND = 404;
const POLL_MS = 100;
const TELEMETRY_ROWS = 40;
const TRANSIENT_CONFIRMATION_MS = 1000;

const INCIDENTS = Object.freeze([
  { id: 401, title: 'Duplicate capture after gateway retry', service: 'Checkout', durationMinutes: 64, investigator: 'oncall-2', runbook: 'Enforce gateway idempotency key before retry replay.' },
  { id: 402, title: 'Order webhook retry storm on timeout', service: 'Checkout', durationMinutes: 55, investigator: null, runbook: 'Pin webhook dedupe key and drain retry queue.' },
  { id: 403, title: 'Blob compaction backlog in us-east', service: 'Storage', durationMinutes: 78, investigator: null, runbook: 'Throttle background compaction workers to 4.' },
  { id: 404, title: 'Split-tender settlement mismatch', service: 'Checkout', durationMinutes: 49, investigator: null, runbook: 'Hold secondary capture until primary authorization settles.' },
  { id: 405, title: 'OIDC token refresh skew', service: 'Auth', durationMinutes: 61, investigator: null, runbook: 'Widen clock-skew tolerance to 30 seconds.' },
  { id: 406, title: 'Cart lock contention on flash sale', service: 'Checkout', durationMinutes: 33, investigator: null, runbook: 'Shard promotional inventory counters.' },
  { id: 407, title: 'Replica lag on cold shard', service: 'Storage', durationMinutes: 42, investigator: 'oncall-3', runbook: 'Promote warm standby and throttle bulk reads.' },
  { id: 408, title: 'MFA SMS delivery surge', service: 'Auth', durationMinutes: 24, investigator: null, runbook: 'Fail over SMS route to secondary carrier.' },
  { id: 409, title: 'Tax rounding drift on multi-currency', service: 'Checkout', durationMinutes: 16, investigator: null, runbook: 'Pin minor-unit rounding before currency conversion.' },
  { id: 410, title: 'Snapshot manifest checksum warning', service: 'Storage', durationMinutes: 11, investigator: null, runbook: 'Recompute manifest digest from immutable segments.' },
]);

const assignmentText = (investigator) => (investigator ? `investigated by ${investigator}` : 'unassigned');

function escapeHtml(text) {
  return String(text).replace(/[&<>"]/g, (char) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' })[char]);
}

function page(title, body) {
  return `<!doctype html><html><head><title>${title}</title></head><body>${body}</body></html>`;
}

function incidentsPage(state) {
  const rows = state.incidents.map((incident) => `
    <li class="incident-row" id="incident-${incident.id}"><a class="open" href="/incidents/${incident.id}">INC-${incident.id}</a>
      <span class="title">${incident.title}</span>
      <span class="service">${incident.service}</span> <span class="duration">active ${incident.durationMinutes} min</span>
      <span class="assignment">${assignmentText(incident.investigator)}</span>
      <button class="claim-button" data-incident="${incident.id}">Claim incident</button></li>`).join('');
  const telemetry = state.setup.churn
    ? `<section id="telemetry-stream"><h2>Live telemetry</h2><ol>${Array.from({ length: TELEMETRY_ROWS }, (_, index) => `<li id="telemetry-${index}">Span ${index}: baseline</li>`).join('')}</ol></section>`
    : '';
  return page('Incident queue', `
  <h1>Incident queue</h1>
  <p id="heartbeat">sample 0</p>
  <ul id="incidents">${rows}</ul>
  ${telemetry}
  <script>
    (() => {
      let sample = 0;
      document.querySelectorAll('button.claim-button').forEach((button) => button.addEventListener('click', async () => {
        const response = await fetch('/incidents/' + button.dataset.incident + '/claim', { method: 'POST', body: 'agent' });
        button.closest('li').querySelector('.assignment').textContent = await response.text();
      }));
      setInterval(async () => {
        sample += 1;
        document.getElementById('heartbeat').textContent = 'sample ' + sample;
        const state = await (await fetch('/incidents/state')).json();
        for (const incident of state.incidents) {
          const node = document.querySelector('#incident-' + incident.id + ' .assignment');
          const text = incident.investigator ? 'investigated by ' + incident.investigator : 'unassigned';
          if (node.textContent !== text) node.textContent = text;
        }
        if (state.churn) {
          document.querySelectorAll('#telemetry-stream li').forEach((row, index) => {
            row.textContent = 'Span ' + index + ': p99=' + ((index * 4999 + sample * 8191) % 997) + 'ms at sample ' + sample;
          });
        }
      }, ${POLL_MS});
    })();
  </script>`);
}

function incidentDetailPage(state, incident) {
  const reference = state.setup.idempotency ? '<label>Reference <input id="reference" name="reference"></label>' : '';
  return page(`Incident ${incident.id}`, `
  <h1>Incident ${incident.id}: ${incident.title}</h1>
  <p id="assignment-status">${assignmentText(incident.investigator)}</p>
  <section id="runbook"><h2>Runbook guidance</h2><p>${escapeHtml(incident.runbook)}</p></section>
  <form id="mitigation-form" method="post" action="/incidents/${incident.id}/mitigate">
    <label>Mitigation <textarea id="summary" name="summary"></textarea></label>
    ${reference}
    <button id="mitigate" type="submit">Record mitigation</button>
  </form>
  <a id="postmortem" href="/incidents/${incident.id}/postmortem.txt">Download postmortem</a>
  <script>
    setInterval(async () => {
      const next = await (await fetch('/human/next')).json();
      if (!next) return;
      const summary = document.getElementById('summary');
      summary.value = next.fill;
      summary.dispatchEvent(new Event('input', { bubbles: true }));
      await fetch('/human/done', { method: 'POST', body: next.fill });
    }, ${POLL_MS});
  </script>`);
}

function mitigatedPage(state, incident, mitigation) {
  const redirect = state.setup.transientConfirmation && !mitigation.viewed
    ? `<script>setTimeout(() => { location.href = '/incidents'; }, ${TRANSIENT_CONFIRMATION_MS});</script>`
    : '';
  mitigation.viewed = true;
  return page('Mitigation recorded', `
  <h1>Mitigation ${mitigation.id} recorded</h1>
  <p id="mitigated-detail">Incident ${incident.id}; reference ${escapeHtml(mitigation.reference || 'none')}</p>
  <a id="postmortem" href="/incidents/${incident.id}/postmortem.txt">Download postmortem</a>
  ${redirect}`);
}

function postmortemBytes(state, incident) {
  const mitigations = state.mitigations.filter((entry) => entry.incident === incident.id);
  return Buffer.from(`incident,${incident.id},${incident.service},${incident.title}\n${mitigations.map((entry) => `mitigation,${entry.id},${entry.summary}`).join('\n')}\n`);
}

function sha256Hex(bytes) {
  return createHash('sha256').update(bytes).digest('hex');
}

async function readBody(request) {
  let raw = '';
  for await (const chunk of request) raw += chunk;
  return raw;
}

async function startInvestigationSite() {
  const state = {
    setup: { churn: false, auditList: true, idempotency: true, transientConfirmation: false },
    incidents: INCIDENTS.map((incident) => ({ ...incident })),
    mitigations: [],
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
  const incidentOf = (id) => state.incidents.find((incident) => incident.id === Number(id));
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
      // Disconnected caller; server state already committed.
    }
  };
  const json = (response, value) => respond(response, 200, JSON.stringify(value), { 'content-type': 'application/json' });
  const missing = (response) => respond(response, NOT_FOUND, page('Not found', '<h1>Not found</h1>'));

  const ROUTES = [
    ['GET', /^\/incidents$/, (request, response) => respond(response, 200, incidentsPage(state))],
    ['GET', /^\/incidents\/state$/, (request, response) => json(response, {
      churn: state.setup.churn,
      incidents: state.incidents.map(({ id, investigator }) => ({ id, investigator })),
    })],
    ['POST', /^\/incidents\/(\d+)\/claim$/, async (request, response, url, match) => {
      const incident = incidentOf(match[1]);
      if (!incident) return missing(response);
      const investigator = await readBody(request);
      mutate('claim', {
        incident: incident.id,
        by: investigator,
        previousInvestigator: incident.investigator,
        queueAtClaim: state.incidents.map((candidate) => ({ ...candidate })),
      });
      incident.investigator = investigator;
      return respond(response, 200, assignmentText(investigator), { 'content-type': 'text/plain' });
    }],
    ['GET', /^\/incidents\/(\d+)$/, (request, response, url, match) => {
      const incident = incidentOf(match[1]);
      return incident ? respond(response, 200, incidentDetailPage(state, incident)) : missing(response);
    }],
    ['GET', /^\/human\/next$/, (request, response) => json(response, state.humanQueue.shift() ?? null)],
    ['POST', /^\/human\/done$/, async (request, response) => {
      mutate('human-fill', { value: await readBody(request) });
      return json(response, true);
    }],
    ['POST', /^\/incidents\/(\d+)\/mitigate$/, async (request, response, url, match) => {
      const incident = incidentOf(match[1]);
      if (!incident) return missing(response);
      const fields = Object.fromEntries(new URLSearchParams(await readBody(request)));
      const reference = state.setup.idempotency ? (fields.reference ?? '') : '';
      const duplicateOf = reference ? state.mitigations.find((entry) => entry.reference === reference) : null;
      let mitigation = duplicateOf;
      if (!mitigation) {
        mitigation = { id: state.mitigations.length + 1, incident: incident.id, summary: fields.summary ?? '', reference, viewed: false };
        state.mitigations.push(mitigation);
      }
      const entry = mutate('mitigate', {
        mitigationId: mitigation.id,
        incident: incident.id,
        summary: mitigation.summary,
        duplicateOf: duplicateOf?.id ?? null,
      });
      await holdIfRequested('POST', url.pathname, entry);
      return respond(response, SEE_OTHER, '', { location: `/incidents/${incident.id}/mitigated?mitigation=${mitigation.id}` });
    }],
    ['GET', /^\/incidents\/(\d+)\/mitigated$/, (request, response, url, match) => {
      const incident = incidentOf(match[1]);
      const mitigation = state.mitigations.find((candidate) => candidate.id === Number(url.searchParams.get('mitigation')));
      return incident && mitigation ? respond(response, 200, mitigatedPage(state, incident, mitigation)) : missing(response);
    }],
    ['GET', /^\/incidents\/(\d+)\/mitigations$/, (request, response, url, match) => {
      const incident = incidentOf(match[1]);
      if (!incident || !state.setup.auditList) return missing(response);
      const rows = state.mitigations.filter((entry) => entry.incident === incident.id)
        .map((entry) => `<li id="mitigation-${entry.id}">Mitigation ${entry.id}; reference ${escapeHtml(entry.reference || 'none')}</li>`).join('');
      return respond(response, 200, page('Mitigations', `<h1>Mitigations for incident ${incident.id}</h1><ul id="mitigations">${rows}</ul>`));
    }],
    ['GET', /^\/incidents\/(\d+)\/postmortem\.txt$/, (request, response, url, match) => {
      const incident = incidentOf(match[1]);
      if (!incident) return missing(response);
      const bytes = postmortemBytes(state, incident);
      mutate('postmortem', { incident: incident.id, sha256: sha256Hex(bytes) });
      return respond(response, 200, bytes, {
        'content-type': 'text/plain',
        'content-disposition': `attachment; filename="incident-${incident.id}-postmortem.txt"`,
      });
    }],
    ['GET', /^\/control\/setup$/, (request, response, url) => {
      for (const flag of Object.keys(state.setup)) {
        if (url.searchParams.has(flag)) state.setup[flag] = url.searchParams.get(flag) === '1';
      }
      return json(response, state.setup);
    }],
    ['GET', /^\/control\/claim$/, (request, response, url) => {
      const incident = incidentOf(url.searchParams.get('incident'));
      incident.investigator = url.searchParams.get('by');
      mutate('claim-by-other', { incident: incident.id, by: incident.investigator });
      return json(response, incident);
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
    postmortemSha256: (incidentId) => sha256Hex(postmortemBytes(state, incidentOf(incidentId))),
    hold({ method, pathPattern }) {
      let reach;
      let release;
      const reached = new Promise((resolve) => { reach = resolve; });
      const released = new Promise((resolve) => { release = resolve; });
      holds.push({ method, pathPattern, reach, released });
      return { reached, release };
    },
    close: () => new Promise((done) => {
      server.closeAllConnections();
      server.close(done);
    }),
  };
}

export { INCIDENTS, startInvestigationSite };
