import assert from 'node:assert/strict';
import { inspectBeginFrame } from '../support/headless-render-control.js';

const available = await inspectBeginFrame(async (method, params) => {
  assert.equal(method, 'HeadlessExperimental.beginFrame');
  assert.equal(params.screenshot.format, 'png');
  return { hasDamage: true, screenshotData: Buffer.from('fixture bytes').toString('base64') };
});
assert.equal(available.status, 'available');
assert.equal(available.screenshot.toString(), 'fixture bytes');
const unsupported = await inspectBeginFrame(async () => {
  throw Error("Protocol error (HeadlessExperimental.beginFrame): 'HeadlessExperimental.beginFrame' wasn't found");
});
assert.equal(unsupported.status, 'unsupported');
for (const message of ['Target closed', 'Browser launch timed out', 'Invalid parameters']) {
  await assert.rejects(inspectBeginFrame(async () => { throw Error(message); }), error => error.message === message);
}
console.log('ok: method absence is unsupported; transport and invocation failures remain failures');
