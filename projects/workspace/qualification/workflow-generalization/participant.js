#!/usr/bin/env node
// One-person offline repeat instrument. Task effects use the workspace service, never the UI DOM.
import { createServer } from 'node:http';
import { randomBytes, randomUUID, timingSafeEqual } from 'node:crypto';
import { existsSync, mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import { resolve, join } from 'node:path';
import { WorkspaceService } from '../../src/service.js';
import { loadServiceConfig } from '../../src/config.js';
import { createPlaywrightAdapter } from '../../src/adapters/playwright-adapter.js';
import { TraceDag } from '../../src/client/trace-dag.js';
import { structuralLocator } from '../../src/adapters/page-query.js';
import { sha256Hex } from '../../src/journal.js';
import { createFixture } from './fixture.js';
import { groupsFor, intermediateClicks } from './contracts.js';

const args = process.argv.slice(2), outAt = args.indexOf('--out');
if (args.includes('--help')) { console.log('participant.js --out NEW_PRIVATE_DIR [--port PORT]'); process.exit(0); }
if (outAt < 0 || !args[outAt + 1]) throw Error('--out required');
for (let i = 0; i < args.length; i++) {
  if (!['--out', '--port'].includes(args[i]) || !args[++i]) throw Error('Invalid participant option');
}
const out = resolve(args[outAt + 1]), portAt = args.indexOf('--port');
const port = portAt < 0 ? 4886 : Number(args[portAt + 1]);
if (!Number.isSafeInteger(port) || port < 1024 || port > 65535 || existsSync(out)) throw Error('Use a valid port and new output directory');
mkdirSync(out, { recursive: true, mode: 0o700 });
const policy = JSON.parse(readFileSync(new URL('./policy.json', import.meta.url)));
const workspaceRoot = new URL('../../', import.meta.url);
const sourcePaths = ['qualification/workflow-generalization/participant.js',
  'qualification/workflow-generalization/fixture.js', 'qualification/workflow-generalization/forms.json',
  'qualification/workflow-generalization/oracle.json', 'qualification/workflow-generalization/contracts.js',
  'qualification/workflow-generalization/policy.json', 'src/service.js', 'src/admission.js', 'src/conditions.js',
  'src/client/trace-dag.js', 'src/client/field-group-scope.js', 'src/adapters/page-query.js',
  'src/adapters/playwright-adapter.js', '../../config/fawn-workspace-service.json'];
const hashes = () => Object.fromEntries(sourcePaths.map(path => [path, sha256Hex(readFileSync(new URL(path, workspaceRoot)))]));
const sourceHashes = hashes();
const fixture = await createFixture(), token = randomBytes(32).toString('hex');
const dag = new TraceDag(policy.limits), steps = [
  { name: 'Teach the contact task', split: 'learn', variant: 'heldout', mode: 'learn' },
  { name: 'Reuse on reordered controls', split: 'evaluate', variant: 'reordered', mode: 'reuse' },
  { name: 'Repair an added question', split: 'evaluate', variant: 'extra-question', mode: 'reuse' },
  { name: 'Repeat the added-question task', split: 'evaluate', variant: 'extra-question', mode: 'reuse' },
];
const records = [];
let openedAt = null, nextIndex = 0;
let adapter, service, current = null, busy = false, stopped = false, origin, closed = false;
const save = () => writeFileSync(join(out, 'participant.json'), JSON.stringify({ schemaVersion: 1,
  classification: 'Participant interaction with offline contact projections; no live-site or retention qualification',
  participantSetupMs: records[0] && openedAt ? records[0].startedAt - openedAt : null,
  scriptAuthoringAndMaintenanceMs: null, records, completed: nextIndex === steps.length,
  sourceHashes, sourceUnchanged: JSON.stringify(hashes()) === JSON.stringify(sourceHashes),
  productAdvantageEstablished: false, fixtureHash: sha256Hex(readFileSync(new URL('./test-freeze-v2.json', import.meta.url))) }, null, 2), { mode: 0o600 });
const observe = async () => {
  if (!current) return null;
  current.observation = await service.observe(current.owner);
  return current.observation;
};
const verify = async () => {
  const result = await fixture.verify(current.id, current.page, policy.inputs);
  current.record.verification = result;
  current.record.elapsedMs = Date.now() - current.record.startedAt;
  if (current.record.repairStartedAt) current.record.repairElapsedMs = Date.now() - current.record.repairStartedAt;
  save();
  return result;
};
async function start() {
  const requestedAt = Date.now();
  if (current && !current.record.confirmedAt && !current.record.abandonedAt) throw Error('Verify or explicitly restart the current attempt');
  const index = nextIndex;
  if (index >= steps.length) return;
  const definition = steps[index], id = `participant-${records.length}`;
  const admin = { workspaceId: id, ...await service.createWorkspace({ workspaceId: id, scopedReads: true }) };
  await service.grantAuthorization({ ...admin, grantId: 'offline-contact', ownerId: 'agent', intents: ['offline-contact'],
    actionKinds: ['navigate', 'fill', 'select', 'click'], targetOrigins: [fixture.origin], pageIds: ['main'], readRegions: null });
  const owner = { workspaceId: id, ...await service.assignOwner({ ...admin, ownerId: 'agent' }) };
  const initial = await service.observe(owner);
  const url = fixture.add(id, 'greenhouse', definition.split, definition.variant);
  const navigation = await (await service.submitAction({ ...owner, observationVersion: initial.observationVersion,
    actionId: randomUUID(), authorizedIntent: 'offline-contact', kind: 'navigate', target: { url } })).result;
  if (navigation.outcome !== 'completed') throw Error('Local task did not open');
  const controller = new AbortController(), record = { ...definition, requestedAt, startedAt: Date.now(), humanActions: 0,
    repairRequests: 0, cachedSteps: 0, confirmedAt: null };
  records.push(record);
  current = { id, owner, admin, definition, record, controller, page: adapter._page(id, 'main') };
  const sessionOptions = { service, owner, pageId: 'main', intent: 'offline-contact', template: 'participant-contact-v1',
    accountScope: 'offline-participant', inputs: policy.inputs, intermediateClicks, signal: controller.signal,
    assertContext: async () => { controller.signal.throwIfAborted(); },
    authorizeStep: async ({ kind, slot, locator }) => {
      if (kind === 'click') {
        if (!intermediateClicks.some(candidate => JSON.stringify(candidate) === JSON.stringify(locator))) throw Error('Transition not authorized');
        return;
      }
      const allowed = groupsFor('greenhouse').flatMap(group => group.steps).filter(step => step.slot === slot);
      if (slot === 'city' && locator[1] === 'Current city') return;
      if (!allowed.some(step => step.kind === kind && step.locators.some(candidate => JSON.stringify(candidate) === JSON.stringify(locator)))) {
        throw Error('That slot does not match this field meaning');
      }
    } };
  current.recorder = dag.session({ ...sessionOptions, fieldGroups: groupsFor('greenhouse') });
  if (definition.mode === 'reuse') {
    const replay = await current.recorder.replay();
    record.cachedSteps = replay.steps;
    record.replayReason = replay.reason;
    if (replay.reason !== 'submit-boundary') {
      if (replay.reason !== 'unseen-branch') throw Error(`Replay stopped: ${replay.reason}`);
      record.repairRequests++;
      // Deliberately do not publish partial repaired suffixes: measure the actual missing feature.
      current.recorder = dag.session(sessionOptions);
    }
  }
  await observe(); await verify(); save();
}
async function act({ handle, slot }) {
  if (!current || current.record.confirmedAt || stopped) throw Error('No active task');
  const observation = await observe();
  const targets = observation.elements.filter(element => element.handle === handle);
  if (targets.length !== 1) throw Error('Choose one fresh control');
  const element = targets[0], isClick = element.tag === 'button';
  if (isClick && !intermediateClicks.some(locator => locator[1] === element.label)) throw Error('Final submission is excluded');
  if (!isClick && !Object.hasOwn(policy.inputs, slot)) throw Error('Choose a synthetic profile slot');
  if (current.record.repairRequests && !current.record.repairStartedAt) current.record.repairStartedAt = Date.now();
  current.record.humanActions++;
  let result;
  try {
    result = await current.recorder.record({ kind: isClick ? 'click' : element.tag === 'select' ? 'select' : 'fill',
      locator: structuralLocator(element), ...(!isClick ? { slot } : {}) }, observation);
  } catch (error) {
    stopped = true; current.record.error = error.message; save(); throw error;
  }
  if (result.status !== 'completed') { stopped = true; throw Error(`Action stopped: ${result.reason}; no automatic retry`); }
  await observe(); await verify();
}
async function confirm() {
  if (!current || stopped) throw Error('No confirmable task');
  const result = await verify();
  if (!result.completed) throw Error('Independent semantic check has not passed');
  if (current.definition.mode === 'learn') {
    const published = await current.recorder.finish();
    if (published.reason !== 'recorded-submit-boundary') throw Error('Could not publish verified teaching');
  }
  current.record.confirmedAt = Date.now();
  nextIndex++;
  current.record.elapsedMs = Date.now() - current.record.startedAt;
  current.record.completeTaskMs = Date.now() - current.record.requestedAt;
  save();
}
const view = () => ({ busy, stopped, index: nextIndex, total: steps.length,
  nextTask: nextIndex < steps.length ? steps[nextIndex].name : null,
  current: current ? { name: current.definition.name, record: current.record,
    observation: { text: current.observation?.text, elements: current.observation?.elements.map(({ handle, label, tag, value }) => ({ handle, label, tag, value })) } } : null,
  inputs: policy.inputs, records });
const html = `<!doctype html><meta charset="utf-8"><title>Fawn offline repeat test</title>
<style>body{font:16px system-ui;max-width:960px;margin:32px auto;padding:0 20px;color:#18242d;background:#f5f7f8}button,select{font:inherit;padding:8px;margin:4px}article{padding:16px;background:white;margin:12px 0;border:1px solid #bcc8cd;border-radius:8px}pre{white-space:pre-wrap}#error{color:#a11}small{display:block}</style>
<h1>Teach, reuse, repair, repeat</h1><p>Offline synthetic details only. No application will be sent. First teach the task by choosing the correct profile slot for each field, then advance using Continue and Review application. Inspect the review and confirm it.</p>
<p>The following tasks change the order and add a question. We measure the help actually needed. Repair learning is not implemented: the last task tests that gap.</p>
<button id="start">Start next task</button><button id="confirm">I checked the review; it is correct</button><button id="stop">Stop</button><button id="restart">Restart this attempt</button><p id="error"></p><h2 id="name"></h2><section id="controls"></section><h2>Synthetic profile</h2><pre id="profile"></pre><h2>Observed page and result</h2><pre id="page"></pre><h2>Recorded tasks</h2><pre id="records"></pre>
<script>
const key=location.hash.slice(1)||sessionStorage.getItem('fawn-repeat-key');if(key)sessionStorage.setItem('fawn-repeat-key',key);history.replaceState(null,'',location.pathname);let state,lastSignature;
async function request(path,input){const response=await fetch(path,{method:input?'POST':'GET',headers:{Authorization:'Bearer '+key,...(input?{'Content-Type':'application/json'}:{})},...(input?{body:JSON.stringify(input)}:{})});const result=await response.json();if(!response.ok)throw Error(result.error);return result;}
async function command(operation,input={}){try{document.querySelector('#error').textContent='';await request('/command',{operation,...input});await refresh();}catch(error){document.querySelector('#error').textContent=error.message;}}
async function refresh(){state=await request('/status');const signature=JSON.stringify(state);if(signature===lastSignature)return;lastSignature=signature;document.querySelector('#name').textContent=state.current?.name??'Ready';document.querySelector('#profile').textContent=JSON.stringify(state.inputs,null,2);document.querySelector('#page').textContent=state.current?.observation?.text??'';document.querySelector('#records').textContent=JSON.stringify(state.records.map(row=>({task:row.name,cachedSteps:row.cachedSteps,humanActions:row.humanActions,repairRequests:row.repairRequests,elapsedMs:row.completeTaskMs,verified:row.verification?.completed,abandoned:!!row.abandonedAt})),null,2);document.querySelector('#start').disabled=state.busy||state.stopped||!state.nextTask||!!(state.current&&!state.current.record.confirmedAt&&!state.current.record.abandonedAt);document.querySelector('#confirm').disabled=state.busy||state.stopped||!state.current?.record.verification?.completed||!!state.current?.record.confirmedAt;document.querySelector('#restart').disabled=state.busy||!state.current||!!state.current.record.confirmedAt;document.querySelector('#stop').disabled=!state.current||!!state.current.record.confirmedAt;const root=document.querySelector('#controls');root.replaceChildren();if(!state.current||state.busy||state.stopped||state.current.record.confirmedAt||state.current.record.abandonedAt)return;
for(const field of state.current.observation.elements){if(field.tag==='button'&&!['Continue','Review application'].includes(field.label))continue;const card=document.createElement('article'),title=document.createElement('strong');title.textContent=field.label;card.append(title);if(field.tag!=='button'){const value=document.createElement('small');value.textContent='Current value: '+field.value;card.append(value);const select=document.createElement('select');select.append(new Option('Choose the profile meaning',''));for(const slot of Object.keys(state.inputs))select.append(new Option(slot+' — '+state.inputs[slot],slot));card.append(select);const button=document.createElement('button');button.textContent='Fill this field';button.onclick=()=>command('act',{handle:field.handle,slot:select.value});card.append(button);}else{const button=document.createElement('button');button.textContent=field.label;button.onclick=()=>command('act',{handle:field.handle});card.append(button);}root.append(card);}}
document.querySelector('#start').onclick=()=>command('start');document.querySelector('#confirm').onclick=()=>command('confirm');document.querySelector('#stop').onclick=()=>command('stop');document.querySelector('#restart').onclick=()=>command('restart');setInterval(()=>refresh().catch(()=>{}),1500);refresh().catch(error=>document.querySelector('#error').textContent=error.message);
</script>`;
const server = createServer(async (req, res) => {
  res.setHeader('cache-control', 'no-store');
  res.setHeader('content-security-policy', "default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; connect-src 'self'; frame-ancestors 'none'; form-action 'none'");
  if (req.method === 'GET' && req.url === '/') { openedAt ??= Date.now(); res.setHeader('content-type', 'text/html'); res.end(html); return; }
  const supplied = Buffer.from(req.headers.authorization ?? ''), expected = Buffer.from(`Bearer ${token}`);
  if (supplied.length !== expected.length || !timingSafeEqual(supplied, expected)
    || (req.method === 'POST' && req.headers.origin !== origin)) { res.writeHead(403); res.end('{"error":"Unauthorized local test request"}'); return; }
  res.setHeader('content-type', 'application/json');
  try {
    if (req.method === 'GET' && req.url === '/status') { res.end(JSON.stringify(view())); return; }
    if (req.method !== 'POST' || req.url !== '/command') throw Error('Unknown route');
    let body = '';
    for await (const chunk of req) { body += chunk; if (Buffer.byteLength(body) > 4096) throw Error('Request too large'); }
    const input = JSON.parse(body);
    if (input.operation === 'stop') {
      stopped = true; current?.controller.abort();
      if (current) await service.assignOwner({ ...current.admin, ownerId: 'human' });
      save();
    }
    else {
      if (busy || (stopped && input.operation !== 'restart')) throw Error('The test is busy or stopped');
      busy = true;
      try {
        if (input.operation === 'restart') {
          if (!current || current.record.confirmedAt) throw Error('No restartable attempt');
          current.controller.abort();
          await service.assignOwner({ ...current.admin, ownerId: 'human' });
          current.record.abandonedAt = Date.now(); stopped = false; save();
        }
        else if (input.operation === 'start') await start();
        else if (input.operation === 'act') await act(input);
        else if (input.operation === 'confirm') await confirm();
        else throw Error('Unknown operation');
      } finally { busy = false; }
    }
    res.end(JSON.stringify(view()));
  } catch (error) { res.writeHead(400); res.end(JSON.stringify({ error: error.message })); }
});
try {
  service = await WorkspaceService.open({ stateDir: join(out, 'service'),
    config: loadServiceConfig(undefined, { browserChannel: 'chrome', headless: true }),
    createAdapter: options => (adapter = createPlaywrightAdapter(options)) });
  await new Promise((done, reject) => { server.once('error', reject); server.listen(port, '127.0.0.1', done); });
  origin = `http://127.0.0.1:${port}`;
  writeFileSync(join(out, 'access.private.json'), JSON.stringify({ url: `${origin}/#${token}` }), { mode: 0o600 });
  save();
  console.log(JSON.stringify({ participantUrl: `${origin}/#${token}`, report: join(out, 'participant.json') }));
} catch (error) { await service?.close(); await fixture.close(); throw error; }
const close = async () => {
  if (closed) return;
  closed = true; current?.controller.abort(); save(); await new Promise(done => server.close(done));
  await service.close(); await fixture.close();
};
process.once('SIGINT', () => close().finally(() => process.exit()));
process.once('SIGTERM', () => close().finally(() => process.exit()));
