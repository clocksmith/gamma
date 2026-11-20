import { MAX_PATCHES_V1, normalizePatchV1, schedulePatchDependenciesV1 } from '../src/client/patch-ir.js';

/**
 * Offline comparison for controlled qualification only. Supply patch declarations
 * and completed dispatch IDs from independent, trusted fixture code. This is not
 * an adapter, evidence verifier, authorization decision or execution schedule.
 */
export function compareObservedPatchOrderV1(declarations, observedIds) {
  if (!Array.isArray(declarations) || !Array.isArray(observedIds)
      || declarations.length === 0 || declarations.length > MAX_PATCHES_V1
      || declarations.length !== observedIds.length) {
    throw new TypeError('Patch shadow requires one declaration per completed dispatch');
  }
  const patches = Array.from(declarations, normalizePatchV1);
  const byId = new Map(patches.map(patch => [patch.id, patch]));
  const observedOrder = Object.freeze([...observedIds]);
  const positions = new Map(observedOrder.map((id, index) => [id, index]));
  if (positions.size !== observedOrder.length || byId.size !== patches.length
      || observedOrder.some(id => !byId.has(id))) {
    throw new TypeError('Patch shadow requires an exact, unique dispatch/declaration match');
  }

  const reference = observedOrder.map(id => byId.get(id));
  if (reference.some((patch, i) => patch.after.some(id => !positions.has(id) || positions.get(id) >= i))) {
    throw new TypeError('Observed order violates a declared patch dependency');
  }
  const { order } = schedulePatchDependenciesV1(reference);
  return Object.freeze({
    observedOrder,
    proposedOrder: Object.freeze(order),
    orderDiffers: order.some((id, index) => observedOrder[index] !== id),
  });
}
