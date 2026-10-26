'use strict';

// 873. Length of Longest Fibonacci Subsequence: extend subsequences indexed by their last two positions.
// O(n^2) expected time and O(n^2) auxiliary space; inputs are read-only.
function solve(arr) {
  const size = arr.length;
  const positions = new Map(arr.map((value, index) => [value, index]));
  const lengths = Array.from({ length: size }, () => new Uint16Array(size));
  let answer = 0;
  for (let right = 0; right < size; right += 1) {
    for (let middle = 0; middle < right; middle += 1) {
      const needed = arr[right] - arr[middle];
      if (needed >= arr[middle]) continue;
      const left = positions.get(needed);
      if (left !== undefined) {
        lengths[middle][right] = (lengths[left][middle] || 2) + 1;
        answer = Math.max(answer, lengths[middle][right]);
      }
    }
  }
  return answer;
}

const lenLongestFibSubseq = solve;
class Solution {
  lenLongestFibSubseq(arr) { return solve(arr); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, lenLongestFibSubseq };
