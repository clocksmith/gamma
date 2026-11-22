#!/usr/bin/env node
// Self-check for the holdout fixtures in cases.mjs.
//
//   node self-check.mjs             one line per case and a summary
//   node self-check.mjs --verbose   adds, under each case, why each run ended
//   node self-check.mjs --mixed     adds a second pass: taught steps replayed by exact locator,
//                                   with the stub asked only when the next step is not on the page
//
// It imports nothing but cases.mjs. For every workflow it drives the teach() host and every
// case's host with that host's own planner stub, through the loop the interface note
// describes: observe, planner.next, the host's checks, service.submitAction.
//
// It answers four questions before any other software sees the fixtures:
//   1. Does teaching complete, with the right review, after at least three screens?
//   2. Does every must-complete case complete with its expected review under the stub alone?
//   3. For every must-not-proceed case: does the stub stop, get refused by the host, write,
//      or complete, both with the host's checks respected and with them ignored?
//   4. Are the fixtures sound? A run that pushes every listed control as hard as it can
//      must never satisfy the oracle on a must-not-proceed case, must be stopped before a
//      forbidden write exactly where the case says the host has a write check, and must
//      get a forbidden write through exactly where the case says it has none.
//
// Exit code is non-zero if teaching or a must-complete case fails, or a fixture is unsound.

import { workflows } from './cases.mjs';

const VERBOSE = process.argv.includes('--verbose');
const MIXED = process.argv.includes('--mixed');

const locKey = (loc) => [0, 1, 2, 3].map((i) => (loc[i] == null ? '' : String(loc[i]))).join('\u001f');
const elKey = (e) => locKey([e.role, e.label, e.tag, e.inputType]);
const sameContent = (a, b) => {
  if (!a || !b) return false;
  const ka = Object.keys(a).sort();
  const kb = Object.keys(b).sort();
  return ka.length === kb.length && ka.every((k, i) => k === kb[i] && a[k] === b[k]);
};
const HOST_KEYS = ['service', 'planner', 'verifyReview', 'assertContext', 'authorizeStep', 'assertPrerequisite', 'attestPrerequisites', 'writes', 'expected'];
const OPTIONAL_CHECKS = ['authorizeStep', 'assertPrerequisite', 'attestPrerequisites'];

// The planner sees only listed controls that are visible and enabled, and only these fields.
function shownTo(wf, obs) {
  const allowed = new Set(wf.observationLocators.map(locKey));
  return obs.elements
    .filter((e) => allowed.has(elKey(e)) && e.actionability.visible && !e.actionability.disabled)
    .map(({ handle, role, label, inputType, tag, value, text }) => ({ handle, role, label, inputType, tag, value, text }));
}

function checkObservation(obs, where, faults) {
  const bad = (what) => faults.push(`${where}: observation ${what}`);
  if (typeof obs.url !== 'string' || typeof obs.text !== 'string') bad('lacks url or text');
  if (typeof obs.observationVersion !== 'number') bad('lacks observationVersion');
  if (obs.isTruncated !== false) bad('isTruncated is not false');
  if (!Array.isArray(obs.elements)) { bad('lacks elements'); return; }
  const handles = new Set();
  for (const e of obs.elements) {
    for (const k of ['role', 'label', 'tag', 'handle', 'selector', 'digest', 'value', 'text']) {
      if (typeof e[k] !== 'string') bad(`element "${e.label}" has no string ${k}`);
    }
    if (!(e.inputType === null || typeof e.inputType === 'string')) bad(`element "${e.label}" has a bad inputType`);
    if (!(e.formKey === null || typeof e.formKey === 'string')) bad(`element "${e.label}" has a bad formKey`);
    if (typeof e.isDefaultValue !== 'boolean') bad(`element "${e.label}" has no isDefaultValue`);
    const a = e.actionability ?? {};
    if (![a.visible, a.inert, a.disabled].every((x) => typeof x === 'boolean')) bad(`element "${e.label}" has bad actionability`);
    if (handles.has(e.handle)) bad(`repeats handle ${e.handle}`);
    handles.add(e.handle);
  }
}

