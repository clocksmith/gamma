/**
 * 4004. Minimum Moves to Balance Circular Array II
 * Candidate source; not executed, syntax-checked, tested, or qualified.
 * Specification: https://leetcode.com/problems/minimum-moves-to-balance-circular-array-ii/description/
 * Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/4000-4099/4004.Minimum%20Moves%20to%20Balance%20Circular%20Array%20II/README_EN.md
 * Complexity: O(A*n*log n) time for A bottleneck augmentations, O(n) space.
 * Min-cost flow on the bidirectional cycle with feasible reduced-cost potentials; aggregate capacities, not unit transfers. Maximum-size runtime not measured. Inputs preserved.
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

function solve(balance) {
  let total = 0, need = 0;
  for (const value of balance) { total += value; if (value < 0) need -= value; }
  if (total < 0) return -1;
  if (need === 0) return 0;
  const n = balance.length, source = n, sink = n + 1, size = n + 2;
  const graph = Array.from({length: size}, () => []);
  function edge(u, v, capacity, cost) {
    graph[u].push([v, capacity, cost, graph[v].length]);
    graph[v].push([u, 0, -cost, graph[u].length - 1]);
  }
  for (let i = 0; i < n; i++) {
    if (balance[i] > 0) edge(source, i, balance[i], 0);
    else if (balance[i] < 0) edge(i, sink, -balance[i], 0);
    for (const j of new Set([(i - 1 + n) % n, (i + 1) % n])) edge(i, j, need, 1);
  }
  const potential = new Float64Array(size);
  let answer = 0;
  while (need > 0) {
    const distance = new Float64Array(size).fill(Infinity), previous = Array(size).fill(null);
    const queue = new BinaryHeap((a, b) => a[0] < b[0]);
    distance[source] = 0; queue.push([0, source]);
    while (queue.length) {
      const [d, u] = queue.pop();
      if (d !== distance[u]) continue;
      for (let index = 0; index < graph[u].length; index++) {
        const [v, capacity, cost] = graph[u][index];
        const candidate = d + cost + potential[u] - potential[v];
        if (capacity > 0 && candidate < distance[v]) {
          distance[v] = candidate; previous[v] = [u, index]; queue.push([candidate, v]);
        }
      }
    }
    if (previous[sink] === null) return -1;
    for (let v = 0; v < size; v++) if (Number.isFinite(distance[v])) potential[v] += distance[v];
    let amount = need;
    for (let v = sink; v !== source;) { const [u, index] = previous[v]; amount = Math.min(amount, graph[u][index][1]); v = u; }
    for (let v = sink; v !== source;) {
      const [u, index] = previous[v], e = graph[u][index];
      answer += amount * e[2]; e[1] -= amount; graph[v][e[3]][1] += amount; v = u;
    }
    need -= amount;
  }
  return answer;
}

function minMoves(balance) {
  return solve(balance);
}

class Solution {
  minMoves(balance) {
    return solve(balance);
  }
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { solve, minMoves, Solution };
}
