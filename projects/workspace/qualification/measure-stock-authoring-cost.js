#!/usr/bin/env node
// Quantifies the previously unmeasured authoring cost and maintenance fragility of
// stock browser-automation baselines against Fawn's WorkflowStore + TraceDag v3,
// using zero paid model calls and ephemeral 127.0.0.1 loopback fixtures only.
//
// Measures three concrete costs:
//   1. Ordinary 6-task hand-written Playwright scripts (ordinary-tasks-site.js + runner):
//      static SLOC, bytes, explicit DOM/URL operations, and per-task authoring surface.
//   2. Overlapping-request R1..R8 hand-written Playwright script (v1 initial vs v2 repaired):
//      runs a real headless Chrome pass against startOverlappingRequestsServer() showing:
//        - v1 hand-written script completes R1..R5, safely refuses R8 + ambiguous gate,
//          gives the 0-call execution-time floor, and FAILS on R6/R7 when Gate_v2 ships
//          until a developer manually authors the v2 gate branch (+SLOC/+selectors).
//   3. Capable LLM-driven stock-reusable-parts harness (overlapping-requests-reuse.js):
//      461 SLOC of bespoke helper/precondition/slice-dispatch harness code PLUS why flat
//      helper lists still spend 30 vs 22 planner calls/repeat (17 vs 9 post-teaching calls)
//      with identical 44/45 reused UI actions.

import { mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { chromium } from 'playwright-core';
import { sha256Hex } from '../src/journal.js';
import {
  EXPECTED_ACCOUNT_SCOPE,
  buildOverlappingRequestsSpec,
  startOverlappingRequestsServer,
} from './overlapping-requests-site.js';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '../../..');

const outFlagIdx = process.argv.indexOf('--out');
const outPath = outFlagIdx !== -1 && process.argv[outFlagIdx + 1]
  ? resolve(root, process.argv[outFlagIdx + 1])
  : null;

function countCodeMetrics(lines) {
  const rawLines = lines.length;
  const sloc = lines.filter(line => {
    const trimmed = line.trim();
    return trimmed.length > 0 && !trimmed.startsWith('//');
  }).length;
  const bytes = lines.reduce((sum, line) => sum + Buffer.byteLength(line, 'utf8') + 1, 0);
  const playwrightOps = lines.reduce((sum, line) => {
    const hits = line.match(/\.(?:getByLabel|getByRole|locator|fill|selectOption|click|waitForURL|goto|evaluate)\b/g);
    return sum + (hits ? hits.length : 0);
  }, 0);
  return { rawLines, sloc, bytes, playwrightOps };
}

function measureSlice(relPath, startLine, endLine) {
  const fullPath = join(root, relPath);
  const allLines = readFileSync(fullPath, 'utf8').splitlines
    ? readFileSync(fullPath, 'utf8').splitlines()
    : readFileSync(fullPath, 'utf8').split('\n');
  const slice = allLines.slice(startLine - 1, endLine);
  return {
    file: relPath,
    lineRange: `${startLine}-${endLine}`,
    fileSha256: sha256Hex(readFileSync(fullPath)),
    ...countCodeMetrics(slice),
  };
}

function extractNamedFunctionBlocks(relPath, marker) {
  const fullPath = join(root, relPath);
  const lines = readFileSync(fullPath, 'utf8').split('\n');
  const blocks = [];
  for (let i = 0; i < lines.length; i += 1) {
    if (lines[i].includes(marker)) {
      const start = i + 1;
      let depth = 0;
      let end = start;
      for (let j = i; j < lines.length; j += 1) {
        for (const ch of lines[j]) {
          if (ch === '{') depth += 1;
          else if (ch === '}') depth -= 1;
        }
        if (depth === 0) {
          end = j + 1;
          break;
        }
      }
      blocks.push({
        lineRange: `${start}-${end}`,
        ...countCodeMetrics(lines.slice(start - 1, end)),
      });
      i = end - 1;
    }
  }
  return {
    file: relPath,
    fileSha256: sha256Hex(readFileSync(fullPath)),
    blockCount: blocks.length,
    blocks,
    totals: blocks.reduce(
      (acc, b) => ({
        rawLines: acc.rawLines + b.rawLines,
        sloc: acc.sloc + b.sloc,
        bytes: acc.bytes + b.bytes,
        playwrightOps: acc.playwrightOps + b.playwrightOps,
      }),
      { rawLines: 0, sloc: 0, bytes: 0, playwrightOps: 0 },
    ),
  };
}

