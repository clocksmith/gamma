'use strict';

// 1542. Find Longest Awesome Substring.
// O(10*n) time, O(2^10) space. Keep the earliest prefix for each parity mask.
function solve(s) {
  const first = new Int32Array(1024).fill(s.length);
  first[0] = -1;
  let mask = 0;
  let answer = 0;
  for (let index = 0; index < s.length; index += 1) {
    mask ^= 1 << (s.charCodeAt(index) - 48);
    answer = Math.max(answer, index - first[mask]);
    for (let digit = 0; digit < 10; digit += 1) {
      answer = Math.max(answer, index - first[mask ^ (1 << digit)]);
    }
    if (first[mask] === s.length) first[mask] = index;
  }
  return answer;
}

const longestAwesome = solve;
class Solution {
  longestAwesome(s) { return solve(s); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, longestAwesome };
