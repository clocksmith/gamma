// Only pre-Playwright proposal validation can attest that no browser call began.
export function validateStockProposal(tool, input, pages, observations) {
  const reject = message => {
    const error = Error(message); error.code = 'STOCK_PROPOSAL_INVALID';
    error.details = { neverDispatched: { code: error.code } }; throw error;
  };
  if (!['observe', 'capture', 'repository_read', 'record', 'artifact_read', 'act'].includes(tool)) reject(`Unsupported tool ${tool}`);
  const pageId = input.pageId ?? 'main', page = pages.get(pageId);
  if (['observe', 'capture', 'act'].includes(tool) && !page) reject('Unknown page');
  if (tool !== 'act') return { input, pageId, page };
  if (!['navigate', 'fill', 'click', 'submit'].includes(input.kind)) reject(`Unsupported action ${input.kind}`);
  if (typeof input.target === 'string') input = { ...input, target: /^https?:/.test(input.target) ? { url: input.target } : { handle: input.target } };
  if (input.kind === 'navigate') {
    let url; try { url = new URL(input.target?.url); } catch { reject('Navigate requires an absolute HTTP(S) URL'); }
    if (!['http:', 'https:'].includes(url.protocol)) reject('Navigate requires an absolute HTTP(S) URL');
    return { input, pageId, page };
  }
  const element = observations.get(pageId)?.elements.find(value => value.handle === input.target?.handle);
  if (!element) reject('Observe this page before acting; unknown handle');
  if (input.kind === 'fill' && typeof (input.params?.value ?? '') !== 'string') reject('Fill value must be text');
  return { input, pageId, page, element };
}
export const recoverStockProposal = error => error.code === 'STOCK_PROPOSAL_INVALID'
  && error.details?.neverDispatched?.code === error.code;

/**
 * What a durable tracker can check for itself on resume: each action whose outcome came back unknown
 * and that declared how its completion shows on the page. Already-checked actions are not repeated.
 */
export function uncertainStockActions(activity) {
  const requests = new Map(activity.filter(event => event.event === 'tool-requested').map(event => [event.callId, event]));
  const checked = new Set(activity.filter(event => event.event === 'tool-result' && event.output?.result === 'effect-present' && event.output.forCallId)
    .map(event => event.output.forCallId));
  return activity.filter(event => event.event === 'tool-result' && event.output?.isUncertain && !checked.has(event.callId)).flatMap(event => {
    const request = requests.get(event.callId), declared = request?.input?.completion?.completedWhen;
    const conditions = Array.isArray(declared) ? declared : declared && typeof declared === 'object' ? [declared] : [];
    return request?.tool === 'act' && conditions.length ? [{ forCallId: event.callId, pageId: request.input.pageId ?? 'main', conditions }] : [];
  });
}
