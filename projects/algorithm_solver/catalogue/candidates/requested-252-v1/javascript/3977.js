/**
 * 3977. Minimum Time to Reach Target With Limited Power
 * Candidate source; not executed, syntax-checked, tested, or qualified.
 * Specification: https://leetcode.com/problems/minimum-time-to-reach-target-with-limited-power/description/
 * Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3900-3999/3977.Minimum%20Time%20to%20Reach%20Target%20With%20Limited%20Power/README_EN.md
 * Complexity: O(power*(n+m)) time, O(n*power + m) space.
 * Positive departure costs make remaining-power states acyclic even when graph nodes contain cycles. Target incurs no cost unless departed. Minimum time, then maximum remaining power. Inputs preserved.
 */

function solve(n, edges, power, cost, source, target) {
  const graph = Array.from({ length: n }, () => []);
  for (const [start, end, duration] of edges) graph[start].push([end, duration]);
  const distance = Array.from({ length: n }, () => new Float64Array(power + 1).fill(Infinity));
  distance[source][power] = 0;
  for (let remaining = power; remaining >= 0; remaining--) {
    for (let node = 0; node < n; node++) {
      const current = distance[node][remaining];
      if (!Number.isFinite(current) || remaining < cost[node]) continue;
      const following = remaining - cost[node];
      for (const [neighbor, duration] of graph[node]) {
        distance[neighbor][following] = Math.min(distance[neighbor][following], current + duration);
      }
    }
  }
  let best = Infinity, reserve = -1;
  for (let remaining = 0; remaining <= power; remaining++) {
    if (distance[target][remaining] <= best && Number.isFinite(distance[target][remaining])) {
      best = distance[target][remaining]; reserve = remaining;
    }
  }
  return Number.isFinite(best) ? [best, reserve] : [-1, -1];
}

function minTimeMaxPower(n, edges, power, cost, source, target) {
  return solve(n, edges, power, cost, source, target);
}

class Solution {
  minTimeMaxPower(n, edges, power, cost, source, target) {
    return solve(n, edges, power, cost, source, target);
  }
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { solve, minTimeMaxPower, Solution };
}
