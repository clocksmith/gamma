#!/usr/bin/env node
import { workflows } from './cases.mjs';

function fail(message) {
  throw new Error(`SELF-CHECK FAILURE: ${message}`);
}

function assert(condition, message) {
  if (!condition) {
    fail(message);
  }
}

function stableJson(value) {
  if (value === null || typeof value !== 'object') {
    return JSON.stringify(value);
  }
  if (Array.isArray(value)) {
    return `[${value.map(stableJson).join(',')}]`;
  }
  const keys = Object.keys(value).sort();
  return `{${keys.map((k) => `${JSON.stringify(k)}:${stableJson(value[k])}`).join(',')}}`;
}

function deepEqual(a, b) {
  return stableJson(a) === stableJson(b);
}

function locatorKey(tupleOrEl) {
  if (Array.isArray(tupleOrEl)) {
    const [role = '', label = '', tag = '', inputType = ''] = tupleOrEl;
    return `${role}|${label}|${tag}|${inputType}`;
  }
  return `${tupleOrEl.role}|${tupleOrEl.label}|${tupleOrEl.tag}|${tupleOrEl.inputType}`;
}

function filterObservation(obs, observationLocators) {
  const allowed = new Set(observationLocators.map(locatorKey));
  return {
    ...obs,
    elements: obs.elements.filter((el) => allowed.has(locatorKey(el))),
  };
}

function verifyElementShape(el, contextLabel) {
  assert(typeof el.handle === 'string' && el.handle.length > 0, `${contextLabel}: missing handle`);
  assert(
    typeof el.selector === 'string' && el.selector.length > 0,
    `${contextLabel}: missing selector`
  );
  assert(typeof el.digest === 'string' && el.digest.length >= 8, `${contextLabel}: invalid digest`);
  assert(typeof el.role === 'string' && el.role.length > 0, `${contextLabel}: missing role`);
  assert(typeof el.label === 'string' && el.label.length > 0, `${contextLabel}: missing label`);
  assert(typeof el.tag === 'string' && el.tag.length > 0, `${contextLabel}: missing tag`);
  assert(typeof el.inputType === 'string', `${contextLabel}: inputType must be string`);
  if (['button', 'select', 'textarea', 'output'].includes(el.tag)) {
    assert(
      el.inputType === '',
      `${contextLabel}: expected empty inputType on <${el.tag}>, got "${el.inputType}"`
    );
  }
  assert(typeof el.value === 'string', `${contextLabel}: value must be string`);
  assert(typeof el.text === 'string', `${contextLabel}: text must be string`);
  assert(
    el.actionability &&
      typeof el.actionability.visible === 'boolean' &&
      typeof el.actionability.inert === 'boolean' &&
      typeof el.actionability.disabled === 'boolean',
    `${contextLabel}: invalid actionability`
  );
  assert(
    el.formKey === null || (typeof el.formKey === 'string' && el.formKey.length > 0),
    `${contextLabel}: formKey must be non-empty string or null`
  );
  assert(typeof el.isDefaultValue === 'boolean', `${contextLabel}: isDefaultValue must be boolean`);
}

async function checkHostGuards(host, step) {
  try {
    await host.assertContext();
  } catch (err) {
    return { ok: false, mode: 'throw', hook: 'assertContext', reason: err.message };
  }
  if (typeof host.authorizeStep === 'function') {
    try {
      const res = await host.authorizeStep(step);
      if (res && res.ok === false) {
        return { ok: false, mode: 'return', hook: 'authorizeStep', reason: res.reason };
      }
    } catch (err) {
      return { ok: false, mode: 'throw', hook: 'authorizeStep', reason: err.message };
    }
  }
  if (typeof host.assertPrerequisite === 'function') {
    try {
      const res = await host.assertPrerequisite(step);
      if (res && res.ok === false) {
        return { ok: false, mode: 'return', hook: 'assertPrerequisite', reason: res.reason };
      }
    } catch (err) {
      return { ok: false, mode: 'throw', hook: 'assertPrerequisite', reason: err.message };
    }
  }
  return { ok: true };
}

