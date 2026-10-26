'use strict';

// 3410. Maximize Subarray Sum After Removing All Occurrences of One Element.
// Temporarily erase each negative value in a maximum-subarray segment tree, then restore it; O(n log n) time and O(n) space. Inputs are preserved.

function solve(nums) {
  let maximum = -Infinity, size = 1;
  for (const value of nums) maximum = Math.max(maximum, value);
  if (maximum < 0) return maximum;
  while (size < nums.length) size *= 2;
  const total = new Float64Array(2 * size), prefix = new Float64Array(2 * size);
  const suffix = new Float64Array(2 * size), best = new Float64Array(2 * size), groups = new Map();
  nums.forEach((value, index) => {
    total[size + index] = value;
    prefix[size + index] = suffix[size + index] = best[size + index] = Math.max(0, value);
    if (value < 0) { if (!groups.has(value)) groups.set(value, []); groups.get(value).push(index); }
  });
  function pull(node) {
    const left = 2 * node, right = left + 1;
    total[node] = total[left] + total[right];
    prefix[node] = Math.max(prefix[left], total[left] + prefix[right]);
    suffix[node] = Math.max(suffix[right], total[right] + suffix[left]);
    best[node] = Math.max(best[left], best[right], suffix[left] + prefix[right]);
  }
  for (let node = size - 1; node > 0; node -= 1) pull(node);
  function update(index, value) {
    let node = size + index;
    total[node] = value; prefix[node] = suffix[node] = best[node] = Math.max(0, value);
    for (node = Math.floor(node / 2); node > 0; node = Math.floor(node / 2)) pull(node);
  }
  let answer = best[1];
  for (const [value, indices] of groups) {
    for (const index of indices) update(index, 0);
    answer = Math.max(answer, best[1]);
    for (const index of indices) update(index, value);
  }
  return answer;
}

const maxSubarraySum = solve;
class Solution {
  maxSubarraySum(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maxSubarraySum };
