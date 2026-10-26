'use strict';

// 2318. Number of Distinct Roll Sequences: rolling dynamic programming over the previous two die faces.
// O(6^3 * n) time and O(6^2) auxiliary space. Inputs are preserved.
function solve(n) {
  const modulus = 1000000007;
  function gcd(first, second) {
    while (second !== 0) [first, second] = [second, first % second];
    return first;
  }
  const allowed = Array.from({ length: 7 }, () => []);
  for (let previous = 1; previous <= 6; previous += 1) {
    for (let face = 1; face <= 6; face += 1) {
      if (face !== previous && gcd(face, previous) === 1) allowed[previous].push(face);
    }
  }
  let states = Array.from({ length: 7 }, () => Array(7).fill(0));
  for (let face = 1; face <= 6; face += 1) states[0][face] = 1;
  for (let roll = 1; roll < n; roll += 1) {
    const following = Array.from({ length: 7 }, () => Array(7).fill(0));
    for (let earlier = 0; earlier <= 6; earlier += 1) {
      for (let previous = 1; previous <= 6; previous += 1) {
        const count = states[earlier][previous];
        if (count === 0) continue;
        for (const face of allowed[previous]) {
          if (face !== earlier) following[previous][face] = (following[previous][face] + count) % modulus;
        }
      }
    }
    states = following;
  }
  return states.flat().reduce((sum, count) => (sum + count) % modulus, 0);
}

const distinctSequences = solve;
class Solution {
  distinctSequences(n) { return solve(n); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, distinctSequences };
