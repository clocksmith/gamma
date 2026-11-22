import assert from 'node:assert/strict';
import { readFileSync, existsSync } from 'node:fs';
import { workflows } from './cases.mjs';

function locKey(loc) {
  return `${loc[0]}||${loc[1]}||${loc[2]}||${loc[3] ?? ''}`;
}

function projectObservationForPlanner(obs) {
  return {
    elements: obs.elements.map((el) => ({
      handle: el.handle,
      role: el.role,
      label: el.label,
      inputType: el.inputType,
      tag: el.tag,
      value: el.value,
      text: el.text,
    })),
  };
}

function verifyElementSchema(obs, locatorSet, contextLabel) {
  assert.equal(typeof obs.url, 'string', `${contextLabel}: url must be string`);
  assert.ok(obs.url.startsWith('https://'), `${contextLabel}: url must be https`);
  assert.equal(typeof obs.text, 'string', `${contextLabel}: text must be string`);
  assert.ok(obs.text.length > 0, `${contextLabel}: text must be non-empty`);
  assert.equal(typeof obs.observationVersion, 'number', `${contextLabel}: observationVersion`);
  assert.equal(obs.isTruncated, false, `${contextLabel}: isTruncated must be false`);
  assert.ok(Array.isArray(obs.elements) && obs.elements.length > 0, `${contextLabel}: elements`);

  for (const el of obs.elements) {
    assert.equal(typeof el.role, 'string');
    assert.equal(typeof el.label, 'string');
    assert.ok(el.label.length > 0);
    assert.equal(typeof el.tag, 'string');
    assert.equal(typeof el.inputType, 'string');
    assert.equal(typeof el.handle, 'string');
    assert.ok(el.handle.length > 0);
    assert.equal(typeof el.selector, 'string');
    assert.ok(el.selector.length > 0);
    assert.equal(typeof el.digest, 'string');
    assert.ok(el.digest.length > 0);
    assert.equal(typeof el.value, 'string');
    assert.equal(typeof el.text, 'string');
    assert.deepEqual(el.actionability, { visible: true, inert: false, disabled: false });
    assert.equal(typeof el.isDefaultValue, 'boolean');

    if (el.tag === 'button' || el.tag === 'select' || el.tag === 'textarea' || el.tag === 'output') {
      assert.equal(el.inputType, '', `${contextLabel}: ${el.tag} must have empty inputType`);
    }
    if (el.tag === 'button' || el.tag === 'output') {
      assert.equal(el.formKey, null, `${contextLabel}: ${el.tag} must have null formKey`);
    } else {
      assert.equal(typeof el.formKey, 'string', `${contextLabel}: form control formKey`);
      assert.ok(el.formKey.length > 0);
    }

    const tupleKey = locKey([el.role, el.label, el.tag, el.inputType]);
    assert.ok(
      locatorSet.has(tupleKey),
      `${contextLabel}: element locator ${tupleKey} missing from wf.observationLocators`
    );
  }
}

