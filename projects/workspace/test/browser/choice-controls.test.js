// Real stock Chromium: custom widgets are observable and targetable, and `select` reports a
// choice as completed only when the page keeps it, through both adapters.
import assert from 'node:assert/strict';
import { createServer } from 'node:http';
import { mkdtempSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { randomUUID } from 'node:crypto';
import { WorkspaceService } from '../../src/service.js';
import { loadServiceConfig } from '../../src/config.js';
import { createPlaywrightAdapter } from '../../src/adapters/playwright-adapter.js';
import { createCdpAdapter } from '../../src/adapters/cdp-adapter.js';

// Each popup opens 50 ms after its click, as many widget libraries do. `revert` puts its text
// back 15 ms after a choice (late hydration); `elsewhere` shows its choice beside an empty input.
const PAGE = `<!doctype html><title>Choices</title>
<select id="native"><option value="">Pick</option><option value="y">Yes</option><option value="n">No</option></select>
<div id="sponsor-box"><div id="sponsor" role="combobox" tabindex="0" aria-haspopup="listbox" aria-expanded="false" aria-controls="sponsor-list">Choose</div>
<ul id="sponsor-list" role="listbox" hidden><li role="option">Yes, I need sponsorship</li><li role="option">No sponsorship</li></ul></div>
<div id="revert-box"><div id="revert" role="combobox" tabindex="0" aria-expanded="false" aria-controls="revert-list">Choose</div>
<ul id="revert-list" role="listbox" hidden><li role="option">Remote</li><li role="option">Onsite</li></ul></div>
<div id="elsewhere-box"><input id="elsewhere" role="combobox" aria-expanded="false" aria-controls="elsewhere-list" value=""><span id="elsewhere-shown"></span>
<ul id="elsewhere-list" role="listbox" hidden><li role="option">Full time</li><li role="option">Contract</li></ul></div>
<script>
function wire(id, { revertAfterMs = null, showIn = null } = {}) {
  const box = document.getElementById(id);
  const list = document.getElementById(box.getAttribute('aria-controls'));
  box.addEventListener('click', () => setTimeout(() => { list.hidden = false; box.setAttribute('aria-expanded', 'true'); }, 50));
  list.addEventListener('click', (event) => {
    const option = event.target.closest('[role=option]');
    if (!option) return;
    list.querySelectorAll('[role=option]').forEach((each) => each.setAttribute('aria-selected', String(each === option)));
    list.hidden = true;
    box.setAttribute('aria-expanded', 'false');
    const shown = option.textContent.trim();
    if (showIn) document.getElementById(showIn).textContent = shown;
    else box.textContent = shown;
    if (revertAfterMs !== null) setTimeout(() => { box.textContent = 'Choose'; }, revertAfterMs);
  });
}
wire('sponsor');
wire('revert', { revertAfterMs: 15 });
wire('elsewhere', { showIn: 'elsewhere-shown' });
</script>`;

const server = createServer((req, res) => {
  res.setHeader('content-type', 'text/html');
  res.end(PAGE);
});
await new Promise((resolve) => server.listen(0, '127.0.0.1', resolve));
const origin = `http://127.0.0.1:${server.address().port}`;
const root = mkdtempSync(join(tmpdir(), 'fawn-choices-'));
const base = loadServiceConfig(undefined, { browserChannel: process.env.FAWN_WORKSPACE_TEST_BROWSER_CHANNEL ?? 'chrome', headless: true });
// A short completion window keeps the never-shown cases quick; it still exceeds the 50 ms popups.
const config = { ...base, dispatch: { ...base.dispatch, completionTimeoutMs: 1500 } };
try {
  for (const [name, createAdapter] of Object.entries({ playwright: createPlaywrightAdapter, cdp: createCdpAdapter })) {
    const service = await WorkspaceService.open({ stateDir: join(root, name), config, createAdapter });
    try {
      const workspaceId = 'choices';
      const admin = { workspaceId, ...await service.createWorkspace({ workspaceId }) };
      await service.grantAuthorization({ ...admin, grantId: 'form', ownerId: 'agent', intents: ['form'],
        actionKinds: ['navigate', 'select'], targetOrigins: [origin] });
      const owner = { workspaceId, ...await service.assignOwner({ ...admin, ownerId: 'agent' }) };
      const act = async (spec) => {
        const observation = await service.observe(owner);
        const target = spec.selector ? observation.elements.find((element) => element.selector === spec.selector) : undefined;
        if (spec.selector) assert.ok(target, `${name}: ${spec.selector} must be observable`);
        return (await service.submitAction({ ...owner, actionId: randomUUID(), authorizedIntent: 'form',
          observationVersion: observation.observationVersion, kind: spec.kind, target: target ?? spec.target,
          ...(spec.params ? { params: spec.params } : {}), ...(spec.completion ? { completion: spec.completion } : {}) })).result;
      };
      assert.equal((await act({ kind: 'navigate', target: { url: `${origin}/form` } })).outcome, 'completed');

      const native = await act({ kind: 'select', selector: '#native', params: { value: 'No' } });
      assert.equal(native.outcome, 'completed', `${name}: a native select chosen by label`);
      assert.equal(native.outcomeBasis, 'value-verified');

      const custom = await act({ kind: 'select', selector: '#sponsor', params: { value: 'No sponsorship' } });
      assert.equal(custom.outcome, 'completed', `${name}: a div combobox whose options appear late`);
      assert.equal(custom.outcomeBasis, 'value-verified');
      const outline = await service.observe({ ...owner, view: 'outline', regions: ['#sponsor-box'] });
      assert.match(outline.regions['#sponsor-box'].outline, /combobox "No sponsorship" = "No sponsorship"/);

      const reverted = await act({ kind: 'select', selector: '#revert', params: { value: 'Remote' } });
      assert.equal(reverted.outcome, 'unknown', `${name}: a choice the page resets is not success`);
      assert.equal(reverted.outcomeBasis, 'value-reverted');

      const elsewhere = await act({ kind: 'select', selector: '#elsewhere', params: { value: 'Contract' } });
      assert.equal(elsewhere.outcome, 'unknown', `${name}: a choice shown beside an empty input is not verified`);
      assert.equal(elsewhere.outcomeBasis, 'value-unverified');
      const declared = await act({ kind: 'select', selector: '#elsewhere', params: { value: 'Full time' },
        completion: { completedWhen: [{ kind: 'element-text-includes', selector: '#elsewhere-shown', value: 'Full time' }] } });
      assert.equal(declared.outcome, 'completed', `${name}: the caller can name where the page shows the choice`);
      assert.equal(declared.outcomeBasis, 'completion-condition');

      const missing = await act({ kind: 'select', selector: '#sponsor', params: { value: 'Maybe' } });
      assert.equal(missing.outcome, 'unknown', `${name}: an option that never appears`);
      assert.equal(missing.outcomeBasis, 'effect-exception');
      console.log(`ok: ${name} native and custom choices, late popups, reverted and unverified choices`);
    } finally {
      await service.close();
    }
  }
} finally {
  await new Promise((resolve) => server.close(resolve));
  rmSync(root, { recursive: true, force: true });
}
