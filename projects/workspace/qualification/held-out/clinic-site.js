// Fawn workspace differentiation — held-out clinic booking application.
//
// Implemented after the model-driven suite was frozen, to its specification in
// model-agent/held-out-workflows.json, and never used to tune prompts or tools. A live slot
// table loses slots in place as other patients book them; a booking form confirms one slot.
// The server's own bookings and mutation log decide success and incorrect actions.

import { createHash } from 'node:crypto';
import { createServer } from 'node:http';

const LOOPBACK = '127.0.0.1';
const SEE_OTHER = 303;
const CONFLICT = 409;
const NOT_FOUND = 404;
const POLL_MS = 100;
const OTHER_PATIENT_BOOKING_MS = 2000;
const FEED_ROWS = 40;
const TRANSIENT_CONFIRMATION_MS = 1000;

const CLINICIANS = Object.freeze({
  mensah: { name: 'Dr. Ama Mensah', type: 'dermatologist' },
  park: { name: 'Dr. Lee Park', type: 'dermatologist' },
  novak: { name: 'Dr. Ivo Novak', type: 'cardiologist' },
  ruiz: { name: 'Dr. Sara Ruiz', type: 'general practitioner' },
});

const SLOTS = Object.freeze([
  { id: 'S01', clinician: 'mensah', date: '2026-11-01', time: '10:00' },
  { id: 'S02', clinician: 'novak', date: '2026-11-02', time: '08:00' },
  { id: 'S03', clinician: 'ruiz', date: '2026-11-02', time: '09:00' },
  { id: 'S04', clinician: 'park', date: '2026-11-03', time: '09:30' },
  { id: 'S05', clinician: 'ruiz', date: '2026-11-03', time: '11:00' },
  { id: 'S06', clinician: 'mensah', date: '2026-11-03', time: '14:00' },
  { id: 'S07', clinician: 'novak', date: '2026-11-04', time: '10:30' },
  { id: 'S08', clinician: 'ruiz', date: '2026-11-04', time: '13:00' },
  { id: 'S09', clinician: 'park', date: '2026-11-05', time: '08:30' },
  { id: 'S10', clinician: 'novak', date: '2026-11-05', time: '15:00' },
  { id: 'S11', clinician: 'ruiz', date: '2026-11-06', time: '09:15' },
  { id: 'S12', clinician: 'mensah', date: '2026-11-09', time: '09:00' },
]);

// Other patients take only slots that do not change the task's answer.
const OTHER_PATIENT_SLOTS = Object.freeze(['S03', 'S07', 'S05', 'S10', 'S08', 'S11']);

function page(title, body) {
  return `<!doctype html><html><head><title>${title}</title></head><body>${body}</body></html>`;
}

