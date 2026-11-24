// Check 1 for ERPNext as amendment 4 of second-upgrade-drift-rule.md defines it (clocksmith/deco#88):
// on the three labelled public cases, does a scripted run of the REST reads that frozen work depends on
// reach the wrong decision, on 3 of 3 repeats? No model, no page write, no arm, no sealed case.
//
//   node second-upgrade-read-check-erpnext.mjs --receipt FILE --self-check
//   node second-upgrade-read-check-erpnext.mjs --receipt FILE --releases v15.30.0,v15.40.0,...
//
// Two kinds of frozen work are run, because the two arms that reuse work read differently:
//  - written: a guard written by hand for the public family, reading the raw REST fields;
//  - learned: the real learner and its real adapter, taught on v15.20.0 and frozen there.
// Both are frozen on the first-upgrade target and decide fresh cases on the candidate. Labels come from
// how each case was built, never from a live read, so a read that changed cannot also change the answer.
//
// --self-check runs on v15.20.0 against itself, which is not one of the 17 stride points. Besides the plain
// run it alters REST answers inside this process, to show the check can fire. Those alterations are this
// probe's own control: they are not injected drift, and they say nothing about any release.
import { execFileSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import { existsSync, readFileSync, statfsSync, writeFileSync } from 'node:fs';
import { loadavg } from 'node:os';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { erpRequester, provisionErpRecipe, readErpState } from './three-arm-erpnext/erp-app.mjs';
import { createTeacher, decide as decideLearned } from './three-arm-erpnext/erp-learner.mjs';
import { provisionWithRefusalCapture } from './three-arm-next/runner.mjs';

const HERE = dirname(fileURLToPath(import.meta.url));
export const DEFAULT_MIN_FREE_GIB = 25;

export function freeDiskGiB(path = HERE, statfsFn = statfsSync) {
  const st = statfsFn(path);
  return Number(((BigInt(st.bavail) * BigInt(st.bsize)) / (1024n * 1024n)).toString()) / 1024;
}

export function assertFreeDiskForDockerScreen(minGiB = DEFAULT_MIN_FREE_GIB, path = HERE, statfsFn = statfsSync) {
  const free = freeDiskGiB(path, statfsFn);
  if (free < minGiB) {
    const err = Error(
      `refusing Docker image pull: ${free.toFixed(2)} GiB free at ${path}, below the ${minGiB} GiB safety floor (benchmark-spec.md)`,
    );
    err.code = 'insufficient-disk-space';
    err.freeGiB = Number(free.toFixed(2));
    err.requiredGiB = minGiB;
    throw err;
  }
  return Number(free.toFixed(2));
}
const FIRST_UPGRADE_TARGET = 'v15.20.0';
const KEEP_IMAGES = [FIRST_UPGRADE_TARGET, 'v15.10.0'];
const IMAGE = 'frappe/erpnext';
const PLATFORM = 'linux/amd64';
const REPEATS = 3;
const FAMILY = 'example-quotation-covers-order';
const PLAN = [{ role: 'order', target: true }, { role: 'quotation', follow: { role: 'order', field: 'items.0.supplier_quotation', doctype: 'Supplier Quotation' } }];

let serial = 0;
const recipe = (routeId, quotationQty, submit, orderQty) => ({
  routeId, familyId: FAMILY, entryBranch: 'direct',
  setup: [
    { as: 'approver', method: 'POST', path: '/api/resource/Supplier%20Quotation',
      body: { company: 'Stage2 Qual Corp', supplier: 'Stage2 Approved Vendor', transaction_date: '2026-02-01', items: [{ item_code: 'STAGE2-UNIT', qty: quotationQty, rate: 100 }] },
      save: { quotation: 'data.name', quotationDoc: 'data' } },
    ...(submit ? [{ as: 'approver', method: 'POST', path: '/api/method/frappe.client.submit', body: { doc: '{quotationDoc}' } }] : []),
    { as: 'author', method: 'POST', path: '/api/resource/Purchase%20Order',
      body: { company: 'Stage2 Qual Corp', supplier: 'Stage2 Approved Vendor', transaction_date: '2026-02-01', schedule_date: '2026-02-15',
        items: [{ item_code: 'STAGE2-UNIT', qty: orderQty, rate: 100, schedule_date: '2026-02-15', supplier_quotation: '{quotation}' }] }, save: { order: 'data.name' } },
  ],
  target: { doctype: 'Purchase Order', name: '{order}' }, write: { reference: `READ-${String(serial += 1).padStart(4, '0')}` },
});
const CASES = {
  valid: { build: () => recipe('read-valid', 12, true, 12), expect: 'write' },
  draft: { build: () => recipe('read-lookalike-draft', 12, false, 12), expect: 'stop' },
  quantity: { build: () => recipe('read-lookalike-quantity', 5, true, 12), expect: 'stop' },
};

const sh = (file, argv = [], options = {}) => execFileSync(file, argv, { encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe'], ...options });
const short = error => String(error?.stderr || error?.message || error).trim().split('\n').slice(-2).join(' | ').replaceAll(HERE, '.').slice(0, 400);
const load = () => loadavg().map(v => Number(v.toFixed(2)));
const documentPath = (doctype, name) => `/api/resource/${encodeURIComponent(doctype)}/${encodeURIComponent(name)}`;

/** Retries only what says nothing about the release: a connection failure or a 5xx. A 4xx is an answer and is kept. */
const steady = request => async (...call) => {
  let last = null;
  let failure = null;
  for (let attempt = 1; attempt <= 5; attempt += 1) {
    try {
      last = await request(...call);
      failure = null;
      if (last.status < 500) return last;
    } catch (error) { failure = error; }
    await new Promise(done => setTimeout(done, 1000 * attempt));
  }
  if (failure) throw failure;
  return last;
};
const reader = request => async path => {
  const r = await request('approver', 'GET', path);
  return { ok: r.status >= 200 && r.status < 300, status: r.status, body: r.body };
};

/** The hand-written guard, reading the raw fields as a guard written on v15.20.0 would. */
export async function decideWritten(route, get) {
  const order = await get(documentPath('Purchase Order', route.name));
  if (!order.ok) return { decision: 'stop', reason: `order read answered ${order.status}` };
  const quotationName = order.body?.data?.items?.[0]?.supplier_quotation;
  if (typeof quotationName !== 'string' || !quotationName) return { decision: 'stop', reason: 'the order names no quotation' };
  const quotation = await get(documentPath('Supplier Quotation', quotationName));
  if (!quotation.ok) return { decision: 'stop', reason: `quotation read answered ${quotation.status}` };
  const submitted = quotation.body?.data?.docstatus === 1;
  const sameQuantity = quotation.body?.data?.total_qty === order.body?.data?.total_qty;
  return submitted && sameQuantity ? { decision: 'write', reason: 'quotation submitted, same quantity' }
    : { decision: 'stop', reason: submitted ? 'quantities differ' : 'quotation not submitted' };
}

/** Teaches the real learner on v15.20.0, with two differing valid examples and two look-alikes, and freezes it. */
export async function freezeLearned(rel, requesterFn = erpRequester) {
  const request = steady(requesterFn(rel));
  const get = reader(request);
  const teacher = createTeacher([FAMILY]);
  const planned = teacher.setReadPlan(FAMILY, PLAN);
  if (!planned.ok) throw Error(`read plan refused: ${planned.problems}`);
  const examples = [['valid', 12, true, 12], ['valid', 7, true, 7], ['invalid', 7, false, 7], ['invalid', 4, true, 7]];
  for (const [index, [label, quotationQty, submit, orderQty]] of examples.entries()) {
    const route = await provisionErpRecipe(recipe(`teach-${index}`, quotationQty, submit, orderQty), { request, tag: `teach${index}` });
    const added = await teacher.addExample(FAMILY, label, route, get);
    if (!added.ok) throw Error(`example refused: ${added.problems}`);
  }
  const boundary = teacher.learn(FAMILY);
  if (boundary?.status !== 'learned') throw Error(`the learner did not learn a guard: ${boundary?.reason ?? 'unknown'}`);
  const { artifact } = teacher.freeze();
  return { artifact, boundarySha256: createHash('sha256').update(JSON.stringify(artifact.families[FAMILY].boundary)).digest('hex') };
}

/**
 * Runs one 3-repeat screening round while capturing any setup 403 / refusal under
 * Owner Correction (d) (`benchmark-spec.md:62-72`) without bypassing permissions.
 */
export async function oneRound(rel, artifact, alter = null, requesterFn = erpRequester) {
  const request = steady(requesterFn(rel));
  const plain = reader(request);
  const get = alter ? async path => alter(path, structuredClone(await plain(path))) : plain;
  const rows = [];
  for (let repeat = 1; repeat <= REPEATS; repeat += 1) {
    for (const [key, spec] of Object.entries(CASES)) {
      const built = await provisionWithRefusalCapture({
        application: 'erpnext', recipe: spec.build(), request, tag: `${key}${repeat}`,
      });
      if (built.notTestable) {
        return { notTestable: true, caseKey: key, repeat, refusal: built.refusal, rows };
      }
      const route = built.route;
      const written = await decideWritten(route, get);
      const learned = await decideLearned(artifact, route, get);
      rows.push({ repeat, case: key, expected: spec.expect, written: { decision: written.decision, reason: written.reason },
        learned: { decision: learned.decision, reason: String(learned.reason).slice(0, 120) } });
    }
  }
  return { notTestable: false, rows };
}

function readRound(rows) {
  const tally = {};
  for (const path of ['written', 'learned']) {
    tally[path] = {};
    for (const key of Object.keys(CASES)) {
      const ofCase = rows.filter(r => r.case === key);
      tally[path][key] = ofCase.filter(r => r[path].decision !== r.expected).length;
    }
  }
  const counts = Object.values(tally).flatMap(v => Object.values(v));
  return { wrongOfThreeByCase: tally, met: counts.some(n => n === REPEATS), mixed: counts.some(n => n > 0 && n < REPEATS),
    allCorrect: counts.every(n => n === 0) };
}

/** A mixed round (a case wrong in 1 or 2 of 3) is repeated once, both rounds are kept, and the second one stands. */
export async function checkRelease(rel, artifact, alter = null, requesterFn = erpRequester) {
  let first = await oneRound(rel, artifact, alter, requesterFn);
  if (first.notTestable) return first;
  let rows = first.rows;
  let reading = readRound(rows);
  let firstRound = null;
  if (reading.mixed) {
    firstRound = { reading, rows };
    const second = await oneRound(rel, artifact, alter, requesterFn);
    if (second.notTestable) return second;
    rows = second.rows;
    reading = readRound(rows);
  }
  return { notTestable: false, ...reading, rows, ...(firstRound ? { firstRoundRepeatedBecauseMixed: firstRound } : {}) };
}

function bringUp(tag) {
  const failures = [];
  for (let attempt = 1; attempt <= 3; attempt += 1) {
    try {
      sh(join(HERE, 'bringup', 'erpnext-down.sh'));
      sh(join(HERE, 'bringup', 'erpnext-up.sh'), [FIRST_UPGRADE_TARGET, tag], { timeout: 40 * 60 * 1000 });
      return { ok: true, failures };
    } catch (error) { failures.push(`attempt ${attempt}: ${short(error)}`); }
  }
  return { ok: false, failures };
}

function cleanUp(tag) {
  try { sh(join(HERE, 'bringup', 'erpnext-down.sh')); } catch { /* nothing to remove */ }
  if (!KEEP_IMAGES.includes(tag)) { try { sh('docker', ['rmi', `${IMAGE}:${tag}`]); } catch { /* not present */ } }
}

async function main(argv) {
  const option = name => (argv.includes(name) ? argv[argv.indexOf(name) + 1] : undefined);
  const receiptFile = resolve(option('--receipt') ?? '');
  const releases = (option('--releases') ?? '').split(',').filter(Boolean);
  const selfCheck = argv.includes('--self-check');
  const stopOnRefusal = argv.includes('--stop-on-refusal');
  const minFreeGiB = option('--min-free-gb') !== undefined ? Number(option('--min-free-gb')) : DEFAULT_MIN_FREE_GIB;

  if (!option('--receipt') || (!releases.length && !selfCheck)) {
    console.error('usage: second-upgrade-read-check-erpnext.mjs --receipt FILE (--self-check | --releases tag,tag,...) [--min-free-gb 25] [--stop-on-refusal]');
    process.exit(2);
  }

  assertFreeDiskForDockerScreen(minFreeGiB);

  const receipt = existsSync(receiptFile) ? JSON.parse(readFileSync(receiptFile, 'utf8')) : {};
  receipt.checked ??= [];
  const save = () => writeFileSync(receiptFile, `${JSON.stringify(receipt, null, 1)}\n`);

  if (selfCheck) {
    const up = bringUp(FIRST_UPGRADE_TARGET);
    if (!up.ok) throw Error(`bring-up failed: ${up.failures.join(' ; ')}`);
    try {
      const state = readErpState();
      const { artifact, boundarySha256 } = await freezeLearned(state.old);
      const dropQuotationLink = (path, answer) => {
        if (path.includes('Purchase%20Order') && answer.body?.data?.items) for (const item of answer.body.data.items) delete item.supplier_quotation;
        return answer;
      };
      const everyQuotationSubmitted = (path, answer) => {
        if (path.includes('Supplier%20Quotation') && answer.body?.data) answer.body.data.docstatus = 1;
        return answer;
      };
      const plain = await checkRelease(state.new, artifact);
      const dropped = await checkRelease(state.new, artifact, dropQuotationLink);
      const submitted = await checkRelease(state.new, artifact, everyQuotationSubmitted);
      const brief = r => ({ met: r.met, allCorrect: r.allCorrect, wrongOfThreeByCase: r.wrongOfThreeByCase });
      receipt.probeSelfCheck = { at: new Date().toISOString(), pair: `${FIRST_UPGRADE_TARGET}->${FIRST_UPGRADE_TARGET}`, boundarySha256,
        note: 'Not a stride point. The two altered runs change REST answers inside this process to show the check can fire. They are not injected drift and say nothing about any release.',
        plainRunShouldNotMeet: brief(plain), answerLosesTheQuotationLinkShouldMeet: brief(dropped), everyQuotationReadsSubmittedShouldMeet: brief(submitted),
        passed: !plain.met && plain.allCorrect && dropped.met && submitted.met };
      save();
      console.log(`self-check ${receipt.probeSelfCheck.passed ? 'passed' : 'FAILED'}: plain met=${plain.met}, link lost met=${dropped.met}, all submitted met=${submitted.met}`);
      process.exit(receipt.probeSelfCheck.passed ? 0 : 1);
    } finally { cleanUp(FIRST_UPGRADE_TARGET); }
  }

  for (const tag of releases) {
    if (receipt.checked.some(e => e.release === tag)) { console.log(`${tag}: already checked`); continue; }
    assertFreeDiskForDockerScreen(minFreeGiB);
    const entry = { release: tag, pair: `${FIRST_UPGRADE_TARGET}->${tag}`, startedAt: new Date().toISOString(), loadAverageAtStart: load(), image: null, check1: null, notTestable: false, note: null };
    try {
      sh('docker', ['pull', '-q', '--platform', PLATFORM, `${IMAGE}:${tag}`], { timeout: 60 * 60 * 1000 });
      entry.image = sh('docker', ['inspect', '--format', '{{index .RepoDigests 0}}', `${IMAGE}:${tag}`]).trim();
      const up = bringUp(tag);
      if (up.failures.length) entry.bringUpFailures = up.failures;
      if (!up.ok) {
        entry.notTestable = true;
        entry.note = 'not testable: frozen bring-up/seeder could not bring up or seed this release';
        if (stopOnRefusal) entry.stopAndAsk = true;
      } else {
        const state = readErpState();
        const frozen = await freezeLearned(state.old);
        entry.boundarySha256 = frozen.boundarySha256;
        const baseline = await checkRelease(state.old, frozen.artifact);
        entry.baselineOnFirstUpgradeTarget = { allCorrect: baseline.allCorrect, wrongOfThreeByCase: baseline.wrongOfThreeByCase };
        if (!baseline.allCorrect) {
          entry.note = 'the frozen work was not right on its own release: this entry is invalid';
          entry.stopAndAsk = true;
        } else {
          const result = await checkRelease(state.new, frozen.artifact);
          if (result.notTestable) {
            entry.notTestable = true;
            entry.setupRefusal = {
              caseKey: result.caseKey,
              repeat: result.repeat,
              request: { as: result.refusal.as, method: result.refusal.method, path: result.refusal.path },
              response: { status: result.refusal.status, body: result.refusal.response },
            };
            entry.note = `not testable under owner correction (d): ${result.caseKey} setup[${result.refusal.stepIndex}] ${result.refusal.method} ${result.refusal.path} returned ${result.refusal.status}`;
            if (stopOnRefusal) entry.stopAndAsk = true;
          } else {
            entry.check1 = {
              met: result.met,
              allCorrect: result.allCorrect,
              mixedAfterRepeat: result.mixed,
              wrongOfThreeByCase: result.wrongOfThreeByCase,
              rows: result.rows,
              ...(result.firstRoundRepeatedBecauseMixed ? { firstRoundRepeatedBecauseMixed: result.firstRoundRepeatedBecauseMixed } : {}),
            };
          }
        }
      }
    } catch (error) {
      entry.note = `check failed: ${short(error)}`;
      entry.stopAndAsk = true;
    }
    entry.endedAt = new Date().toISOString();
    entry.loadAverageAtEnd = load();
    cleanUp(tag);
    receipt.checked.push(entry);
    save();
    const c = entry.check1;
    console.log(`${tag}: ${entry.notTestable ? 'NOT TESTABLE' : c ? (c.met ? 'MET' : 'not met') : 'not run'}${c ? ` | all decisions right ${c.allCorrect}` : ''}${entry.note ? ` (${entry.note})` : ''}`);
    if (entry.stopAndAsk) { console.log(`stopped at ${tag}: a ruling is needed`); break; }
  }
  console.log('READ_CHECK_DONE');
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  await main(process.argv.slice(2));
}
