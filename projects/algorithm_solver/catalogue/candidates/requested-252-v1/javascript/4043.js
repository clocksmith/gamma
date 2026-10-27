'use strict';

// 4043. Count Rotations With Exactly K Equal Adjacent Pairs.
// Specification: https://leetcode.com/problems/count-rotations-with-exactly-k-equal-adjacent-pairs/description/
// O(n) time and O(1) auxiliary space; count rotations by cut position, including identical resulting strings. Inputs are preserved.
function solve(s, k) {
  let circular = 0;
  for (let index = 0; index < s.length; index++) if (s[index] === s[(index + 1) % s.length]) circular++;
  let answer = 0;
  for (let index = 0; index < s.length; index++) {
    const omitted = s[index] === s[(index + 1) % s.length] ? 1 : 0;
    if (circular - omitted === k) answer++;
  }
  return answer;
}

if (typeof module !== 'undefined') module.exports = { solve };
