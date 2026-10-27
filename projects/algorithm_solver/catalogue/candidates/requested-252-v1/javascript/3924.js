/**
 * 3924. Minimum Threshold Path With Limited Heavy Edges
 * Candidate source; not executed, syntax-checked, tested, or qualified.
 * Specification: https://leetcode.com/problems/minimum-threshold-path-with-limited-heavy-edges/description/
 * Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3900-3999/3924.Minimum%20Threshold%20Path%20With%20Limited%20Heavy%20Edges/README_EN.md
 * Complexity: O((n+m) log(m+1)) time, O(n+m) space.
 * Threshold domain is nonnegative as illustrated by source==target returning 0. 0-1 BFS counts heavy edges. Native name pending.
 */

function solve(n, edges, source, target, k) {
  const graph = Array.from({ length: n }, () => []);
  for (const [first, second, weight] of edges) {
    graph[first].push([second, weight]);
    graph[second].push([first, weight]);
  }
  const thresholds = [...new Set([0, ...edges.map(edge => edge[2])])].sort((a, b) => a - b);
  function feasible(threshold) {
    const distances = Array(n).fill(n + 1);
    distances[source] = 0;
    // Integer-key deque avoids O(n) Array.unshift operations.
    const queue = new Map([[0, [source, 0]]]);
    let first = 0;
    let last = 1;
    while (first < last) {
      const [node, distance] = queue.get(first);
      queue.delete(first++);
      if (distance !== distances[node]) continue;
      if (node === target) return true;
      for (const [neighbor, weight] of graph[node]) {
        const heavy = weight > threshold ? 1 : 0;
        const updated = distance + heavy;
        if (updated <= k && updated < distances[neighbor]) {
          distances[neighbor] = updated;
          if (heavy) queue.set(last++, [neighbor, updated]);
          else queue.set(--first, [neighbor, updated]);
        }
      }
    }
    return false;
  }
  if (!feasible(thresholds[thresholds.length - 1])) return -1;
  let left = 0;
  let right = thresholds.length - 1;
  while (left < right) {
    const middle = Math.floor((left + right) / 2);
    if (feasible(thresholds[middle])) right = middle;
    else left = middle + 1;
  }
  return thresholds[left];
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { solve };
}