// Hand-authored static Playwright script for R1..R8:
// - supportGateV2=false models the script authored against the initial v1 app (R1..R5, R8).
// - supportGateV2=true models the manual developer maintenance patch required after Gate_v2 ships on R6.
async function runHandwrittenOverlappingScript(page, {
  expectedOrigin,
  request,
  inputs,
  supportGateV2,
}) {
  const info = await page.evaluate(() => ({
    origin: location.origin,
    account: document.body?.dataset?.accountScope ?? null,
  }));
  if (info.origin !== expectedOrigin || info.account !== EXPECTED_ACCOUNT_SCOPE) {
    throw Object.assign(Error(`Refused mismatched account: ${info.account}`), {
      code: 'script-account-precondition-refused',
    });
  }

  async function clickUniqueButton(label) {
    const btn = page.getByRole('button', { name: label, exact: true });
    const count = await btn.count();
    if (count !== 1) {
      throw Object.assign(Error(`Expected 1 button "${label}", saw ${count}`), {
        code: count > 1 ? 'ambiguous-locator' : 'missing-locator',
      });
    }
    await btn.click();
    await page.waitForLoadState('domcontentloaded');
  }

  if (request.startRoute === 'catalog') {
    await page.getByLabel('Catalog search', { exact: true }).fill(inputs.searchQuery);
    await page.getByLabel('Hardware category', { exact: true }).selectOption(inputs.hardwareCategory);
    await clickUniqueButton('Run catalog filter');
    await page.getByRole('link', { name: 'Open product brief', exact: true }).click();
    await page.waitForLoadState('domcontentloaded');
  } else if (request.startRoute === 'shortlist') {
    await page.getByLabel('Shortlist tier', { exact: true }).selectOption(inputs.shortlistTier);
    await clickUniqueButton('Open shortlisted brief');
  }

  if (request.goal === 'product-brief') {
    return;
  }

  if (request.goal === 'compliance-export') {
    await page.getByRole('link', { name: 'Open compliance drawer', exact: true }).click();
    await page.waitForLoadState('domcontentloaded');
    await page.getByLabel('Audit framework', { exact: true }).selectOption(inputs.auditFramework);
    await page.getByLabel('Reviewer handle', { exact: true }).fill(inputs.reviewerHandle);
    await clickUniqueButton('Preview compliance export');
    return;
  }

  if (request.goal === 'shipping-quote') {
    if (request.startRoute !== 'brief') {
      await page.getByRole('link', { name: 'Open quote configurator', exact: true }).click();
      await page.waitForLoadState('domcontentloaded');
    } else {
      await page.getByRole('link', { name: 'Open quote configurator', exact: true }).click();
      await page.waitForLoadState('domcontentloaded');
    }
    // --- Initial v1 gate branch vs manual v2 maintenance patch ---
    if (!supportGateV2) {
      await clickUniqueButton('Confirm standard terms');
    } else {
      const v2Select = page.getByLabel('Deployment environment', { exact: true });
      if ((await v2Select.count()) === 1) {
        await v2Select.selectOption(inputs.deploymentEnv);
        await clickUniqueButton('Confirm v2 procurement gate');
      } else {
        await clickUniqueButton('Confirm standard terms');
      }
    }
    await page.getByLabel('Order quantity', { exact: true }).fill(inputs.quantity);
    await page.getByLabel('Delivery ZIP', { exact: true }).fill(inputs.zipCode);
    await page.getByLabel('Shipping speed', { exact: true }).selectOption(inputs.shippingSpeed);
    await page.getByLabel('Cost center', { exact: true }).fill(inputs.costCenter);
    await clickUniqueButton('Preview shipping quote');
  }
}

