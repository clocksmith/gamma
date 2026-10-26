'use strict';

// 2262. Total Appeal of A String. Last occurrence contributions for substrings ending at each position; O(n) time and O(26) space. Inputs are preserved.

function solve(s) {
  const last = Array(26).fill(-1);
  let ending = 0;
  let answer = 0;
  for (let index = 0; index < s.length; index += 1) {
    const letter = s.charCodeAt(index) - 97;
    ending += index - last[letter];
    last[letter] = index;
    answer += ending;
  }
  return answer;
}

const appealSum = solve;
class Solution {
  appealSum(s) { return solve(s); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, appealSum };