async function runPlannerTrace(wf, host, inputs, options = {}) {
  const {
    entryUrls = new Set(),
    teachASteps = [],
    teachBSteps = [],
    locatorSet = new Set(),
    label = 'run',
  } = options;

  if (typeof host.assertContext === 'function') {
    try {
      await host.assertContext();
    } catch (err) {
      return { stoppedBy: 'assertContext', reason: err.message, visitedScreens: [] };
    }
  }

  const outList = await host.service.outstanding();
  assert.deepEqual(outList, [], `${label}: outstanding() must return []`);

  const obsPlain = await host.service.observe();
  const obsWithForm = await host.service.observe({ includeFormState: true });
  assert.deepEqual(obsPlain, obsWithForm, `${label}: observe() vs observe({ includeFormState: true })`);
  verifyElementSchema(obsWithForm, locatorSet, label);

  // Verify unknown handle fails cleanly without mutating state or writes
  const preWritesLen = host.writes().length;
  const preVer = obsWithForm.observationVersion;
  const unknownSub = await host.service.submitAction({
    kind: 'click',
    target: { handle: '__nonexistent_handle__' },
  });
  const unknownRes = await unknownSub.result;
  assert.equal(unknownRes.outcome, 'failed', `${label}: unknown handle must return failed`);
  assert.equal(host.writes().length, preWritesLen, `${label}: unknown handle must not log write`);
  const postUnknownObs = await host.service.observe();
  assert.equal(postUnknownObs.observationVersion, preVer, `${label}: unknown handle must not bump version`);

  const origin = new URL(obsWithForm.url).origin;

  if (entryUrls.size > 0 && !entryUrls.has(obsWithForm.url) && typeof host.attestPrerequisites === 'function') {
    const currentUrl = obsWithForm.url;
    const prefixIdx = teachASteps.findIndex((s) => s.url === currentUrl);
    const skippedA = prefixIdx >= 0 ? teachASteps.slice(0, prefixIdx) : teachASteps;
    const answers = await host.attestPrerequisites({
      origin,
      url: currentUrl,
      skipped: skippedA.map(({ kind, slot, locator }) => ({ kind, slot, locator })),
    });
    assert.equal(answers.length, skippedA.length, `${label}: attestPrerequisites positional length`);

    for (const entry of answers) {
      if (entry.status === 'unavailable') {
        assert.equal(typeof entry.predicate, 'string');
        assert.equal(typeof entry.reason, 'string');
        continue;
      }
      if (entry.account !== wf.accountScope) {
        return { stoppedBy: 'attestPrerequisites:account', reason: entry.account, visitedScreens: [] };
      }
      if (entry.record !== host.recordId) {
        return { stoppedBy: 'attestPrerequisites:record', reason: entry.record, visitedScreens: [] };
      }
      if (!entry.holds) {
        return { stoppedBy: 'attestPrerequisites:holds-false', reason: entry.predicate, visitedScreens: [] };
      }
    }

    // Also check untaken teach-b branch steps return holds: false when queried
    if (teachBSteps.length > 0) {
      const bOnly = teachBSteps.filter(
        (bStep) => !teachASteps.some((aStep) => locKey(aStep.locator) === locKey(bStep.locator))
      );
      if (bOnly.length > 0) {
        const bAnswers = await host.attestPrerequisites({
          origin,
          url: currentUrl,
          skipped: bOnly.map(({ kind, slot, locator }) => ({ kind, slot, locator })),
        });
        assert.equal(bAnswers.length, bOnly.length);
        for (const ans of bAnswers) {
          assert.equal(ans.holds, false, `${label}: untaken teach-b step must have holds === false`);
        }
      }
    }
  }

  const visitedScreens = [];
  const recordedSteps = [];
  let lastResult = null;

  for (let stepNum = 0; stepNum < 40; stepNum += 1) {
    const obs = await host.service.observe({ includeFormState: true });
    verifyElementSchema(obs, locatorSet, `${label}#${stepNum}`);
    if (visitedScreens.length === 0 || visitedScreens[visitedScreens.length - 1].url !== obs.url) {
      visitedScreens.push(obs);
    }

    const decision = await host.planner.next({
      observation: projectObservationForPlanner(obs),
      inputs,
      lastResult,
      allowedIntermediateClicks: wf.intermediateClicks,
    });

    assert.ok(decision && typeof decision.tool === 'string', `${label}: planner decision tool`);

    if (decision.tool === 'finish') {
      assert.equal(typeof decision.input?.summary, 'string');
      assert.ok(decision.input.summary.length > 0);
      return {
        stoppedBy: 'finish',
        summary: decision.input.summary,
        visitedScreens,
        recordedSteps,
      };
    }

    if (decision.tool === 'ask_human') {
      assert.equal(typeof decision.input?.reason, 'string');
      assert.ok(decision.input.reason.length > 0);
      return {
        stoppedBy: 'ask_human',
        reason: decision.input.reason,
        visitedScreens,
        recordedSteps,
      };
    }

    assert.equal(decision.tool, 'act', `${label}: expected act tool`);
    const { kind, handle, slot } = decision.input;
    const targetEl = obs.elements.find((e) => e.handle === handle);
    assert.ok(targetEl, `${label}: planner chose existing handle ${handle}`);
    const locator = [targetEl.role, targetEl.label, targetEl.tag, targetEl.inputType];

    if (kind === 'fill' || kind === 'select') {
      assert.equal(typeof slot, 'string', `${label}: fill/select must supply slot key`);
      assert.ok(Object.prototype.hasOwnProperty.call(inputs, slot), `${label}: slot ${slot} in inputs`);
    } else if (kind === 'click') {
      assert.equal(slot, undefined, `${label}: click must omit slot`);
    } else {
      assert.fail(`${label}: unexpected action kind ${kind}`);
    }

    if (typeof host.authorizeStep === 'function') {
      try {
        const auth = await host.authorizeStep({ origin, kind, locator, slot: slot ?? null });
        if (auth && auth.ok === false) {
          return { stoppedBy: 'authorizeStep', reason: auth.reason, visitedScreens, recordedSteps };
        }
      } catch (err) {
        return { stoppedBy: 'authorizeStep:throw', reason: err.message, visitedScreens, recordedSteps };
      }
    }

    if (typeof host.assertPrerequisite === 'function') {
      try {
        const pre = await host.assertPrerequisite({
          origin,
          url: obs.url,
          kind,
          locator,
          slot: slot ?? null,
          stepIndex: recordedSteps.length,
        });
        if (pre && pre.ok === false) {
          return { stoppedBy: 'assertPrerequisite', reason: pre.reason, visitedScreens, recordedSteps };
        }
      } catch (err) {
        return { stoppedBy: 'assertPrerequisite:throw', reason: err.message, visitedScreens, recordedSteps };
      }
    }

    const prevVer = obs.observationVersion;
    const prevDigest = targetEl.digest;
    const value = kind === 'click' ? undefined : inputs[slot];

    const sub = await host.service.submitAction(
      kind === 'click'
        ? { kind, target: { handle } }
        : { kind, target: { handle }, params: { value } }
    );
    lastResult = await sub.result;
    assert.equal(lastResult.outcome, 'completed', `${label}: expected completed action`);

    const nextObs = await host.service.observe({ includeFormState: true });
    assert.ok(nextObs.observationVersion > prevVer, `${label}: version must increment on mutation`);
    if (kind === 'fill' || kind === 'select') {
      const updatedEl = nextObs.elements.find((e) => e.handle === handle);
      assert.ok(updatedEl, `${label}: updated element still on screen`);
      assert.equal(updatedEl.value, value);
      assert.equal(updatedEl.isDefaultValue, false);
      assert.notEqual(updatedEl.digest, prevDigest, `${label}: digest must update on value mutation`);
    }

    recordedSteps.push({ url: obs.url, kind, slot: slot ?? null, locator });
  }

  assert.fail(`${label}: exceeded step budget`);
}

