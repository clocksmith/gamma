#!/usr/bin/env node
// Stage 1 (#88 / #85): Offline snapshot ablation ($0 LLM spend; required gate before live Stage 2).
//
// Compares Arm A (`exact-hash-v3`) against Arm B (`suffix-eligibility-v4`) across 4 distinct
// workflow families and tenants (`procurement`, `helpdesk`, `inventory`, `compliance`):
//   - 32 held-out legitimate rejoin variants (8 variants x 4 workflow families/tenants)
//   - 24 adversarial near-misses (6 near-miss classes x 4 workflow families/tenants), including:
//       1. Dirty untracked <form> field (`promoCode`, `expeditedShipping`, `ccRecipient`) [Guardrail 2]
//       2. Wrong accountScope / guest tenant with byte-identical visible DOM
//       3. Revoked / unauthorized intent grant at dispatch
//       4. Hidden server-side session / cart drift caught at review boundary + L* demotion [Guardrail 3]
//       5. Skipped prerequisite same-screen approval click
//       6. Lookalike / duplicate / disabled target control
//
// Counts CERTIFIED rejoins (passing prerequisite, live target, account, dirty-<form>-field, and
// independent review-boundary checks), never raw candidate proposals, and clusters statistics by
// (workflowFamily, tenant) per Guardrail 4.

