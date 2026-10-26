'use strict';

// 1535. Find the Winner of an Array Game: track the current champion until its streak wins or it becomes the global maximum.
// O(n) time and O(1) auxiliary space; inputs are read-only.
function solve(arr, k) {
  let champion = arr[0];
  let streak = 0;
  for (let index = 1; index < arr.length; index += 1) {
    if (champion > arr[index]) streak += 1;
    else {
      champion = arr[index];
      streak = 1;
    }
    if (streak >= k) return champion;
  }
  return champion;
}

const getWinner = solve;
class Solution {
  getWinner(arr, k) { return solve(arr, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, getWinner };
