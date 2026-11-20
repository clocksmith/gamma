// Fawn workspace — declarative page conditions
//
// Preconditions, completion and reconciliation checks share one evaluator table. A condition
// that cannot be evaluated is unestablished; it never passes by default.

import { REJECTION_CODES, workspaceError } from './errors.js';

const SINGLE_MATCH = 1;

const CONDITION_FIELDS = Object.freeze({
  'url-equals': ['value'],
  'url-not-equals': ['value'],
  'url-prefix': ['value'],
  'element-present': ['selector'],
  'element-absent': ['selector'],
  'element-text-includes': ['selector', 'value'],
  'element-text-excludes': ['selector', 'value'],
  'input-value-equals': ['selector', 'value'],
  'choice-equals': ['selector', 'value'],
  'input-files-equal': ['selector'],
});

const CONDITION_EVALUATORS = Object.freeze({
  'input-files-equal': async (probe, condition) => {
    const element = await probe.element(condition.selector);
    const files = element.files ?? null;
    const established = element.count === SINGLE_MATCH && element.inputType === 'file'
      && Array.isArray(files) && files.length === condition.files.length
      && files.every((file, index) => file.name === condition.files[index].name
        && file.byteLength === condition.files[index].byteLength);
    return { established, observed: { count: element.count, files } };
  },
  'url-equals': async (probe, condition) => {
    const url = await probe.url();
    return { established: url === condition.value, observed: url };
  },
  'url-not-equals': async (probe, condition) => {
    const url = await probe.url();
    return { established: url !== condition.value, observed: url };
  },
  'url-prefix': async (probe, condition) => {
    const url = await probe.url();
    return { established: url.startsWith(condition.value), observed: url };
  },
  'element-present': async (probe, condition) => {
    const element = await probe.element(condition.selector);
    return { established: element.count >= SINGLE_MATCH, observed: { count: element.count } };
  },
  'element-absent': async (probe, condition) => {
    const element = await probe.element(condition.selector);
    return { established: element.count === 0, observed: { count: element.count } };
  },
  'element-text-includes': async (probe, condition) => {
    const element = await probe.element(condition.selector);
    const established = element.count === SINGLE_MATCH && element.text.includes(condition.value);
    return { established, observed: { count: element.count, text: element.text } };
  },
  // Absence needs positive evidence: exactly one element whose text lacks the value.
  'element-text-excludes': async (probe, condition) => {
    const element = await probe.element(condition.selector);
    const established = element.count === SINGLE_MATCH && !element.text.includes(condition.value);
    return { established, observed: { count: element.count, text: element.text } };
  },
  'input-value-equals': async (probe, condition) => {
    const element = await probe.element(condition.selector);
    const established = element.count === SINGLE_MATCH && element.value === condition.value;
    return { established, observed: { count: element.count, value: element.value } };
  },
  // The choice the control shows: a native select's selected option (value or label), an ARIA
  // combobox's own value or text, or a listbox's single selected option.
  'choice-equals': async (probe, condition) => {
    const element = await probe.element(condition.selector);
    const choice = element.count === SINGLE_MATCH ? (element.choice ?? null) : null;
    const established = choice !== null && (choice.value === condition.value || choice.label === condition.value);
    return { established, observed: { count: element.count, choice } };
  },
});

/**
 * Reject condition specs the service cannot evaluate before any intent is admitted.
 * @param {unknown} conditions
 * @param {string[]} allowedKinds config.conditionKinds
 * @param {string} path
 */
function validateConditions(conditions, allowedKinds, path) {
  if (!Array.isArray(conditions)) {
    throw workspaceError(REJECTION_CODES.INVALID_COMMAND, `${path}: expected array`, {
      path,
      received: conditions,
    });
  }
  conditions.forEach((condition, index) => {
    const conditionPath = `${path}[${index}]`;
    const fields = CONDITION_FIELDS[condition?.kind];
    if (!fields || !allowedKinds.includes(condition.kind)) {
      throw workspaceError(REJECTION_CODES.UNSUPPORTED_CONDITION, `${conditionPath}.kind`, {
        path: `${conditionPath}.kind`,
        expected: allowedKinds,
        received: condition?.kind,
      });
    }
    for (const field of fields) {
      if (typeof condition[field] !== 'string' || condition[field].length === 0) {
        throw workspaceError(REJECTION_CODES.INVALID_COMMAND, `${conditionPath}.${field}`, {
          path: `${conditionPath}.${field}`,
          expected: 'non-empty string',
          received: condition[field],
        });
      }
    }
    if (condition.kind === 'input-files-equal' && (!Array.isArray(condition.files) || !condition.files.length
      || condition.files.some(file => typeof file?.name !== 'string' || !file.name
        || !Number.isSafeInteger(file.byteLength) || file.byteLength < 0))) {
      throw workspaceError(REJECTION_CODES.INVALID_COMMAND, `${conditionPath}.files: expected file names and byte lengths`);
    }
  });
}

/**
 * Evaluate every condition against the live page; failures to evaluate are unestablished.
 */
async function evaluateConditions(conditions, probe) {
  const results = [];
  for (const condition of conditions) {
    try {
      await probe.validate?.(condition);
      const result = await CONDITION_EVALUATORS[condition.kind](probe, condition);
      results.push({ condition, ...result });
    } catch (error) {
      results.push({ condition, established: false, observed: null, error: error.message });
    }
  }
  return { allEstablished: results.every((result) => result.established), results };
}

export { CONDITION_FIELDS, evaluateConditions, validateConditions };