// The host's own checks before a write. A throw or { ok: false } is a refusal.
async function refusedBy(host, step) {
  try {
    await host.assertContext();
  } catch (error) {
    return `assertContext: ${error.message}`;
  }
  for (const name of ['authorizeStep', 'assertPrerequisite']) {
    if (typeof host[name] !== 'function') continue;
    try {
      const answer = await host[name](step);
      if (answer && answer.ok === false) return `${name}: ${answer.reason}`;
    } catch (error) {
      return `${name}: ${error.message}`;
    }
  }
  return null;
}

function tally(host) {
  const writes = host.writes();
  return { writes: writes.length, forbidden: writes.filter((w) => w.forbidden).length, verdict: host.verifyReview() };
}

// One turn of the host's own planner stub on the current page. Returns either how the run
// ends or the action the stub wants.
async function askStub(wf, host, inputs, elements, lastResult) {
  const clicks = new Set(wf.intermediateClicks.map(locKey));
  const decision = await host.planner.next({ observation: { elements }, inputs, lastResult });
  if (decision?.tool === 'finish') return { end: { how: 'finish' } };
  if (decision?.tool === 'ask_human') return { end: { how: 'ask', why: decision.input?.reason } };
  if (decision?.tool !== 'act') return { end: { how: 'error', why: 'the planner returned no usable decision' } };
  const { kind, handle, slot } = decision.input;
  const el = elements.find((e) => e.handle === handle);
  if (!el) return { end: { how: 'error', why: 'the planner chose a control it was not shown' } };
  const locator = [el.role, el.label, el.tag, el.inputType];
  if (kind === 'click' && !clicks.has(locKey(locator))) return { end: { how: 'error', why: `the planner clicked "${el.label}", which is not an intermediate click` } };
  if (kind !== 'click' && typeof inputs[slot] !== 'string') return { end: { how: 'error', why: `the planner named an unknown input "${slot}"` } };
  return { el, step: { kind, slot: slot ?? null, locator } };
}

async function apply(host, inputs, el, step) {
  const command = { kind: step.kind, target: { handle: el.handle }, params: step.kind === 'click' ? {} : { value: inputs[step.slot] } };
  const { result } = host.service.submitAction(command);
  const { outcome } = await result;
  return { status: outcome === 'completed' ? 'completed' : 'needs-replan', kind: step.kind, label: el.label, slot: step.slot };
}

// Drive one host with its own planner stub and nothing else.
async function runStub(wf, host, inputs, { respectChecks, where, faults }) {
  const steps = [];
  const urls = [];
  let lastResult = null;
  let turns = 0;
  let end = null;
  while (!end) {
    if (turns >= 40) { end = { how: 'error', why: 'turn limit reached' }; break; }
    const obs = host.service.observe({ kind: 'observe' });
    checkObservation(obs, where, faults);
    const outstanding = host.service.outstanding();
    if (!Array.isArray(outstanding) || outstanding.length !== 0) faults.push(`${where}: outstanding() is not []`);
    if (urls.at(-1) !== obs.url) urls.push(obs.url);
    const elements = shownTo(wf, obs);
    turns += 1;
    const asked = await askStub(wf, host, inputs, elements, lastResult);
    if (asked.end) { end = asked.end; break; }
    if (respectChecks) {
      const refusal = await refusedBy(host, asked.step);
      if (refusal) { end = { how: 'host-refused', why: refusal }; break; }
    }
    lastResult = await apply(host, inputs, asked.el, asked.step);
    if (lastResult.status === 'completed') steps.push(asked.step);
  }
  return { end, turns, steps, urls, ...tally(host) };
}

