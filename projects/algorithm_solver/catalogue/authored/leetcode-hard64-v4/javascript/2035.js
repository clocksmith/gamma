'use strict';

// 2035. Partition Array Into Two Arrays to Minimize Sum Difference. Meet-in-the-middle sums grouped by cardinality; O(n*2^n) time and O(2^n) space for 2n values. Inputs are preserved.

function solve(nums) {
  const half = nums.length / 2;
  function grouped(start) {
    const groups = Array.from({ length: half + 1 }, () => []);
    groups[0].push(0);
    for (let index = 0; index < half; index += 1) {
      const value = nums[start + index];
      for (let count = index + 1; count > 0; count -= 1) {
        for (const subtotal of groups[count - 1]) groups[count].push(subtotal + value);
      }
    }
    return groups;
  }
  const left = grouped(0);
  const right = grouped(half);
  let total = 0;
  for (const value of nums) total += value;
  let answer = Infinity;
  for (let count = 0; count <= half; count += 1) {
    const choices = right[half - count].sort((a, b) => a - b);
    for (const subtotal of left[count]) {
      let low = 0;
      let high = choices.length;
      while (low < high) {
        const middle = Math.floor((low + high) / 2);
        if (2 * (subtotal + choices[middle]) < total) low = middle + 1;
        else high = middle;
      }
      if (low < choices.length) answer = Math.min(answer, Math.abs(total - 2 * (subtotal + choices[low])));
      if (low > 0) answer = Math.min(answer, Math.abs(total - 2 * (subtotal + choices[low - 1])));
    }
  }
  return answer;
}

const minimumDifference = solve;
class Solution {
  minimumDifference(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minimumDifference };
