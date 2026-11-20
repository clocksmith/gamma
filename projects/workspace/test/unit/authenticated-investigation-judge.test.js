// The authenticated investigation's acceptance is mechanical and re-gradable from saved records.
// It must not pass on page captures and linked notes alone, and it never grades the diagnosis.
import assert from 'node:assert/strict';
import { judgeAuthenticatedInvestigation, gradeDiagnosis, ACCEPTANCE, DIAGNOSIS_UNGRADED } from '../../qualification/authenticated-investigation-judge.js';
import { sha256Hex } from '../../src/journal.js';

const issueUrl = 'https://tracker.example/acme/checkout/issues/7';
const CODE_PATH = 'src/cache.js', CODE_BYTES = 'export const TTL_SECONDS = 900;\n';
const code = { kind: 'repository', paths: [CODE_PATH, 'src/checkout.js'], hashes: { [CODE_PATH]: sha256Hex(CODE_BYTES) } };
const pageEvidence = (id, url, content) => ({ id, kind: 'evidence', status: 'current', text: `Page evidence: ${id}`, dependsOn: [],
  source: { kind: 'page', pageId: 'main', url, content, sha256: sha256Hex(content) } });
const fileEvidence = (id, path, content) => ({ id, kind: 'evidence', status: 'current', text: `Repository evidence: ${path}`, dependsOn: [],
  source: { kind: 'repository', path, content, sha256: sha256Hex(content) } });
const note = (id, kind, dependsOn = [], text = `${kind} ${id}`) => ({ id, kind, status: 'current', text, dependsOn, source: null });
let seq = 0;
const call = (tool, input, output) => { const callId = `c${++seq}`; return [{ seq: ++seq, event: 'tool-requested', callId, tool, input },
  ...(output === undefined ? [] : [{ seq: ++seq, event: 'tool-result', callId, output }])]; };
function trial(codeArtifact = fileEvidence('code', CODE_PATH, CODE_BYTES)) {
  seq = 0;
  const artifacts = {
    issue: pageEvidence('issue', issueUrl, 'Open, 2 comments'), code: codeArtifact,
    fresh: pageEvidence('fresh', `${issueUrl}#comment-3`, 'Open, 3 comments. Rolled back.'),
    summary: note('summary', 'finding', ['issue', 'code']), state: note('state', 'finding', ['fresh']),
    open: note('open', 'question'), next: note('next', 'decision'),
  };
  const activity = [...call('capture', { pageId: 'main' }, artifacts.issue), ...call('repository_read', { path: CODE_PATH }, artifacts.code)];
  const boundaries = { interrupted: seq, resumeStarted: seq };
  activity.push(...call('observe', { pageId: 'main' }, { text: 'Page not found' }), ...call('ask_human', { reason: 'Sign in' }), { seq: ++seq, event: 'ask_human', text: 'Sign in' });
  activity.push({ seq: ++seq, event: 'human-note', text: 'Signed in again; continue.' });
  boundaries.secondSignIn = seq;
  activity.push(...call('capture', { pageId: 'main' }, artifacts.fresh), ...call('record', { kind: 'finding' }, artifacts.summary), ...call('record', { kind: 'question' }, artifacts.open),
    ...call('record', { kind: 'decision' }, artifacts.next), ...call('record', { kind: 'finding' }, artifacts.state));
  return { project: { artifacts, activity, run: { status: 'completed' } },
    options: { issueUrl, code, boundaries, evidenceAtInterruption: ['issue', 'code'], freshMarker: 'Rolled back' } };
}
const grade = (mutate = () => {}, codeArtifact) => { const value = trial(codeArtifact); mutate(value); return judgeAuthenticatedInvestigation(value.project, value.options); };

assert.equal(ACCEPTANCE.length, 7);
const good = grade();
assert.equal(good.mechanicallyAccepted, true, JSON.stringify(good.checks));
assert.equal(good.accepted, undefined, 'the judge alone never accepts a trial');
assert.deepEqual(good.diagnosis, DIAGNOSIS_UNGRADED);
assert.deepEqual(good.counts, { evidence: 3, issueEvidence: 2, declaredCodeEvidence: 1, otherEvidence: 0, evidenceAtInterruption: 2, findings: 2,
  questions: 1, decisions: 1, signInRequests: 1, dispatchedNonNavigation: 0, recordsWhileSignedOut: 0 });

const failing = (name, mutate, codeArtifact) => { const result = grade(mutate, codeArtifact);
  assert.equal(result.mechanicallyAccepted, false, name); assert.equal(result.checks[name], false, `${name}: ${JSON.stringify(result.checks)}`); return result; };

