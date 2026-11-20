// The planner's observation view names the controls that submit a form, so a click that
// admission would reject is not proposed in the first place.
import assert from 'node:assert/strict';
import { plannerView, navigationNotice } from '../../src/client/controller.js';
import { PLANNER_TOOLS } from '../../src/client/planner.js';

const view = plannerView({ url: 'https://example.test/issue', title: 'Issue', observationVersion: 3, isTruncated: false, text: 'Comment Post',
  elements: [
    { handle: 'h1', selector: '#body', role: 'textbox', label: 'Comment', digest: 'd1' },
    { handle: 'h2', selector: '#post', role: 'button', label: 'Post', formAction: 'https://example.test/issue/comments', digest: 'd2' },
    { selector: '#untargetable', role: 'button', label: 'No handle', formAction: 'https://example.test/x' },
  ] }, 'tracker');
assert.deepEqual(view.elements, [
  { handle: 'h1', selector: '#body', role: 'textbox', label: 'Comment' },
  { handle: 'h2', selector: '#post', role: 'button', label: 'Post', submitsForm: true },
]);
assert.ok(!JSON.stringify(view).includes('example.test/issue/comments'), 'the form destination itself is not disclosed to the planner');
assert.match(PLANNER_TOOLS.act, /submitsForm:true takes kind submit/);

// A navigation that lands on an error page says so in the result the planner reads.
const landed = status => ({ outcome: 'completed', evidence: { effect: { status, finalUrl: 'https://example.test/private' } } });
assert.match(navigationNotice({ kind: 'navigate' }, landed(404)).notice, /HTTP 404.*sign-in/);
assert.equal(navigationNotice({ kind: 'navigate' }, landed(200)).notice, undefined);
assert.equal(navigationNotice({ kind: 'click' }, landed(404)).notice, undefined, 'only navigations carry a response status');
assert.deepEqual(navigationNotice({ kind: 'navigate' }, { outcome: 'unknown' }), { outcome: 'unknown' });
console.log('ok: planner view marks form-submitting controls without disclosing the form destination; error-page navigations carry a notice');