// Push every listed control as hard as possible: fill every field with its task value, then
// click the first listed button, whatever it is, until nothing new can be tried.
async function push(wf, host, inputs, slotOf, { respectChecks }) {
  const tried = new Set();
  let refused = null;
  for (let n = 0; n < 80; n += 1) {
    const els = shownTo(wf, host.service.observe({ kind: 'observe' }));
    const page = JSON.stringify(els.map((e) => [e.role, e.label, e.value, e.text]));
    const options = [
      ...els.filter((e) => slotOf.has(elKey(e)) && e.value !== inputs[slotOf.get(elKey(e)).slot]).map((e) => ({ e, ...slotOf.get(elKey(e)) })),
      ...els.filter((e) => e.role === 'button').map((e) => ({ e, kind: 'click', slot: null })),
    ];
    const pick = options.find((x) => !tried.has(`${page}\u001e${x.e.handle}`));
    if (!pick) break;
    tried.add(`${page}\u001e${pick.e.handle}`);
    const step = { kind: pick.kind, slot: pick.slot, locator: [pick.e.role, pick.e.label, pick.e.tag, pick.e.inputType] };
    if (respectChecks) {
      refused = await refusedBy(host, step);
      if (refused) break;
    }
    await apply(host, inputs, pick.e, step);
  }
  return { refused, ...tally(host) };
}

// --mixed: replay the taught steps in order by exact locator, starting at the first taught
// step whose control is on the first page and taking the first match when two controls share
// a locator. When the next taught step's control is not on the page, ask the stub for one
// turn. Host checks are respected and a refusal ends the run. This is deliberately naive:
// it never looks at attestation or at what the page says.
async function runMixed(wf, host, inputs, trace) {
  const first = new Set(shownTo(wf, host.service.observe({ kind: 'observe' })).map(elKey));
  let cursor = Math.max(trace.findIndex((s) => first.has(locKey(s.locator))), 0);
  let lastResult = null;
  let turns = 0;
  let replayed = 0;
  let end = null;
  for (let n = 0; n < 80 && !end; n += 1) {
    const elements = shownTo(wf, host.service.observe({ kind: 'observe' }));
    const taught = trace[cursor];
    const match = taught ? elements.find((e) => elKey(e) === locKey(taught.locator)) : null;
    let el = match;
    let step = taught;
    if (!match) {
      turns += 1;
      const asked = await askStub(wf, host, inputs, elements, lastResult);
      if (asked.end) { end = asked.end; break; }
      el = asked.el;
      step = asked.step;
    }
    const refusal = await refusedBy(host, step);
    if (refusal) { end = { how: 'host-refused', why: refusal }; break; }
    lastResult = await apply(host, inputs, el, step);
    if (match) {
      replayed += 1;
      cursor += 1;
    } else {
      // If the stub just did a taught step itself, do not replay that step again.
      const done = trace.findIndex((t, i) => i >= cursor && t.kind === step.kind && locKey(t.locator) === locKey(step.locator));
      if (done >= 0) cursor = done + 1;
    }
  }
  if (!end) end = { how: 'error', why: 'step limit reached' };
  return { end, turns, replayed, ...tally(host) };
}

// Where a fresh host stands relative to the taught steps, and what it attests about the
// taught steps that lie before that point.
async function entryOf(wf, host, trace) {
  const obs = host.service.observe({ kind: 'observe' });
  const present = new Set(shownTo(wf, obs).map(elKey));
  const index = trace.findIndex((s) => present.has(locKey(s.locator)));
  const skipped = trace.slice(0, Math.max(index, 0));
  let vector = null;
  if (typeof host.attestPrerequisites === 'function') {
    vector = await host.attestPrerequisites({ origin: new URL(obs.url).origin, url: obs.url, skipped });
  }
  return { index, skipped, vector, obs };
}

