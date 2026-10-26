'use strict';

// 3480. Maximize Subarrays After Removing One Conflicting Pair: sweep the two strongest forbidden left endpoints and accumulate removal gains.
// O(n + q) time and O(n + q) auxiliary space. Inputs are preserved.
function solve(n, conflictingPairs) {
  const ending = Array.from({ length: n + 1 }, () => []);
  for (let index = 0; index < conflictingPairs.length; index += 1) {
    const [a, b] = conflictingPairs[index];
    ending[Math.max(a, b)].push([Math.min(a, b), index]);
  }
  const gain = new Float64Array(conflictingPairs.length);
  let largest = 0;
  let secondLargest = 0;
  let owner = -1;
  let base = 0;
  for (let right = 1; right <= n; right += 1) {
    for (const [left, index] of ending[right]) {
      if (left > largest) {
        secondLargest = largest;
        largest = left;
        owner = index;
      } else if (left > secondLargest) {
        secondLargest = left;
      }
    }
    base += right - largest;
    if (owner >= 0) gain[owner] += largest - secondLargest;
  }
  let best = 0;
  for (const value of gain) best = Math.max(best, value);
  return base + best;
}

const maxSubarrays = solve;
class Solution {
  maxSubarrays(n, conflictingPairs) { return solve(n, conflictingPairs); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maxSubarrays };