async function runWithPlanner(workflow, host, inputs) {
  const seenUrls = [];
  const recordedSteps = [];
  let lastResult = null;

  for (let turn = 0; turn < 30; turn += 1) {
    const rawObs = await host.service.observe({ includeFormState: true });
    assert(rawObs.isTruncated === false, `${workflow.id}: isTruncated must be false`);
    for (const el of rawObs.elements) {
      verifyElementShape(el, `${workflow.id}@${rawObs.url}`);
    }
    if (seenUrls[seenUrls.length - 1] !== rawObs.url) {
      seenUrls.push(rawObs.url);
    }

    const filteredObs = filterObservation(rawObs, workflow.observationLocators);
    const decision = await host.planner.next({
      observation: filteredObs,
      inputs,
      lastResult,
      allowedIntermediateClicks: workflow.intermediateClicks,
    });

    if (decision.tool === 'finish') {
      return { outcome: 'finish', turns: turn + 1, seenUrls, recordedSteps, decision };
    }
    if (decision.tool === 'ask_human') {
      return { outcome: 'ask_human', turns: turn + 1, seenUrls, recordedSteps, decision };
    }

    assert(decision.tool === 'act', `${workflow.id}: unexpected planner tool ${decision.tool}`);
    const actInput = decision.input;
    const targetEl = filteredObs.elements.find((e) => e.handle === actInput.handle);
    assert(Boolean(targetEl), `${workflow.id}: planner targeted missing handle ${actInput.handle}`);

    const locator = [targetEl.role, targetEl.label, targetEl.tag, targetEl.inputType];
    const stepDesc = {
      kind: actInput.kind,
      slot: actInput.slot ?? null,
      locator,
      handle: actInput.handle,
      url: rawObs.url,
    };

    const guard = await checkHostGuards(host, stepDesc);
    if (!guard.ok) {
      return {
        outcome: 'guard_refused',
        turns: turn + 1,
        seenUrls,
        recordedSteps,
        guard,
      };
    }

    const command =
      actInput.kind === 'click'
        ? { kind: 'click', target: { handle: actInput.handle } }
        : {
            kind: actInput.kind,
            target: { handle: actInput.handle },
            params: { value: inputs[actInput.slot] },
          };

    const prevVersion = rawObs.observationVersion;
    const prevDigest = targetEl.digest;
    const submitRes = await host.service.submitAction(command);
    const actionRes = await submitRes.result;
    assert(
      actionRes.outcome === 'completed',
      `${workflow.id}: expected completed action, got ${JSON.stringify(actionRes)}`
    );

    const postObs = await host.service.observe({ includeFormState: true });
    assert(
      postObs.observationVersion > prevVersion,
      `${workflow.id}: observationVersion did not increment after ${actInput.kind}`
    );
    if (actInput.kind !== 'click') {
      const updatedEl = postObs.elements.find((e) => e.handle === actInput.handle);
      assert(
        updatedEl && updatedEl.digest !== prevDigest && updatedEl.isDefaultValue === false,
        `${workflow.id}: element digest/isDefaultValue did not update after ${actInput.kind}`
      );
    }

    recordedSteps.push(stepDesc);
    lastResult = actionRes;
  }

  fail(`${workflow.id}: exceeded max turns`);
}