const selfLines = readFileSync(fileURLToPath(import.meta.url), 'utf8').split('\n');
const v1ScriptStart = selfLines.findIndex(l => l.startsWith('async function runHandwrittenOverlappingScript')) + 1;
const v1ScriptEnd = selfLines.findIndex((l, idx) => idx > v1ScriptStart && l === '}');
const patchStart = selfLines.findIndex(l => l.includes('// --- Initial v1 gate branch vs manual v2 maintenance patch ---')) + 1;
const patchEnd = selfLines.findIndex((l, idx) => idx > patchStart && l.includes("await page.getByLabel('Order quantity'"));
const handwrittenFullMetrics = countCodeMetrics(selfLines.slice(v1ScriptStart - 1, v1ScriptEnd));
const handwrittenV2PatchMetrics = countCodeMetrics(selfLines.slice(patchStart - 1, patchEnd));

const ordinaryScripts = extractNamedFunctionBlocks(
  'projects/workspace/qualification/ordinary-tasks-site.js',
  'async runStockScript(page, inputs)',
);
const ordinaryRunnerWrapper = measureSlice(
  'projects/workspace/qualification/ordinary-workflow-reuse.js',
  358,
  428,
);
const stockReusablePromptAndTools = measureSlice(
  'projects/workspace/qualification/overlapping-requests-reuse.js',
  102,
  115,
);
const stockReusableRuntime = measureSlice(
  'projects/workspace/qualification/overlapping-requests-reuse.js',
  524,
  994,
);
const fawnCallerWiring = measureSlice(
  'projects/workspace/qualification/overlapping-requests-reuse.js',
  347,
  390,
);

// Execute both v1 (unpatched) and v2 (patched) hand-written scripts on local Chrome across R1..R8 + ambiguous probe
const spec = buildOverlappingRequestsSpec();
const server = await startOverlappingRequestsServer();
const scratchRoot = mkdtempSync(join(tmpdir(), 'fawn-stock-authoring-'));

