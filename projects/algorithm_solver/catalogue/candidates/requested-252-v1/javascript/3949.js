/**
 * 3949. Subtree Inversion Sum II
 * Candidate source; not executed, syntax-checked, tested, or qualified.
 * Specification: https://leetcode.com/problems/subtree-inversion-sum-ii/description/
 * Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3900-3999/3949.Subtree%20Inversion%20Sum%20II/README_EN.md
 * Complexity: O(n*k) time and O(n*k) worst-case space; iterative tree order.
 * All selected pairs, including different child branches, must be at distance at least k. Nearest-selected-distance states and suffix maxima enforce this. Inputs preserved; native judge method pending.
 */

function solve(edges, nums, k) {
  if (k === 1) return nums.reduce((sum, value) => sum + Math.abs(value), 0);
  const n = nums.length;
  const graph = Array.from({ length: n }, () => []);
  for (const [left, right] of edges) {
    graph[left].push(right);
    graph[right].push(left);
  }
  const parent = new Int32Array(n).fill(-1);
  const order = [0];
  for (let cursor = 0; cursor < order.length; cursor++) {
    const node = order[cursor];
    for (const child of graph[node]) {
      if (child === parent[node]) continue;
      parent[child] = node;
      order.push(child);
    }
  }
  const tables = new Array(n);
  for (let cursor = n - 1; cursor >= 0; cursor--) {
    const node = order[cursor];
    const states = [new Float64Array(k + 1).fill(-Infinity), new Float64Array(k + 1).fill(-Infinity)];
    const selected = [-nums[node], nums[node]];
    states[0][k] = nums[node];
    states[1][k] = -nums[node];
    for (const child of graph[node]) {
      if (child === parent[node]) continue;
      const childStates = tables[child];
      for (let parity = 0; parity < 2; parity++) {
        const opposite = childStates[1 - parity];
        selected[parity] += Math.max(opposite[k - 1], opposite[k]);
        const other = new Float64Array(k + 1).fill(-Infinity);
        for (let distance = 1; distance < k; distance++) other[distance] = childStates[parity][distance - 1];
        other[k] = Math.max(childStates[parity][k - 1], childStates[parity][k]);
        const current = states[parity];
        const suffixCurrent = current.slice();
        const suffixOther = other.slice();
        for (let distance = k - 1; distance >= 0; distance--) {
          suffixCurrent[distance] = Math.max(suffixCurrent[distance], suffixCurrent[distance + 1]);
          suffixOther[distance] = Math.max(suffixOther[distance], suffixOther[distance + 1]);
        }
        const merged = new Float64Array(k + 1).fill(-Infinity);
        for (let distance = 0; distance <= k; distance++) {
          const lower = Math.max(distance, k - distance);
          merged[distance] = Math.max(current[distance] + suffixOther[lower], other[distance] + suffixCurrent[lower]);
        }
        states[parity] = merged;
      }
      tables[child] = null;
    }
    states[0][0] = selected[0];
    states[1][0] = selected[1];
    tables[node] = states;
  }
  let answer = -Infinity;
  for (const value of tables[0][0]) answer = Math.max(answer, value);
  return answer;
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { solve };
}
