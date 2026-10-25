'use strict';

// 2433. Find The Original Array of Prefix Xor: cancel adjacent prefix XOR values.
// O(n) time and O(1) auxiliary space excluding the result; inputs are read-only.
function solve(pref) {
  const answer = [];
  let previous = 0;
  for (const value of pref) {
    answer.push(previous ^ value);
    previous = value;
  }
  return answer;
}

const findArray = solve;
class Solution {
  findArray(pref) { return solve(pref); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, findArray };