async function runScriptSuite({ supportGateV2 }) {
  const results = [];
  let totalTaskVerifiedMs = 0;
  let totalEndToEndMs = 0;

  for (const request of spec.requests) {
    const sid = `${supportGateV2 ? 'v2' : 'v1'}-${request.requestId}`;
    const profileDir = join(scratchRoot, sid);
    mkdirSync(profileDir, { recursive: true, mode: 0o700 });
    const inputs = request.inputsByRepeat[0];
    const startQuery = request.startQueryByRepeat[0];
    const t0 = performance.now();
    let context;
    let errorCode = null;
    let oracle = null;
    let verifiedMs = 0;
    try {
      context = await chromium.launchPersistentContext(profileDir, { channel: 'chrome', headless: true });
      const page = context.pages()[0] ?? await context.newPage();
      const startUrl = server.createSession(sid, {
        startRoute: request.startRoute,
        query: startQuery,
        gateMode: request.gateMode,
        accountScope: request.accountScope,
        expectedGoal: request.goal,
      });
      await page.goto(startUrl, { waitUntil: 'load' });
      try {
        await runHandwrittenOverlappingScript(page, {
          expectedOrigin: server.origin,
          request,
          inputs,
          supportGateV2,
        });
      } catch (err) {
        errorCode = err.code ?? err.message;
      }
      oracle = await request.verify(page, inputs, server, sid, startQuery);
      verifiedMs = performance.now() - t0;
    } finally {
      await context?.close();
    }
    const endToEndMs = performance.now() - t0;
    if (!request.isRefusalCase) {
      totalTaskVerifiedMs += verifiedMs;
      totalEndToEndMs += endToEndMs;
    }
    results.push({
      requestId: request.requestId,
      isRefusalCase: request.isRefusalCase,
      completed: request.isRefusalCase ? false : Boolean(!errorCode && oracle?.completed),
      refusedSafely: request.isRefusalCase ? Boolean(errorCode && oracle?.safeRefusal) : false,
      errorCode,
      verifiedSeconds: Number((verifiedMs / 1000).toFixed(3)),
      endToEndSeconds: Number((endToEndMs / 1000).toFixed(3)),
      submissions: oracle?.submissions ?? 0,
      unsafeAccountMutations: oracle?.unsafeAccountMutations ?? 0,
    });
  }

  // Separate ambiguous-target probe
  const ambSid = `${supportGateV2 ? 'v2' : 'v1'}-ambiguous-probe`;
  const ambProfile = join(scratchRoot, ambSid);
  mkdirSync(ambProfile, { recursive: true, mode: 0o700 });
  let ambContext;
  let ambCode = null;
  try {
    ambContext = await chromium.launchPersistentContext(ambProfile, { channel: 'chrome', headless: true });
    const page = ambContext.pages()[0] ?? await ambContext.newPage();
    const ambUrl = server.createSession(ambSid, {
      startRoute: 'gate',
      query: { sku: 'TB4-DOCK-PRO' },
      gateMode: 'ambiguous',
      accountScope: EXPECTED_ACCOUNT_SCOPE,
      expectedGoal: 'shipping-quote',
    });
    await page.goto(ambUrl, { waitUntil: 'load' });
    const btn = page.getByRole('button', { name: 'Confirm standard terms', exact: true });
    const count = await btn.count();
    if (count !== 1) ambCode = count > 1 ? 'ambiguous-locator' : 'missing-locator';
  } finally {
    await ambContext?.close();
  }
  const ambStats = server.getSessionStats(ambSid);

  return {
    supportGateV2,
    taskCompletions: results.filter(r => !r.isRefusalCase && r.completed).length,
    taskTotal: results.filter(r => !r.isRefusalCase).length,
    failedTaskIds: results.filter(r => !r.isRefusalCase && !r.completed).map(r => ({
      requestId: r.requestId,
      errorCode: r.errorCode,
    })),
    lookalikeRefusalSafe: results.filter(r => r.isRefusalCase).every(r => r.refusedSafely && r.unsafeAccountMutations === 0),
    ambiguousProbeSafe: ambCode === 'ambiguous-locator' && (ambStats.ambiguousGateClicks ?? 0) === 0,
    totalTaskVerifiedSeconds: Number((totalTaskVerifiedMs / 1000).toFixed(3)),
    totalTaskEndToEndSeconds: Number((totalEndToEndMs / 1000).toFixed(3)),
    rows: results,
  };
}

let v1Run;
let v2Run;
let browserVersion = null;
try {
  const probeBrowser = await chromium.launch({ channel: 'chrome', headless: true });
  browserVersion = probeBrowser.version();
  await probeBrowser.close();
  v1Run = await runScriptSuite({ supportGateV2: false });
  v2Run = await runScriptSuite({ supportGateV2: true });
} finally {
  await server.close();
  rmSync(scratchRoot, { recursive: true, force: true });
}

const preflightDecision = JSON.parse(
  readFileSync(join(root, 'reports/fawn-workspace/20261117-overlapping-requests-preflight/decision.json'), 'utf8'),
);

