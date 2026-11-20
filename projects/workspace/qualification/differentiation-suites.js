// Fawn workspace differentiation — the application side of each frozen suite.
//
// A suite names its fixture site, shared policy, per-arm tool profiles, control variant, task,
// perturbation hooks and judge. The judge reads only the fixture's own state.

import { readFileSync } from 'node:fs';
import { helpdeskFawnProfile, helpdeskPlaywrightProfile } from './agents/helpdesk-tools.js';
import { oldestOpen, runTriage } from './agents/helpdesk-policy.js';
import { investigationFawnProfile, investigationPlaywrightProfile } from './agents/investigation-tools.js';
import { longestUnassigned, runInvestigation } from './agents/investigation-policy.js';
import { cheapestValid, runProcurement } from './agents/procurement-policy.js';
import { procurementFawnProfile, procurementPlaywrightProfile } from './agents/procurement-tools.js';
import { startHelpdeskSite } from './helpdesk-site.js';
import { startInvestigationSite } from './investigation-site.js';
import { startWorkbenchSite } from './workbench-site.js';

const BUDGET_CENTS = 1000;
const TASK_ADDRESS = '1 Task Street';
const HUMAN_ADDRESS = '9 Human Road';
const RAISED_PRICE_CENTS = 1500;
const AGENT_NAME = 'agent';
const OTHER_AGENT = 'agent-7';
const PRODUCT = 'Billing';
const TEMPLATE = 'Thanks for reaching out. We are looking into this and will update you within one business day.';
const SUPERVISOR_TEXT = 'Escalated to billing operations; the duplicate charge will be refunded today.';
const TARGET_SERVICE = 'Checkout';
const SUMMARY_PREFIX = 'Mitigated via runbook';
const OTHER_ONCALL = 'oncall-9';
const COMMANDER_TEXT = 'Incident commander override: drained retry queue and pinned gateway dedupe key.';
const INVESTIGATION_SUITE_CONFIG = JSON.parse(
  readFileSync(new URL('../config/fawn-engineering-investigation-suite.json', import.meta.url), 'utf8'),
);

const inWindow = (window) => (entry) => Boolean(window.start) && entry.at >= window.start && entry.at <= window.end;

const procurement = Object.freeze({
  startSite: startWorkbenchSite,
  policy: runProcurement,
  profiles: { treatment: procurementFawnProfile, control: procurementPlaywrightProfile },
  controlOptions: {},
  intent: 'procure:one-item',
  duplicateField: 'duplicateOrders',
  humanFill: HUMAN_ADDRESS,
  holdTarget: { method: 'POST', path: '/orders' },
  applications: {
    'order-list-and-idempotency-reference': { orderList: true, idempotency: true, transientConfirmation: false },
    'no-order-list-no-idempotency-and-a-confirmation-that-redirects-away': { orderList: false, idempotency: false, transientConfirmation: true },
  },
  defaultApplication: 'order-list-and-idempotency-reference',
  task: (site, id) => ({ budget: BUDGET_CENTS, address: TASK_ADDRESS, reference: `ref-${id}`, pageCount: site.pageCount }),
  async perturb({ site, scenario, stage, info, startHumanControl }) {
    if (scenario.area === 'changing-content' && stage === 'add' && info.decision === 1) {
      await fetch(`${site.origin}/control/price?item=${site.state.items.find((item) => item.name === info.item.name).slug}&price=${RAISED_PRICE_CENTS}`);
    }
    if (scenario.area === 'human-handoff' && stage === 'fill-address') startHumanControl();
  },
  judge(site, task, scenario, outcome, humanWindow) {
    const { orders, mutations } = site.state;
    const order = orders[0] ?? null;
    const expectedAddress = scenario.area === 'human-handoff' ? HUMAN_ADDRESS : TASK_ADDRESS;
    const valid = order ? cheapestValid(order.catalogAtOrder, task.budget) : null;
    const correctItem = Boolean(order && order.lines.length === 1 && valid && order.lines[0].slug === valid.slug
      && order.lines[0].priceAtOrder <= task.budget && order.lines[0].stockAtOrder > 0);
    const addressCorrect = order?.address === expectedAddress;
    const invoiceCorrect = Boolean(order && outcome.result?.invoiceSha256 === site.invoiceSha256(order));
    const duplicates = Math.max(0, orders.length - 1);
    const constraintViolatingMutations = mutations.filter((entry) => entry.kind === 'cart-add'
      && (entry.price > task.budget || entry.stock <= 0)).length;
    return {
      taskSuccess: outcome.result?.status === 'completed' && orders.length === 1 && correctItem && addressCorrect && invoiceCorrect,
      incorrectActions: constraintViolatingMutations + duplicates + (order && !correctItem ? 1 : 0) + (order && !addressCorrect ? 1 : 0),
      constraintViolatingMutations,
      mutationsDuringHumanControl: mutations.filter((entry) => ['cart-add', 'cart-remove', 'order'].includes(entry.kind))
        .filter(inWindow(humanWindow)).length,
      humanReviews: outcome.result?.status === 'human-review' ? 1 : 0,
      duplicateOrders: duplicates,
      details: {
        status: outcome.result?.status ?? null,
        error: outcome.error,
        orders: orders.map((entry) => ({ id: entry.id, items: entry.lines.map((line) => line.slug), address: entry.address })),
        expectedItem: valid?.slug ?? null,
        addressCorrect,
        invoiceCorrect,
      },
    };
  },
  evidence: (site) => ({ mutations: site.state.mutations, orders: site.state.orders.map(({ catalogAtOrder, ...order }) => order) }),
});