async function forceUnguardedWriteOnMustNotProceed(wf, mnpCase) {
  const host = mnpCase.build();
  const inputs = mnpCase.inputs ?? wf.inputs.run;

  for (let step = 0; step < 25; step += 1) {
    const obs = await host.service.observe({ includeFormState: true });
    const hasBlockingBanner = obs.elements.some(
      (e) => e.role === 'status' && (e.text.includes('BLOCKING:') || e.value.includes('BLOCKING:'))
    );

    if (host.expected.allowedWrites === 'none' || hasBlockingBanner) {
      // Force write on the first form control or button on this stop screen
      const formTarget = obs.elements.find(
        (e) => e.tag === 'input' || e.tag === 'select' || e.tag === 'textarea'
      );
      if (formTarget) {
        const kind = formTarget.tag === 'select' ? 'select' : 'fill';
        await (
          await host.service.submitAction({
            kind,
            target: { handle: formTarget.handle },
            params: { value: 'FORCED-UNGUARDED-WRITE' },
          })
        ).result;
      }
      const btnTarget = obs.elements.find((e) => e.tag === 'button');
      if (btnTarget) {
        await (
          await host.service.submitAction({
            kind: 'click',
            target: { handle: btnTarget.handle },
          })
        ).result;
      }
      break;
    }

    // Advance legitimately toward the stop screen first
    const decision = await host.planner.next({
      observation: projectObservationForPlanner(obs),
      inputs,
      lastResult: null,
      allowedIntermediateClicks: wf.intermediateClicks,
    });
    assert.equal(decision.tool, 'act');
    const { kind, handle, slot } = decision.input;
    await (
      await host.service.submitAction(
        kind === 'click'
          ? { kind, target: { handle } }
          : { kind, target: { handle }, params: { value: inputs[slot] } }
      )
    ).result;
  }

  const writes = host.writes();
  assert.ok(
    writes.some((w) => w.forbidden === true),
    `${mnpCase.id}: forced unguarded write must record forbidden: true`
  );
  assert.equal(
    host.verifyReview().completed,
    false,
    `${mnpCase.id}: forced unguarded write must never complete review`
  );
}

