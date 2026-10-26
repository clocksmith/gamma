'use strict';

// 1759. Count Number of Homogenous Substrings: add the length of the equal-character suffix at each position.
// O(n) time and O(1) auxiliary space; inputs are read-only.
function solve(s) {
  const modulus = 1000000007;
  let previous = '';
  let run = 0;
  let result = 0;
  for (const letter of s) {
    run = letter === previous ? run + 1 : 1;
    result = (result + run) % modulus;
    previous = letter;
  }
  return result;
}

const countHomogenous = solve;
class Solution {
  countHomogenous(s) { return solve(s); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, countHomogenous };
