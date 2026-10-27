/**
 * 3928. Minimum Cost to Buy Apples II
 * Candidate source; not executed, syntax-checked, tested, or qualified.
 * Specification: https://leetcode.com/problems/minimum-cost-to-buy-apples-ii/description/
 * Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3900-3999/3928.Minimum%20Cost%20to%20Buy%20Apples%20II/README_EN.md
 * Complexity: O(n*(n+m)*log(n+m)) time, O(n+m) auxiliary space.
 * Outbound and return paths may differ. Distances computed for cost and cost*tax separately, never merged into a single road weight. n<=1000, m<=2000; sums safe in Number. Native name pending.
 */

class BinaryHeap {
  constructor(less) { this.items = []; this.less = less; }
  get length() { return this.items.length; }
  peek() { return this.items[0]; }
  push(value) {
    const items = this.items;
    let index = items.length;
    items.push(value);
    while (index > 0) {
      const parent = Math.floor((index - 1) / 2);
      if (!this.less(value, items[parent])) break;
      items[index] = items[parent]; index = parent;
    }
    items[index] = value;
  }
  pop() {
    const items = this.items, result = items[0], last = items.pop();
    if (items.length === 0) return result;
    let index = 0;
    while (index * 2 + 1 < items.length) {
      let child = index * 2 + 1;
      if (child + 1 < items.length && this.less(items[child + 1], items[child])) child += 1;
      if (!this.less(items[child], last)) break;
      items[index] = items[child]; index = child;
    }
    items[index] = last;
    return result;
  }
}

function solve(n, prices, roads) {
  const graph = Array.from({ length: n }, () => []);
  for (const [first, second, cost, tax] of roads) {
    graph[first].push([second, cost, cost * tax]);
    graph[second].push([first, cost, cost * tax]);
  }
  function distances(source, loaded) {
    const result = Array(n).fill(Infinity);
    result[source] = 0;
    const heap = new BinaryHeap((a, b) => a[0] < b[0]);
    heap.push([0, source]);
    while (heap.length) {
      const [distance, node] = heap.pop();
      if (distance !== result[node]) continue;
      for (const edge of graph[node]) {
        const neighbor = edge[0];
        const updated = distance + edge[loaded ? 2 : 1];
        if (updated < result[neighbor]) {
          result[neighbor] = updated;
          heap.push([updated, neighbor]);
        }
      }
    }
    return result;
  }
  const answer = [];
  for (let source = 0; source < n; source += 1) {
    const outward = distances(source, false);
    const inward = distances(source, true);
    let best = prices[source];
    for (let shop = 0; shop < n; shop += 1) best = Math.min(best, prices[shop] + outward[shop] + inward[shop]);
    answer.push(best);
  }
  return answer;
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { solve };
}
