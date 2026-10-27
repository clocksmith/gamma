/**
 * 4003. Minimum Cost Path with Alternating Directions III
 * Candidate source; not executed, syntax-checked, tested, or qualified.
 * Specification: https://leetcode.com/problems/minimum-cost-path-with-alternating-directions-iii/description/
 * Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/4000-4099/4003.Minimum%20Cost%20Path%20with%20Alternating%20Directions%20III/README_EN.md
 * Complexity: O(m*n*log(m*n)) time, O(m*n) space.
 * Dijkstra state includes next-action parity. Waiting and moves both flip parity; violations charge the departure cell. Includes starting entrance cost. Inputs preserved.
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

function solve(m, n, penalty) {
  const distance = new Float64Array(2 * m * n).fill(Infinity);
  const queue = new BinaryHeap((a, b) => a[0] < b[0]);
  distance[1] = 1; queue.push([1, 1]);
  while (queue.length) {
    const [total, state] = queue.pop();
    if (total !== distance[state]) continue;
    const cell = Math.floor(state / 2), odd = state % 2;
    if (cell === m * n - 1) return total;
    const row = Math.floor(cell / n), col = cell % n, surcharge = penalty[row][col];
    const neighbors = [[cell, surcharge]];
    for (const [dr, dc] of [[1, 0], [0, 1], [-1, 0], [0, -1]]) {
      const r = row + dr, c = col + dc;
      if (r >= 0 && r < m && c >= 0 && c < n) {
        const extra = (dr + dc > 0) === Boolean(odd) ? 0 : surcharge;
        neighbors.push([r * n + c, (r + 1) * (c + 1) + extra]);
      }
    }
    for (const [neighbor, cost] of neighbors) {
      const following = 2 * neighbor + (odd ^ 1), candidate = total + cost;
      if (candidate < distance[following]) { distance[following] = candidate; queue.push([candidate, following]); }
    }
  }
  return -1;
}

function minCost(m, n, penalty) {
  return solve(m, n, penalty);
}

class Solution {
  minCost(m, n, penalty) {
    return solve(m, n, penalty);
  }
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { solve, minCost, Solution };
}
