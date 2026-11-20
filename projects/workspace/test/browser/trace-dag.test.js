// Synthetic ATS-style multi-step form; real stock Chromium and trusted workspace dispatch.
import assert from 'node:assert/strict';
import { createServer } from 'node:http';
import { randomUUID } from 'node:crypto';
import { mkdtempSync, readFileSync, writeFileSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { WorkspaceService } from '../../src/service.js';
import { loadServiceConfig } from '../../src/config.js';
import { createPlaywrightAdapter } from '../../src/adapters/playwright-adapter.js';
import { createCdpAdapter } from '../../src/adapters/cdp-adapter.js';
import { TraceDag } from '../../src/client/trace-dag.js';
import { structuralLocator } from '../../src/adapters/page-query.js';

let submissions = 0;
const server = createServer((req, res) => {
  if (req.url === '/submit') { submissions++; res.end('submitted'); return; }
  const suffix = randomUUID();
  const unseen = req.url.includes('unseen');
  const ambiguous = req.url.includes('ambiguous');
  res.setHeader('content-type', 'text/html');
  res.end(`<!doctype html><title>Requisition ${suffix}</title>
    <h1>Different job description ${suffix}</h1><main>
    <label for="name-${suffix}">Full name</label><input id="name-${suffix}" name="field-${suffix}">
    ${ambiguous ? '<label>Full name<input></label>' : ''}
    <label>Work mode<select id="mode-${suffix}">
    <option>Choose</option><option>Remote</option><option>Office</option></select></label>
    <button type="button" id="next-${suffix}">Continue</button></main>
    <script>
    document.querySelector('button').onclick = () => {
      const name = document.querySelector('input').value;
      const mode = document.querySelector('select').value;
      document.querySelector('main').innerHTML = '<p id="summary"></p><form action="/submit" method="post">'
        + '<label for="city-${suffix}">City</label><input id="city-${suffix}">'
        + ${JSON.stringify(unseen ? '<label>New question<input></label>' : '')}
        + '<button type="submit">Send application</button></form>';
      document.getElementById('summary').textContent = name + ' / ' + mode;
    };
    </script>`);
});
await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
const origin = `http://127.0.0.1:${server.address().port}`;
const root = mkdtempSync(join(tmpdir(), 'fawn-trace-dag-'));
const limits = { maxNodes: 64, maxEdges: 64, maxSteps: 12 };
const config = loadServiceConfig(undefined, {
  browserChannel: process.env.FAWN_WORKSPACE_TEST_BROWSER_CHANNEL ?? 'chrome', headless: true,
});
const receipts = [];
try {
  for (const [adapter, createAdapter] of Object.entries({ playwright: createPlaywrightAdapter, cdp: createCdpAdapter })) {
    const service = await WorkspaceService.open({ stateDir: join(root, adapter), config, createAdapter });
    try {
      const workspaceId = 'trace';
      const admin = { workspaceId, ...await service.createWorkspace({ workspaceId }) };
      const grant = { ...admin, grantId: 'form', ownerId: 'agent', intents: ['form'],
        actionKinds: ['navigate', 'fill', 'select', 'click'], targetOrigins: [origin] };
      await service.grantAuthorization(grant);
      const owner = { workspaceId, ...await service.assignOwner({ ...admin, ownerId: 'agent' }) };
      const navigate = async path => {
        const observation = await service.observe(owner);
        assert.equal((await (await service.submitAction({ ...owner, actionId: randomUUID(), authorizedIntent: 'form',
          observationVersion: observation.observationVersion, kind: 'navigate', target: { url: origin + path } })).result).outcome, 'completed');
      };
      await navigate('/board-a/jobs/one');
      const initial = await service.observe(owner);
      const locator = label => structuralLocator(initial.elements.find(element => element.label === label));
      const name = locator('Full name'), mode = locator('Work mode'), next = locator('Continue');
      const options = { service, owner, pageId: 'main', intent: 'form', template: 'fixture-form-v1',
        inputs: { name: 'PERSONAL_SENTINEL_ALPHA', mode: 'Remote', city: 'CITY_SENTINEL_ALPHA' }, intermediateClicks: [next] };
      let dag = new TraceDag(limits);
      const recording = dag.session(options);
      let plannerCalls = 0;
      // A controlled recording planner requests the four steps. Replay gets no planner port.
      const plan = async spec => { plannerCalls++; return recording.record(spec); };
      assert.equal((await plan({ kind: 'fill', locator: name, slot: 'name' })).status, 'completed');
      assert.equal((await service.observe(owner)).structuralHash, initial.structuralHash, 'Filling leaves the structural outline unchanged');
      assert.equal((await plan({ kind: 'select', locator: mode, slot: 'mode' })).status, 'completed');
      assert.equal((await plan({ kind: 'click', locator: next })).status, 'completed');
      const city = structuralLocator((await service.observe(owner)).elements.find(element => element.label === 'City'));
      assert.equal((await plan({ kind: 'fill', locator: city, slot: 'city' })).status, 'completed');
      assert.equal((await recording.finish()).reason, 'recorded-submit-boundary');
      const encoded = JSON.stringify(dag.export());
      for (const privateText of ['PERSONAL_SENTINEL', 'CITY_SENTINEL', origin, 'Full name', 'Continue', initial.elements[0].selector]) {
        assert.ok(!encoded.includes(privateText), `Cache must not retain ${privateText}`);
      }
      const path = join(root, `${adapter}-private-cache.json`);
      writeFileSync(path, encoded, { mode: 0o600 });
      dag = TraceDag.restore(JSON.parse(readFileSync(path)), limits);
      await navigate('/board-b/jobs/two');
      const second = await service.observe(owner);
      assert.equal(second.structuralHash, initial.structuralHash);
      assert.notEqual(second.contentHash, initial.contentHash);
      assert.notEqual(second.elements[0].selector, initial.elements[0].selector);
      const replayOptions = { ...options, inputs: { name: 'PERSONAL_SENTINEL_BETA', mode: 'Office', city: 'CITY_SENTINEL_BETA' } };
      const beforeCalls = plannerCalls;
      const start = performance.now();
      const replay = await dag.session(replayOptions).replay();
      const elapsedMs = performance.now() - start;
      assert.equal(replay.reason, 'submit-boundary');
      assert.equal(replay.steps, 4);
      assert.equal(plannerCalls - beforeCalls, 0);
      const reviewed = await service.observe(owner);
      assert.ok(reviewed.text.includes('PERSONAL_SENTINEL_BETA / Office'));
      assert.equal(reviewed.elements.find(element => element.label === 'City').value, 'CITY_SENTINEL_BETA');
      const submit = structuralLocator(reviewed.elements.find(element => element.formAction));
      assert.equal((await dag.session({ ...options, intermediateClicks: [submit] })
        .record({ kind: 'click', locator: submit })).reason, 'unsupported-target', 'A native submit cannot masquerade as an intermediate click');
      assert.equal(submissions, 0);

      // Commuting stage-1 order (mode -> name -> next -> city) reconverges as a confluent diamond.
      await navigate('/board-diamond/jobs/reordered');
      const reorderedSession = dag.session(options);
      assert.equal((await reorderedSession.record({ kind: 'select', locator: mode, slot: 'mode' })).status, 'completed');
      assert.equal((await reorderedSession.record({ kind: 'fill', locator: name, slot: 'name' })).status, 'completed');
      assert.equal((await reorderedSession.record({ kind: 'click', locator: next })).status, 'completed');
      assert.equal((await reorderedSession.record({ kind: 'fill', locator: city, slot: 'city' })).status, 'completed');
      assert.equal((await reorderedSession.finish()).reason, 'recorded-submit-boundary');
      assert.equal(dag.compressionStats().confluentDiamonds, 1);

      // Modular recipe composition (stage 1 + stage 2) and mid-recipe stage-2 entry.
      await navigate('/board-compose/stage-one');
      const stageOneDag = new TraceDag(limits);
      const stageTwoDag = new TraceDag(limits);
      stageTwoDag.key = stageOneDag.key;
      const recStageOne = stageOneDag.session(options);
      await recStageOne.record({ kind: 'fill', locator: name, slot: 'name' });
      await recStageOne.record({ kind: 'select', locator: mode, slot: 'mode' });
      await recStageOne.record({ kind: 'click', locator: next });
      assert.equal((await recStageOne.finish()).reason, 'recorded-submit-boundary');
      const recStageTwo = stageTwoDag.session(options);
      await recStageTwo.record({ kind: 'fill', locator: city, slot: 'city' });
      assert.equal((await recStageTwo.finish()).reason, 'recorded-submit-boundary');
      const composed = TraceDag.compose(stageOneDag.export(), stageTwoDag.export(), limits);
      await navigate('/board-compose/full-replay');
      const composedReplay = await composed.session(replayOptions).replay();
      assert.equal(composedReplay.reason, 'submit-boundary');
      assert.equal(composedReplay.steps, 4);
      await navigate('/board-compose/mid-entry');
      const stageOneOnly = stageOneDag.session(replayOptions);
      assert.equal((await stageOneOnly.replay()).reason, 'submit-boundary');
      const midEntryReplay = await composed.session(replayOptions).replay();
      assert.equal(midEntryReplay.reason, 'submit-boundary');
      assert.equal(midEntryReplay.steps, 1, 'Mid-recipe entry executes only the remaining stage-2 suffix');

      await navigate('/board-c/jobs/unseen');
      const branch = await dag.session(replayOptions).replay();
      assert.equal(branch.reason, 'unseen-branch');
      assert.equal(branch.steps, 3, 'New question stops replay before filling the next stage');
      assert.equal((await service.observe(owner)).elements.find(element => element.label === 'City').value, '');
      await navigate('/board-d/jobs/ambiguous');
      assert.equal((await dag.session(options).record({ kind: 'fill', locator: name, slot: 'name' })).reason, 'ambiguous-locator');
      await navigate('/board-e/jobs/five');
      assert.equal((await dag.session({ ...replayOptions, inputs: {} }).replay()).reason, 'missing-input-slot');
      assert.equal((await dag.session(options).record({ kind: 'fill', locator: name, params: { value: 'never cache' } })).reason, 'uncacheable-step');
      assert.equal((await dag.session(options).record({ kind: 'submit', locator: next })).reason, 'uncacheable-step');
      const noClicks = await dag.session({ ...replayOptions, intermediateClicks: [] }).replay();
      assert.equal(noClicks.reason, 'intermediate-click-not-authorized');
      assert.equal(noClicks.steps, 2);
      await navigate('/board-f/jobs/six');
      const staleService = {
        outstanding: command => service.outstanding(command),
        observe: command => service.observe(command),
        submitAction: async command => {
          await service.observe(owner); // Another observation supersedes the cached step's binding.
          return service.submitAction(command);
        },
      };
      await assert.rejects(dag.session({ ...replayOptions, service: staleService }).replay(), error => error.code === 'stale-observation');
      assert.equal((await service.observe(owner)).elements.find(element => element.label === 'Full name').value, '');
      await service.revokeAuthorization({ ...admin, grantId: 'form' });
      await assert.rejects(dag.session(replayOptions).replay(), /authoriz|grant/i);
      await service.grantAuthorization(grant);
      await service.assignOwner({ ...admin, ownerId: 'human' });
      await assert.rejects(dag.session(replayOptions).replay(), /owner|generation/i);
      assert.equal(submissions, 0);
      receipts.push({ adapter, recordedSteps: 4, replaySteps: replay.steps, replayPlannerCalls: plannerCalls - beforeCalls,
        elapsedMs, submissions, unseenBranchStopsAtStep: branch.steps });
    } finally { await service.close(); }
  }
  console.log(JSON.stringify({ classification: 'synthetic browser development check, not ATS qualification or comparative performance', receipts }));
} finally { await new Promise(resolve => server.close(resolve)); rmSync(root, { recursive: true, force: true }); }
