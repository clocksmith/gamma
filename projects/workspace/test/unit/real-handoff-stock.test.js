import assert from 'node:assert/strict';
import { validateStockProposal, recoverStockProposal } from '../../qualification/real-handoff-stock.js';
let browserCalls = 0;
const page = new Proxy({}, { get() { browserCalls++; throw Error('Browser API began'); } });
const pages = new Map([['main', page]]), observations = new Map([['main', { elements: [{ handle: 'h1', selector: '#post' }] }]]);
for (const [tool, input] of [['act', { kind: 'unsupported' }], ['act', { kind: 'click', target: { handle: 'missing' } }],
  ['act', { kind: 'navigate', target: { url: 'invalid' } }], ['observe', { pageId: 'missing' }], ['handoff_read', {}],
  ['act', { kind: 'fill', target: { handle: 'h1' }, params: { value: {} } }]]) {
  assert.throws(() => validateStockProposal(tool, input, pages, observations), error => recoverStockProposal(error));
}
assert.equal(browserCalls, 0, 'recoverable attestation precedes every Playwright call');
assert.equal(recoverStockProposal(Error('Failure after a click may have begun')), false);
assert.equal(recoverStockProposal({ code: 'STOCK_PROPOSAL_INVALID' }), false);
assert.equal(validateStockProposal('act', { kind: 'click', target: { handle: 'h1' } }, pages, observations).element.selector, '#post');
assert.equal(validateStockProposal('artifact_read', {}, pages, observations).page, page);

// The stronger control: what the tracker can check for itself on resume.
{
  const { uncertainStockActions } = await import('../../qualification/real-handoff-stock.js');
  const condition = { kind: 'element-text-includes', selector: '#comments', value: 'posted text' };
  const activity = [
    { event: 'tool-requested', callId: 'post', tool: 'act', input: { pageId: 'tracker', kind: 'click', target: { handle: 'h1' }, completion: { completedWhen: [condition] } } },
    { event: 'tool-result', callId: 'post', output: { error: 'Connection reset; outcome unknown', isUncertain: true } },
    { event: 'tool-requested', callId: 'single', tool: 'act', input: { kind: 'submit', target: { handle: 'h2' }, completion: { completedWhen: condition } } },
    { event: 'tool-result', callId: 'single', output: { isUncertain: true } },
    // No declared completion: nothing the tracker can check without a planner.
    { event: 'tool-requested', callId: 'bare', tool: 'act', input: { pageId: 'tracker', kind: 'click', target: { handle: 'h3' } } },
    { event: 'tool-result', callId: 'bare', output: { isUncertain: true } },
    // A settled action is not uncertain.
    { event: 'tool-requested', callId: 'fine', tool: 'act', input: { pageId: 'tracker', kind: 'fill', target: { handle: 'h4' }, completion: { completedWhen: [condition] } } },
    { event: 'tool-result', callId: 'fine', output: { ok: true } },
  ];
  assert.deepEqual(uncertainStockActions(activity), [{ forCallId: 'post', pageId: 'tracker', conditions: [condition] },
    { forCallId: 'single', pageId: 'main', conditions: [condition] }]);
  // Once a check established the effect, it is not repeated; an inconclusive one is tried again.
  activity.push({ event: 'tool-result', callId: 'c1', output: { forCallId: 'post', result: 'effect-present' } },
    { event: 'tool-result', callId: 'c2', output: { forCallId: 'single', result: 'inconclusive' } });
  assert.deepEqual(uncertainStockActions(activity).map(value => value.forCallId), ['single']);
}
console.log('ok: stock proposal recovery is limited to attested pre-browser failures; the stronger control selects only uncertain actions with a declared completion');
