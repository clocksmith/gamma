'use strict';

// 689. Maximum Sum of 3 Non-Overlapping Subarrays. Best left/right windows enforce non-overlap and lexicographic tie-breaking.

function solve(nums, k) {
  const windows = [];
  let total = 0;
  for (let i = 0; i < k; i += 1) total += nums[i];
  windows.push(total);
  for (let i = k; i < nums.length; i += 1) { total += nums[i] - nums[i - k]; windows.push(total); }
  const size = windows.length, left = Array(size), right = Array(size);
  let best = 0;
  for (let i = 0; i < size; i += 1) { if (windows[i] > windows[best]) best = i; left[i] = best; }
  best = size - 1;
  for (let i = size - 1; i >= 0; i -= 1) { if (windows[i] >= windows[best]) best = i; right[i] = best; }
  let answer = null, maximum = -Infinity;
  for (let middle = k; middle < size - k; middle += 1) {
    const a = left[middle - k], c = right[middle + k], score = windows[a] + windows[middle] + windows[c];
    const candidate = [a, middle, c];
    const earlier = answer === null || a < answer[0] || (a === answer[0] && (middle < answer[1] || (middle === answer[1] && c < answer[2])));
    if (score > maximum || (score === maximum && earlier)) { maximum = score; answer = candidate; }
  }
  return answer;
}

const maxSumOfThreeSubarrays = solve;
class Solution {
  maxSumOfThreeSubarrays(nums, k) { return solve(nums, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maxSumOfThreeSubarrays };
