'use strict';

// 1503. Last Moment Before All Ants Fall Out of a Plank: treat colliding ants as exchanging identities.
// O(|left| + |right|) time and O(1) auxiliary space; inputs are read-only.
function solve(n, left, right) {
  let answer = 0;
  for (const position of left) answer = Math.max(answer, position);
  for (const position of right) answer = Math.max(answer, n - position);
  return answer;
}

const getLastMoment = solve;
class Solution {
  getLastMoment(n, left, right) { return solve(n, left, right); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, getLastMoment };
