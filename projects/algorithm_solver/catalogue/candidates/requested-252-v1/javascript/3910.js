/**
 * 3910. Count Connected Subgraphs with Even Node Sum
 * Candidate source; not executed, syntax-checked, tested, or qualified.
 * Specification: https://leetcode.com/problems/count-connected-subgraphs-with-even-node-sum/description/
 * Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3900-3999/3910.Count%20Connected%20Subgraphs%20with%20Even%20Node%20Sum/README_EN.md
 * Complexity: O(n*2^n + m) time, O(2^n+n) space.
 * n<=13, binary node values, undirected simple graph. Canonical solve; native method pending.
 */

function solve(nums, edges) {
  const n = nums.length;
  const neighbors = Array(n).fill(0);
  for (const [first, second] of edges) {
    neighbors[first] |= 1 << second;
    neighbors[second] |= 1 << first;
  }
  const parity = new Uint8Array(1 << n);
  let answer = 0;
  for (let subset = 1; subset < (1 << n); subset += 1) {
    const first = subset & -subset;
    parity[subset] = parity[subset ^ first] ^ nums[31 - Math.clz32(first)];
    if (parity[subset]) continue;
    let frontier = first;
    let reached = 0;
    while (frontier) {
      const bit = frontier & -frontier;
      frontier ^= bit;
      reached |= bit;
      frontier |= neighbors[31 - Math.clz32(bit)] & subset & ~reached;
    }
    if (reached === subset) answer += 1;
  }
  return answer;
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { solve };
}
