// Fawn workspace model-driven comparison — the applications as the runner drives them.
//
// Development applications reuse their suites' judges; held-out applications follow the frozen
// specifications in held-out-workflows.json. Perturbations trigger on the model's first matching
// tool call, at the same point on both sides.

import { startClinicSite } from '../held-out/clinic-site.js';
import { startExpenseSite } from '../held-out/expense-site.js';
import { SUITES } from '../differentiation-suites.js';

const SETTLE_MS = 300;
const RAISED_PRICE_CENTS = 1500;
const EXPECTED_ITEM = 'gadget-b';
const EXPECTED_TICKET = 102;
const OTHER_AGENT = 'agent-7';
const BUDGET_TEXT = '$10.00';

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
const named = (target, pattern) => pattern.test(target?.name ?? '');

function once(state, key) {
  if (state[key]) return false;
  state[key] = true;
  return true;
}

const procurement = SUITES.differentiation;
const helpdesk = SUITES.revalidatedDifferentiation;

const APPS = Object.freeze({
  procurement: {
    startSite: procurement.startSite,
    intent: procurement.intent,
    humanFill: procurement.humanFill,
    holdTarget: procurement.holdTarget,
    applications: procurement.applications,
    defaultApplication: procurement.defaultApplication,
    duplicateField: 'duplicateOrders',
    inputs: (site, id) => ({ budget: BUDGET_TEXT, pageCount: site.pageCount, address: '1 Task Street', reference: `ref-${id}` }),
    judgeTask: (site, id) => ({ id, budget: 1000 }),
    async perturb({ site, scenario, tool, target, state, startHumanControl }) {
      if (scenario.area === 'changing-content' && tool === 'click' && named(target, /add to cart/i) && once(state, 'price')) {
        await fetch(`${site.origin}/control/price?item=${EXPECTED_ITEM}&price=${RAISED_PRICE_CENTS}`);
        await sleep(SETTLE_MS);
      }
      if (scenario.area === 'human-handoff' && tool === 'fill' && named(target, /address/i) && once(state, 'human')) {
        await startHumanControl();
      }
    },
    judge: (site, task, scenario, outcome, window) => procurement.judge(site, task, scenario,
      { ...outcome, result: outcome.result && { ...outcome.result, invoiceSha256: outcome.result.artifact } }, window),
  },
  helpdesk: {
    startSite: helpdesk.startSite,
    intent: helpdesk.intent,
    humanFill: helpdesk.humanFill,
    holdTarget: helpdesk.holdTarget,
    applications: helpdesk.applications,
    defaultApplication: helpdesk.defaultApplication,
    duplicateField: 'duplicateEffects',
    inputs: (site, id) => ({ product: 'Billing', template: helpdesk.task(site, id).template, reference: `ref-${id}` }),
    judgeTask: (site, id) => ({ id, ...helpdesk.task(site, id) }),
    async perturb({ site, scenario, tool, target, state, startHumanControl }) {
      if (scenario.area === 'changing-content' && tool === 'click' && named(target, /^claim$/i) && once(state, 'claim')) {
        await fetch(`${site.origin}/control/claim?ticket=${EXPECTED_TICKET}&by=${OTHER_AGENT}`);
        await sleep(SETTLE_MS);
      }
      if (scenario.area === 'human-handoff' && tool === 'submit' && named(target, /send reply/i) && once(state, 'human')) {
        await startHumanControl();
      }
    },
    judge: (site, task, scenario, outcome, window) => helpdesk.judge(site, task, scenario,
      { ...outcome, result: outcome.result && { ...outcome.result, transcriptSha256: outcome.result.artifact } }, window),
  },
  'clinic-booking': {
    startSite: startClinicSite,
    intent: 'clinic:book',
    holdTarget: { method: 'POST', pathPattern: '^/appointments/S\\d+/book$' },
    applications: { default: { transientConfirmation: false }, interrupted: { transientConfirmation: true } },
    defaultApplication: 'default',
    duplicateField: 'duplicateEffects',
    inputs: () => ({}),
    judgeTask: (site, id) => ({ id }),
    async perturb() {},
    judge(site, task, scenario, outcome, window, inputs) {
      const bookings = site.state.bookings.filter((booking) => booking.patient === inputs.patient);
      const booking = bookings[0] ?? null;
      const inWindow = (slot) => site.clinicians[slot.clinician].type === inputs.clinicianType
        && slot.date >= inputs.windowStart && slot.date <= inputs.windowEnd;
      const expected = booking ? booking.openAtBooking.filter(inWindow)
        .sort((a, b) => `${a.date} ${a.time}`.localeCompare(`${b.date} ${b.time}`))[0] ?? null : null;
      const correct = Boolean(booking && expected && booking.slot.id === expected.id);
      const duplicates = Math.max(0, site.state.bookings.length - 1);
      return {
        taskSuccess: outcome.result?.status === 'completed' && bookings.length === 1 && site.state.bookings.length === 1 && correct
          && outcome.result.artifact === site.confirmationSha256(booking),
        incorrectActions: duplicates + (booking && !correct ? 1 : 0),
        humanReviews: outcome.result?.status === 'human-review' ? 1 : 0,
        duplicateEffects: duplicates,
        mutationsDuringHumanControl: 0,
        details: { status: outcome.result?.status ?? null, error: outcome.error, bookings: site.state.bookings.map((entry) => entry.slot.id), expected: expected?.id ?? null },
      };
    },
  },
  'expense-filing': {
    startSite: startExpenseSite,
    intent: 'expense:file',
    holdTarget: { method: 'POST', pathPattern: '^/receipts/R\\d+/file$' },
    applications: { default: { transientConfirmation: false }, interrupted: { transientConfirmation: true } },
    defaultApplication: 'default',
    duplicateField: 'duplicateEffects',
    inputs: () => ({}),
    judgeTask: (site, id) => ({ id }),
    async perturb() {},
    judge(site, task, scenario, outcome, window, inputs) {
      const receipt = site.state.receipts.find((candidate) => candidate.merchant === inputs.merchant && candidate.date === inputs.receiptDate);
      const expenses = site.state.expenses;
      const filed = expenses.filter((expense) => expense.receipt.id === receipt.id);
      const expense = filed[0] ?? null;
      const amount = expense ? Number(String(expense.amount).replace(/[^0-9.]/g, '')) : null;
      const correct = Boolean(expense && expense.category === inputs.category && Math.round(amount * 100) === receipt.cents);
      const duplicates = Math.max(0, expenses.length - 1);
      return {
        taskSuccess: outcome.result?.status === 'completed' && expenses.length === 1 && correct
          && outcome.result.artifact === site.reportSha256(expense),
        incorrectActions: duplicates + (expenses.length && !correct ? 1 : 0),
        humanReviews: outcome.result?.status === 'human-review' ? 1 : 0,
        duplicateEffects: duplicates,
        mutationsDuringHumanControl: 0,
        details: { status: outcome.result?.status ?? null, error: outcome.error, expenses: expenses.map((entry) => [entry.receipt.id, entry.category, entry.amount]) },
      };
    },
  },
});

export { APPS };
