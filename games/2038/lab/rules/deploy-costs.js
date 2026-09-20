/**
 * Calculates the final Compute cost for a Deploy action at a given destination.
 *
 * - Location waiver at Human Access District ("consumer") sets cost to 0.
 * - Compute Estate ("cloud") subtracts 1 from the base Compute cost, floored at 0.
 * - Tactical price cut modifier waives the cost completely.
 *
 * @param {object|string} destination - The destination tile object or its category string.
 * @param {object} [options]
 * @param {number} [options.baseCost=1] - The standard/variant Deploy Compute cost.
 * @param {boolean} [options.tacticPriceCut=false] - Whether a tactical price cut is active.
 * @returns {number} The floored Compute cost (non-negative integer).
 */
export function calculateDeployComputeCost(destination, { baseCost = 1, tacticPriceCut = false } = {}) {
  if (tacticPriceCut) return 0;
  const category = typeof destination === "string" ? destination : destination?.category;
  if (category === "consumer") return 0;
  const rawCost = Number(baseCost);
  const cost = category === "cloud" ? Math.max(0, rawCost - 1) : rawCost;
  return Math.max(0, cost);
}
