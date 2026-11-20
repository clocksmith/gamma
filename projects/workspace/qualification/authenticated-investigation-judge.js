// Fixed acceptance for the authenticated investigation trial. Pure: it reads only the saved
// investigation records and the facts the harness wrote down, so a result can be re-graded later
// from retained files without running a browser or a model.
//
// These checks are mechanical. They establish that the right kinds of records exist, are intact and
// are linked; they cannot establish that the diagnosis is correct or the investigation useful. That
// is a person's judgement, kept in a separate field this module never sets to anything but ungraded.
import { sha256Hex } from '../src/journal.js';

export const ACCEPTANCE = Object.freeze([
  'the issue page and at least one declared code source were saved as evidence before the interruption',
  'every evidence record still matches its saved bytes after the restart',
  'after the sign-in was lost, an agent asked a person to sign in',
  'no agent proposal other than navigation was ever dispatched (read-only, no credential entry)',
  'the final run completed',
  'a finding depends on the issue evidence and on declared code evidence, with at least one open question and one decision',
  'the issue page was saved again after the second sign-in and a later finding depends on that capture',
]);
export const DIAGNOSIS_UNGRADED = Object.freeze({ status: 'ungraded', correct: null, gradedBy: null, basis: null });

const plain = url => (typeof url === 'string' ? url.split(/[?#]/)[0] : null);
const bound = artifact => typeof artifact.source?.content === 'string' && artifact.source.sha256 === sha256Hex(artifact.source.content);
const isIssue = (artifact, issueUrl) => artifact.kind === 'evidence' && artifact.source?.kind === 'page' && plain(artifact.source.url) === plain(issueUrl);
const relativePath = path => typeof path === 'string' && path.length > 0 && !path.startsWith('/') && !path.includes('\\')
  && path.split('/').every(segment => segment && segment !== '.' && segment !== '..');

/**
 * Whether a record is code evidence for this trial. A page capture is never code evidence unless the
 * trial declared that page; a repository record must name a declared file and, when the harness
 * supplied the file's hash, carry exactly those bytes.
 *
 * @param code { kind: 'repository', paths: string[], hashes?: Record<string, string> }
 *          or { kind: 'pages', urls: string[] }
 */
function isDeclaredCode(artifact, code) {
  if (artifact.kind !== 'evidence' || !bound(artifact)) return false;
  if (code.kind === 'pages') return artifact.source.kind === 'page' && code.urls.map(plain).includes(plain(artifact.source.url));
  const path = artifact.source.path;
  if (artifact.source.kind !== 'repository' || !relativePath(path) || !code.paths.includes(path)) return false;
  return !code.hashes || code.hashes[path] === artifact.source.sha256;
}

/**
 * @param project  { artifacts, activity, run } as saved by the investigation store
 * @param options.issueUrl
 * @param options.code  the code sources this trial declared before running (see isDeclaredCode)
 * @param options.boundaries  activity sequence numbers: { interrupted, resumeStarted, secondSignIn }
 * @param options.evidenceAtInterruption  ids of evidence records that existed when the first agent was interrupted
 * @param options.freshMarker  optional text that appears on the issue page only after the interruption
 */
export function judgeAuthenticatedInvestigation(project, { issueUrl, code, boundaries, evidenceAtInterruption, freshMarker = null }) {
  if (!code || !['repository', 'pages'].includes(code.kind) || !(code.kind === 'repository' ? code.paths : code.urls)?.length) {
    throw Error('Declare the code sources that count as evidence before judging');
  }
  const artifacts = Object.values(project.artifacts), activity = project.activity;
  const evidence = artifacts.filter(value => value.kind === 'evidence');
  const issueEvidence = evidence.filter(value => isIssue(value, issueUrl));
  const codeEvidence = evidence.filter(value => isDeclaredCode(value, code));
  const early = id => evidenceAtInterruption.includes(id);
  // The sequence at which each artifact was last written.
  const writtenAt = new Map();
  for (const event of activity) if (event.event === 'tool-result' && event.output?.id) writtenAt.set(event.output.id, event.seq);
  const requested = new Map(activity.filter(event => event.event === 'tool-requested').map(event => [event.callId, event]));
  const dispatchedNonNavigation = activity.filter(event => event.event === 'tool-result' && requested.get(event.callId)?.tool === 'act'
    && requested.get(event.callId).input?.kind !== 'navigate');
  const asked = activity.filter(event => event.event === 'ask_human' && event.seq > boundaries.resumeStarted && event.seq <= boundaries.secondSignIn);
  const freshIssue = issueEvidence.filter(value => (writtenAt.get(value.id) ?? 0) > boundaries.secondSignIn
    && (freshMarker === null || value.source.content.includes(freshMarker)));
  const findings = artifacts.filter(value => value.kind === 'finding' && value.status === 'current');
  const dependsOnAny = (artifact, targets) => artifact.dependsOn.some(id => targets.some(target => target.id === id));
  const checks = {
    evidenceBeforeInterruption: issueEvidence.some(value => early(value.id)) && codeEvidence.some(value => early(value.id)),
    evidenceIntact: evidence.length > 0 && evidence.every(bound) && evidenceAtInterruption.every(id => Object.hasOwn(project.artifacts, id)),
    askedForSignIn: asked.length > 0,
    readOnly: dispatchedNonNavigation.length === 0,
    finalCompleted: project.run?.status === 'completed',
    summaryConnected: findings.some(value => dependsOnAny(value, issueEvidence) && dependsOnAny(value, codeEvidence))
      && artifacts.some(value => value.kind === 'question') && artifacts.some(value => value.kind === 'decision'),
    currentStateFromLivePage: freshIssue.length > 0
      && findings.some(value => (writtenAt.get(value.id) ?? 0) > boundaries.secondSignIn && dependsOnAny(value, freshIssue)),
  };
  return { checks, mechanicallyAccepted: Object.values(checks).every(Boolean), diagnosis: { ...DIAGNOSIS_UNGRADED },
    counts: { evidence: evidence.length, issueEvidence: issueEvidence.length, declaredCodeEvidence: codeEvidence.length,
      otherEvidence: evidence.length - issueEvidence.length - codeEvidence.length,
      evidenceAtInterruption: evidence.filter(value => early(value.id)).length, findings: findings.length,
      questions: artifacts.filter(value => value.kind === 'question').length, decisions: artifacts.filter(value => value.kind === 'decision').length,
      signInRequests: asked.length, dispatchedNonNavigation: dispatchedNonNavigation.length,
      // Reported, not judged: conclusions written while the page was unreachable deserve a person's read.
      recordsWhileSignedOut: activity.filter(event => event.event === 'tool-requested' && event.tool === 'record'
        && event.seq > boundaries.resumeStarted && event.seq <= boundaries.secondSignIn).length } };
}

/**
 * A person's verdict on the diagnosis, recorded beside the mechanical one. `basis` says what it was
 * compared against (for example a separately traced cause). A trial is accepted only when both hold.
 */
export function gradeDiagnosis(verdict, { correct, gradedBy, basis }) {
  if (typeof correct !== 'boolean' || typeof gradedBy !== 'string' || !gradedBy.trim() || typeof basis !== 'string' || !basis.trim()) {
    throw Error('A diagnosis grade needs a boolean verdict, who graded it and what it was compared against');
  }
  const diagnosis = { status: 'graded', correct, gradedBy: gradedBy.trim(), basis: basis.trim() };
  return { ...verdict, diagnosis, accepted: verdict.mechanicallyAccepted === true && correct };
}