// Review case: page captures only, a finding that admits it has no code diagnosis, and unrelated
// question and decision records. Any second page used to count as code evidence.
const fabricated = failing('evidenceBeforeInterruption', value => {
  value.project.artifacts.summary.text = 'No code diagnosis provided';
  value.project.artifacts.open.text = 'What is for lunch?'; value.project.artifacts.next.text = 'Decide later.';
}, pageEvidence('code', 'https://tracker.example/', 'Welcome to the tracker'));
assert.equal(fabricated.checks.summaryConnected, false);
assert.deepEqual([fabricated.counts.declaredCodeEvidence, fabricated.counts.otherEvidence], [0, 1]);

// Code evidence must be a repository record for a declared file, carrying that file's bytes.
failing('evidenceBeforeInterruption', () => {}, pageEvidence('code', 'https://tracker.example/acme/checkout/blob/main/src/cache.js', CODE_BYTES));
failing('summaryConnected', () => {}, fileEvidence('code', 'README.md', '# readme'));
failing('summaryConnected', () => {}, fileEvidence('code', '../outside/src/cache.js', CODE_BYTES));
failing('summaryConnected', () => {}, fileEvidence('code', '/etc/passwd', 'root'));
failing('summaryConnected', () => {}, fileEvidence('code', CODE_PATH, 'invented contents that are not the file'));
failing('summaryConnected', value => { value.project.artifacts.code.source.sha256 = 'f'.repeat(64); });
// When the trial supplied file hashes, a declared file without one cannot be verified and does not count.
failing('summaryConnected', () => {}, fileEvidence('code', 'src/checkout.js', 'export function total() {}\n'));
// A trial that supplied no hashes accepts a declared file on its own binding.
assert.equal(grade(value => { value.options.code = { kind: 'repository', paths: ['src/checkout.js'] }; },
  fileEvidence('code', 'src/checkout.js', 'export function total() {}\n')).mechanicallyAccepted, true);
// A trial that declared pages as its code sources accepts exactly those pages.
const pages = value => { value.options.code = { kind: 'pages', urls: ['https://tracker.example/acme/checkout/blob/main/src/cache.js'] }; };
assert.equal(grade(pages, pageEvidence('code', 'https://tracker.example/acme/checkout/blob/main/src/cache.js?plain=1', CODE_BYTES)).mechanicallyAccepted, true);
failing('evidenceBeforeInterruption', pages, pageEvidence('code', 'https://tracker.example/acme/checkout/blob/main/src/other.js', CODE_BYTES));
assert.throws(() => grade(value => { delete value.options.code; }), /Declare the code sources/);
assert.throws(() => grade(value => { value.options.code = { kind: 'repository', paths: [] }; }), /Declare the code sources/);

failing('evidenceIntact', value => { value.project.artifacts.issue.source.content += ' edited after saving'; });
failing('evidenceIntact', value => { delete value.project.artifacts.code; value.project.artifacts.summary.dependsOn = ['issue']; });
// A person signing in without being asked is not the agent detecting the loss.
failing('askedForSignIn', value => { value.project.activity = value.project.activity.filter(event => event.event !== 'ask_human'); });
failing('readOnly', value => { value.project.activity.push(...call('act', { kind: 'fill', target: { handle: 'h1' }, params: { value: 'x' } }, { outcome: 'completed' })); });
failing('finalCompleted', value => { value.project.run.status = 'needs-attention'; });
failing('summaryConnected', value => { value.project.artifacts.summary.dependsOn = ['issue']; });
failing('summaryConnected', value => { delete value.project.artifacts.open; });
// A state finding that rests on the capture from before the interruption is stale.
failing('currentStateFromLivePage', value => { value.project.artifacts.state.dependsOn = ['issue']; });
failing('currentStateFromLivePage', value => { value.options.freshMarker = 'text that never appeared'; });
// A refused proposal is not a dispatched action.
const refused = grade(value => { value.project.activity.push(...call('act', { kind: 'fill', target: { handle: 'h1' } }), { seq: ++seq, event: 'tool-failed', callId: `c${seq - 1}`, error: 'refused' }); });
assert.equal(refused.checks.readOnly, true);

// Acceptance needs a person's verdict on the diagnosis as well as the mechanical checks.
const graded = gradeDiagnosis(good, { correct: true, gradedBy: 'owner', basis: 'sealed cause traced before the trial' });
assert.equal(graded.accepted, true); assert.equal(graded.diagnosis.status, 'graded');
assert.equal(gradeDiagnosis(good, { correct: false, gradedBy: 'owner', basis: 'names the wrong cause' }).accepted, false);
assert.equal(gradeDiagnosis(fabricated, { correct: true, gradedBy: 'owner', basis: 'n/a' }).accepted, false, 'a correct diagnosis cannot rescue failed mechanical checks');
assert.throws(() => gradeDiagnosis(good, { correct: true, gradedBy: '', basis: 'x' }), /who graded it/);
assert.throws(() => gradeDiagnosis(good, { correct: 'yes', gradedBy: 'owner', basis: 'x' }), /boolean verdict/);
console.log('ok: declared code evidence required, fabricated page-only case rejected, each criterion failing alone, diagnosis graded separately by a person');
