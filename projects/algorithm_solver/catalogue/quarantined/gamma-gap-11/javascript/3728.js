'use strict';

// 3728. Stable Subarrays With Equal Boundary and Interior Sum.
// O(n) expected time and O(n) space; prefix sums handle negative values and enforce length >= 3.
function solve(capacity) {
  const prefix = [0];
  for (const value of capacity) prefix.push(prefix[prefix.length - 1] + value);
  const counts = new Map();
  let answer = 0;
  for (let right = 2; right < capacity.length; right += 1) {
    const left = right - 2;
    const key = `${capacity[left]},${prefix[left + 1] + capacity[left]}`;
    counts.set(key, (counts.get(key) || 0) + 1);
    answer += counts.get(`${capacity[right]},${prefix[right]}`) || 0;
  }
  return answer;
}

const countStableSubarrays = solve;
class Solution {
  countStableSubarrays(capacity) { return solve(capacity); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, countStableSubarrays };