const helpdesk = Object.freeze({
  startSite: startHelpdeskSite,
  policy: runTriage,
  profiles: { treatment: helpdeskFawnProfile, control: helpdeskPlaywrightProfile },
  controlOptions: { revalidate: true, cancelOnTakeover: true },
  intent: 'support:triage',
  duplicateField: 'duplicateEffects',
  humanFill: SUPERVISOR_TEXT,
  holdTarget: { method: 'POST', pathPattern: '^/tickets/\\d+/reply$' },
  applications: {
    'sent-list-and-idempotency-reference': { sentList: true, idempotency: true, transientConfirmation: false },
    'no-sent-list-no-idempotency-and-a-confirmation-that-redirects-away': { sentList: false, idempotency: false, transientConfirmation: true },
  },
  defaultApplication: 'sent-list-and-idempotency-reference',
  task: (site, id) => ({ product: PRODUCT, agentName: AGENT_NAME, template: TEMPLATE, reference: `ref-${id}` }),
  async perturb({ site, scenario, stage, info, startHumanControl }) {
    if (scenario.area === 'changing-content' && stage === 'claim' && info.decision === 1) {
      await fetch(`${site.origin}/control/claim?ticket=${info.ticket.id}&by=${OTHER_AGENT}`);
    }
    if (scenario.area === 'human-handoff' && stage === 'send') startHumanControl();
  },
  judge(site, task, scenario, outcome, humanWindow) {
    const { replies, mutations } = site.state;
    const claims = mutations.filter((entry) => entry.kind === 'claim' && entry.by === AGENT_NAME);
    const stolen = claims.filter((entry) => entry.previousClaimant && entry.previousClaimant !== AGENT_NAME).length;
    const claim = claims.at(-1) ?? null;
    const expectedTicket = claim ? oldestOpen(claim.queueAtClaim, task.product) : null;
    const correctTicket = Boolean(claim && expectedTicket && claim.ticket === expectedTicket.id && !claim.previousClaimant);
    const ticketReplies = claim ? replies.filter((reply) => reply.ticket === claim.ticket) : [];
    const reply = ticketReplies[0] ?? null;
    const expectedBody = scenario.area === 'human-handoff' ? SUPERVISOR_TEXT : TEMPLATE;
    const bodyCorrect = reply?.body === expectedBody;
    const duplicates = Math.max(0, replies.length - 1);
    const transcriptCorrect = Boolean(claim && outcome.result?.transcriptSha256 === site.transcriptSha256(claim.ticket));
    return {
      taskSuccess: outcome.result?.status === 'completed' && replies.length === 1 && correctTicket && bodyCorrect && transcriptCorrect,
      incorrectActions: stolen + duplicates + (claim && !correctTicket ? 1 : 0) + (reply && !bodyCorrect ? 1 : 0),
      constraintViolatingMutations: stolen,
      mutationsDuringHumanControl: mutations.filter((entry) => ['claim', 'reply'].includes(entry.kind)).filter(inWindow(humanWindow)).length,
      humanReviews: outcome.result?.status === 'human-review' ? 1 : 0,
      duplicateEffects: duplicates,
      details: {
        status: outcome.result?.status ?? null,
        error: outcome.error,
        claims: claims.map((entry) => ({ ticket: entry.ticket, previousClaimant: entry.previousClaimant })),
        replies: replies.map((entry) => ({ id: entry.id, ticket: entry.ticket, body: entry.body })),
        expectedTicket: expectedTicket?.id ?? null,
        bodyCorrect,
        transcriptCorrect,
      },
    };
  },
  evidence: (site) => ({
    mutations: site.state.mutations.map(({ queueAtClaim, ...entry }) => entry),
    replies: site.state.replies,
  }),
});