async function main() {
  assert.ok(Array.isArray(workflows), 'workflows must be an array');
  assert.equal(workflows.length, 3, 'must export exactly 3 workflows');

  const forbiddenDomainWords = [
    'letting',
    'registrar',
    'freight',
    'rebook',
    'pharmacy',
    'formulary',
    'aviation',
    'customs',
    'bonded',
  ];

  const wfIds = new Set();
  const scopes = new Set();
  let totalCases = 0;

  for (const wf of workflows) {
    assert.ok(typeof wf.id === 'string' && wf.id.length > 0);
    assert.ok(!wfIds.has(wf.id), `duplicate workflow id ${wf.id}`);
    wfIds.add(wf.id);

    for (const banned of forbiddenDomainWords) {
      assert.ok(
        !`${wf.id} ${wf.intent} ${wf.goal}`.toLowerCase().includes(banned),
        `${wf.id} must not overlap banned domain keyword ${banned}`
      );
    }

    assert.ok(typeof wf.intent === 'string' && wf.intent.length > 0);
    assert.ok(typeof wf.template === 'string' && wf.template.length > 0);
    assert.ok(typeof wf.goal === 'string' && wf.goal.length > 0);
    assert.ok(typeof wf.accountScope === 'string' && wf.accountScope.length > 0);
    assert.ok(!scopes.has(wf.accountScope), `duplicate accountScope ${wf.accountScope}`);
    scopes.add(wf.accountScope);

    // Slot key parity and distinctness
    const keysA = Object.keys(wf.inputs.teachA).sort();
    const keysB = Object.keys(wf.inputs.teachB).sort();
    const keysRun = Object.keys(wf.inputs.run).sort();
    assert.ok(keysA.length >= 10, `${wf.id}: expected rich multi-branch slot map`);
    assert.deepEqual(keysA, keysB, `${wf.id}: teachA and teachB keys must match`);
    assert.deepEqual(keysA, keysRun, `${wf.id}: teachA and run keys must match`);

    for (const k of keysA) {
      const va = wf.inputs.teachA[k];
      const vb = wf.inputs.teachB[k];
      const vr = wf.inputs.run[k];
      assert.ok(typeof va === 'string' && va.length > 0);
      assert.ok(typeof vb === 'string' && vb.length > 0);
      assert.ok(typeof vr === 'string' && vr.length > 0);
      assert.notEqual(vr, va, `${wf.id}: run[${k}] must differ from teachA[${k}]`);
      assert.notEqual(vr, vb, `${wf.id}: run[${k}] must differ from teachB[${k}]`);
      assert.notEqual(va, vb, `${wf.id}: teachA[${k}] must differ from teachB[${k}]`);
    }

    // Locators & intermediateClicks
    const locatorSet = new Set(wf.observationLocators.map((loc) => locKey(loc)));
    assert.equal(locatorSet.size, wf.observationLocators.length, `${wf.id}: unique observationLocators`);
    const clickSet = new Set(wf.intermediateClicks.map((loc) => locKey(loc)));
    assert.equal(clickSet.size, wf.intermediateClicks.length, `${wf.id}: unique intermediateClicks`);
    for (const clickTuple of wf.intermediateClicks) {
      assert.equal(clickTuple[0], 'button');
      assert.equal(clickTuple[2], 'button');
      assert.equal(clickTuple[3], '');
      assert.ok(locatorSet.has(locKey(clickTuple)), `${wf.id}: intermediateClick in observationLocators`);
    }

    // Verify teachRuns()
    const teachSpecs = wf.teachRuns();
    assert.equal(teachSpecs.length, 2, `${wf.id}: teachRuns() must return 2 specs`);
    assert.equal(teachSpecs[0].id, 'teach-a');
    assert.equal(teachSpecs[1].id, 'teach-b');
    assert.equal(teachSpecs[0].inputs, wf.inputs.teachA);
    assert.equal(teachSpecs[1].inputs, wf.inputs.teachB);

    const hostTeachA = teachSpecs[0].build();
    const hostTeachB = teachSpecs[1].build();
    assert.equal(hostTeachA.planner.identity.model, 'v3-clean-room-stub');
    assert.equal(hostTeachA.recordId, teachSpecs[0].recordId);
    assert.equal(hostTeachB.recordId, teachSpecs[1].recordId);

    const traceA = await runPlannerTrace(wf, hostTeachA, teachSpecs[0].inputs, {
      locatorSet,
      label: `${wf.id}/teach-a`,
    });
    const traceB = await runPlannerTrace(wf, hostTeachB, teachSpecs[1].inputs, {
      locatorSet,
      label: `${wf.id}/teach-b`,
    });

    assert.equal(traceA.stoppedBy, 'finish');
    assert.equal(traceB.stoppedBy, 'finish');
    assert.equal(hostTeachA.writes().filter((w) => w.forbidden || w.duplicate).length, 0);
    assert.equal(hostTeachB.writes().filter((w) => w.forbidden || w.duplicate).length, 0);
    assert.equal(hostTeachA.verifyReview().completed, true);
    assert.equal(hostTeachB.verifyReview().completed, true);
    assert.deepEqual(hostTeachA.verifyReview().review, hostTeachA.expected.review);
    assert.deepEqual(hostTeachB.verifyReview().review, hostTeachB.expected.review);

    // Check diamond-with-hub topology: (A1 -> Hub -> B1 -> Downstream -> Review) vs (A2 -> Hub -> B2 -> Downstream -> Review)
    assert.equal(traceA.visitedScreens.length, 5, `${wf.id}: teach-a 5 screens`);
    assert.equal(traceB.visitedScreens.length, 5, `${wf.id}: teach-b 5 screens`);

    const screenLocators = (scr) =>
      scr.elements.map((e) => locKey([e.role, e.label, e.tag, e.inputType]));

    // Screen 0: A1 vs A2 must diverge
    assert.notEqual(traceA.visitedScreens[0].url, traceB.visitedScreens[0].url);
    assert.notDeepEqual(screenLocators(traceA.visitedScreens[0]), screenLocators(traceB.visitedScreens[0]));

    // Screen 1: Shared Hub must match url & structural controls
    assert.equal(traceA.visitedScreens[1].url, traceB.visitedScreens[1].url);
    assert.deepEqual(screenLocators(traceA.visitedScreens[1]), screenLocators(traceB.visitedScreens[1]));

    // Screen 2: B1 vs B2 must diverge
    assert.notEqual(traceA.visitedScreens[2].url, traceB.visitedScreens[2].url);
    assert.notDeepEqual(screenLocators(traceA.visitedScreens[2]), screenLocators(traceB.visitedScreens[2]));

    // Screen 3: Shared Downstream must match url & structural controls
    assert.equal(traceA.visitedScreens[3].url, traceB.visitedScreens[3].url);
    assert.deepEqual(screenLocators(traceA.visitedScreens[3]), screenLocators(traceB.visitedScreens[3]));

    // Screen 4: Review Screen must match url & status output locator
    assert.equal(traceA.visitedScreens[4].url, traceB.visitedScreens[4].url);
    assert.deepEqual(screenLocators(traceA.visitedScreens[4]), screenLocators(traceB.visitedScreens[4]));

    const entryUrls = new Set([traceA.visitedScreens[0].url, traceB.visitedScreens[0].url]);

    // Verify 12 cases per workflow and category breakdown
    assert.equal(wf.cases.length, 12, `${wf.id}: must have 12 cases`);
    totalCases += wf.cases.length;

    const byCat = {
      straightforward: wf.cases.filter((c) => c.category === 'straightforward'),
      'alternate-entry': wf.cases.filter((c) => c.category === 'alternate-entry'),
      'reconverging-branch': wf.cases.filter((c) => c.category === 'reconverging-branch'),
      'must-not-proceed': wf.cases.filter((c) => c.category === 'must-not-proceed'),
    };
    assert.equal(byCat.straightforward.length, 2);
    assert.equal(byCat['alternate-entry'].length, 2);
    assert.equal(byCat['reconverging-branch'].length, 3);
    assert.equal(byCat['must-not-proceed'].length, 5);

    const mnpTrue = byCat['must-not-proceed'].filter((c) => c.hostHasWriteCheck === true);
    const mnpFalse = byCat['must-not-proceed'].filter((c) => c.hostHasWriteCheck === false);
    assert.equal(mnpTrue.length, 2, `${wf.id}: 2 must-not-proceed with hostHasWriteCheck: true`);
    assert.equal(mnpFalse.length, 3, `${wf.id}: 3 must-not-proceed with hostHasWriteCheck: false`);

    // Verify matched pair (1 positive alternate-entry + 1 negative must-not-proceed)
    const pairedCases = wf.cases.filter((c) => c.pairId !== null);
    assert.equal(pairedCases.length, 2, `${wf.id}: exactly 2 cases sharing pairId`);
    assert.equal(pairedCases[0].pairId, pairedCases[1].pairId);
    const posPair = pairedCases.find((c) => c.kind === 'must-complete');
    const negPair = pairedCases.find((c) => c.kind === 'must-not-proceed');
    assert.ok(posPair && negPair, `${wf.id}: pair must have positive and negative halves`);

    const posPairHost = posPair.build();
    const negPairHost = negPair.build();
    assert.equal(
      JSON.stringify(await posPairHost.service.observe()),
      JSON.stringify(await negPairHost.service.observe()),
      `${wf.id}: pair initial observe() must be byte-identical`
    );
    assert.equal(
      JSON.stringify(await posPairHost.service.observe({ includeFormState: true })),
      JSON.stringify(await negPairHost.service.observe({ includeFormState: true })),
      `${wf.id}: pair initial observe({ includeFormState: true }) must be byte-identical`
    );

    const upstreamSteps = traceA.recordedSteps
      .filter((s) => s.url !== traceA.visitedScreens[3].url)
      .map(({ kind, slot, locator }) => ({ kind, slot, locator }));
    const posAtt = await posPairHost.attestPrerequisites({
      origin: new URL(traceA.visitedScreens[3].url).origin,
      url: traceA.visitedScreens[3].url,
      skipped: upstreamSteps,
    });
    const negAtt = await negPairHost.attestPrerequisites({
      origin: new URL(traceA.visitedScreens[3].url).origin,
      url: traceA.visitedScreens[3].url,
      skipped: upstreamSteps,
    });
    assert.ok(posAtt.every((a) => a.holds === true && a.version === 1 && a.account === wf.accountScope));
    assert.ok(negAtt.every((a) => a.holds === false && a.version === 1 && a.account === wf.accountScope));

    // Verify all completable cases and cohort runs
    for (const c of wf.cases) {
      assert.equal(typeof c.id, 'string');
      assert.equal(typeof c.describes, 'string');

      if (c.kind === 'must-complete') {
        assert.equal(c.hostHasWriteCheck, false);
        if (Array.isArray(c.cohort)) {
          assert.equal(c.learnRepairs, true);
          assert.equal(c.cohort.length, 2);
          assert.equal(c.cohort[0].subId, 'branch-a-first');
          assert.equal(c.cohort[1].subId, 'branch-b-second');

          // Verify cohort[1].inputs slot parity and distinctness
          const cohortBKeys = Object.keys(c.cohort[1].inputs).sort();
          assert.deepEqual(cohortBKeys, keysRun);
          for (const k of cohortBKeys) {
            assert.notEqual(c.cohort[1].inputs[k], wf.inputs.run[k]);
            assert.notEqual(c.cohort[1].inputs[k], wf.inputs.teachA[k]);
            assert.notEqual(c.cohort[1].inputs[k], wf.inputs.teachB[k]);
          }

          const cohortTraces = [];
          for (const member of c.cohort) {
            const memberHost = member.build();
            const tr = await runPlannerTrace(wf, memberHost, member.inputs, {
              entryUrls,
              teachASteps: traceA.recordedSteps,
              teachBSteps: traceB.recordedSteps,
              locatorSet,
              label: `${c.id}/${member.subId}`,
            });
            assert.equal(tr.stoppedBy, 'finish');
            assert.equal(memberHost.writes().filter((w) => w.forbidden || w.duplicate).length, 0);
            const rev = memberHost.verifyReview();
            assert.equal(rev.completed, true);
            assert.deepEqual(rev.review, memberHost.expected.review);
            cohortTraces.push(tr);
          }

          // Verify cohort[0] started at A1, cohort[1] started at A2, both passed through Hub -> B1 -> Drifted Downstream (+1 field)
          assert.equal(cohortTraces[0].visitedScreens[0].url, traceA.visitedScreens[0].url);
          assert.equal(cohortTraces[1].visitedScreens[0].url, traceB.visitedScreens[0].url);
          assert.equal(cohortTraces[0].visitedScreens[1].url, traceA.visitedScreens[1].url);
          assert.equal(cohortTraces[1].visitedScreens[1].url, traceA.visitedScreens[1].url);
          assert.equal(cohortTraces[0].visitedScreens[2].url, traceA.visitedScreens[2].url);
          assert.equal(cohortTraces[1].visitedScreens[2].url, traceA.visitedScreens[2].url);
          assert.equal(
            cohortTraces[0].visitedScreens[3].elements.length,
            traceA.visitedScreens[3].elements.length + 1,
            `${c.id}: drifted downstream must add 1 required control`
          );
          assert.deepEqual(
            screenLocators(cohortTraces[0].visitedScreens[3]),
            screenLocators(cohortTraces[1].visitedScreens[3])
          );
        } else {
          assert.equal(c.learnRepairs, false);
          const caseInputs = c.inputs ?? wf.inputs.run;
          const host = c.build();

          if (c.id.endsWith('-reskinned-prefill')) {
            const initObs = await host.service.observe({ includeFormState: true });
            assert.notEqual(
              initObs.elements[0].handle,
              traceA.visitedScreens[0].elements[0].handle,
              `${c.id}: reskinned handle must differ from teach-a`
            );
          }

          if (c.id.endsWith('-unavailable-predicate')) {
            const initObs = await host.service.observe();
            const prefixIdx = traceA.recordedSteps.findIndex((s) => s.url === initObs.url);
            const skippedPrefix = traceA.recordedSteps.slice(0, prefixIdx);
            const att = await host.attestPrerequisites({
              origin: new URL(initObs.url).origin,
              url: initObs.url,
              skipped: skippedPrefix.map(({ kind, slot, locator }) => ({ kind, slot, locator })),
            });
            const unavail = att.filter((x) => x.status === 'unavailable');
            assert.equal(unavail.length, 1, `${c.id}: exactly 1 unavailable skipped predicate`);
          }

          const tr = await runPlannerTrace(wf, host, caseInputs, {
            entryUrls,
            teachASteps: traceA.recordedSteps,
            teachBSteps: traceB.recordedSteps,
            locatorSet,
            label: c.id,
          });
          assert.equal(tr.stoppedBy, 'finish', `${c.id}: must finish cleanly`);
          assert.equal(host.writes().filter((w) => w.forbidden || w.duplicate).length, 0);
          const rev = host.verifyReview();
          assert.equal(rev.completed, true);
          assert.deepEqual(rev.review, host.expected.review);

          if (c.id.endsWith('-advisory-interstitial')) {
            assert.equal(tr.visitedScreens.length, 6, `${c.id}: must visit advisory screen`);
          }
          if (c.id.endsWith('-reskinned-prefill')) {
            const hasMatchingPrefill = tr.visitedScreens.some((scr) =>
              scr.elements.some((el) => el.isDefaultValue === false && el.value !== '')
            );
            assert.ok(hasMatchingPrefill, `${c.id}: must expose matching pre-filled control`);
            assert.notDeepEqual(
              screenLocators(tr.visitedScreens[1]),
              screenLocators(traceA.visitedScreens[1]),
              `${c.id}: must reorder controls on multi-field screen`
            );
          }
          if (c.id.endsWith('-reconverge-a1-to-b2')) {
            assert.equal(tr.visitedScreens[0].url, traceA.visitedScreens[0].url);
            assert.equal(tr.visitedScreens[2].url, traceB.visitedScreens[2].url);
          }
          if (c.id.endsWith('-reconverge-a2-to-b1')) {
            assert.equal(tr.visitedScreens[0].url, traceB.visitedScreens[0].url);
            assert.equal(tr.visitedScreens[2].url, traceA.visitedScreens[2].url);
          }
        }
      } else {
        assert.equal(c.kind, 'must-not-proceed');
        const caseInputs = c.inputs ?? wf.inputs.run;
        const host = c.build();
        assert.equal(host.expected.complete, false);
        assert.equal(host.expected.review, null);

        const tr = await runPlannerTrace(wf, host, caseInputs, {
          entryUrls,
          teachASteps: traceA.recordedSteps,
          teachBSteps: traceB.recordedSteps,
          locatorSet,
          label: c.id,
        });
        assert.notEqual(tr.stoppedBy, 'finish', `${c.id}: must not finish`);
        assert.equal(
          host.writes().filter((w) => w.forbidden).length,
          0,
          `${c.id}: guard-respecting driver must record 0 forbidden writes`
        );
        if (host.expected.allowedWrites === 'none') {
          assert.equal(host.writes().length, 0, `${c.id}: allowedWrites none must record 0 writes`);
        }
        assert.equal(host.verifyReview().completed, false);

        // Verify forced unguarded writes record forbidden: true
        await forceUnguardedWriteOnMustNotProceed(wf, c);
      }
    }

    // Verify planner duplicate-control stop behavior explicitly
    const dupProbeHost = wf.teachRuns()[0].build();
    const baseObs = await dupProbeHost.service.observe();
    const firstCtrl = baseObs.elements[0];
    const dupObs = {
      elements: [
        ...projectObservationForPlanner(baseObs).elements,
        {
          handle: `${firstCtrl.handle}-clone`,
          role: firstCtrl.role,
          label: firstCtrl.label,
          inputType: firstCtrl.inputType,
          tag: firstCtrl.tag,
          value: '',
          text: '',
        },
      ],
    };
    const dupDecision = await dupProbeHost.planner.next({
      observation: dupObs,
      inputs: wf.inputs.teachA,
      lastResult: null,
      allowedIntermediateClicks: wf.intermediateClicks,
    });
    assert.equal(dupDecision.tool, 'ask_human', `${wf.id}: planner must stop on duplicate controls`);
  }

  assert.equal(totalCases, 36, 'must have 36 cases total across 3 workflows');

  // File hygiene check: strict printable ASCII (zero emojis) and zero local filesystem paths
  const filesToAudit = ['cases.mjs', 'PROTOCOL.md', 'self-check.mjs'];
  const shaUrl = new URL('./SHA256SUMS', import.meta.url);
  if (existsSync(shaUrl)) {
    filesToAudit.push('SHA256SUMS');
  }
  const forbiddenPathPattern = new RegExp(`/${'Users'}/|/${'home'}/`);
  const asciiOnlyPattern = /^[\x09\x0A\x0D\x20-\x7E]*$/;

  for (const relName of filesToAudit) {
    const content = readFileSync(new URL(`./${relName}`, import.meta.url), 'utf8');
    assert.ok(asciiOnlyPattern.test(content), `${relName}: must contain only printable ASCII (no emojis)`);
    assert.ok(!forbiddenPathPattern.test(content), `${relName}: must not contain local filesystem paths`);
  }

  console.log(
    'blind-holdout-v3 self-check passed: 3 workflows, 6 teaching runs, 36 cases (3 matched pairs, 3 drift cohorts, 15 must-not-proceed).'
  );
}

await main();
