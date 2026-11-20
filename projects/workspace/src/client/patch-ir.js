// An analysis-only IR for trusted, already-described local operations.
// Predicates and verifier identities are data. This module cannot execute or
// authorize a patch, resolve resource aliases, or certify an adapter's effects.
export const PATCH_IR_V1 = 'gamma.patch/v1';
export const MAX_PATCHES_V1 = 128;
const MAX_DECLARATIONS = 32;
const ID = /^[a-zA-Z0-9._:/-]{1,128}$/;
const MODES = new Set(['local', 'ambient', 'external', 'unknown']);
const validId = value => typeof value === 'string' && ID.test(value);
const exactKeys = (value, keys) => value !== null && typeof value === 'object' && !Array.isArray(value)
  && Object.keys(value).sort().join(',') === keys;
const invalid = message => { throw new TypeError(message); };

function idSet(value, label) {
  if (!Array.isArray(value) || value.length > MAX_DECLARATIONS
      || [...value].some(id => !validId(id)) || new Set(value).size !== value.length) {
    invalid(`Invalid or ambiguous patch ${label}`);
  }
  return [...value].sort();
}

function facts(value, resources, label) {
  if (!Array.isArray(value) || value.length > MAX_DECLARATIONS) invalid(`Invalid patch ${label}`);
  const seen = new Set();
  const allowed = new Set(resources);
  for (const entry of value) {
    if (!exactKeys(entry, 'fact,resource') || !validId(entry.resource) || !validId(entry.fact)
        || !allowed.has(entry.resource) || seen.has(entry.resource)) {
      invalid(`Invalid or ambiguous patch ${label} resource`);
    }
    seen.add(entry.resource);
  }
  return value.map(({ resource, fact }) => ({ resource, fact }))
    .sort((a, b) => a.resource < b.resource ? -1 : a.resource > b.resource ? 1 : 0);
}

export function normalizePatchV1(patch) {
  if (!exactKeys(patch, 'after,effects,guards,id,mode,reads,verifier,version,writes')
      || patch.version !== PATCH_IR_V1 || !validId(patch.id) || !MODES.has(patch.mode)) {
    invalid('Invalid patch IR v1 declaration');
  }
  const { verifier } = patch;
  if (!exactKeys(verifier, 'id,version') || !validId(verifier.id)
      || !Number.isSafeInteger(verifier.version) || verifier.version < 1) {
    invalid('Patch must declare an unambiguous verifier identity and version');
  }
  const reads = idSet(patch.reads, 'reads');
  const writes = idSet(patch.writes, 'writes');
  const after = idSet(patch.after, 'dependencies');
  if (after.includes(patch.id)) invalid('Patch cannot depend on itself');
  const guards = facts(patch.guards, reads, 'guard');
  const effects = facts(patch.effects, writes, 'effect');
  if (patch.mode === 'local' && effects.length !== writes.length) {
    invalid('Local patch must declare an effect for every write');
  }
  return { version: PATCH_IR_V1, id: patch.id, mode: patch.mode, reads, writes, guards, effects,
    verifier: { id: verifier.id, version: verifier.version }, after };
}

function canCommute(a, b) {
  if (a.mode !== 'local' || b.mode !== 'local') return false;
  const aObserved = new Set([...a.reads, ...a.writes]);
  const bObserved = new Set([...b.reads, ...b.writes]);
  return a.writes.every(r => !bObserved.has(r)) && b.writes.every(r => !aObserved.has(r));
}

/**
 * The input is a recorded/reference serial order of trusted, canonically
 * named resources. Explicit dependencies supplement that order. Consequences
 * outside the known-local declarations fence every prior and later step.
 * Returns only a dependency graph and one lexicographic topological order.
 */
export function schedulePatchDependenciesV1(serial) {
  if (!Array.isArray(serial) || serial.length > MAX_PATCHES_V1) invalid('Invalid patch schedule size');
  const patches = Array.from(serial, normalizePatchV1);
  const ids = new Set(patches.map(patch => patch.id));
  if (ids.size !== patches.length) invalid('Ambiguous duplicate patch ID');
  const successors = new Map([...ids].map(id => [id, new Set()]));
  const inDegree = new Map([...ids].map(id => [id, 0]));
  function add(before, after) {
    if (successors.get(before).has(after)) return;
    successors.get(before).add(after);
    inDegree.set(after, inDegree.get(after) + 1);
  }

  for (const patch of patches) for (const before of patch.after) {
    if (!ids.has(before)) invalid(`Unknown patch dependency: ${before}`);
    add(before, patch.id);
  }
  for (const [i, before] of patches.entries()) {
    for (let j = i + 1; j < patches.length; j++) {
      const after = patches[j];
      if (!canCommute(before, after)) add(before.id, after.id);
    }
  }

  const ready = [...ids].filter(id => inDegree.get(id) === 0).sort().reverse();
  const order = [];
  while (ready.length) {
    const id = ready.pop();
    order.push(id);
    for (const next of successors.get(id)) {
      const remaining = inDegree.get(next) - 1;
      inDegree.set(next, remaining);
      if (remaining === 0) ready.push(next);
    }
    ready.sort().reverse();
  }
  if (order.length !== patches.length) invalid('Cyclic patch dependencies or incompatible reference order');

  const dependencies = [...ids].sort().flatMap(before =>
    [...successors.get(before)].sort().map(after => ({ before, after })));
  return { version: PATCH_IR_V1, order, dependencies };
}
