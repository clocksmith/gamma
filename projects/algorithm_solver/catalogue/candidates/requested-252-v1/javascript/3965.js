/**
 * 3965. Finish Time of Tasks I
 * Candidate source; not executed, syntax-checked, tested, or qualified.
 * Specification: https://leetcode.com/problems/finish-time-of-tasks-i/description/
 * Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3900-3999/3965.Finish%20Time%20of%20Tasks%20I/README_EN.md
 * Complexity: O(n) time and space, iterative traversal.
 * Edges are directed parent-child pairs as stated. Every task finish is guaranteed below 2^53; evaluate latest+(latest-earliest)+base, not an unsafe doubled intermediate. Inputs preserved; native method pending.
 */

function solve(n, edges, baseTime) {
  const children = Array.from({ length: n }, () => []);
  for (const [parent, child] of edges) children[parent].push(child);
  const order = [0];
  for (let index = 0; index < order.length; index++) {
    for (const child of children[order[index]]) order.push(child);
  }
  const finish = baseTime.slice();
  for (let index = n - 1; index >= 0; index--) {
    const node = order[index];
    if (children[node].length === 0) continue;
    let earliest = Infinity;
    let latest = -Infinity;
    for (const child of children[node]) {
      earliest = Math.min(earliest, finish[child]);
      latest = Math.max(latest, finish[child]);
    }
    finish[node] = latest + (latest - earliest) + baseTime[node];
  }
  return finish[0];
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { solve };
}