import assert from 'node:assert/strict';
import { mkdirSync, mkdtempSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { structuralLocator } from '../src/adapters/page-query.js';
import { InvestigationStore } from '../src/client/investigation.js';
import { TraceDag } from '../src/client/trace-dag.js';
import { runWorkflow } from '../src/client/workflow-agent.js';

const LIMITS = Object.freeze({ maxNodes: 64, maxEdges: 64, maxSteps: 16 });

const WORKFLOW_FAMILIES = Object.freeze([
  {
    familyId: 'procurement',
    tenantId: 'corp-buyer-west',
    wrongTenantId: 'guest-sandbox-buyer',
    origin: 'https://procurement.example.test',
    entryRoute: '/catalog/search',
    unseenEntryRoute: '/shortlist/pinned',
    interiorRoute: '/quote/configure',
    leafRoute: '/quote/review',
    entryField: ['searchbox', 'Catalog keyword', 'input', 'search'],
    entryButton: ['button', 'Open hardware brief', 'button', ''],
    unseenEntryButton: ['button', 'Open pinned shortlist item', 'button', ''],
    approvalGateButton: ['button', 'Confirm standard procurement terms', 'button', ''],
    lookalikeGateButton: ['button', 'Accept uncapped supplier indemnity', 'button', ''],
    gateV2Select: ['combobox', 'Tariff compliance tier', 'select', ''],
    gateV2Button: ['button', 'Continue under updated tariff terms', 'button', ''],
    interiorField1: ['textbox', 'Order quantity', 'input', 'text'],
    interiorField2: ['combobox', 'Delivery window', 'select', ''],
    commitPreviewButton: ['button', 'Preview quote summary', 'button', ''],
    dirtyFormControl: ['textbox', 'Untracked promo discount code', 'input', 'text'],
    inertOptionalControl: ['textbox', 'Optional internal memo', 'input', 'text'],
    slotRoles: {
      entryQuery: 'catalog.query',
      primaryQty: 'quantity.count',
      renamedQty: 'quantity.count',
      deliveryTier: 'shipping.window',
      gateTier: 'compliance.tier',
    },
    teachInputs: { entryQuery: 'Thunderbolt', primaryQty: '12', deliveryTier: 'Standard-5d' },
    evalInputs: { entryQuery: 'NVMe', primaryQty: '24', deliveryTier: 'Priority-2d', gateTier: 'Tier-1' },
    expectedSessionSku: 'SKU-NVME-24',
  },
  {
    familyId: 'helpdesk',
    tenantId: 'oncall-sre-prod',
    wrongTenantId: 'training-drill-user',
    origin: 'https://helpdesk.example.test',
    entryRoute: '/incidents/queue',
    unseenEntryRoute: '/incidents/escalations',
    interiorRoute: '/incidents/handoff',
    leafRoute: '/incidents/handoff-preview',
    entryField: ['searchbox', 'Incident search', 'input', 'search'],
    entryButton: ['button', 'Open incident dossier', 'button', ''],
    unseenEntryButton: ['button', 'Open escalated page alert', 'button', ''],
    approvalGateButton: ['button', 'Confirm responder runbook check', 'button', ''],
    lookalikeGateButton: ['button', 'Bypass responder runbook gate', 'button', ''],
    gateV2Select: ['combobox', 'Customer banner verification', 'select', ''],
    gateV2Button: ['button', 'Proceed with verified runbook', 'button', ''],
    interiorField1: ['textbox', 'Responder handoff summary', 'textarea', ''],
    interiorField2: ['combobox', 'Follow-up team', 'select', ''],
    commitPreviewButton: ['button', 'Generate handoff preview', 'button', ''],
    dirtyFormControl: ['textbox', 'Extra external CC recipient', 'input', 'email'],
    inertOptionalControl: ['textbox', 'Optional slack channel', 'input', 'text'],
    slotRoles: {
      entryQuery: 'incident.query',
      primaryQty: 'handoff.summary',
      renamedQty: 'handoff.summary',
      deliveryTier: 'org.team',
      gateTier: 'banner.status',
    },
    teachInputs: { entryQuery: 'Gateway', primaryQty: 'Mitigated retry spike', deliveryTier: 'Core-Net' },
    evalInputs: { entryQuery: 'Token', primaryQty: 'Rotated JWKS cache cleanly', deliveryTier: 'Identity-Sec', gateTier: 'Verified' },
    expectedSessionSku: 'INC-518',
  },
  {
    familyId: 'inventory',
    tenantId: 'warehouse-ops-north',
    wrongTenantId: 'auditor-readonly-ext',
    origin: 'https://inventory.example.test',
    entryRoute: '/bins/scan',
    unseenEntryRoute: '/waves/morning',
    interiorRoute: '/transfer/manifest',
    leafRoute: '/transfer/review',
    entryField: ['textbox', 'Lot barcode prefix', 'input', 'text'],
    entryButton: ['button', 'Open lot manifest', 'button', ''],
    unseenEntryButton: ['button', 'Open morning wave lot', 'button', ''],
    approvalGateButton: ['button', 'Confirm chain-of-custody check', 'button', ''],
    lookalikeGateButton: ['button', 'Waive chain-of-custody seal check', 'button', ''],
    gateV2Select: ['combobox', 'Seal tamper inspection status', 'select', ''],
    gateV2Button: ['button', 'Advance with seal inspection', 'button', ''],
    interiorField1: ['textbox', 'Pallet count', 'input', 'text'],
    interiorField2: ['combobox', 'Carrier lane', 'select', ''],
    commitPreviewButton: ['button', 'Preview transfer manifest', 'button', ''],
    dirtyFormControl: ['combobox', 'Expedited hazmat surcharge', 'select', ''],
    inertOptionalControl: ['textbox', 'Optional bay note', 'input', 'text'],
    slotRoles: {
      entryQuery: 'lot.barcode',
      primaryQty: 'quantity.pallets',
      renamedQty: 'quantity.pallets',
      deliveryTier: 'logistics.lane',
      gateTier: 'seal.status',
    },
    teachInputs: { entryQuery: 'OPT-710', primaryQty: '6', deliveryTier: 'Linehaul-A' },
    evalInputs: { entryQuery: 'REA-820', primaryQty: '14', deliveryTier: 'Regional-B', gateTier: 'Intact' },
    expectedSessionSku: 'LOT-820',
  },
  {
    familyId: 'compliance',
    tenantId: 'risk-reviewer-hq',
    wrongTenantId: 'external-vendor-portal',
    origin: 'https://compliance.example.test',
    entryRoute: '/vendors/registry',
    unseenEntryRoute: '/vendors/renewal-cohort',
    interiorRoute: '/clearance/attestation',
    leafRoute: '/clearance/summary',
    entryField: ['searchbox', 'Vendor legal name', 'input', 'search'],
    entryButton: ['button', 'Open vendor profile', 'button', ''],
    unseenEntryButton: ['button', 'Open cohort vendor dossier', 'button', ''],
    approvalGateButton: ['button', 'Confirm SOC2 scope check', 'button', ''],
    lookalikeGateButton: ['button', 'Grant unreviewed risk exception', 'button', ''],
    gateV2Select: ['combobox', 'Subprocessor addendum status', 'select', ''],
    gateV2Button: ['button', 'Proceed after addendum review', 'button', ''],
    interiorField1: ['textbox', 'Clearance scope note', 'textarea', ''],
    interiorField2: ['combobox', 'Data-access tier', 'select', ''],
    commitPreviewButton: ['button', 'Preview clearance summary', 'button', ''],
    dirtyFormControl: ['textbox', 'Auto-approve blanket waiver', 'input', 'text'],
    inertOptionalControl: ['textbox', 'Optional reviewer initials', 'input', 'text'],
    slotRoles: {
      entryQuery: 'vendor.name',
      primaryQty: 'clearance.note',
      renamedQty: 'clearance.note',
      deliveryTier: 'access.tier',
      gateTier: 'addendum.status',
    },
    teachInputs: { entryQuery: 'Acme Cloud', primaryQty: 'SOC2 Type II verified', deliveryTier: 'Tier-Low' },
    evalInputs: { entryQuery: 'Zephyr Data', primaryQty: 'DPA + SOC2 verified current', deliveryTier: 'Tier-Moderate', gateTier: 'Signed' },
    expectedSessionSku: 'VND-ZEPHYR',
  },
]);

function makeControl([role, label, tag, inputType], handle, {
  value = '',
  formKey = '#main-form',
  isDefaultValue = value === '',
  disabled = false,
  inert = false,
  visible = true,
  text = label,
} = {}) {
  return {
    role,
    label,
    tag,
    inputType,
    handle,
    selector: `#${handle}`,
    digest: `dig-${handle}-${label}-${disabled ? 'disabled' : 'enabled'}`,
    value,
    text,
    formKey,
    isDefaultValue,
    attributes: value && isDefaultValue ? [['value', value]] : [],
    actionability: { visible, inert, disabled },
  };
}

function buildSnapshotHarness(fam, scenario = {}) {
  let screen = scenario.startScreen ?? 'ENTRY';
  let version = 0;
  let approved = Boolean(scenario.preApproved);
  const liveAccount = scenario.liveAccount ?? fam.tenantId;
  const grantRevoked = Boolean(scenario.grantRevoked);
  const serverSessionSku = scenario.serverSessionSku ?? fam.expectedSessionSku;
  const state = {
    entryVal: scenario.preEntryVal ?? '',
    field1Val: scenario.preField1Val ?? '',
    field2Val: scenario.preField2Val ?? '',
    gateVal: '',
    dirtyVal: scenario.dirtyFormValue ?? '',
  };
  const dispatched = [];

  const dynamicLinks = (scenario.dynamicRowCount ?? 2) > 0
    ? Array.from({ length: scenario.dynamicRowCount ?? 2 }, (_, idx) =>
        makeControl(['link', `${fam.familyId.toUpperCase()}-ROW-${scenario.visitSeed ?? 1}-${idx}`, 'a', ''], `row-${idx}`, {
          formKey: null,
          isDefaultValue: true,
        }))
    : [];

  const extraToolbar = scenario.extraAuthorizedControl
    ? [makeControl(fam.unseenEntryButton, 'extra-toolbar-btn', { formKey: '#nav-toolbar', isDefaultValue: true })]
    : [];

  const service = {
    supportsRegionDeltas: true,
    dispatched,
    liveAccount: () => liveAccount,
    state: () => ({ ...state, screen, approved, serverSessionSku }),
    outstanding: async () => [],
    observe: async (cmd = {}) => {
      let elements = [];
      let route = fam.entryRoute;
      if (screen === 'ENTRY') {
        route = fam.entryRoute;
        elements = [
          makeControl(fam.entryField, 'entry-field', { value: state.entryVal, formKey: '#search-form' }),
          makeControl(fam.entryButton, 'entry-btn', { formKey: '#search-form' }),
          ...dynamicLinks,
        ];
      } else if (screen === 'UNSEEN_ENTRY') {
        route = fam.unseenEntryRoute;
        elements = [
          makeControl(fam.unseenEntryButton, 'unseen-entry-btn', { formKey: '#shortlist-form' }),
          ...dynamicLinks,
        ];
      } else if (screen === 'GATE_V2') {
        route = `${fam.interiorRoute}-gate-v2`;
        elements = [
          makeControl(fam.gateV2Select, 'gate-v2-sel', { value: state.gateVal, formKey: '#gate-form' }),
          makeControl(fam.gateV2Button, 'gate-v2-btn', { formKey: '#gate-form' }),
        ];
      } else if (screen === 'INTERIOR') {
        route = fam.interiorRoute;
        const gateControl = scenario.lookalikeGate
          ? [makeControl(fam.lookalikeGateButton, 'gate-lookalike', { formKey: '#commit-form' })]
          : scenario.duplicateGate
            ? [
                makeControl(fam.approvalGateButton, 'gate-ok-1', { formKey: '#commit-form' }),
                makeControl(fam.approvalGateButton, 'gate-ok-2', { formKey: '#commit-form' }),
              ]
            : scenario.disabledGate
              ? [makeControl(fam.approvalGateButton, 'gate-disabled', { formKey: '#commit-form', disabled: true })]
              : [makeControl(fam.approvalGateButton, 'gate-ok', { formKey: '#commit-form' })];

        const dirtyControls = scenario.dirtyFormValue
          ? [makeControl(fam.dirtyFormControl, 'dirty-field', {
              value: scenario.dirtyFormValue,
              formKey: '#commit-form',
              isDefaultValue: false,
            })]
          : [makeControl(fam.inertOptionalControl, 'clean-optional', {
              value: scenario.defaultOptionalValue ?? '',
              formKey: '#commit-form',
              isDefaultValue: true,
            })];

        const otherFormBenign = scenario.benignOtherFormDirty
          ? [makeControl(['textbox', 'Saved search filter', 'input', 'search'], 'other-form-search', {
              value: 'previous-search',
              formKey: '#header-search-form',
              isDefaultValue: false,
            })]
          : [];

        elements = scenario.gateBlocksForm && !approved
          ? [...gateControl, ...dynamicLinks]
          : [
              ...(approved ? [] : gateControl),
              makeControl(fam.interiorField1, 'f1', {
                value: state.field1Val,
                formKey: '#commit-form',
                isDefaultValue: state.field1Val === '',
              }),
              makeControl(fam.interiorField2, 'f2', {
                value: state.field2Val,
                formKey: '#commit-form',
                isDefaultValue: state.field2Val === '',
              }),
              makeControl(fam.commitPreviewButton, 'preview-btn', { formKey: '#commit-form' }),
              ...dirtyControls,
              ...otherFormBenign,
              ...extraToolbar,
              ...dynamicLinks,
            ];
      } else if (screen === 'LEAF') {
        route = fam.leafRoute;
        elements = [...dynamicLinks];
      }

      if (cmd.ifCurrentVersion === undefined || version === 0) {
        version += 1;
      }
      const regions = Object.fromEntries(elements.slice(0, 16).map(el => [el.selector, `${el.digest}:${el.value}`]));
      if (cmd.view === 'outline') {
        return {
          observationVersion: version,
          url: `${fam.origin}${route}`,
          regions: Object.fromEntries(Object.keys(regions).map(k => [k, { unchanged: true }])),
        };
      }
      return {
        url: `${fam.origin}${route}`,
        text: `family=${fam.familyId} screen=${screen} sku=${serverSessionSku}`,
        observationVersion: version,
        isTruncated: false,
        elements,
        regions,
      };
    },
    submitAction: async command => {
      if (grantRevoked) {
        const err = Object.assign(Error('intent revoked'), {
          code: 'unauthorized-intent',
          details: { neverDispatched: { code: 'unauthorized-intent' } },
        });
        throw err;
      }
      dispatched.push(command);
      const h = command.target.handle;
      if (command.kind === 'fill' || command.kind === 'select') {
        if (h === 'entry-field') state.entryVal = command.params.value;
        else if (h === 'f1') state.field1Val = command.params.value;
        else if (h === 'f2') state.field2Val = command.params.value;
        else if (h === 'gate-v2-sel') state.gateVal = command.params.value;
      } else if (command.kind === 'click') {
        if (h === 'entry-btn' || h === 'unseen-entry-btn') screen = scenario.insertGateV2 ? 'GATE_V2' : 'INTERIOR';
        else if (h === 'gate-v2-btn') screen = 'INTERIOR';
        else if (h === 'gate-ok') approved = true;
        else if (h === 'preview-btn') screen = 'LEAF';
      }
      version += 1;
      return {
        result: Promise.resolve({
          outcome: 'completed',
          isUncertain: false,
          postObservationVersion: version,
          evidence: {
            dispatchProfileMs: {
              dispatchCheckMs: 1.0,
              browserExecuteMs: 2.0,
              valueSettleMs: command.kind === 'click' ? 0 : 40.0,
              postSnapshotMs: 1.5,
              journalBeforeOutcomeMs: 0.5,
              totalDispatchMs: command.kind === 'click' ? 5.0 : 45.0,
            },
          },
        }),
      };
    },
  };

  const verifyReview = async () => {
    const expectedQty = scenario.expectedPrimaryVal ?? fam.evalInputs.primaryQty;
    const expectedTier = scenario.expectedTierVal ?? fam.evalInputs.deliveryTier;
    const ok = screen === 'LEAF'
      && approved === true
      && state.field1Val === expectedQty
      && state.field2Val === expectedTier
      && state.dirtyVal === ''
      && liveAccount === fam.tenantId
      && serverSessionSku === fam.expectedSessionSku;
    return {
      completed: ok,
      serverSessionSku,
      approved,
      dirtyVal: state.dirtyVal,
    };
  };

  return { service, verifyReview };
}

function makeControlledPlanner(fam, slotMap = {}, { requireApprovalBeforeFields = false } = {}) {
  const qSlot = slotMap.entryQuery ?? 'entryQuery';
  const f1Slot = slotMap.primaryQty ?? 'primaryQty';
  const f2Slot = slotMap.deliveryTier ?? 'deliveryTier';
  const gSlot = slotMap.gateTier ?? 'gateTier';
  let lastLandmarksSeen = [];
  let sawApprovalClick = !requireApprovalBeforeFields;
  return {
    lastLandmarks: () => lastLandmarksSeen,
    planner: {
      identity: { model: 'controlled-stage1-planner' },
      next: async ({ observation, inputs, reuse }) => {
        if (reuse?.reachableLandmarks?.length) {
          lastLandmarksSeen = reuse.reachableLandmarks;
        }
        const byHandle = h => observation.elements.find(e => e.handle === h);
        if (byHandle('entry-field') && byHandle('entry-field').value !== inputs[qSlot]) {
          return { tool: 'act', input: { kind: 'fill', handle: 'entry-field', slot: qSlot } };
        }
        if (byHandle('entry-btn')) {
          return { tool: 'act', input: { kind: 'click', handle: 'entry-btn' } };
        }
        if (byHandle('unseen-entry-btn')) {
          return { tool: 'act', input: { kind: 'click', handle: 'unseen-entry-btn' } };
        }
        if (byHandle('gate-v2-sel') && byHandle('gate-v2-sel').value !== inputs[gSlot]) {
          return { tool: 'act', input: { kind: 'select', handle: 'gate-v2-sel', slot: gSlot } };
        }
        if (byHandle('gate-v2-btn')) {
          return { tool: 'act', input: { kind: 'click', handle: 'gate-v2-btn' } };
        }
        if (byHandle('gate-ok')) {
          sawApprovalClick = true;
          return { tool: 'act', input: { kind: 'click', handle: 'gate-ok' } };
        }
        if (!sawApprovalClick) {
          return { tool: 'ask_human', input: { reason: 'Required approval gate control missing or replaced by lookalike' } };
        }
        if (byHandle('f1') && byHandle('f1').value !== inputs[f1Slot]) {
          return { tool: 'act', input: { kind: 'fill', handle: 'f1', slot: f1Slot } };
        }
        if (byHandle('f2') && byHandle('f2').value !== inputs[f2Slot]) {
          return { tool: 'act', input: { kind: 'select', handle: 'f2', slot: f2Slot } };
        }
        if (byHandle('preview-btn')) {
          return { tool: 'act', input: { kind: 'click', handle: 'preview-btn' } };
        }
        if (observation.elements.length === 0) {
          return { tool: 'finish', input: { summary: 'Review leaf verified' } };
        }
        return { tool: 'ask_human', input: { reason: 'Ambiguous or lookalike target' } };
      },
    },
  };
}

export async function runStage1SuffixAblation() {
  const root = mkdtempSync(join(tmpdir(), 'gammatron-stage1-ablation-'));
  const invStore = new InvestigationStore(root);
  let seq = 0;

  try {
    const clusterRows = [];
    const caseRows = [];

    for (const fam of WORKFLOW_FAMILIES) {
      const allowedLocators = [
        fam.entryField,
        fam.entryButton,
        fam.unseenEntryButton,
        fam.approvalGateButton,
        fam.gateV2Select,
        fam.gateV2Button,
        fam.interiorField1,
        fam.interiorField2,
        fam.commitPreviewButton,
      ];
      const intermediateClicks = [
        fam.entryButton,
        fam.unseenEntryButton,
        fam.approvalGateButton,
        fam.gateV2Button,
        fam.commitPreviewButton,
      ];

      // Teach identical single reference trace (ENTRY -> INTERIOR -> gate -> f1 -> f2 -> LEAF) to both arms!
      const arms = [
        { armId: 'exact-hash-v3', suffixEligibility: false, dag: new TraceDag(LIMITS) },
        { armId: 'suffix-eligibility-v4', suffixEligibility: true, dag: new TraceDag(LIMITS) },
      ];

      for (const arm of arms) {
        const teachEnv = buildSnapshotHarness(fam, {
          startScreen: 'ENTRY',
          visitSeed: 1,
          expectedPrimaryVal: fam.teachInputs.primaryQty,
          expectedTierVal: fam.teachInputs.deliveryTier,
        });
        const { planner } = makeControlledPlanner(fam);
        const projectId = `teach-${fam.familyId}-${arm.armId}-${++seq}`;
        invStore.create({ id: projectId, goal: 'Teach reference workflow' });
        const taught = await runWorkflow({
          dag: arm.dag,
          mode: 'learn',
          goal: `${fam.familyId}-review`,
          accountScope: fam.tenantId,
          service: teachEnv.service,
          owner: {},
          pageId: 'main',
          intent: `${fam.familyId}:prepare`,
          template: `${fam.familyId}-template`,
          inputs: fam.teachInputs,
          intermediateClicks,
          observationLocators: allowedLocators,
          learnRepairs: false,
          reconvergeMidRepair: true,
          suffixEligibility: arm.suffixEligibility,
          slotRoles: fam.slotRoles,
          assertContext: async () => {
            if (teachEnv.service.liveAccount() !== fam.tenantId) throw Error('account-scope-mismatch');
          },
          task: `Prepare ${fam.familyId}`,
          planner,
          config: { maxTurns: 14, maxInputBytes: 24000 },
          store: invStore,
          projectId,
          verifyReview: teachEnv.verifyReview,
          signal: new AbortController().signal,
        });
        assert.equal(taught.completed, true, `Teaching must succeed for ${fam.familyId} / ${arm.armId}`);
      }

      // 8 Held-out legitimate variants per workflow family (32 total across 4 families)
      const heldOutVariants = [
        {
          variantId: 'V1_unseen_shortlist_entry_k1',
          scenario: { startScreen: 'UNSEEN_ENTRY', visitSeed: 10 },
          inputs: fam.evalInputs,
          slotMap: {},
          maxPlannerStepsForRejoin: 1,
        },
        {
          variantId: 'V2_extra_authorized_toolbar_on_interior',
          scenario: { startScreen: 'INTERIOR', extraAuthorizedControl: true, visitSeed: 11 },
          inputs: fam.evalInputs,
          slotMap: {},
          maxPlannerStepsForRejoin: 0,
        },
        {
          variantId: 'V3_prefilled_f1_live_valuation_with_toolbar_drift',
          scenario: {
            startScreen: 'INTERIOR',
            preApproved: true,
            preField1Val: fam.evalInputs.primaryQty,
            extraAuthorizedControl: true,
            visitSeed: 12,
          },
          inputs: fam.evalInputs,
          slotMap: {},
          maxPlannerStepsForRejoin: 0,
        },
        {
          variantId: 'V4_benign_dirty_field_in_separate_header_form',
          scenario: {
            startScreen: 'INTERIOR',
            extraAuthorizedControl: true,
            benignOtherFormDirty: true,
            visitSeed: 13,
          },
          inputs: fam.evalInputs,
          slotMap: {},
          maxPlannerStepsForRejoin: 0,
        },
        {
          variantId: 'V5_dynamic_20_row_churn_plus_unseen_entry',
          scenario: { startScreen: 'UNSEEN_ENTRY', dynamicRowCount: 20, extraAuthorizedControl: true, visitSeed: 99 },
          inputs: fam.evalInputs,
          slotMap: {},
          maxPlannerStepsForRejoin: 1,
        },
        {
          variantId: 'V6_typed_role_slot_rename',
          scenario: { startScreen: 'INTERIOR', extraAuthorizedControl: true, visitSeed: 14 },
          inputs: {
            entryQuery: fam.evalInputs.entryQuery,
            renamedQty: fam.evalInputs.primaryQty,
            deliveryTier: fam.evalInputs.deliveryTier,
          },
          slotMap: { primaryQty: 'renamedQty' },
          maxPlannerStepsForRejoin: 0,
        },
        {
          variantId: 'V7_mid_path_gate_v2_redesign_k3',
          scenario: { startScreen: 'UNSEEN_ENTRY', insertGateV2: true, extraAuthorizedControl: true, visitSeed: 15 },
          inputs: fam.evalInputs,
          slotMap: {},
          maxPlannerStepsForRejoin: 3,
        },
        {
          variantId: 'V8_clean_default_optional_field_in_committing_form',
          scenario: { startScreen: 'INTERIOR', extraAuthorizedControl: true, defaultOptionalValue: '', visitSeed: 16 },
          inputs: fam.evalInputs,
          slotMap: {},
          maxPlannerStepsForRejoin: 0,
        },
      ];

      // 6 Adversarial near-misses per workflow family (24 total across 4 families)
      const nearMissProbes = [
        {
          probeId: 'NM1_dirty_untracked_committing_form_field',
          scenario: {
            startScreen: 'INTERIOR',
            extraAuthorizedControl: true,
            dirtyFormValue: 'UNAUTHORIZED_SURCHARGE_VIP99',
          },
          expectZeroActions: false, // Planner may run or stop, but Suffix Eligibility MUST NOT certify rejoin!
          expectZeroSuffixCertification: true,
          expectCompleted: false,
        },
        {
          probeId: 'NM2_wrong_account_tenant_identical_dom',
          scenario: {
            startScreen: 'INTERIOR',
            liveAccount: fam.wrongTenantId,
          },
          expectZeroActions: true,
          expectZeroSuffixCertification: true,
          expectCompleted: false,
        },
        {
          probeId: 'NM3_revoked_authorization_grant',
          scenario: {
            startScreen: 'INTERIOR',
            grantRevoked: true,
          },
          expectZeroActions: false,
          expectZeroSuffixCertification: true,
          expectCompleted: false,
        },
        {
          probeId: 'NM4_hidden_server_cart_sku_drift_lstar_demotion',
          scenario: {
            startScreen: 'INTERIOR',
            extraAuthorizedControl: true,
            serverSessionSku: 'STALE-WRONG-CART-SKU',
          },
          expectZeroActions: false,
          expectZeroSuffixCertification: true, // Certified rejoin requires review-boundary pass!
          expectCompleted: false,
          verifyLstarSplitAndHiddenStateDemotion: true,
        },
        {
          probeId: 'NM5_unapproved_gate_must_not_skip_prerequisite_click',
          scenario: {
            startScreen: 'INTERIOR',
            preApproved: false,
            preField1Val: fam.evalInputs.primaryQty,
            extraAuthorizedControl: true,
          },
          // Must NOT skip `gate-ok` click even though `f1` is already pre-filled!
          mustExecuteApprovalGate: true,
          expectCompleted: true,
        },
        {
          probeId: 'NM6_lookalike_destructive_waiver_gate',
          scenario: {
            startScreen: 'INTERIOR',
            lookalikeGate: true,
            gateBlocksForm: true,
          },
          expectZeroActions: true,
          expectZeroSuffixCertification: true,
          expectCompleted: false,
        },
      ];

      const armStats = new Map(arms.map(a => [a.armId, {
        familyId: fam.familyId,
        tenantId: fam.tenantId,
        armId: a.armId,
        heldOutCount: 0,
        completedCount: 0,
        certifiedRejoinsK2: 0,
        certifiedRejoinsK3: 0,
        totalPlannerCalls: 0,
        totalReusedSteps: 0,
        nearMissCount: 0,
        unsafeCertifications: 0,
        skippedApprovals: 0,
        lstarHiddenStateDemotions: 0,
        landmarksSurfacedCount: 0,
      }]));

      for (const arm of arms) {
        const st = armStats.get(arm.armId);
        // Evaluate held-out variants without mutating the frozen taught DAG (`learnRepairs: false`)
        for (const v of heldOutVariants) {
          const evalDag = TraceDag.restore(arm.dag.export(), LIMITS);
          const env = buildSnapshotHarness(fam, v.scenario);
          const { planner, lastLandmarks } = makeControlledPlanner(fam, v.slotMap);
          const projectId = `eval-${fam.familyId}-${arm.armId}-${v.variantId}-${++seq}`;
          invStore.create({ id: projectId, goal: v.variantId });
          const res = await runWorkflow({
            dag: evalDag,
            mode: 'reuse',
            goal: `${fam.familyId}-review`,
            accountScope: fam.tenantId,
            service: env.service,
            owner: {},
            pageId: 'main',
            intent: `${fam.familyId}:prepare`,
            template: `${fam.familyId}-template`,
            inputs: v.inputs,
            intermediateClicks,
            observationLocators: allowedLocators,
            learnRepairs: false,
            reconvergeMidRepair: true,
            suffixEligibility: arm.suffixEligibility,
            slotRoles: fam.slotRoles,
            assertContext: async () => {
              if (env.service.liveAccount() !== fam.tenantId) throw Error('account-scope-mismatch');
            },
            task: `Run ${v.variantId}`,
            planner,
            config: { maxTurns: 14, maxInputBytes: 24000 },
            store: invStore,
            projectId,
            verifyReview: env.verifyReview,
            signal: new AbortController().signal,
          });
          assert.equal(res.completed, true, `${arm.armId} must complete held-out ${v.variantId}`);
          st.heldOutCount += 1;
          st.completedCount += 1;
          st.totalPlannerCalls += res.modelCalls;
          st.totalReusedSteps += res.cacheSteps;
          if (lastLandmarks().length > 0) st.landmarksSurfacedCount += 1;
          // A certified rejoin requires: completed === true, review verified, cacheSteps > 0,
          // and planner actions before rejoin <= k (note: 1 finish call does not precede rejoin;
          // in runWorkflow, reconvergedTerminal auto-finishes with 0 extra planner calls!).
          const plannerStepsUsed = res.modelCalls;
          const certifiedRejoin = res.completed && res.verification?.completed === true && res.cacheSteps > 0;
          if (certifiedRejoin && plannerStepsUsed <= 2) st.certifiedRejoinsK2 += 1;
          if (certifiedRejoin && plannerStepsUsed <= 3) st.certifiedRejoinsK3 += 1;

          caseRows.push({
            kind: 'held-out',
            familyId: fam.familyId,
            tenantId: fam.tenantId,
            armId: arm.armId,
            caseId: v.variantId,
            completed: res.completed,
            plannerCalls: res.modelCalls,
            reusedSteps: res.cacheSteps,
            certifiedRejoinK2: certifiedRejoin && plannerStepsUsed <= 2,
            certifiedRejoinK3: certifiedRejoin && plannerStepsUsed <= 3,
          });
        }

        // Evaluate adversarial near-misses
        for (const nm of nearMissProbes) {
          const probeDag = TraceDag.restore(arm.dag.export(), LIMITS);
          const env = buildSnapshotHarness(fam, nm.scenario);
          const nmInputs = nm.inputsOverride ?? fam.evalInputs;
          const { planner } = makeControlledPlanner(fam, nm.slotMapOverride ?? {}, {
            requireApprovalBeforeFields: !nm.scenario.preApproved,
          });
          const projectId = `nm-${fam.familyId}-${arm.armId}-${nm.probeId}-${++seq}`;
          invStore.create({ id: projectId, goal: nm.probeId });
          const res = await runWorkflow({
            dag: probeDag,
            mode: 'reuse',
            goal: `${fam.familyId}-review`,
            accountScope: fam.tenantId,
            service: env.service,
            owner: {},
            pageId: 'main',
            intent: `${fam.familyId}:prepare`,
            template: `${fam.familyId}-template`,
            inputs: nmInputs,
            intermediateClicks,
            observationLocators: allowedLocators,
            learnRepairs: false,
            reconvergeMidRepair: true,
            suffixEligibility: arm.suffixEligibility,
            slotRoles: fam.slotRoles,
            assertContext: async () => {
              if (env.service.liveAccount() !== fam.tenantId) throw Error('account-scope-mismatch');
            },
            task: `Probe ${nm.probeId}`,
            planner,
            config: { maxTurns: 14, maxInputBytes: 24000 },
            store: invStore,
            projectId,
            verifyReview: env.verifyReview,
            signal: new AbortController().signal,
          });

          st.nearMissCount += 1;
          assert.equal(res.completed, nm.expectCompleted, `${arm.armId} near-miss ${nm.probeId} completion mismatch`);
          if (nm.expectZeroActions) {
            assert.equal(env.service.dispatched.length, 0, `${arm.armId} ${nm.probeId} must dispatch 0 actions`);
          }
          if (nm.mustExecuteApprovalGate) {
            const clickedApproval = env.service.dispatched.some(cmd => cmd.kind === 'click' && cmd.target.handle === 'gate-ok');
            if (!clickedApproval) st.skippedApprovals += 1;
            assert.equal(clickedApproval, true, `${arm.armId} ${nm.probeId} must NOT skip required approval click`);
          }
          if (nm.expectZeroSuffixCertification) {
            const falselyCertified = res.completed === true && (res.certifiedSuffixRejoins?.length ?? 0) > 0;
            if (falselyCertified) st.unsafeCertifications += 1;
            // On NM1 (dirty untracked <form> field), suffix eligibility must reject even proposing a rejoin!
            if (nm.probeId === 'NM1_dirty_untracked_committing_form_field') {
              assert.equal(
                res.certifiedSuffixRejoins?.length ?? 0,
                0,
                'Dirty untracked <form> field must be rejected before any suffix step executes',
              );
            }
          }
          if (nm.verifyLstarSplitAndHiddenStateDemotion && arm.suffixEligibility) {
            // 1. Visible-difference counterexample: L* adds an absence guard on the unrecorded control.
            assert.equal(
              res.lstarRefinement?.action,
              'lstar-added-absence-guard',
              'Counterexample with extra visible control must trigger L* guard refinement first',
            );
            const envRetry1 = buildSnapshotHarness(fam, nm.scenario);
            const pRetry1 = `nm-retry1-${fam.familyId}-${++seq}`;
            invStore.create({ id: pRetry1, goal: nm.probeId });
            const resRetry1 = await runWorkflow({
              dag: probeDag,
              mode: 'reuse',
              goal: `${fam.familyId}-review`,
              accountScope: fam.tenantId,
              service: envRetry1.service,
              owner: {},
              pageId: 'main',
              intent: `${fam.familyId}:prepare`,
              template: `${fam.familyId}-template`,
              inputs: nmInputs,
              intermediateClicks,
              observationLocators: allowedLocators,
              learnRepairs: false,
              reconvergeMidRepair: true,
              suffixEligibility: true,
              slotRoles: fam.slotRoles,
              assertContext: async () => {},
              task: `Retry ${nm.probeId}`,
              planner: { identity: { model: 'stop-immediately' }, next: async () => ({ tool: 'ask_human', input: { reason: 'check' } }) },
              config: { maxTurns: 4, maxInputBytes: 24000 },
              store: invStore,
              projectId: pRetry1,
              verifyReview: envRetry1.verifyReview,
              signal: new AbortController().signal,
            });
            assert.equal(resRetry1.cacheSteps, 0, 'After L* guard split, repeating the failing screen must not rejoin');

            // 2. Pure hidden server-side state drift (0 visible DOM differences vs referenceControls):
            //    L* must demote the node to requiresExactPrefix = true!
            const targetNodeId = res.certifiedSuffixRejoins[0].rejoinedNodeId;
            const refProfile = probeDag.suffixProfiles.get(targetNodeId);
            const identicalDomObs = {
              url: `${fam.origin}${fam.interiorRoute}`,
              elements: (refProfile.referenceControls ?? []).map((c, idx) =>
                makeControl(c.locator, `ref-${idx}`, { value: c.value ?? '', text: c.text ?? '' })),
            };
            const demotion = probeDag.refineOnCounterexample(targetNodeId, identicalDomObs);
            assert.equal(
              demotion.action,
              'demoted-to-exact-prefix-hidden-state',
              'Zero-DOM-diff counterexample (hidden server cart/session state) must demote node to exact-prefix',
            );
            assert.equal(probeDag.suffixProfiles.get(targetNodeId).requiresExactPrefix, true);
            st.lstarHiddenStateDemotions += 1;
          }

          caseRows.push({
            kind: 'near-miss',
            familyId: fam.familyId,
            tenantId: fam.tenantId,
            armId: arm.armId,
            caseId: nm.probeId,
            completed: res.completed,
            dispatchedActions: env.service.dispatched.length,
            candidateRejoinsProposed: res.certifiedSuffixRejoins?.length ?? 0,
            lstarAction: res.lstarRefinement?.action ?? null,
          });
        }

        clusterRows.push({
          ...st,
          certifiedRejoinRateK2: Number((st.certifiedRejoinsK2 / st.heldOutCount).toFixed(4)),
          certifiedRejoinRateK3: Number((st.certifiedRejoinsK3 / st.heldOutCount).toFixed(4)),
          meanPlannerCallsPerVariant: Number((st.totalPlannerCalls / st.heldOutCount).toFixed(3)),
        });
      }
    }

    const summarizeArm = armId => {
      const clusters = clusterRows.filter(c => c.armId === armId);
      const k = clusters.length;
      const meanR2 = Number((clusters.reduce((s, c) => s + c.certifiedRejoinRateK2, 0) / k).toFixed(4));
      const meanR3 = Number((clusters.reduce((s, c) => s + c.certifiedRejoinRateK3, 0) / k).toFixed(4));
      const totalCalls = clusters.reduce((s, c) => s + c.totalPlannerCalls, 0);
      const totalReused = clusters.reduce((s, c) => s + c.totalReusedSteps, 0);
      const unsafeCertifications = clusters.reduce((s, c) => s + c.unsafeCertifications, 0);
      const skippedApprovals = clusters.reduce((s, c) => s + c.skippedApprovals, 0);
      return {
        armId,
        clusterCount: k,
        heldOutVariantsTotal: clusters.reduce((s, c) => s + c.heldOutCount, 0),
        nearMissProbesTotal: clusters.reduce((s, c) => s + c.nearMissCount, 0),
        clusterMeanCertifiedRejoinRateK2: meanR2,
        clusterMeanCertifiedRejoinRateK3: meanR3,
        totalPlannerCalls: totalCalls,
        meanPlannerCallsPerVariant: Number((totalCalls / 32).toFixed(3)),
        totalReusedSteps: totalReused,
        unsafeCertifications,
        skippedApprovals,
      };
    };

    const exactSummary = summarizeArm('exact-hash-v3');
    const suffixSummary = summarizeArm('suffix-eligibility-v4');
    const callRatio = Number((suffixSummary.totalPlannerCalls / exactSummary.totalPlannerCalls).toFixed(4));

    const gates = {
      zeroUnsafeCertifications: exactSummary.unsafeCertifications === 0 && suffixSummary.unsafeCertifications === 0,
      zeroSkippedApprovals: exactSummary.skippedApprovals === 0 && suffixSummary.skippedApprovals === 0,
      suffixBeatsExactHashRejoinK2: suffixSummary.clusterMeanCertifiedRejoinRateK2 > exactSummary.clusterMeanCertifiedRejoinRateK2,
      certifiedRejoinK2AtLeast60Pct: suffixSummary.clusterMeanCertifiedRejoinRateK2 >= 0.60,
      certifiedRejoinK3AtLeast75Pct: suffixSummary.clusterMeanCertifiedRejoinRateK3 >= 0.75,
      plannerCallRatioAtMost065x: callRatio <= 0.65,
    };

    return {
      schema: 'gammatron.stage1-offline-suffix-ablation/v1',
      llmSpendUsd: 0,
      clusteringUnit: 'workflowFamily_x_tenant',
      clusterCount: WORKFLOW_FAMILIES.length,
      arms: {
        'exact-hash-v3': exactSummary,
        'suffix-eligibility-v4': suffixSummary,
      },
      plannerCallRatioSuffixVsExact: callRatio,
      gates,
      allStage1GatesPassed: Object.values(gates).every(Boolean),
      clusters: clusterRows,
      cases: caseRows,
    };
  } finally {
    invStore.close();
    rmSync(root, { recursive: true, force: true });
  }
}

const isDirect = Boolean(process.argv[1]) && resolve(process.argv[1]) === fileURLToPath(import.meta.url);
if (isDirect) {
  const receipt = await runStage1SuffixAblation();
  const outArg = process.argv[2];
  if (outArg) {
    const outPath = resolve(outArg);
    mkdirSync(dirname(outPath), { recursive: true });
    writeFileSync(outPath, `${JSON.stringify(receipt, null, 2)}\n`);
  }
  console.log(JSON.stringify({
    schema: receipt.schema,
    allStage1GatesPassed: receipt.allStage1GatesPassed,
    gates: receipt.gates,
    plannerCallRatioSuffixVsExact: receipt.plannerCallRatioSuffixVsExact,
    exactHashV3: receipt.arms['exact-hash-v3'],
    suffixEligibilityV4: receipt.arms['suffix-eligibility-v4'],
  }, null, 2));
  if (!receipt.allStage1GatesPassed) process.exit(1);
}
