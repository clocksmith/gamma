// Fawn workspace — document research workflow adapter
//
// Task logic only: follows index links whose text names a topic and extracts matching passages.

import { REJECTION_CODES } from '../errors.js';
import { OUTCOMES } from '../state.js';
import { findElement } from './owner-session.js';

const PASSAGE_SEPARATOR = /\n+/;

function settledOrStop(record, steps) {
  steps.push(record);
  return record.outcome === OUTCOMES.COMPLETED;
}

/**
 * @param {ReturnType<import('./owner-session.js').createOwnerSession>} session
 * @param {{runId: string, intent: string, indexUrl: string, topics: string[], maxDocuments: number}} task
 */
async function runDocumentResearch(session, { runId, intent, indexUrl, topics, maxDocuments }) {
  const steps = [];
  const findings = [];
  const skipped = [];
  const lowerTopics = topics.map((topic) => topic.toLowerCase());
  const navigateIndex = async (step) => settledOrStop(await session.act(await session.observe(), {
    actionId: `${runId}-index-${step}`,
    authorizedIntent: intent,
    kind: 'navigate',
    target: { url: indexUrl },
  }), steps);

  if (!await navigateIndex(0)) return { status: 'stopped', findings, skipped, steps };
  const index = await session.observe();
  const documents = index.elements
    .filter((element) => element.tag === 'a' && lowerTopics.some((topic) => element.text.toLowerCase().includes(topic)))
    .slice(0, maxDocuments)
    .map((element) => ({ href: element.href, text: element.text }));

  let onIndex = true;
  for (const [position, document] of documents.entries()) {
    if (!onIndex && !await navigateIndex(position)) return { status: 'stopped', findings, skipped, steps };
    const current = await session.observe();
    let record;
    try {
      record = await session.act(current, {
        actionId: `${runId}-open-${position}`,
        authorizedIntent: intent,
        kind: 'click',
        target: findElement(current, (element) => element.href === document.href, `link ${document.href}`),
        completion: { completedWhen: [{ kind: 'url-equals', value: document.href }] },
      });
    } catch (error) {
      // A document outside the granted origins is not readable for this task; record and move on.
      if (error.code !== REJECTION_CODES.UNAUTHORIZED_TARGET) throw error;
      skipped.push({ href: document.href, code: error.code });
      onIndex = true;
      continue;
    }
    onIndex = false;
    if (!settledOrStop(record, steps)) return { status: 'stopped', findings, skipped, steps };
    const page = await session.observe();
    const passages = page.text.split(PASSAGE_SEPARATOR)
      .filter((passage) => lowerTopics.some((topic) => passage.toLowerCase().includes(topic)));
    findings.push({ url: page.url, title: page.title, passages, observationVersion: page.observationVersion });
  }
  return { status: 'completed', findings, skipped, steps };
}

export { runDocumentResearch };
