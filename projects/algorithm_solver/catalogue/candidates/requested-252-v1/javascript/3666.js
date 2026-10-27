/**
 * 3666. Minimum Operations to Equalize Binary String
 * Candidate source; not executed, syntax-checked, tested, or qualified.
 * Specification: https://leetcode.com/problems/minimum-operations-to-equalize-binary-string/description/
 * Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3600-3699/3666.Minimum%20Operations%20to%20Equalize%20Binary%20String/README_EN.md
 * Complexity: O(n alpha(n)) amortized time; O(n) space.
 * Zero-count BFS, with parity-separated successor sets; all flips use exactly k distinct positions.
 */

function solve(s, k) {
  const n = s.length;
  let zeros = 0;
  for (const character of s) if (character === '0') zeros += 1;
  const successor = Array.from({ length: n + 3 }, (_, i) => i);
  function find(value) {
    let root = value;
    while (successor[root] !== root) root = successor[root];
    while (successor[value] !== value) { const following = successor[value]; successor[value] = root; value = following; }
    return root;
  }
  const distances = Array(n + 1).fill(-1), queue = [zeros];
  distances[zeros] = 0; successor[zeros] = find(zeros + 2);
  for (let head = 0; head < queue.length; head += 1) {
    const current = queue[head];
    if (current === 0) return distances[current];
    const low = Math.abs(current - k), high = Math.min(current + k, 2 * n - current - k);
    let following = find(low);
    while (following <= high) {
      distances[following] = distances[current] + 1;
      queue.push(following); successor[following] = find(following + 2);
      following = find(following);
    }
  }
  return -1;
}

function minOperations(s, k) {
  return solve(s, k);
}

class Solution {
  minOperations(s, k) {
    return solve(s, k);
  }
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { solve, minOperations, Solution };
}