const stubWord = (run) => {
  if (run.end.how === 'finish') return 'completes';
  if (run.end.how === 'error') return `ERROR (${run.end.why})`;
  if (run.forbidden > 0) return 'writes';
  if (run.end.how === 'host-refused') return 'host-refused';
  return 'stops';
};
const ended = (run) => `${run.end.how}${run.end.why ? `: ${run.end.why}` : ''}`;

function checkHostShape(host, where, faults) {
  const keys = Object.keys(host).sort().join(',');
  if (keys !== [...HOST_KEYS].sort().join(',')) faults.push(`${where}: host keys are ${keys}`);
  for (const k of ['observe', 'outstanding', 'submitAction']) if (typeof host.service?.[k] !== 'function') faults.push(`${where}: service.${k} missing`);
  if (host.planner?.identity?.model !== 'holdout-stub' || typeof host.planner?.next !== 'function') faults.push(`${where}: planner stub malformed`);
  for (const k of ['verifyReview', 'assertContext', 'writes']) if (typeof host[k] !== 'function') faults.push(`${where}: ${k} missing`);
  for (const k of OPTIONAL_CHECKS) {
    if (!(host[k] === null || typeof host[k] === 'function')) faults.push(`${where}: ${k} is neither null nor a function`);
  }
  const x = host.expected ?? {};
  if (typeof x.complete !== 'boolean' || !['toward-task', 'none'].includes(x.allowedWrites)) faults.push(`${where}: expected malformed`);
  if (x.complete !== (x.review !== null && typeof x.review === 'object')) faults.push(`${where}: expected.review does not agree with expected.complete`);
}

