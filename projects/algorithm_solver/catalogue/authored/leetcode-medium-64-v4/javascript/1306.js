'use strict';

// 1306. Jump Game III: search reachable indices without marking the input array.
// O(n) time and O(n) auxiliary space; inputs are read-only.
function solve(arr, start) {
  const seen = new Uint8Array(arr.length);
  seen[start] = 1;
  const stack = [start];
  while (stack.length) {
    const index = stack.pop();
    if (arr[index] === 0) return true;
    for (const following of [index - arr[index], index + arr[index]]) {
      if (following >= 0 && following < arr.length && !seen[following]) {
        seen[following] = 1;
        stack.push(following);
      }
    }
  }
  return false;
}

const canReach = solve;
class Solution {
  canReach(arr, start) { return solve(arr, start); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, canReach };
