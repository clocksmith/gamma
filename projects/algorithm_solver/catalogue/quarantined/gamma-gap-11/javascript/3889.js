'use strict';

// 3889. Mirror Frequency Distance.
// O(n) time and O(1) alphabet space; count each alphabetic or numeric mirror pair exactly once.
function solve(s) {
  const letters = Array(26).fill(0);
  const digits = Array(10).fill(0);
  for (const char of s) {
    if (char >= '0' && char <= '9') digits[char.charCodeAt(0) - 48] += 1;
    else letters[char.charCodeAt(0) - 97] += 1;
  }
  let answer = 0;
  for (let index = 0; index < 13; index += 1) answer += Math.abs(letters[index] - letters[25 - index]);
  for (let index = 0; index < 5; index += 1) answer += Math.abs(digits[index] - digits[9 - index]);
  return answer;
}

const mirrorDistance = solve;
class Solution {
  mirrorDistance(s) { return solve(s); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, mirrorDistance };