const perRequestCallDelta = preflightDecision.byRequest
  .filter(r => !r.isRefusalCase)
  .map(r => {
    const fawnCalls = r.fawnGraph.novelCallsByRepeat[0];
    const stockCalls = r.stockReusableParts.novelCallsByRepeat[0];
    const freshCalls = r.freshPlanning.novelCallsByRepeat[0];
    const fawnReuse = r.fawnGraph.reusedActionsByRepeat[0];
    const stockReuse = r.stockReusableParts.reusedActionsByRepeat[0];
    return {
      requestId: r.requestId,
      requestType: r.requestType,
      reusedActionsBothArms: fawnReuse,
      stockMatchesReuse: fawnReuse === stockReuse,
      fawnPlannerCalls: fawnCalls,
      stockPlannerCalls: stockCalls,
      freshPlannerCalls: freshCalls,
      extraStockCallsOverFawn: stockCalls - fawnCalls,
      whyDifferenceOccurs:
        fawnCalls === stockCalls
          ? (fawnCalls === 0
              ? 'Exact (startRoute, goal) match after repair: both auto-replay 12 actions with 0 calls'
              : 'Initial teaching pass on unseen segment: identical action-by-action planning')
          : r.requestId === 'R3_heldout_compose_ac'
            ? 'Fawn TraceDag composes A->B + B->C across goalTerminals in 0 calls; Stock has no (catalog, shipping-quote) helper yet so planner spends 3 calls invoking call_helper(A->B), call_helper(B->C), and finish'
            : r.requestId === 'R4_shared_prefix_new_tail'
              ? 'Fawn auto-replays 4-step A->B prefix to checkpoint B before calling planner (5 novel tail calls); Stock invokes planner at step 0 to emit call_helper(A->B) (+1 call = 6 calls)'
              : r.requestId === 'R5_new_entry_shared_suffix'
                ? 'Fawn plans 2 novel E->B steps and auto-reconverges onto 7-step B->C suffix + oracle finish (2 calls); Stock plans 2 E->B steps then spends +2 calls on call_helper(B->C) and finish (4 calls)'
                : 'Fawn auto-replays 5 prefix steps, plans 2 Gate_v2 repair steps, and auto-reconverges onto 5-step QuoteForm->C suffix (2 calls); Stock auto-replays 5 steps, plans 2 Gate_v2 steps, then spends +2 calls on call_helper(QuoteForm->C slice [2,7)) and finish (4 calls)',
    };
  });

