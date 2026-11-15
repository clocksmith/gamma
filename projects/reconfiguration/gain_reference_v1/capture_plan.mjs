export const SAME_PASS_REFERENCE = 'same-pass-content-complement/v1';
export function capturePlan(contract, candidate) {
  if (candidate.reference === 'A') return {reference: 'A', contentSpan: null};
  if (candidate.reference !== SAME_PASS_REFERENCE) throw Error('Unsupported prospective reference rule');
  const count = contract.inputIds.length;
  const templates = contract.span.templatePositions;
  if (!Array.isArray(templates) || templates.some(i=>!Number.isInteger(i)||i<0||i>=count)) {
    throw Error('Exact original template positions required');
  }
  const excluded = new Set(templates);
  let start = 0, stop = count;
  while (excluded.has(start) && start < stop) start++;
  while (excluded.has(stop - 1) && stop > start) stop--;
  if (templates.some(i=>i>=start&&i<stop) || start>contract.span.start || stop<contract.span.stop ||
      stop-start<=contract.span.stop-contract.span.start) {
    throw Error('Original content must be contiguous and have a nonempty instruction complement');
  }
  return {reference: SAME_PASS_REFERENCE, contentSpan: {start, stop}};
}
