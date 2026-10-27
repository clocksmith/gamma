'use strict';

// 3632. Subarrays with XOR at Least K.
// Specification: https://leetcode.com/problems/subarrays-with-xor-at-least-k/description/
// Authored candidate; not executed, syntax-checked, tested, or Gamma-qualified.
// O(n * bitWidth) time and space; unsigned nonnegative 32-bit input domain.
// Inputs are not modified.
// Exact Gamma input bounds and method signature require coordinator reconciliation.

function solve(nums, k) {
  let maximum = k;
  for (const value of nums) maximum = Math.max(maximum, value);
  let width = 1;
  while (2 ** width <= maximum) width++;
  const children = [[-1, -1]], counts = [0];
  function insert(value) {
    let node = 0; counts[node]++;
    for (let bit = width - 1; bit >= 0; bit--) {
      const direction = Math.floor(value / 2 ** bit) % 2;
      if (children[node][direction] === -1) { children[node][direction] = children.length; children.push([-1, -1]); counts.push(0); }
      node = children[node][direction]; counts[node]++;
    }
  }
  function lessThan(value) {
    let node = 0, total = 0;
    for (let bit = width - 1; bit >= 0 && node !== -1; bit--) {
      const direction = Math.floor(value / 2 ** bit) % 2;
      if (Math.floor(k / 2 ** bit) % 2 === 1) {
        const same = children[node][direction];
        if (same !== -1) total += counts[same];
        node = children[node][direction ^ 1];
      } else node = children[node][direction];
    }
    return total;
  }
  insert(0);
  let prefix = 0, answer = 0;
  for (let index = 0; index < nums.length; index++) {
    prefix = (prefix ^ nums[index]) >>> 0;
    answer += index + 1 - lessThan(prefix);
    insert(prefix);
  }
  return answer;
}

const countSubarrays = solve;
class Solution {
  countSubarrays(nums, k) { return solve(nums, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, countSubarrays };
