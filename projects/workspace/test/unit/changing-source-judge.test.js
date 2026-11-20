// The changing-source investigation is accepted mechanically only when its conclusions rest on the
// sources as they are now. Each criterion fails alone; the diagnosis itself is never graded here.
import assert from 'node:assert/strict';
import { comparisonValidity, judgeChangingSourceInvestigation, ACCEPTANCE } from '../../qualification/changing-source-judge.js';
import { sha256Hex } from '../../src/journal.js';

const OLD = 'await this._closed;\n', NEW = 'if (await exitedWithin(timeoutMs)) return;\n', LAUNCHER = 'gracefullyClose();\n';
const CDP = 'src/adapters/cdp-adapter.js', LIB = 'node_modules/playwright-core/lib/server/utils/processLauncher.js';
const file = (id, path, content, revision = 1) => ({ id, kind: 'evidence', status: 'current', revision, text: path, dependsOn: [], source: { kind: 'repository', path, content, sha256: sha256Hex(content) } });
const note = (id, kind, dependsOn = [], extra = {}) => ({ id, kind, status: 'current', revision: 1, text: `${kind} ${id}`, dependsOn, source: null, ...extra });
function trial() {
  const artifacts = {
    cdp: file('cdp', CDP, NEW, 2), launcher: file('launcher', LIB, LAUNCHER),
    page: { id: 'page', kind: 'evidence', status: 'current', revision: 1, text: 'docs', dependsOn: [], source: { kind: 'page', url: 'https://docs.example/', content: 'docs', sha256: sha256Hex('docs') } },
    adapter: note('adapter', 'finding', ['cdp']), cause: note('cause', 'finding', ['launcher', 'page']),
    waits: note('waits', 'hypothesis', ['launcher'], { disposition: { state: 'supported', reason: 'the launcher awaits cleanup' } }),
    chrome: note('chrome', 'hypothesis', ['launcher'], { disposition: { state: 'rejected', reason: 'not shown by the source' } }),
    open: note('open', 'question'), next: note('next', 'decision', ['adapter']),
  };
  const activity = [{ seq: 5, event: 'tool-result', callId: 'a', output: { id: 'adapter' } }, { seq: 20, event: 'tool-result', callId: 'b', output: { id: 'adapter' } },
    { seq: 21, event: 'tool-result', callId: 'c', output: { id: 'next' } }];
  return { project: { artifacts, activity, run: { status: 'completed' } },
    options: { liveHashes: { [CDP]: sha256Hex(NEW), [LIB]: sha256Hex(LAUNCHER) }, changedSources: [CDP], restingOnChangingSource: ['adapter'], boundaries: { resumeStarted: 10 } } };
}
const grade = (mutate = () => {}) => { const value = trial(); mutate(value); return judgeChangingSourceInvestigation(value.project, value.options); };
const failing = (name, mutate) => { const result = grade(mutate); assert.equal(result.mechanicallyAccepted, false, name); assert.equal(result.checks[name], false, `${name}: ${JSON.stringify(result.checks)}`); return result; };

assert.equal(ACCEPTANCE.length, 8);
const good = grade();
assert.equal(good.mechanicallyAccepted, true, JSON.stringify(good.checks));
assert.equal(good.diagnosis.status, 'ungraded');
assert.deepEqual(good.counts, { evidence: 3, records: 6, hypotheses: 2, settledHypotheses: 2, rejectedHypotheses: 1, needingReview: 0,
  restingOnSupersededSource: 0, restedOnChangingSourceAtInterruption: 1, notWrittenAgain: 0 });

failing('finalCompleted', value => { value.project.run.status = 'needs-attention'; });
failing('evidenceIntact', value => { value.project.artifacts.launcher.source.content += 'edited'; });
failing('changedSourcesRead', value => { value.options.changedSources.push('docs/status/fawn-workspace.md'); });
failing('hypothesesSettled', value => { delete value.project.artifacts.chrome; });
failing('hypothesesSettled', value => { for (const key of ['waits', 'chrome']) value.project.artifacts[key].disposition = { state: 'open', reason: '' }; });
failing('noRecordNeedsReview', value => { value.project.artifacts.next.status = 'needs-review'; });
// The record still points at the file as it was before the commit: the control case where nothing re-read it.
const stale = failing('conclusionsOnCurrentSources', value => { value.project.artifacts.cdp = file('cdp', CDP, OLD); });
assert.equal(stale.counts.restingOnSupersededSource, 2, 'the finding and the decision built on it');
// Re-reading into a new record does not help while the conclusion still points at the old one.
failing('conclusionsOnCurrentSources', value => { value.project.artifacts.cdp = file('cdp', CDP, OLD); value.project.artifacts.cdp2 = file('cdp2', CDP, NEW); });
// A conclusion that rested on the changing source and was never written again was not rechecked.
failing('interruptedConclusionsRechecked', value => { value.project.activity = value.project.activity.filter(event => event.seq !== 20); });
failing('connectedDiagnosis', value => { value.project.artifacts.adapter.dependsOn = ['launcher']; value.project.artifacts.next.dependsOn = []; });
failing('connectedDiagnosis', value => { delete value.project.artifacts.open; });
// A source the trial did not pin (a page) never counts as superseded.
assert.equal(grade(value => { value.project.artifacts.page.source.content = 'other'; value.project.artifacts.page.source.sha256 = sha256Hex('other'); }).checks.conclusionsOnCurrentSources, true);
// A pair is comparable only when both arms reached the case the trial is for and no harness limit cut one short.
const armRow = (arm, extra = {}) => ({ arm, interrupted: true, restingOnChangingSource: ['adapter'], plannerErrors: ['Interrupted'], ...extra });
assert.deepEqual(comparisonValidity([armRow('fawn'), armRow('stock')]), { valid: true, reasons: [] });
// The retained second run: the control's first agent stopped on the per-request cap before recording anything.
const cut = comparisonValidity([armRow('fawn'), armRow('stock', { interrupted: undefined, restingOnChangingSource: [], plannerErrors: ['Planner per-request budget reached'] })]);
assert.equal(cut.valid, false);
assert.deepEqual(cut.reasons.map(entry => entry.arm), ['stock', 'stock']);
assert.match(cut.reasons[0].reason, /harness limit.*per-request budget/);
assert.match(cut.reasons[1].reason, /not interrupted/);
assert.equal(comparisonValidity([armRow('fawn', { plannerErrors: ['Planner deadline exceeded', 'Planner deadline exceeded'] }), armRow('stock')]).reasons[0].reason,
  'a harness limit stopped a planner request: Planner deadline exceeded');
assert.equal(comparisonValidity([armRow('fawn', { error: 'Error: boom' }), armRow('stock')]).valid, false);
assert.equal(comparisonValidity([armRow('fawn')]).valid, false, 'one arm is not a comparison');
// A planner's own mistake is the arm's result, not a harness limit.
assert.equal(comparisonValidity([armRow('fawn', { plannerErrors: ['Planner returned no valid structured tool proposal'] }), armRow('stock')]).valid, true);
console.log('ok: a cut-short arm invalidates the pair, conclusions must rest on current sources, interrupted conclusions must be written again, each criterion fails alone, diagnosis left ungraded');