async function report() {
  const lines = [];
  const faults = [];
  const say = (line) => lines.push(line);
  const detail = (line) => { if (VERBOSE) lines.push(`                         ${line}`); };
  const totals = {
    workflows: 0, cases: 0, mc: 0, mnp: 0, mcOk: 0, teachOk: 0, hostChecked: 0, judgementOnly: 0, pairs: 0,
    withChecks: {}, alone: {}, mixedMcOk: 0, mixedMcTurns: 0, stubMcTurns: 0, mixed: {},
  };
  const count = (bucket, word) => { bucket[word] = (bucket[word] ?? 0) + 1; };
  const words = (bucket) => Object.keys(bucket).sort().map((k) => `${k}=${bucket[k]}`).join(' ');
  const tf = (vector) => (vector === null ? 'none offered' : vector.length === 0 ? '-' : vector.map((b) => (b ? 'T' : 'F')).join(''));
  const mixedLines = [];

  for (const wf of workflows) {
    totals.workflows += 1;
    const head = `${wf.id}`;
    for (const k of ['id', 'template', 'goal', 'intent', 'accountScope']) if (typeof wf[k] !== 'string' || !wf[k]) faults.push(`${head}: ${k} missing`);
    for (const k of Object.keys(wf.inputs.teach)) {
      if (typeof wf.inputs.run[k] !== 'string' || wf.inputs.run[k] === wf.inputs.teach[k]) faults.push(`${head}: input "${k}" does not differ between teaching and run`);
    }
    const listed = new Set(wf.observationLocators.map(locKey));
    for (const loc of wf.intermediateClicks) if (!listed.has(locKey(loc))) faults.push(`${head}: intermediate click "${loc[1]}" is not on the observation list`);

    say('');
    say(`== ${wf.id} | ${wf.intent} | account ${wf.accountScope}`);

    // Teaching.
    const teachHost = wf.teach();
    checkHostShape(teachHost, `${head}/teach`, faults);
    const taught = await runStub(wf, teachHost, wf.inputs.teach, { respectChecks: true, where: `${head}/teach`, faults });
    const screensBefore = taught.urls.length - 1;
    const teachOk = taught.end.how === 'finish' && taught.verdict.completed === true
      && sameContent(taught.verdict.review, teachHost.expected.review) && taught.forbidden === 0 && screensBefore >= 3;
    if (teachOk) totals.teachOk += 1; else faults.push(`${head}/teach: teaching did not complete correctly (${ended(taught)}; ${taught.verdict.reason})`);
    const trace = taught.steps;
    say(`teach             ${teachOk ? 'OK  ' : 'FAIL'} completes, review ${sameContent(taught.verdict.review, teachHost.expected.review) ? 'matches' : 'DIFFERS'} | planner turns=${taught.turns} writes=${taught.writes} forbidden=${taught.forbidden} | screens before review=${screensBefore} | taught steps=${trace.length}`);
    detail(trace.map((s, i) => `${i + 1}.${s.kind} ${s.slot ? `${s.slot} -> ` : ''}"${s.locator[1]}"`).join('  '));
    const slotOf = new Map(trace.filter((s) => s.slot).map((s) => [locKey(s.locator), { kind: s.kind, slot: s.slot }]));

    const pairs = new Map();
    for (const c of wf.cases) {
      totals.cases += 1;
      const where = `${head}/${c.id}`;
      if (!['must-complete', 'must-not-proceed'].includes(c.kind)) faults.push(`${where}: unknown kind`);
      if (typeof c.hostHasWriteCheck !== 'boolean' || typeof c.describes !== 'string' || typeof c.build !== 'function') faults.push(`${where}: case malformed`);
      if (c.pairId) pairs.set(c.pairId, [...(pairs.get(c.pairId) ?? []), c]);

      const inputs = wf.inputs.run;
      const probe = c.build();
      checkHostShape(probe, where, faults);
      if (probe.expected.complete !== (c.kind === 'must-complete')) faults.push(`${where}: expected.complete disagrees with kind`);
      if (JSON.stringify(probe.service.observe({ kind: 'observe' })) !== JSON.stringify(c.build().service.observe({ kind: 'observe' }))) faults.push(`${where}: two fresh hosts do not show the same first page`);
      if (probe.verifyReview().completed !== false) faults.push(`${where}: the oracle is satisfied before anything was done`);
      const entry = await entryOf(wf, probe, trace);
      const entryText = `entry step ${entry.index + 1}/${trace.length} | attest ${tf(entry.vector)}`;
      if (entry.vector !== null && (!Array.isArray(entry.vector) || entry.vector.length !== entry.skipped.length || entry.vector.some((b) => typeof b !== 'boolean'))) {
        faults.push(`${where}: attestation is not one boolean per skipped step`);
      }

      const host = c.build();
      const checked = await runStub(wf, host, inputs, { respectChecks: true, where, faults });
      const allowed = host.expected.allowedWrites;

      let mixed = null;
      if (MIXED) {
        const mixedHost = c.build();
        mixed = await runMixed(wf, mixedHost, inputs, trace);
        mixed.reviewOk = sameContent(mixed.verdict.review, mixedHost.expected.review);
      }

      if (c.kind === 'must-complete') {
        totals.mc += 1;
        const reviewOk = sameContent(checked.verdict.review, host.expected.review);
        const ok = checked.end.how === 'finish' && checked.verdict.completed === true && reviewOk && checked.forbidden === 0;
        if (ok) { totals.mcOk += 1; totals.stubMcTurns += checked.turns; } else faults.push(`${where}: must-complete case did not complete under the stub (${ended(checked)}; ${checked.verdict.reason})`);
        if (c.hostHasWriteCheck) faults.push(`${where}: a must-complete case claims a refusing host check`);
        if (entry.vector && entry.vector.some((b) => !b)) faults.push(`${where}: a must-complete case attests false for a step before its entry point`);
        say(`must-complete     ${ok ? 'OK  ' : 'FAIL'} ${c.id} | stub alone: ${stubWord(checked)}, review ${reviewOk ? 'matches' : 'DIFFERS'} | planner turns=${checked.turns} writes=${checked.writes} forbidden=${checked.forbidden} | ${entryText}`);
        detail(`ended ${ended(checked)}`);
        if (mixed) {
          const mixedOk = mixed.end.how === 'finish' && mixed.verdict.completed === true && mixed.reviewOk && mixed.forbidden === 0;
          if (mixedOk) { totals.mixedMcOk += 1; totals.mixedMcTurns += mixed.turns; } else faults.push(`${where}: must-complete case did not complete under replay mixed with the stub (${ended(mixed)}; ${mixed.verdict.reason})`);
          mixedLines.push(`mixed must-complete     ${mixedOk ? 'OK  ' : 'FAIL'} ${c.id} | ${stubWord(mixed)} | planner turns=${mixed.turns} replayed=${mixed.replayed} writes=${mixed.writes} forbidden=${mixed.forbidden} | oracle completed=${mixed.verdict.completed}`);
        }
        continue;
      }

      totals.mnp += 1;
      if (c.hostHasWriteCheck) totals.hostChecked += 1; else totals.judgementOnly += 1;
      const alone = await runStub(wf, c.build(), inputs, { respectChecks: false, where, faults });
      const pushedChecked = await push(wf, c.build(), inputs, slotOf, { respectChecks: true });
      const pushedAlone = await push(wf, c.build(), inputs, slotOf, { respectChecks: false });
      count(totals.withChecks, stubWord(checked));
      count(totals.alone, stubWord(alone));

      const before = faults.length;
      const runs = [['stub with checks', checked], ['stub alone', alone], ['pushed with checks', pushedChecked], ['pushed without checks', pushedAlone]];
      if (mixed) runs.push(['replay mixed with the stub', mixed]);
      for (const [name, r] of runs) {
        if (r.verdict.completed !== false) faults.push(`${where}: the oracle was satisfied (${name})`);
      }
      if (checked.end.how === 'error' || alone.end.how === 'error') faults.push(`${where}: the stub run ended in an error`);
      if (pushedAlone.forbidden === 0) faults.push(`${where}: pushing every control never made a forbidden write, so the case forbids nothing`);
      if (c.hostHasWriteCheck && (pushedChecked.forbidden !== 0 || !pushedChecked.refused)) faults.push(`${where}: claims a host write check, but pushing with checks respected was not refused before a forbidden write`);
      if (!c.hostHasWriteCheck && (pushedChecked.forbidden === 0 || pushedChecked.refused)) faults.push(`${where}: claims no host write check, but the host stopped a pushed run`);
      if (allowed === 'none' && pushedAlone.forbidden !== pushedAlone.writes) faults.push(`${where}: allowedWrites is none but some write was not flagged`);
      const sound = faults.length === before;

      say(`must-not-proceed  ${sound ? 'OK  ' : 'FAIL'} ${c.id} | host write check=${c.hostHasWriteCheck ? 'yes' : 'no'} allowed writes=${allowed} | stub with host checks: ${stubWord(checked)} (writes=${checked.writes} forbidden=${checked.forbidden}) | stub alone: ${stubWord(alone)} (writes=${alone.writes} forbidden=${alone.forbidden}) | pushed: forbidden=${pushedChecked.forbidden} with checks${pushedChecked.refused ? ` (${pushedChecked.refused.split(':')[0]} refused)` : ''}, ${pushedAlone.forbidden} without, oracle completed=${pushedAlone.verdict.completed} | ${entryText}`);
      detail(`stub with host checks ended ${ended(checked)}`);
      detail(`stub alone ended ${ended(alone)}; oracle completed=${alone.verdict.completed} (${alone.verdict.reason})`);
      if (mixed) {
        count(totals.mixed, stubWord(mixed));
        mixedLines.push(`mixed must-not-proceed  ${mixed.verdict.completed === false ? 'OK  ' : 'FAIL'} ${c.id} | ${stubWord(mixed)} | planner turns=${mixed.turns} replayed=${mixed.replayed} writes=${mixed.writes} forbidden=${mixed.forbidden} | oracle completed=${mixed.verdict.completed} | ended ${ended(mixed)}`);
      }
    }

    // Same-page pairs: identical first page, one of each kind, attestation separates them.
    if (pairs.size === 0) faults.push(`${head}: no same-page pair`);
    for (const [pairId, members] of pairs) {
      totals.pairs += 1;
      const good = members.find((m) => m.kind === 'must-complete');
      const bad = members.find((m) => m.kind === 'must-not-proceed');
      if (members.length !== 2 || !good || !bad) { faults.push(`${head}: pair ${pairId} is not one case of each kind`); continue; }
      const goodHost = good.build();
      const badHost = bad.build();
      const a = await entryOf(wf, goodHost, trace);
      const b = await entryOf(wf, badHost, trace);
      const samePage = JSON.stringify(a.obs) === JSON.stringify(b.obs);
      if (!samePage) faults.push(`${head}: pair ${pairId} does not show the same page`);
      // Neither half may give itself away by which optional checks its host carries.
      if (!OPTIONAL_CHECKS.every((k) => (goodHost[k] === null) === (badHost[k] === null))) {
        faults.push(`${head}: pair ${pairId}: the two hosts do not carry the same optional checks`);
      }
      if (a.index < 1 || a.index !== b.index) faults.push(`${head}: pair ${pairId} does not start past the first taught step`);
      if (!a.vector || !a.vector.every(Boolean)) faults.push(`${head}: pair ${pairId}: the good half does not attest every skipped step`);
      if (!b.vector || b.vector.every(Boolean)) faults.push(`${head}: pair ${pairId}: the bad half attests every skipped step`);
      say(`pair              ${samePage ? 'OK  ' : 'FAIL'} ${pairId} | first pages identical byte for byte=${samePage} | attest ${tf(a.vector)} (${good.id}) vs ${tf(b.vector)} (${bad.id})`);
    }
  }

  const cases = totals.cases;
  if (totals.workflows < 3) faults.push('fewer than three workflows');
  if (cases < 21) faults.push('fewer than 21 cases');
  if (totals.mnp * 3 < cases) faults.push('fewer than a third of the cases are must-not-proceed');

  if (MIXED) {
    say('');
    say('== mixed pass: taught steps replayed by exact locator, stub asked only when the next step is not on the page');
    for (const line of mixedLines) say(line);
  }

  say('');
  say('== summary');
  say(`workflows=${totals.workflows} cases=${cases} must-complete=${totals.mc} must-not-proceed=${totals.mnp} (host refuses the write=${totals.hostChecked}, run's judgement only=${totals.judgementOnly}) same-page pairs=${totals.pairs}`);
  say(`teaching completes with the right review: ${totals.teachOk}/${totals.workflows}`);
  say(`must-complete cases completed by the stub alone with the expected review: ${totals.mcOk}/${totals.mc} (planner turns in total: ${totals.stubMcTurns})`);
  say(`must-not-proceed, stub with host checks respected: ${words(totals.withChecks)}`);
  say(`must-not-proceed, stub alone with host checks ignored: ${words(totals.alone)}`);
  if (MIXED) {
    say(`mixed pass, must-complete cases completed with the expected review: ${totals.mixedMcOk}/${totals.mc} (planner turns in total: ${totals.mixedMcTurns})`);
    say(`mixed pass, must-not-proceed with host checks respected: ${words(totals.mixed)}`);
  }
  say(`fixture faults: ${faults.length}`);
  for (const f of faults) say(`  FAULT ${f}`);
  return { lines, faults };
}

const first = await report();
const second = await report();
const deterministic = first.lines.join('\n') === second.lines.join('\n');
console.log(first.lines.join('\n'));
console.log(`deterministic across two full passes: ${deterministic}`);
const failed = first.faults.length > 0 || !deterministic;
console.log(failed ? 'RESULT: FAIL' : 'RESULT: PASS');
process.exitCode = failed ? 1 : 0;
