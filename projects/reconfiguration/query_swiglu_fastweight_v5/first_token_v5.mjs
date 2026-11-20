// Restrict only the first greedy token to starts observed in this table's support.
// The raw winner comes from the normal full-vocabulary argmax. Ties follow vocabulary order.
export function firstSupportToken(logits, raw, starts) {
  if (!starts.length) throw new Error('No supported code starts');
  let best = starts[0];
  for (const token of starts) {
    if (!Number.isInteger(token) || token < 0 || token >= logits.length) {
      throw new Error(`Invalid support token ID: ${token}`);
    }
    if (logits[token] > logits[best] || (logits[token] === logits[best] && token < best)) best = token;
  }
  return { raw, best_allowed: best, logit_gap: logits[raw] - logits[best] };
}
