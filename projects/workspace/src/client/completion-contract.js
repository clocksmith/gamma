// Host-declared structural deliverables, never a model's claim of correctness or permission.
// Counts prove that current saved records exist, not that their conclusions are right.
const KINDS = ['assumption', 'finding', 'decision', 'question', 'hypothesis'];
export function completionContract(value = null) {
  if (value === null) return null;
  if (!value || typeof value !== 'object' || Array.isArray(value)
    || Object.keys(value).some(key => key !== 'requiredRecords')) throw Error('Invalid completion contract');
  const required = value.requiredRecords;
  if (!required || typeof required !== 'object' || Array.isArray(required)
    || Object.entries(required).some(([kind, count]) => !KINDS.includes(kind) || !Number.isInteger(count) || count < 1 || count > 32)) {
    throw Error('Completion contract requires known record kinds and counts from 1 to 32');
  }
  return Object.freeze({ requiredRecords: Object.freeze({ ...required }) });
}
export function completionProgress(records, contract) {
  if (!contract) return null;
  const current = Object.values(records).filter(record => record.status === 'current' && typeof record.text === 'string' && record.text.trim());
  const counts = Object.fromEntries(Object.keys(contract.requiredRecords).map(kind => [kind, current.filter(record => record.kind === kind).length]));
  const missing = Object.entries(contract.requiredRecords).filter(([kind, count]) => counts[kind] < count)
    .map(([kind, count]) => ({ kind, required: count, saved: counts[kind] }));
  return { requiredRecords: contract.requiredRecords, counts, missing, complete: missing.length === 0 };
}
export function incompleteDeliverables(progress) {
  if (!progress || progress.complete) return null;
  return 'Required current saved records are missing: ' + progress.missing.map(({ kind, required, saved }) => `${kind} ${saved}/${required}`).join(', ')
    + '. Save the required records with the record tool before finishing. A summary does not substitute for saved records. This check establishes presence, not factual correctness.';
}
