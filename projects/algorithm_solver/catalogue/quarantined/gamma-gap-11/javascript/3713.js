'use strict';

// 3713. Longest Balanced Substring I.
// O(n^2) time and O(26) auxiliary space for lowercase ASCII input.
function solve(s) {
  let answer = 0;
  for (let left = 0; left < s.length; left += 1) {
    const counts = new Int32Array(26);
    let distinct = 0;
    let maximum = 0;
    for (let right = left; right < s.length; right += 1) {
      const index = s.charCodeAt(right) - 97;
      if (counts[index] === 0) distinct += 1;
      counts[index] += 1;
      maximum = Math.max(maximum, counts[index]);
      if (maximum * distinct === right - left + 1) answer = Math.max(answer, right - left + 1);
    }
  }
  return answer;
}

const longestBalanced = solve;
class Solution {
  longestBalanced(s) { return solve(s); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, longestBalanced };
