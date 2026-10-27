/**
 * 3923. Minimum Generations to Target Point
 * Candidate source; not executed, syntax-checked, tested, or qualified.
 * Specification: https://leetcode.com/problems/minimum-generations-to-target-point/description/
 * Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3900-3999/3923.Minimum%20Generations%20to%20Target%20Point/README_EN.md
 * Complexity: O(U^2) time, O(U) space, U <= 7^3.
 * Generations are simultaneous. Only pairs involving newly available points need processing. Distinct coordinate pairs, no self-pairing. Native name pending.
 */

function solve(points, target) {
  const known = points.map(point => point.slice());
  const encode = point => (point[0] * 7 + point[1]) * 7 + point[2];
  const seen = new Set(known.map(encode));
  const destination = encode(target);
  if (seen.has(destination)) return 0;
  let firstNew = 0;
  let generation = 0;
  while (firstNew < known.length) {
    const pending = new Map();
    const oldSize = known.length;
    for (let first = firstNew; first < oldSize; first += 1) {
      for (let second = 0; second < first; second += 1) {
        const point = known[first].map((value, axis) => Math.floor((value + known[second][axis]) / 2));
        const key = encode(point);
        if (!seen.has(key)) pending.set(key, point);
      }
    }
    generation += 1;
    if (pending.has(destination)) return generation;
    firstNew = oldSize;
    for (const [key, point] of pending) {
      seen.add(key);
      known.push(point);
    }
  }
  return -1;
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { solve };
}
