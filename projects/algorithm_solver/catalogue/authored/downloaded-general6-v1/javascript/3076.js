'use strict';

// 3076. Shortest Uncommon Substring in an Array (Medium).
// Specification: https://leetcode.com/problems/shortest-uncommon-substring-in-an-array/description/
function solve(arr) {
  const answer = [];
  for (let i = 0; i < arr.length; i++) {
    const s = arr[i];
    let best = '';
    for (let length = 1; length <= s.length && best === ''; length++) {
      const candidates = [];
      for (let start = 0; start + length <= s.length; start++) {
        const sub = s.slice(start, start + length);
        let unique = true;
        for (let j = 0; j < arr.length; j++) {
          if (j !== i && arr[j].includes(sub)) { unique = false; break; }
        }
        if (unique) candidates.push(sub);
      }
      if (candidates.length > 0) { candidates.sort(); best = candidates[0]; }
    }
    answer.push(best);
  }
  return answer;
}
const shortestSubstrings = solve;
class Solution { shortestSubstrings(arr) { return solve(arr); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, shortestSubstrings };
