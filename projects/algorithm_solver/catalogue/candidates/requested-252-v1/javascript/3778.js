/**
 * 3778. Minimum Distance Excluding One Maximum Weighted Edge
 * Authored candidate: not executed, imported, syntax-checked, tested, or qualified.
 * Signature: solve(n, edges).
 * Algorithm: Dijkstra on (vertex, free-edge-used), allowing exactly one traversed edge at zero cost.
 * Complexity: O((n+m) log(n+m)) time; O(n+m) space.
 * Numeric semantics: Exact integer arithmetic on the published input bounds; JavaScript Number results remain safe integers.
 * Mutation: Does not mutate input arrays, rows, strings, or trees.
 * Interface: Ordered-positional solve; native forwarding name included only when confirmed.
 * Specification: https://leetcode.com/problems/minimum-distance-excluding-one-maximum-weighted-edge/description/
 * Consulted public statement/reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3700-3799/3778.Minimum%20Distance%20Excluding%20One%20Maximum%20Weighted%20Edge/README_EN.md
 * Reference repository attribution: Doocs contributors, CC-BY-SA-4.0.
 * New readable implementations; no third-party source bodies copied verbatim.
 * No protected tests or private reference implementations used.
 * Contract note: For any path, choosing its free edge optimally removes a maximum weight. Ties have the same cost; only the minimum cost is returned. The impl processes the supplied edges without assuming a smaller edge-count bound.
 */

class MinHeap {
  constructor(less = (left, right) => left < right) {
    this.items = [];
    this.less = less;
  }
  get size() {
    return this.items.length;
  }
  push(value) {
    const items = this.items;
    let position = items.length;
    items.push(value);
    while (position > 0) {
      const parent = Math.floor((position - 1) / 2);
      if (!this.less(value, items[parent])) break;
      items[position] = items[parent];
      position = parent;
    }
    items[position] = value;
  }
  pop() {
    const items = this.items;
    if (items.length === 0) throw new RangeError("Empty heap.");
    const result = items[0];
    const last = items.pop();
    if (items.length > 0) {
      let position = 0;
      while (2 * position + 1 < items.length) {
        let child = 2 * position + 1;
        if (child + 1 < items.length && this.less(items[child + 1], items[child])) child += 1;
        if (!this.less(items[child], last)) break;
        items[position] = items[child];
        position = child;
      }
      items[position] = last;
    }
    return result;
  }
}

function solve(n, edges) {
  const adjacency = Array.from({ length: n }, () => []);
  for (const [first, second, weight] of edges) {
    adjacency[first].push([second, weight]);
    adjacency[second].push([first, weight]);
  }
  const distances = Array.from({ length: n }, () => [Infinity, Infinity]);
  distances[0][0] = 0;
  const pending = new MinHeap((left, right) => left[0] < right[0]);
  pending.push([0, 0, 0]);
  while (pending.size > 0) {
    const [cost, node, used] = pending.pop();
    if (cost !== distances[node][used]) continue;
    if (node === n - 1 && used === 1) return cost;
    for (const [neighbor, weight] of adjacency[node]) {
      const paid = cost + weight;
      if (paid < distances[neighbor][used]) {
        distances[neighbor][used] = paid;
        pending.push([paid, neighbor, used]);
      }
      if (used === 0 && cost < distances[neighbor][1]) {
        distances[neighbor][1] = cost;
        pending.push([cost, neighbor, 1]);
      }
    }
  }
  return -1;
}

function minCostExcludingMax(n, edges) {
  return solve(n, edges);
}

class Solution {
  minCostExcludingMax(n, edges) {
    return solve(n, edges);
  }
}

if (typeof module !== "undefined" && module.exports) {
  module.exports = { solve, minCostExcludingMax, Solution };
}