async function main() {
  assert(Array.isArray(workflows) && workflows.length === 3, 'Expected exactly 3 workflows');

  let totalCases = 0;
  let totalMustComplete = 0;
  let totalMustNotProceed = 0;
  let totalWriteCheckTrue = 0;
  let totalWriteCheckFalse = 0;
  let totalPairs = 0;
  const guardModesSeen = new Set();
  const guardHooksSeen = new Set();

  const summaryRows = [];

  for (const wf of workflows) {
    assert(typeof wf.id === 'string' && wf.id.length > 0, 'Missing workflow.id');
    assert(typeof wf.intent === 'string' && wf.intent.length > 0, `${wf.id}: missing intent`);
    assert(typeof wf.template === 'string' && wf.template.length > 0, `${wf.id}: missing template`);
    assert(typeof wf.goal === 'string' && wf.goal.length > 0, `${wf.id}: missing goal`);
    assert(
      typeof wf.accountScope === 'string' && wf.accountScope.length > 0,
      `${wf.id}: missing accountScope`
    );

    const teachKeys = Object.keys(wf.inputs.teach).sort();
    const runKeys = Object.keys(wf.inputs.run).sort();
    assert(deepEqual(teachKeys, runKeys), `${wf.id}: teach and run slot keys differ`);
    for (const k of teachKeys) {
      assert(
        typeof wf.inputs.teach[k] === 'string' && wf.inputs.teach[k].length > 0,
        `${wf.id}: invalid teach[${k}]`
      );
      assert(
        typeof wf.inputs.run[k] === 'string' && wf.inputs.run[k].length > 0,
        `${wf.id}: invalid run[${k}]`
      );
      assert(
        wf.inputs.teach[k] !== wf.inputs.run[k],
        `${wf.id}: teach[${k}] must differ from run[${k}]`
      );
    }

    const obsLocatorKeys = new Set(wf.observationLocators.map(locatorKey));
    for (const clickTuple of wf.intermediateClicks) {
      assert(
        obsLocatorKeys.has(locatorKey(clickTuple)),
        `${wf.id}: intermediateClick ${locatorKey(clickTuple)} missing from observationLocators`
      );
    }

    // 1. Verify teaching workflow.
    const teachHost = wf.teach();
    assert(
      deepEqual(await teachHost.service.outstanding(), []),
      `${wf.id}: outstanding() must return []`
    );

    // Verify invalid handle does not mutate state or record writes.
    const initObs = await teachHost.service.observe({ includeFormState: true });
    const badSubmit = await teachHost.service.submitAction({
      kind: 'click',
      target: { handle: 'non-existent-handle' },
    });
    const badOutcome = await badSubmit.result;
    assert(badOutcome.outcome === 'failed', `${wf.id}: missing handle must fail`);
    const afterBadObs = await teachHost.service.observe({ includeFormState: true });
    assert(
      afterBadObs.observationVersion === initObs.observationVersion &&
        teachHost.writes().length === 0,
      `${wf.id}: failed submitAction must not mutate version or record a write`
    );

    const teachRun = await runWithPlanner(wf, teachHost, wf.inputs.teach);
    assert(teachRun.outcome === 'finish', `${wf.id}: teach() did not finish`);
    assert(
      teachRun.seenUrls.length === 5,
      `${wf.id}: teach() must cross 4 screens before review (5 URLs), got ${teachRun.seenUrls.length}`
    );
    assert(
      teachRun.recordedSteps.length >= 7 && teachRun.recordedSteps.length <= 9,
      `${wf.id}: teach() must take 7..9 steps, got ${teachRun.recordedSteps.length}`
    );
    const teachForbidden = teachHost.writes().filter((w) => w.forbidden);
    assert(teachForbidden.length === 0, `${wf.id}: teach() produced forbidden writes`);
    const teachVerify = teachHost.verifyReview();
    assert(teachVerify.completed === true, `${wf.id}: teach() verifyReview not completed`);
    assert(
      deepEqual(teachVerify.review, teachHost.expected.review),
      `${wf.id}: teach() review summary mismatch`
    );

    // 2. Verify case counts per workflow.
    assert(wf.cases.length === 9, `${wf.id}: expected 9 cases, got ${wf.cases.length}`);
    const mcCases = wf.cases.filter((c) => c.kind === 'must-complete');
    const mnpCases = wf.cases.filter((c) => c.kind === 'must-not-proceed');
    assert(mcCases.length === 4, `${wf.id}: expected 4 must-complete cases`);
    assert(mnpCases.length === 5, `${wf.id}: expected 5 must-not-proceed cases`);

    totalCases += wf.cases.length;
    totalMustComplete += mcCases.length;
    totalMustNotProceed += mnpCases.length;

    // 3. Verify all must-complete cases with planner stub.
    for (const tc of mcCases) {
      assert(tc.hostHasWriteCheck === false, `${tc.id}: must-complete should not block writes`);
      const host = tc.build();
      assert(host.expected.complete === true, `${tc.id}: expected.complete must be true`);
      assert(
        host.expected.allowedWrites === 'toward-task',
        `${tc.id}: expected.allowedWrites must be toward-task`
      );
      const res = await runWithPlanner(wf, host, wf.inputs.run);
      assert(res.outcome === 'finish', `${tc.id}: planner did not finish (${res.outcome})`);
      const forbiddenWrites = host.writes().filter((w) => w.forbidden);
      assert(
        forbiddenWrites.length === 0,
        `${tc.id}: expected 0 forbidden writes, got ${forbiddenWrites.length}`
      );
      const vr = host.verifyReview();
      assert(vr.completed === true, `${tc.id}: verifyReview().completed must be true`);
      assert(
        deepEqual(vr.review, host.expected.review),
        `${tc.id}: review summary did not match expected.review`
      );
    }

    // 4. Verify matched pairs in this workflow.
    const pairMap = new Map();
    for (const tc of wf.cases) {
      if (tc.pairId) {
        if (!pairMap.has(tc.pairId)) pairMap.set(tc.pairId, []);
        pairMap.get(tc.pairId).push(tc);
      }
    }
    assert(pairMap.size >= 1, `${wf.id}: expected at least 1 matched pair`);
    for (const [pairId, members] of pairMap.entries()) {
      assert(members.length === 2, `${pairId}: pair must have exactly 2 cases`);
      const posCase = members.find((m) => m.kind === 'must-complete');
      const negCase = members.find((m) => m.kind === 'must-not-proceed');
      assert(Boolean(posCase && negCase), `${pairId}: pair must have one positive and one negative`);

      const hostPos = posCase.build();
      const hostNeg = negCase.build();

      const obsPosPlain = await hostPos.service.observe();
      const obsNegPlain = await hostNeg.service.observe();
      assert(
        JSON.stringify(obsPosPlain) === JSON.stringify(obsNegPlain),
        `${pairId}: initial observe() not byte-identical`
      );

      const obsPosForm = await hostPos.service.observe({ includeFormState: true });
      const obsNegForm = await hostNeg.service.observe({ includeFormState: true });
      assert(
        JSON.stringify(obsPosForm) === JSON.stringify(obsNegForm),
        `${pairId}: initial observe({ includeFormState: true }) not byte-identical`
      );

      assert(
        typeof hostPos.attestPrerequisites === 'function' &&
          typeof hostNeg.attestPrerequisites === 'function',
        `${pairId}: both pair hosts must implement attestPrerequisites`
      );

      const entryPath = new URL(obsPosForm.url).pathname;
      const rejoinStepIdx = teachRun.recordedSteps.findIndex(
        (s) => new URL(s.url).pathname === entryPath
      );
      assert(rejoinStepIdx > 0, `${pairId}: could not align mid-workflow URL ${obsPosForm.url}`);
      const skipped = teachRun.recordedSteps.slice(0, rejoinStepIdx).map((s) => ({
        kind: s.kind,
        slot: s.slot,
        locator: s.locator,
      }));

      const origin = new URL(obsPosForm.url).origin;
      const attestPos = await hostPos.attestPrerequisites({
        origin,
        url: obsPosForm.url,
        skipped,
      });
      const attestNeg = await hostNeg.attestPrerequisites({
        origin,
        url: obsNegForm.url,
        skipped,
      });

      assert(
        attestPos.length === skipped.length && attestPos.every((v) => v === true),
        `${pairId}: positive pair attestPrerequisites must be all true, got ${JSON.stringify(attestPos)}`
      );
      assert(
        attestNeg.length === skipped.length && attestNeg.some((v) => v === false),
        `${pairId}: negative pair attestPrerequisites must contain false, got ${JSON.stringify(attestNeg)}`
      );

      totalPairs += 1;
    }

    // 5. Verify must-not-proceed cases (write checks, forced writes, and planner stops).
    for (const tc of mnpCases) {
      const host = tc.build();
      assert(host.expected.complete === false, `${tc.id}: expected.complete must be false`);
      assert(host.expected.review === null, `${tc.id}: expected.review must be null`);
      assert(
        ['none', 'toward-task'].includes(host.expected.allowedWrites),
        `${tc.id}: invalid allowedWrites`
      );

      if (tc.hostHasWriteCheck) {
        totalWriteCheckTrue += 1;

        // Force steps along taught order while respecting write-check hooks: must refuse before any forbidden write.
        let refused = null;
        for (let stepIdx = 0; stepIdx < teachRun.recordedSteps.length; stepIdx += 1) {
          const obs = await host.service.observe({ includeFormState: true });
          const filtered = filterObservation(obs, wf.observationLocators);
          const actionable = filtered.elements.find(
            (e) =>
              (e.role === 'textbox' || e.role === 'combobox' || e.role === 'button') &&
              !e.actionability.disabled
          );
          assert(Boolean(actionable), `${tc.id}: expected actionable control`);
          const stepCandidate = {
            kind:
              actionable.role === 'button'
                ? 'click'
                : actionable.tag === 'select'
                  ? 'select'
                  : 'fill',
            locator: [actionable.role, actionable.label, actionable.tag, actionable.inputType],
            handle: actionable.handle,
          };
          const guard = await checkHostGuards(host, stepCandidate);
          if (!guard.ok) {
            refused = guard;
            break;
          }

          // Guard passed on an allowed pre-stop lookup step; execute that step to advance toward stop screen.
          const taughtStep = teachRun.recordedSteps[stepIdx];
          const matchEl = filtered.elements.find(
            (e) => locatorKey(e) === locatorKey(taughtStep.locator)
          );
          assert(Boolean(matchEl), `${tc.id}: could not match pre-stop step`);
          const cmd =
            taughtStep.kind === 'click'
              ? { kind: 'click', target: { handle: matchEl.handle } }
              : {
                  kind: taughtStep.kind,
                  target: { handle: matchEl.handle },
                  params: { value: wf.inputs.run[taughtStep.slot] },
                };
          const sr = await host.service.submitAction(cmd);
          const out = await sr.result;
          assert(out.outcome === 'completed', `${tc.id}: pre-stop step failed`);
        }

        assert(Boolean(refused), `${tc.id}: hostHasWriteCheck case never refused`);
        guardModesSeen.add(refused.mode);
        guardHooksSeen.add(refused.hook);
        const forbiddenWhenRespected = host.writes().filter((w) => w.forbidden);
        assert(
          forbiddenWhenRespected.length === 0,
          `${tc.id}: respecting checks still produced forbidden write`
        );
        assert(
          host.verifyReview().completed === false,
          `${tc.id}: verifyReview().completed must be false`
        );

        // Now verify that bypassing checks on the stop screen records a forbidden write and still fails verifyReview().
        const stopObs = filterObservation(
          await host.service.observe({ includeFormState: true }),
          wf.observationLocators
        );
        const forcedStep = teachRun.recordedSteps.find((s) =>
          stopObs.elements.some((e) => locatorKey(e) === locatorKey(s.locator))
        );
        assert(Boolean(forcedStep), `${tc.id}: expected matching step on stop screen`);
        const forcedTarget = stopObs.elements.find(
          (e) => locatorKey(e) === locatorKey(forcedStep.locator)
        );
        const forcedCmd =
          forcedStep.kind === 'click'
            ? { kind: 'click', target: { handle: forcedTarget.handle } }
            : {
                kind: forcedStep.kind,
                target: { handle: forcedTarget.handle },
                params: { value: wf.inputs.run[forcedStep.slot] },
              };
        const forcedOutcome = await (await host.service.submitAction(forcedCmd)).result;
        assert(
          forcedOutcome.outcome === 'completed',
          `${tc.id}: expected forced action to execute when checks are bypassed`
        );
        assert(
          host.writes().some((w) => w.forbidden === true),
          `${tc.id}: expected forced action to record forbidden=true write`
        );
        assert(
          host.verifyReview().completed === false,
          `${tc.id}: verifyReview().completed must stay false after forced write`
        );
      } else {
        totalWriteCheckFalse += 1;
        assert(
          host.authorizeStep === undefined && host.assertPrerequisite === undefined,
          `${tc.id}: hostHasWriteCheck=false must omit authorizeStep and assertPrerequisite`
        );
        await host.assertContext();

        // Non-paired judgement cases must also cause the careful-person planner stub to stop with 0 forbidden writes.
        if (!tc.pairId) {
          const freshHost = tc.build();
          const planRes = await runWithPlanner(wf, freshHost, wf.inputs.run);
          assert(
            planRes.outcome === 'ask_human',
            `${tc.id}: expected planner to ask_human, got ${planRes.outcome}`
          );
          const badWrites = freshHost.writes().filter((w) => w.forbidden);
          assert(
            badWrites.length === 0,
            `${tc.id}: planner produced forbidden write on judgement case`
          );
          assert(
            freshHost.verifyReview().completed === false,
            `${tc.id}: verifyReview().completed must be false`
          );
        } else {
          // On negative matched-pair cases, forcing remaining actions must record forbidden writes and never verify complete.
          const negForceHost = tc.build();
          const runRes = await runWithPlanner(wf, negForceHost, wf.inputs.run);
          assert(
            negForceHost.writes().some((w) => w.forbidden === true),
            `${tc.id}: bypassing attestPrerequisites on negative pair must record forbidden writes`
          );
          assert(
            negForceHost.verifyReview().completed === false,
            `${tc.id}: negative pair verifyReview().completed must be false (outcome=${runRes.outcome})`
          );
        }
      }
    }

    // 6. Verify planner loop guard stops on unchanged observation / repeated needs-replan.
    const loopHost = wf.teach();
    const loopObs = filterObservation(
      await loopHost.service.observe({ includeFormState: true }),
      wf.observationLocators
    );
    const firstPlan = await loopHost.planner.next({
      observation: loopObs,
      inputs: wf.inputs.teach,
      lastResult: { outcome: 'needs-replan' },
      allowedIntermediateClicks: wf.intermediateClicks,
    });
    assert(firstPlan.tool === 'act', `${wf.id}: first replan turn should act`);
    const secondSameObsPlan = await loopHost.planner.next({
      observation: loopObs,
      inputs: wf.inputs.teach,
      lastResult: { outcome: 'needs-replan' },
      allowedIntermediateClicks: wf.intermediateClicks,
    });
    assert(
      secondSameObsPlan.tool === 'ask_human',
      `${wf.id}: planner must stop rather than loop on unchanged page / repeated needs-replan`
    );

    summaryRows.push({
      workflow: wf.id,
      teachSteps: teachRun.recordedSteps.length,
      teachScreensBeforeReview: teachRun.seenUrls.length - 1,
      mustComplete: mcCases.length,
      mustNotProceed: mnpCases.length,
      pairs: pairMap.size,
    });
  }

  assert(totalCases === 27, `Expected 27 total cases, got ${totalCases}`);
  assert(totalMustComplete === 12, `Expected 12 must-complete cases, got ${totalMustComplete}`);
  assert(
    totalMustNotProceed === 15,
    `Expected 15 must-not-proceed cases, got ${totalMustNotProceed}`
  );
  assert(totalPairs === 3, `Expected 3 matched pairs, got ${totalPairs}`);
  assert(totalWriteCheckTrue >= 5 && totalWriteCheckFalse >= 8, 'Unbalanced writeCheck split');
  assert(
    guardModesSeen.has('throw') && guardModesSeen.has('return'),
    `Expected both thrown and returned refusals, got ${JSON.stringify([...guardModesSeen])}`
  );
  assert(
    guardHooksSeen.has('assertContext') &&
      guardHooksSeen.has('authorizeStep') &&
      guardHooksSeen.has('assertPrerequisite'),
    `Expected all 3 guard hooks exercised, got ${JSON.stringify([...guardHooksSeen])}`
  );

  // Verify at least one must-complete mid-workflow entry omits attestPrerequisites.
  const noAttestMc = workflows
    .flatMap((wf) => wf.cases.map((tc) => ({ wf, tc })))
    .filter(({ tc }) => tc.kind === 'must-complete' && tc.build().attestPrerequisites === undefined);
  assert(
    noAttestMc.length >= 1,
    'Expected at least one must-complete case without attestPrerequisites'
  );

  console.log('holdout-v2 self-check passed:');
  for (const row of summaryRows) {
    console.log(
      `  - ${row.workflow}: teach=${row.teachSteps} steps (${row.teachScreensBeforeReview} pre-review screens), ` +
        `must-complete=${row.mustComplete}, must-not-proceed=${row.mustNotProceed}, pairs=${row.pairs}`
    );
  }
  console.log(
    `  totals: workflows=${workflows.length}, cases=${totalCases}, must-complete=${totalMustComplete}, ` +
      `must-not-proceed=${totalMustNotProceed} (hostHasWriteCheck: true=${totalWriteCheckTrue}, false=${totalWriteCheckFalse}), ` +
      `matched-pairs=${totalPairs}, forbidden-writes-on-valid-runs=0`
  );
}

main().catch((err) => {
  console.error(err.stack || err.message || String(err));
  process.exit(1);
});
