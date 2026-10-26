'use strict';

// 2223. Sum of Scores of Built Strings. Z-function prefix matches for every suffix; O(n) time and O(n) space. Inputs are preserved.

function solve(s) {
  const size = s.length;
  const matches = new Int32Array(size);
  let left = 0;
  let right = 0;
  let answer = size;
  for (let index = 1; index < size; index += 1) {
    if (index < right) matches[index] = Math.min(right - index, matches[index - left]);
    while (index + matches[index] < size && s[matches[index]] === s[index + matches[index]]) {
      matches[index] += 1;
    }
    if (index + matches[index] > right) {
      left = index;
      right = index + matches[index];
    }
    answer += matches[index];
  }
  return answer;
}

const sumScores = solve;
class Solution {
  sumScores(s) { return solve(s); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, sumScores };
