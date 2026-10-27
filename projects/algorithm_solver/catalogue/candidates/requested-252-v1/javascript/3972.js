'use strict';

// 3972. Valid Subarrays With Matching Sum Digits II.
// Specification: https://leetcode.com/problems/valid-subarrays-with-matching-sum-digits-ii/description/
// O(n log(sum(nums))) time and O(n) space; positive prefix sums, decimal-magnitude windows, residue counts. Inputs are preserved.
function solve(nums, x) {
  const prefix = new Float64Array(nums.length + 1);
  for (let index = 0; index < nums.length; index++) prefix[index + 1] = prefix[index] + nums[index];
  const total = prefix[nums.length];
  let answer = 0;
  for (let power = 1; x * power <= total; power *= 10) {
    const lower = x * power;
    const upper = (x + 1) * power - 1;
    const residues = new Int32Array(10);
    let added = 0;
    let removed = 0;
    for (let right = 1; right < prefix.length; right++) {
      while (added < right && prefix[added] <= prefix[right] - lower) residues[prefix[added++] % 10]++;
      while (removed < added && prefix[removed] < prefix[right] - upper) residues[prefix[removed++] % 10]--;
      answer += residues[((prefix[right] - x) % 10 + 10) % 10];
    }
  }
  return answer;
}

if (typeof module !== 'undefined') module.exports = { solve };