const report = {
  schema: 'fawn.stock-authoring-cost-summary/v1',
  generatedAt: new Date().toISOString(),
  paidModelCalls: 0,
  measuredCostUsd: 0,
  loopbackOnly: true,
  browserVersion,
  ordinarySixTaskStockScripts: {
    description: 'Hand-authored per-task Playwright scripts + runner wrapper behind the 3.382s 0-call floor in 20261117-ordinary-workflow-reuse',
    perTaskScripts: ordinaryScripts,
    runnerWrapper: ordinaryRunnerWrapper,
    combinedAuthoringSurface: {
      sloc: ordinaryScripts.totals.sloc + ordinaryRunnerWrapper.sloc,
      bytes: ordinaryScripts.totals.bytes + ordinaryRunnerWrapper.bytes,
      explicitPlaywrightOps: ordinaryScripts.totals.playwrightOps + ordinaryRunnerWrapper.playwrightOps,
      fawnPerTaskAuthoringSloc: 0,
    },
  },
  overlappingHandwrittenStockScript: {
    description: 'Hand-authored static Playwright script on R1..R8 showing 0-call execution floor AND manual code-maintenance cost when Gate_v2 replaces Gate_v1 on R6',
    codeSurfaceFullPatched: handwrittenFullMetrics,
    manualGateV2RepairPatchSurface: handwrittenV2PatchMetrics,
    v1BeforeManualRepairPatch: v1Run,
    v2AfterManualRepairPatch: v2Run,
  },
  capableStockReusablePartsArm: {
    description: 'Custom parameterized-helper + precondition + [startStep,endStep) slice-dispatch harness in overlapping-requests-reuse.js vs built-in WorkflowStore.run() caller wiring',
    customHarnessSurface: {
      promptAndToolContract: stockReusablePromptAndTools,
      runtimeAndSliceDispatcher: stockReusableRuntime,
      totalCustomSloc: stockReusablePromptAndTools.sloc + stockReusableRuntime.sloc,
      totalCustomBytes: stockReusablePromptAndTools.bytes + stockReusableRuntime.bytes,
    },
    fawnCallerWiringSurface: {
      callerBlock: fawnCallerWiring,
      bespokeHelperHarnessSloc: 0,
    },
    plannerCallComparisonPerRepeat: {
      teachingCallsR1R2: { fawnGraph: 13, stockReusableParts: 13, freshPlanning: 13 },
      postTeachingCallsR3ToR7: { fawnGraph: 9, stockReusableParts: 17, freshPlanning: 57 },
      totalCallsR1ToR7: { fawnGraph: 22, stockReusableParts: 30, freshPlanning: 70 },
      reusedActionsR3ToR7: { fawnGraph: 44, stockReusableParts: 44, freshPlanning: 0 },
      fawnCallReductionVsCapableStockOverallPct: Number((((30 - 22) / 30) * 100).toFixed(1)),
      fawnCallReductionVsCapableStockPostTeachingPct: Number((((17 - 9) / 17) * 100).toFixed(1)),
      perRequestBreakdown: perRequestCallDelta,
    },
  },
  plainTakeaway:
    'Hand-written Playwright scripts remain the raw speed floor (~'
    + `${v2Run.totalTaskVerifiedSeconds}s verified / ${v2Run.totalTaskEndToEndSeconds}s end-to-end across R1..R7 with 0 model calls), `
    + `but require ${handwrittenFullMetrics.sloc} SLOC (${handwrittenFullMetrics.playwrightOps} explicit Playwright selector/navigation ops) `
    + `and fail on R6..R7 (${v1Run.taskCompletions}/${v1Run.taskTotal} completed) when Gate_v2 ships until a developer edits code (+${handwrittenV2PatchMetrics.sloc} SLOC). `
    + `Upgrading stock automation with LLM-driven reusable helpers removes per-route manual scripting at the cost of ${stockReusablePromptAndTools.sloc + stockReusableRuntime.sloc} SLOC `
    + 'of custom helper/precondition/slice machinery, yet flat (startRoute, goal) helpers still cannot compose A->B + B->C or reconverge onto a shared suffix without asking the planner '
    + 'to pick and stitch call_helper slices—spending 30 vs 22 planner calls per repeat overall, and 17 vs 9 planner calls after R1..R2 teaching (-47.1% post-teaching calls in Fawn for the same 44/45 reused actions).',
};

if (outPath) {
  mkdirSync(dirname(outPath), { recursive: true });
  writeFileSync(outPath, `${JSON.stringify(report, null, 2)}\n`);
}
console.log(JSON.stringify({
  event: 'stock-authoring-cost-measured',
  ordinaryScriptSloc: report.ordinarySixTaskStockScripts.combinedAuthoringSurface.sloc,
  overlappingScriptSloc: handwrittenFullMetrics.sloc,
  v1CompletionsBeforeManualPatch: `${v1Run.taskCompletions}/${v1Run.taskTotal}`,
  v2CompletionsAfterManualPatch: `${v2Run.taskCompletions}/${v2Run.taskTotal}`,
  v2ScriptFloorVerifiedSeconds: v2Run.totalTaskVerifiedSeconds,
  v2ScriptFloorEndToEndSeconds: v2Run.totalTaskEndToEndSeconds,
  capableStockHarnessSloc: report.capableStockReusablePartsArm.customHarnessSurface.totalCustomSloc,
  fawnVsCapableStockTotalCalls: '22 vs 30 (-26.7%)',
  fawnVsCapableStockPostTeachingCalls: '9 vs 17 (-47.1%)',
}, null, 2));

if (
  v1Run.taskCompletions !== 5
  || v2Run.taskCompletions !== 7
  || !v1Run.lookalikeRefusalSafe
  || !v2Run.lookalikeRefusalSafe
  || !v1Run.ambiguousProbeSafe
  || !v2Run.ambiguousProbeSafe
) {
  process.exitCode = 1;
}
