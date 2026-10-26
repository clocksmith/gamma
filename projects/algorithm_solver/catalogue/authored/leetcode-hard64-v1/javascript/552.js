'use strict';

// 552. Student Attendance Record II: six-state attendance dynamic programming.
// O(n) time and O(1) auxiliary space. Inputs are preserved.
function solve(n) {
  const modulus = 1000000007;
  let states = [[1, 0, 0], [0, 0, 0]];
  for (let day = 0; day < n; day += 1) {
    const following = [[0, 0, 0], [0, 0, 0]];
    for (let absent = 0; absent < 2; absent += 1) {
      for (let late = 0; late < 3; late += 1) {
        const count = states[absent][late];
        following[absent][0] = (following[absent][0] + count) % modulus;
        if (absent === 0) following[1][0] = (following[1][0] + count) % modulus;
        if (late < 2) following[absent][late + 1] = (following[absent][late + 1] + count) % modulus;
      }
    }
    states = following;
  }
  return states.flat().reduce((sum, count) => (sum + count) % modulus, 0);
}

const checkRecord = solve;
class Solution {
  checkRecord(n) { return solve(n); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, checkRecord };
