// Pure grading shared by the live trial and adversarial regression controls.
import { sha256Hex } from '../src/journal.js';
const normalized = text => typeof text === 'string' ? text.trim().replace(/\s+/g, ' ') : '';
const samePage = (left, right) => {
  try { const a = new URL(left), b = new URL(right); a.hash = ''; b.hash = ''; return a.href === b.href; }
  catch { return false; }
};
export function judgeHandoff(project, { tracker, docsUrl, repositoryFiles, repostBeforeEstablishing }) {
  const artifacts = Object.values(project.artifacts), current = value => value.status === 'current';
  const evidence = artifacts.filter(a => a.kind === 'evidence');
  const pageIds = new Set(evidence.filter(a => current(a) && a.source.kind === 'page' && samePage(a.source.url, docsUrl)).map(a => a.id));
  const repoIds = repositoryFiles.map(path => new Set(evidence.filter(a => current(a) && a.source.kind === 'repository' && a.source.path === path).map(a => a.id)));
  const findings = artifacts.filter(a => a.kind === 'finding' && current(a) && normalized(a.text)
    && a.dependsOn.some(id => pageIds.has(id)) && repoIds.every(ids => a.dependsOn.some(id => ids.has(id))));
  const checks = {
    runCompleted: project.run?.status === 'completed',
    findingConnected: findings.length > 0,
    questionAndDecision: ['question', 'decision'].every(kind => artifacts.some(a => a.kind === kind && current(a) && normalized(a.text))),
    trackerPostedOnce: tracker.commits === 1 && tracker.comments.length === 1
      && findings.some(finding => normalized(tracker.comments[0]) === normalized(finding.text)),
    evidenceIntact: evidence.every(a => a.source.sha256 === sha256Hex(a.source.content ?? '')),
    noRepostBeforeEstablishing: repostBeforeEstablishing === false,
  };
  return { checks, accepted: Object.values(checks).every(Boolean), trackerCommits: tracker.commits, duplicatePosts: Math.max(0, tracker.commits - 1) };
}
export function repostCheck(activity, startSeq, { trackerPageId, trackerUrl }) {
  const requested = new Map(), pageUrls = new Map([[trackerPageId, trackerUrl]]);
  let established = false;
  for (const event of activity) {
    if (event.event === 'tool-requested') {
      requested.set(event.callId, event);
      const pageId = event.input?.pageId ?? 'main';
      if (event.tool === 'act' && event.input?.kind === 'navigate') pageUrls.set(pageId, event.input.target?.url);
      const couldPost = pageId === trackerPageId || event.input?.effect?.effectKey === 'tracker-comment'
        || !pageUrls.has(pageId) || samePage(pageUrls.get(pageId), trackerUrl);
      if (event.seq > startSeq && event.tool === 'act' && couldPost
        && ['click', 'submit'].includes(event.input?.kind) && !established) return true;
    } else if (event.seq > startSeq && event.event === 'tool-result' && !event.output?.error) {
      const call = requested.get(event.callId);
      if (call?.tool === 'observe' && event.output?.pageId === (call.input?.pageId ?? 'main') && typeof event.output?.text === 'string') {
        pageUrls.set(event.output.pageId, event.output.url);
        if (samePage(event.output.url, trackerUrl)) established = true;
      }
      if (call?.tool === 'reconcile' && ['effect-present', 'effect-absent'].includes(event.output?.reconciliation?.result)) {
        const action = requested.get(call.input?.actionId);
        if (action?.tool === 'act' && action.input?.pageId === trackerPageId && action.input?.effect?.effectKey === 'tracker-comment'
          && event.output?.actionId === call.input.actionId) established = true;
      }
    }
  }
  return false;
}
