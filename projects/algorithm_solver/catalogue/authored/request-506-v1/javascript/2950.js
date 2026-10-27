// Original candidate implementation. Contract: https://leetcode.com/problems/number-of-divisible-substrings/
"use strict";

function solve(word) {
  // Keypad groups: ab, cde, fgh, ijk, lmn, opq, rst, uvw, xyz.
  const values = [...word].map(character =>
    Math.floor((character.charCodeAt(0) - 97 + 1) / 3) + 1
  );
  let answer = 0;
  for (let mean = 1; mean <= 9; mean++) {
    const seen = new Map([[0, 1]]);
    let sum = 0;
    for (const value of values) {
      sum += value - mean;
      answer += seen.get(sum) || 0;
      seen.set(sum, (seen.get(sum) || 0) + 1);
    }
  }
  return answer;
}

module.exports = solve;
