/**
 * 3672. Sum of Weighted Modes in Subarrays
 * Authored candidate: not executed, imported, syntax-checked, tested, or qualified.
 * Signature: solve(nums, k).
 * Algorithm: Sliding-window frequencies; a compressed-value segment tree selects highest frequency, then smallest value.
 * Complexity: O(n log u + u log u) time; O(u) auxiliary space, u distinct values.
 * Numeric semantics: Weighted sum <= 100000 * k * (n-k+1) <= approximately 2.501e14, exact in Number and int.
 * Mutation: Does not mutate input arrays, rows, strings, or trees.
 * Interface: Ordered-positional solve; native forwarding name included only when confirmed.
 * Specification: https://leetcode.com/problems/sum-of-weighted-modes-in-subarrays/description/
 * Consulted public statement/reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3600-3699/3672.Sum%20of%20Weighted%20Modes%20in%20Subarrays/README_EN.md
 * Reference repository attribution: Doocs contributors, CC-BY-SA-4.0.
 * New readable implementations; no third-party source bodies copied verbatim.
 * No protected tests or private reference implementations used.
 */

function solve(nums, k) {
  const values = [...new Set(nums)].sort((a, b) => a - b);
  const ranks = new Map(values.map((value, index) => [value, index]));
  let size = 1;
  while (size < values.length) size *= 2;
  const frequencies = new Int32Array(2 * size).fill(-1);
  const winners = new Int32Array(2 * size);
  for (let index = 0; index < values.length; index += 1) {
    frequencies[size + index] = 0;
    winners[size + index] = index;
  }
  function pull(node) {
    const left = 2 * node;
    const right = left + 1;
    const winner = frequencies[left] >= frequencies[right] ? left : right;
    frequencies[node] = frequencies[winner];
    winners[node] = winners[winner];
  }
  for (let node = size - 1; node > 0; node -= 1) pull(node);
  function update(value, change) {
    let node = size + ranks.get(value);
    frequencies[node] += change;
    node = Math.floor(node / 2);
    while (node > 0) {
      pull(node);
      node = Math.floor(node / 2);
    }
  }
  for (let index = 0; index < k; index += 1) update(nums[index], 1);
  let total = frequencies[1] * values[winners[1]];
  for (let index = k; index < nums.length; index += 1) {
    update(nums[index - k], -1);
    update(nums[index], 1);
    total += frequencies[1] * values[winners[1]];
  }
  return total;
}

function modeWeight(nums, k) {
  return solve(nums, k);
}

class Solution {
  modeWeight(nums, k) {
    return solve(nums, k);
  }
}

if (typeof module !== "undefined" && module.exports) {
  module.exports = { solve, modeWeight, Solution };
}
