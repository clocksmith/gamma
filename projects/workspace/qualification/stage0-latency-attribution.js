#!/usr/bin/env node
// Stage 0 (#85): Local replay latency attribution & Protocol v3 region-delta verification ($0 LLM spend).
//
// Measures the exact per-step and per-task wall-clock breakdown on real stock Chrome across all 4
// structurally distinct sandbox sites (`procurement`, `helpdesk`, `inventory`, `compliance`) on a
// resident browser workspace (isolating workflow execution from OS Chrome process launch) and
// summarizes cold-episode journal/snapshot counts:
//   - Arm 1 (`legacy-page-scope`): `supportsRegionDeltas = false` (full-DOM `observe()` on every step, `page` scope)
//   - Arm 2 (`stage0-region-deltas`): Protocol v3 `observationScope: 'regions'` + `sinceVersion` deltas +
//     `ifCurrentVersion` current-revision observation reuse
//   - Arm 3 (`stock-helper-loop`): Raw Playwright `locator.fill`/`select`/`click` without WorkspaceService journal or `valueSettleMs`
//
// Answers #85 Stage 0's gating question: how much latency does Stage 0 remove at zero SPA risk,
// and what exact share of remaining replay latency is serial `40 ms` `valueSettleMs`?

import assert from 'node:assert/strict';
import { mkdirSync, mkdtempSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { WorkspaceService } from '../src/service.js';
import { loadServiceConfig } from '../src/config.js';
import { createPlaywrightAdapter } from '../src/adapters/playwright-adapter.js';
import { structuralLocator } from '../src/adapters/page-query.js';
import { readVerifiedJournal } from '../src/journal.js';
import { InvestigationStore } from '../src/client/investigation.js';
import { TraceDag } from '../src/client/trace-dag.js';
import { runWorkflow } from '../src/client/workflow-agent.js';
import {
  SCALING_SITES,
  buildMultiSiteScalingSpec,
  createControlledScalingPlanner,
  startMultiSiteScalingServer,
} from './multi-site-scaling-site.js';

const LIMITS = Object.freeze({ maxNodes: 160, maxEdges: 160, maxSteps: 24 });

function wrapLegacyNoRegionDeltas(service) {
  return {
    supportsRegionDeltas: false,
    observe: cmd => service.observe({
      workspaceId: cmd.workspaceId,
      ownerId: cmd.ownerId,
      ownerGeneration: cmd.ownerGeneration,
      ownerCredential: cmd.ownerCredential,
      pageId: cmd.pageId,
    }),
    outstanding: (...args) => service.outstanding(...args),
    submitAction: cmd => {
      const { observationScope: _ignored, ...rest } = cmd;
      return service.submitAction(rest);
    },
  };
}

export async function runStage0LatencyAttribution({ repeats = 3 } = {}) {
  const root = mkdtempSync(join(tmpdir(), 'gammatron-stage0-attrib-'));
  const server = await startMultiSiteScalingServer();
  const serviceConfig = loadServiceConfig(undefined, { browserChannel: 'chrome', headless: true });
  serviceConfig.observation.maxElements = 1000;
  const spec = buildMultiSiteScalingSpec();
  const siteById = new Map(SCALING_SITES.map(s => [s.siteId, s]));

  const forwardTasks = spec.orders.forward.tasks;
  // T1 + T2 teach A->B and B->C so T3 composes A->C in 0 calls across all 4 site architectures!
  const siteBundles = SCALING_SITES.map(site => ({
    site,
    t1: forwardTasks.find(t => t.siteId === site.siteId && t.stageIndex === 1),
    t2: forwardTasks.find(t => t.siteId === site.siteId && t.stageIndex === 2),
    t3: forwardTasks.find(t => t.siteId === site.siteId && t.stageIndex === 3),
  }));

  let adapter;
  let service;
  const invStore = new InvestigationStore(join(root, 'inv'));

  try {
    service = await WorkspaceService.open({
      stateDir: join(root, 'service'),
      config: serviceConfig,
      createAdapter: options => {
        adapter = createPlaywrightAdapter(options);
        return adapter;
      },
    });

    const workspaceId = 'resident-bench';
    const admin = { workspaceId, ...await service.createWorkspace({ workspaceId, scopedReads: true }) };
    await service.grantAuthorization({
      ...admin,
      grantId: 'bench-grant',
      ownerId: 'agent',
      intents: ['scaling-task'],
      actionKinds: ['navigate', 'fill', 'select', 'click'],
      targetOrigins: [server.origin],
      pageIds: ['main'],
      readRegions: null,
    });
    const owner = { workspaceId, ...await service.assignOwner({ ...admin, ownerId: 'agent' }) };
    const page = null;
    void page;

    const navigateToSession = async (sessionId, task) => {
      const obs = await service.observe(owner);
      const startUrl = server.createSession(sessionId, {
        siteId: task.siteId,
        startScreen: task.startScreen,
        query: task.startQuery,
        gateMode: task.gateMode,
        accountScope: task.accountScope,
        expectedAccountScope: task.expectedAccountScope,
        expectedGoal: task.goal,
      });
      const nav = await (await service.submitAction({
        ...owner,
        actionId: `nav-${sessionId}`,
        authorizedIntent: 'scaling-task',
        kind: 'navigate',
        target: { url: startUrl },
        observationVersion: obs.observationVersion,
      })).result;
      assert.equal(nav.outcome, 'completed');
      return adapter._page(workspaceId, 'main');
    };

    // Teach A->B and B->C once per site into each site's TraceDag.
    const dagsBySite = new Map();
    const learnedStepsBySite = new Map();
    let seq = 0;

    for (const bundle of siteBundles) {
      const { site, t1, t2, t3 } = bundle;
      const dag = new TraceDag(LIMITS);
      for (const teachTask of [t1, t2]) {
        const sessId = `teach-${site.siteId}-${teachTask.stageIndex}-${++seq}`;
        const livePage = await navigateToSession(sessId, teachTask);
        const pid = `proj-${sessId}`;
        invStore.create({ id: pid, goal: teachTask.taskPrompt });
        const planner = createControlledScalingPlanner(site, teachTask, { isStock: false });
        const res = await runWorkflow({
          dag,
          mode: 'learn',
          goal: teachTask.goal,
          accountScope: teachTask.expectedAccountScope,
          service,
          owner,
          pageId: 'main',
          intent: 'scaling-task',
          template: `scaling-${site.siteId}`,
          inputs: teachTask.inputs,
          intermediateClicks: teachTask.disclosure.intermediateClicks,
          observationLocators: [
            ...teachTask.disclosure.fields.map(f => f.locator),
            ...teachTask.disclosure.intermediateClicks,
          ],
          learnRepairs: true,
          reconvergeMidRepair: true,
          assertContext: async () => {
            const acct = await livePage.evaluate(() => document.body?.dataset?.accountScope ?? null);
            assert.equal(acct, teachTask.expectedAccountScope);
          },
          task: teachTask.taskPrompt,
          planner,
          config: { maxTurns: 18, maxInputBytes: 24000 },
          store: invStore,
          projectId: pid,
          verifyReview: () => teachTask.verify(livePage, teachTask.inputs, server, sessId),
          signal: new AbortController().signal,
        });
        assert.equal(res.completed, true, `Teach failed on ${teachTask.taskId}`);
      }
      dagsBySite.set(site.siteId, dag);
      // Also record exact step sequence for stock-helper-loop comparison on T3.
      const solved = dag.solve({ inputs: t3.inputs, goal: t3.goal });
      learnedStepsBySite.set(site.siteId, solved);
    }

    const measurements = {
      'legacy-page-scope': [],
      'stage0-region-deltas': [],
      'stock-helper-loop': [],
    };

    const journalPath = join(root, 'service', 'journal.jsonl');

    for (let rep = 0; rep < repeats; rep++) {
      for (const bundle of siteBundles) {
        const { site, t3 } = bundle;
        const dag = dagsBySite.get(site.siteId);
        const obsLocators = [
          ...t3.disclosure.fields.map(f => f.locator),
          ...t3.disclosure.intermediateClicks,
        ];

        // 1. Legacy page-scope arm (full DOM observe after every step, page scope)
        {
          const sessId = `leg-r${rep}-${site.siteId}-${++seq}`;
          const livePage = await navigateToSession(sessId, t3);
          const preJournalLen = readVerifiedJournal(journalPath).records.length;
          const pid = `proj-${sessId}`;
          invStore.create({ id: pid, goal: t3.taskPrompt });
          const t0 = performance.now();
          const res = await runWorkflow({
            dag: TraceDag.restore(dag.export(), LIMITS),
            mode: 'reuse',
            goal: t3.goal,
            accountScope: t3.expectedAccountScope,
            service: wrapLegacyNoRegionDeltas(service),
            owner,
            pageId: 'main',
            intent: 'scaling-task',
            template: `scaling-${site.siteId}`,
            inputs: t3.inputs,
            intermediateClicks: t3.disclosure.intermediateClicks,
            observationLocators: obsLocators,
            learnRepairs: false,
            reconvergeMidRepair: true,
            assertContext: async () => {
              const acct = await livePage.evaluate(() => document.body?.dataset?.accountScope ?? null);
              assert.equal(acct, t3.expectedAccountScope);
            },
            task: t3.taskPrompt,
            planner: null,
            config: { maxTurns: 18, maxInputBytes: 24000 },
            store: invStore,
            projectId: pid,
            verifyReview: () => t3.verify(livePage, t3.inputs, server, sessId),
            signal: new AbortController().signal,
          });
          const wallMs = performance.now() - t0;
          assert.equal(res.completed, true);
          assert.equal(res.modelCalls, 0);
          const newRecords = readVerifiedJournal(journalPath).records.slice(preJournalLen);
          const obsRecorded = newRecords.filter(r => r.type === 'observation-recorded').length;
          const outcomes = newRecords.filter(r => r.type === 'action-outcome');
          const sumProf = key => outcomes.reduce((s, r) => s + (r.body.evidence?.dispatchProfileMs?.[key] ?? 0), 0);
          measurements['legacy-page-scope'].push({
            siteId: site.siteId,
            repeat: rep,
            steps: res.cacheSteps,
            wallMs: Number(wallMs.toFixed(3)),
            journalRecordsAdded: newRecords.length,
            observationsRecorded: obsRecorded,
            dispatchCheckMs: Number(sumProf('dispatchCheckMs').toFixed(3)),
            browserExecuteMs: Number(sumProf('browserExecuteMs').toFixed(3)),
            valueSettleMs: Number(sumProf('valueSettleMs').toFixed(3)),
            postSnapshotMs: Number(sumProf('postSnapshotMs').toFixed(3)),
            journalBeforeOutcomeMs: Number(sumProf('journalBeforeOutcomeMs').toFixed(3)),
          });
        }

        // 2. Stage 0 region-deltas + current-revision reuse arm
        {
          const sessId = `st0-r${rep}-${site.siteId}-${++seq}`;
          const livePage = await navigateToSession(sessId, t3);
          const preJournalLen = readVerifiedJournal(journalPath).records.length;
          const pid = `proj-${sessId}`;
          invStore.create({ id: pid, goal: t3.taskPrompt });
          const t0 = performance.now();
          const res = await runWorkflow({
            dag: TraceDag.restore(dag.export(), LIMITS),
            mode: 'reuse',
            goal: t3.goal,
            accountScope: t3.expectedAccountScope,
            service,
            owner,
            pageId: 'main',
            intent: 'scaling-task',
            template: `scaling-${site.siteId}`,
            inputs: t3.inputs,
            intermediateClicks: t3.disclosure.intermediateClicks,
            observationLocators: obsLocators,
            learnRepairs: false,
            reconvergeMidRepair: true,
            assertContext: async () => {
              const acct = await livePage.evaluate(() => document.body?.dataset?.accountScope ?? null);
              assert.equal(acct, t3.expectedAccountScope);
            },
            task: t3.taskPrompt,
            planner: null,
            config: { maxTurns: 18, maxInputBytes: 24000 },
            store: invStore,
            projectId: pid,
            verifyReview: () => t3.verify(livePage, t3.inputs, server, sessId),
            signal: new AbortController().signal,
          });
          const wallMs = performance.now() - t0;
          assert.equal(res.completed, true);
          assert.equal(res.modelCalls, 0);
          const newRecords = readVerifiedJournal(journalPath).records.slice(preJournalLen);
          const obsRecorded = newRecords.filter(r => r.type === 'observation-recorded').length;
          measurements['stage0-region-deltas'].push({
            siteId: site.siteId,
            repeat: rep,
            steps: res.cacheSteps,
            wallMs: Number(wallMs.toFixed(3)),
            journalRecordsAdded: newRecords.length,
            observationsRecorded: obsRecorded,
            regionScopedActions: res.stage0Profile?.regionScopedActions ?? 0,
            currentRevisionReuses: res.stage0Profile?.currentRevisionReuses ?? 0,
            sinceVersionDeltaChecks: res.stage0Profile?.sinceVersionDeltaChecks ?? 0,
            sinceVersionUnchangedRegions: res.stage0Profile?.sinceVersionUnchangedRegions ?? 0,
            dispatchCheckMs: res.stage0Profile?.dispatchCheckMs ?? 0,
            browserExecuteMs: res.stage0Profile?.browserExecuteMs ?? 0,
            valueSettleMs: res.stage0Profile?.valueSettleMs ?? 0,
            postSnapshotMs: res.stage0Profile?.postSnapshotMs ?? 0,
            journalBeforeOutcomeMs: res.stage0Profile?.journalBeforeOutcomeMs ?? 0,
          });
        }

        // 3. Stock helper raw Playwright loop (no WorkspaceService journal, no 40ms valueSettleMs)
        {
          const sessId = `stk-r${rep}-${site.siteId}-${++seq}`;
          const livePage = await navigateToSession(sessId, t3);
          const t0 = performance.now();
          const acct = await livePage.evaluate(() => document.body?.dataset?.accountScope ?? null);
          assert.equal(acct, t3.expectedAccountScope);
          // Execute exact T3 steps on livePage directly
          for (const f of site.entryFields) {
            const sel = `#${f.id}`;
            if (f.kind === 'fill') await livePage.locator(sel).fill(String(t3.inputs[f.slot]));
            else await livePage.locator(sel).selectOption({ value: String(t3.inputs[f.slot]) });
          }
          await livePage.getByRole('button', { name: site.labels.searchButton }).click();
          await livePage.getByRole('button', { name: site.labels.openBriefButton }).click();
          await livePage.getByRole('button', { name: site.labels.goPrimaryButton }).click();
          await livePage.getByRole('button', { name: site.labels.gateV1Button }).click();
          for (const f of site.primaryFields) {
            const sel = `#${f.id}`;
            if (f.kind === 'fill') await livePage.locator(sel).fill(String(t3.inputs[f.slot]));
            else await livePage.locator(sel).selectOption({ value: String(t3.inputs[f.slot]) });
          }
          await livePage.getByRole('button', { name: site.labels.primaryReviewButton }).click();
          const ver = await t3.verify(livePage, t3.inputs, server, sessId);
          assert.equal(ver.completed, true);
          const wallMs = performance.now() - t0;
          measurements['stock-helper-loop'].push({
            siteId: site.siteId,
            repeat: rep,
            steps: site.entryFields.length + site.primaryFields.length + 5,
            wallMs: Number(wallMs.toFixed(3)),
            journalRecordsAdded: 0,
            observationsRecorded: 0,
            valueSettleMs: 0,
          });
        }
      }
    }
    void siteById;

    const mean = (arr, key) => Number((arr.reduce((s, x) => s + (x[key] ?? 0), 0) / arr.length).toFixed(3));
    const legRows = measurements['legacy-page-scope'];
    const st0Rows = measurements['stage0-region-deltas'];
    const stkRows = measurements['stock-helper-loop'];

    const legWall = mean(legRows, 'wallMs');
    const st0Wall = mean(st0Rows, 'wallMs');
    const stkWall = mean(stkRows, 'wallMs');
    const st0Settle = mean(st0Rows, 'valueSettleMs');
    const st0ShareSettle = Number((st0Settle / st0Wall).toFixed(4));

    return {
      schema: 'gammatron.stage0-latency-attribution/v1',
      llmSpendUsd: 0,
      repeats,
      sitesCount: SCALING_SITES.length,
      episodesPerArm: st0Rows.length,
      residentReplayMeansMs: {
        legacyPageScope: {
          meanWallMs: legWall,
          meanSteps: mean(legRows, 'steps'),
          meanObservationsRecorded: mean(legRows, 'observationsRecorded'),
          meanJournalRecordsAdded: mean(legRows, 'journalRecordsAdded'),
          meanDispatchCheckMs: mean(legRows, 'dispatchCheckMs'),
          meanBrowserExecuteMs: mean(legRows, 'browserExecuteMs'),
          meanValueSettleMs: mean(legRows, 'valueSettleMs'),
          meanPostSnapshotMs: mean(legRows, 'postSnapshotMs'),
          meanJournalBeforeOutcomeMs: mean(legRows, 'journalBeforeOutcomeMs'),
        },
        stage0RegionDeltas: {
          meanWallMs: st0Wall,
          meanSteps: mean(st0Rows, 'steps'),
          meanObservationsRecorded: mean(st0Rows, 'observationsRecorded'),
          meanJournalRecordsAdded: mean(st0Rows, 'journalRecordsAdded'),
          meanRegionScopedActions: mean(st0Rows, 'regionScopedActions'),
          meanCurrentRevisionReuses: mean(st0Rows, 'currentRevisionReuses'),
          meanSinceVersionDeltaChecks: mean(st0Rows, 'sinceVersionDeltaChecks'),
          meanSinceVersionUnchangedRegions: mean(st0Rows, 'sinceVersionUnchangedRegions'),
          meanDispatchCheckMs: mean(st0Rows, 'dispatchCheckMs'),
          meanBrowserExecuteMs: mean(st0Rows, 'browserExecuteMs'),
          meanValueSettleMs: st0Settle,
          meanPostSnapshotMs: mean(st0Rows, 'postSnapshotMs'),
          meanJournalBeforeOutcomeMs: mean(st0Rows, 'journalBeforeOutcomeMs'),
          valueSettleShareOfReplayWall: st0ShareSettle,
        },
        stockHelperLoopNoJournalNoSettle: {
          meanWallMs: stkWall,
          meanSteps: mean(stkRows, 'steps'),
        },
      },
      deltas: {
        wallMsSavedByStage0: Number((legWall - st0Wall).toFixed(3)),
        wallPctSavedByStage0: Number((((legWall - st0Wall) / legWall) * 100).toFixed(2)),
        observationsSavedPerTask: Number((mean(legRows, 'observationsRecorded') - mean(st0Rows, 'observationsRecorded')).toFixed(2)),
        remainingGapVsRawPlaywrightMs: Number((st0Wall - stkWall).toFixed(3)),
        serialValueSettleBottleneckConfirmed: st0Settle > (st0Wall - stkWall) * 0.45,
      },
      rows: measurements,
    };
  } finally {
    invStore.close();
    await service?.close();
    await server.close();
    rmSync(root, { recursive: true, force: true });
  }
}

const isDirect = Boolean(process.argv[1]) && resolve(process.argv[1]) === fileURLToPath(import.meta.url);
if (isDirect) {
  const receipt = await runStage0LatencyAttribution({ repeats: 3 });
  const outArg = process.argv[2];
  if (outArg) {
    const outPath = resolve(outArg);
    mkdirSync(dirname(outPath), { recursive: true });
    writeFileSync(outPath, `${JSON.stringify(receipt, null, 2)}\n`);
  }
  const { rows: _omit, ...summary } = receipt;
  console.log(JSON.stringify(summary, null, 2));
}
