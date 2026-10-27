/**
 * 4015. Weighted Sum of a Tree
 * Candidate source; not executed, syntax-checked, tested, or qualified.
 * Specification: https://leetcode.com/problems/weighted-sum-of-a-tree/description/
 * Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/4000-4099/4015.Weighted%20Sum%20of%20a%20Tree/README_EN.md
 * Complexity: O(n) time and space.
 * Parent labels need not be topologically ordered. Iterative traversal avoids deep recursion. Total weighted sum <=1e6*n*(n+1)/2 <2^53. Native method unconfirmed.
 */

function solve(parent, nums) {
  const n = parent.length, children = Array.from({length: n}, () => []), depth = new Int32Array(n), order = [0];
  for (let node = 1; node < n; node++) children[parent[node]].push(node);
  depth[0] = 1;
  let height = 1;
  for (let head = 0; head < order.length; head++) {
    const node = order[head];
    for (const child of children[node]) { depth[child] = depth[node] + 1; height = Math.max(height, depth[child]); order.push(child); }
  }
  let answer = 0;
  for (let node = 0; node < n; node++) answer += nums[node] * (height - depth[node] + 1);
  return answer;
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { solve };
}