function escapeHtml(text) {
  return String(text).replace(/[&<>"]/g, (char) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' })[char]);
}

const describe = (slot) => `${CLINICIANS[slot.clinician].name}, ${CLINICIANS[slot.clinician].type}, ${slot.date} ${slot.time}`;

function appointmentsPage(state) {
  const rows = state.slots.filter((slot) => !slot.bookedBy).map((slot) => `
    <tr class="slot-row" id="slot-${slot.id}"><td>${CLINICIANS[slot.clinician].name}</td><td>${CLINICIANS[slot.clinician].type}</td>
      <td>${slot.date}</td><td>${slot.time}</td><td><a class="book" href="/appointments/${slot.id}">Book</a></td></tr>`).join('');
  const feed = state.setup.churn
    ? `<section id="waiting-room"><h2>Waiting room</h2><ol>${Array.from({ length: FEED_ROWS }, (_, index) => `<li id="waiting-${index}">Patient ${index}: waiting</li>`).join('')}</ol></section>`
    : '';
  return page('Appointments', `
  <h1>Open appointments</h1>
  <table id="slots"><thead><tr><th>Clinician</th><th>Type</th><th>Date</th><th>Time</th><th></th></tr></thead><tbody>${rows}</tbody></table>
  ${feed}
  <script>
    (() => {
      let tick = 0;
      setInterval(async () => {
        tick += 1;
        const state = await (await fetch('/appointments/state')).json();
        for (const id of state.booked) document.getElementById('slot-' + id)?.remove();
        if (state.churn) {
          document.querySelectorAll('#waiting-room li').forEach((row, index) => {
            row.textContent = 'Patient ' + index + ': waiting ' + ((index * 31 + tick) % 57) + ' min';
          });
        }
      }, ${POLL_MS});
    })();
  </script>`);
}

function slotPage(slot) {
  return page(`Book ${slot.id}`, `
  <h1>Book ${escapeHtml(describe(slot))}</h1>
  <form id="booking-form" method="post" action="/appointments/${slot.id}/book">
    <label>Patient name <input id="patient" name="patient"></label>
    <button id="confirm" type="submit">Confirm booking</button>
  </form>`);
}

function confirmationPage(state, booking) {
  const redirect = state.setup.transientConfirmation && !booking.viewed
    ? `<script>setTimeout(() => { location.href = '/appointments'; }, ${TRANSIENT_CONFIRMATION_MS});</script>`
    : '';
  booking.viewed = true;
  return page('Booking confirmed', `
  <h1>Booking ${booking.id} confirmed</h1>
  <p id="booking-detail">${escapeHtml(describe(booking.slot))}; patient ${escapeHtml(booking.patient)}</p>
  <a id="download" href="/bookings/${booking.id}/confirmation.txt">Download confirmation</a>
  ${redirect}`);
}

function confirmationBytes(booking) {
  return Buffer.from(`booking,${booking.id}\nslot,${booking.slot.id}\nclinician,${CLINICIANS[booking.slot.clinician].name}\n`
    + `date,${booking.slot.date} ${booking.slot.time}\npatient,${booking.patient}\n`);
}

const sha256Hex = (bytes) => createHash('sha256').update(bytes).digest('hex');

async function readBody(request) {
  let raw = '';
  for await (const chunk of request) raw += chunk;
  return raw;
}

/** Start the clinic. `setup` flags: churn, transientConfirmation. There is no booking list. */
async function startClinicSite() {
  const state = {
    setup: { churn: false, transientConfirmation: false },
    slots: SLOTS.map((slot) => ({ ...slot, bookedBy: null })),
    bookings: [],
    mutations: [],
    requests: [],
  };
  const holds = [];
  const mutate = (kind, details) => {
    const entry = { seq: state.mutations.length + 1, at: new Date().toISOString(), kind, ...details };
    state.mutations.push(entry);
    return entry;
  };
  let otherPatient = 0;
  const otherBookings = setInterval(() => {
    const slot = state.slots.find((candidate) => candidate.id === OTHER_PATIENT_SLOTS[otherPatient]);
    otherPatient += 1;
    if (slot && !slot.bookedBy) {
      slot.bookedBy = `other-patient-${otherPatient}`;
      mutate('other-booking', { slot: slot.id });
    }
  }, OTHER_PATIENT_BOOKING_MS);
  otherBookings.unref();
  const respond = (response, status, body, headers = {}) => {
    try {
      response.writeHead(status, { 'content-type': 'text/html; charset=utf-8', ...headers });
      response.end(body);
    } catch {
      // The browser that asked is gone; the booking already changed.
    }
  };
  const missing = (response) => respond(response, NOT_FOUND, page('Not found', '<h1>Not found</h1>'));
  const slotOf = (id) => state.slots.find((slot) => slot.id === id);
  const ROUTES = [
    ['GET', /^\/$/, (request, response) => respond(response, 200, page('Clinic portal', '<h1>Clinic portal</h1><nav><a href="/appointments">Appointments</a></nav>'))],
    ['GET', /^\/appointments$/, (request, response) => respond(response, 200, appointmentsPage(state))],
    ['GET', /^\/appointments\/state$/, (request, response) => respond(response, 200, JSON.stringify({
      churn: state.setup.churn,
      booked: state.slots.filter((slot) => slot.bookedBy).map((slot) => slot.id),
    }), { 'content-type': 'application/json' })],
    ['GET', /^\/appointments\/(S\d+)$/, (request, response, url, match) => {
      const slot = slotOf(match[1]);
      return slot && !slot.bookedBy ? respond(response, 200, slotPage(slot)) : missing(response);
    }],
    ['POST', /^\/appointments\/(S\d+)\/book$/, async (request, response, url, match) => {
      const slot = slotOf(match[1]);
      const fields = Object.fromEntries(new URLSearchParams(await readBody(request)));
      if (!slot || slot.bookedBy) {
        mutate('booking-refused', { slot: match[1], patient: fields.patient ?? '' });
        return respond(response, CONFLICT, page('Unavailable', '<p id="error">That slot is no longer available</p>'));
      }
      const booking = { id: state.bookings.length + 1, slot: { ...slot }, patient: fields.patient ?? '', viewed: false,
        openAtBooking: state.slots.filter((candidate) => !candidate.bookedBy).map((candidate) => ({ ...candidate })) };
      slot.bookedBy = booking.patient;
      state.bookings.push(booking);
      const entry = mutate('booking', { bookingId: booking.id, slot: slot.id, patient: booking.patient });
      const index = holds.findIndex((held) => held.method === 'POST' && new RegExp(held.pathPattern).test(url.pathname));
      if (index !== -1) {
        const [held] = holds.splice(index, 1);
        held.reach(entry);
        await held.released;
      }
      return respond(response, SEE_OTHER, '', { location: `/bookings/${booking.id}` });
    }],
    ['GET', /^\/bookings\/(\d+)$/, (request, response, url, match) => {
      const booking = state.bookings.find((candidate) => candidate.id === Number(match[1]));
      return booking ? respond(response, 200, confirmationPage(state, booking)) : missing(response);
    }],
    ['GET', /^\/bookings\/(\d+)\/confirmation\.txt$/, (request, response, url, match) => {
      const booking = state.bookings.find((candidate) => candidate.id === Number(match[1]));
      if (!booking) return missing(response);
      const bytes = confirmationBytes(booking);
      mutate('download', { bookingId: booking.id, sha256: sha256Hex(bytes) });
      return respond(response, 200, bytes, { 'content-type': 'text/plain', 'content-disposition': `attachment; filename="booking-${booking.id}.txt"` });
    }],
    ['GET', /^\/control\/setup$/, (request, response, url) => {
      for (const flag of Object.keys(state.setup)) {
        if (url.searchParams.has(flag)) state.setup[flag] = url.searchParams.get(flag) === '1';
      }
      return respond(response, 200, JSON.stringify(state.setup), { 'content-type': 'application/json' });
    }],
  ];
  const server = createServer(async (request, response) => {
    const url = new URL(request.url, `http://${request.headers.host}`);
    state.requests.push({ at: new Date().toISOString(), method: request.method, path: url.pathname });
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
    clinicians: CLINICIANS,
    confirmationSha256: (booking) => sha256Hex(confirmationBytes(booking)),
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
      clearInterval(otherBookings);
      server.closeAllConnections();
      server.close(done);
    }),
  };
}

export { CLINICIANS, startClinicSite };