const engineeringInvestigation = Object.freeze({
  suiteConfig: INVESTIGATION_SUITE_CONFIG,
  startSite: startInvestigationSite,
  policy: runInvestigation,
  profiles: { treatment: investigationFawnProfile, control: investigationPlaywrightProfile },
  controlOptions: { revalidate: true, cancelOnTakeover: true },
  intent: 'ops:investigate',
  duplicateField: 'duplicateEffects',
  humanFill: COMMANDER_TEXT,
  holdTarget: { method: 'POST', pathPattern: '^/incidents/\\d+/mitigate$' },
  applications: {
    'audit-log-and-idempotency-reference': { auditList: true, idempotency: true, transientConfirmation: false },
    'no-audit-log-no-idempotency-and-a-confirmation-that-redirects-away': { auditList: false, idempotency: false, transientConfirmation: true },
  },
  defaultApplication: 'audit-log-and-idempotency-reference',
  task: (site, id) => ({ service: TARGET_SERVICE, agentName: AGENT_NAME, summaryPrefix: SUMMARY_PREFIX, reference: `ref-${id}` }),
  async perturb({ site, scenario, stage, info, startHumanControl }) {
    if (scenario.area === 'changing-content' && stage === 'claim' && info.decision === 1) {
      await fetch(`${site.origin}/control/claim?incident=${info.incident.id}&by=${OTHER_ONCALL}`);
    }
    if (scenario.area === 'human-handoff' && stage === 'mitigate') startHumanControl();
  },
  judge(site, task, scenario, outcome, humanWindow) {
    const { mitigations, mutations } = site.state;
    const claims = mutations.filter((entry) => entry.kind === 'claim' && entry.by === AGENT_NAME);
    const stolen = claims.filter((entry) => entry.previousInvestigator && entry.previousInvestigator !== AGENT_NAME).length;
    const claim = claims.at(-1) ?? null;
    const expectedIncident = claim ? longestUnassigned(claim.queueAtClaim, task.service) : null;
    const correctIncident = Boolean(claim && expectedIncident && claim.incident === expectedIncident.id && !claim.previousInvestigator);
    const incidentRecord = claim ? site.state.incidents.find((entry) => entry.id === claim.incident) : null;
    const incidentMitigations = claim ? mitigations.filter((entry) => entry.incident === claim.incident) : [];
    const mitigation = incidentMitigations[0] ?? null;
    const expectedSummary = scenario.area === 'human-handoff'
      ? COMMANDER_TEXT
      : (incidentRecord ? `${SUMMARY_PREFIX}: ${incidentRecord.runbook}` : '');
    const summaryCorrect = mitigation?.summary === expectedSummary;
    const duplicates = Math.max(0, mitigations.length - 1);
    const postmortemCorrect = Boolean(claim && outcome.result?.postmortemSha256 === site.postmortemSha256(claim.incident));
    return {
      taskSuccess: outcome.result?.status === 'completed' && mitigations.length === 1 && correctIncident && summaryCorrect && postmortemCorrect,
      incorrectActions: stolen + duplicates + (claim && !correctIncident ? 1 : 0) + (mitigation && !summaryCorrect ? 1 : 0),
      constraintViolatingMutations: stolen,
      mutationsDuringHumanControl: mutations.filter((entry) => ['claim', 'mitigate'].includes(entry.kind)).filter(inWindow(humanWindow)).length,
      humanReviews: outcome.result?.status === 'human-review' ? 1 : 0,
      duplicateEffects: duplicates,
      details: {
        status: outcome.result?.status ?? null,
        error: outcome.error,
        claims: claims.map((entry) => ({ incident: entry.incident, previousInvestigator: entry.previousInvestigator })),
        mitigations: mitigations.map((entry) => ({ id: entry.id, incident: entry.incident, summary: entry.summary })),
        expectedIncident: expectedIncident?.id ?? null,
        summaryCorrect,
        postmortemCorrect,
      },
    };
  },
  evidence: (site) => ({
    mutations: site.state.mutations.map(({ queueAtClaim, ...entry }) => entry),
    mitigations: site.state.mitigations,
  }),
});

const SUITES = Object.freeze({
  differentiation: procurement,
  revalidatedDifferentiation: helpdesk,
  engineeringInvestigation,
});

export { SUITES };
