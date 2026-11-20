import assert from 'node:assert/strict';
import { chromium } from 'playwright-core';
import { queryPage, snapshotArgs, buildSnapshot } from '../../src/adapters/page-query.js';
import { loadServiceConfig } from '../../src/config.js';
import { scopeWorkflowObservation } from '../../src/client/workflow-agent.js';
const browser = await chromium.launch({ channel: 'chrome', headless: true });
try {
  const page = await browser.newPage();
  await page.setContent(`<label>Search<input id="search" type="search"></label>
    <aside inert id="drawer"><label>Drawer field<input id="inside"></label></aside>
    <label hidden>Hidden field<input id="hidden"></label>
    <fieldset disabled><label>Disabled field<input id="disabled"></label></fieldset>`);
  const config = loadServiceConfig();
  const snapshot = async () => buildSnapshot(await page.evaluate(queryPage, snapshotArgs(config)), 1);
  const before = await snapshot();
  assert.equal(before.elements.find(e=>e.selector==='#inside').actionability.inert, true);
  assert.equal(before.elements.find(e=>e.selector==='#hidden').actionability.visible, false);
  assert.equal(before.elements.find(e=>e.selector==='#disabled').actionability.disabled, true);
  const locators = [['textbox','Search','input','search'],['textbox','Drawer field','input','text'],
    ['textbox','Hidden field','input','text'],['textbox','Disabled field','input','text']];
  const projected = scopeWorkflowObservation({ observe: async()=>before }, 'test', locators);
  assert.deepEqual((await projected.service.observe({})).elements.map(e=>e.selector), ['#search']);
  await page.locator('#drawer').evaluate(node=>node.inert=false);
  const after = await snapshot();
  assert.notEqual(before.elements.find(e=>e.selector==='#inside').digest,
    after.elements.find(e=>e.selector==='#inside').digest, 'Ancestor interactivity changes target identity');
  assert.equal(after.elements.find(e=>e.selector==='#inside').actionability.inert, false);
  await page.addStyleTag({content:'/* CSSOM test */'});
  const styled = await snapshot();
  const htmlBeforeCssChange = await page.content();
  await page.evaluate(()=>document.styleSheets[document.styleSheets.length-1].insertRule('#search { visibility: hidden }'));
  assert.equal(await page.content(), htmlBeforeCssChange, 'CSSOM mutation does not alter serialized HTML');
  const cssChanged = await snapshot();
  assert.notEqual(styled.contentHash, cssChanged.contentHash, 'CSSOM-only visibility changes observation identity');
  console.log('ok: actual Chromium visibility, inert ancestor, disabled fieldset and task-scoped handles');
} finally { await browser.close(); }
