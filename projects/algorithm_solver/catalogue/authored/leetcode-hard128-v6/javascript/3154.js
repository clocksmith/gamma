'use strict';

// 3154. Find Number of Ways to Reach the K-th Stair.
// For j forward jumps choose the nonadjacent downward moves among j+1 gaps; O(log^2(k+2)) time and O(1) space.

function solve(k) {
  function choose(n, r) {
    r = Math.min(r, n - r);
    let result = 1;
    for (let i = 1; i <= r; i += 1) result = result * (n - r + i) / i;
    return Math.round(result);
  }
  let answer = 0, jumps = 0, power = 1;
  while (power - jumps - 1 <= k) {
    const backwards = power - k;
    if (0 <= backwards && backwards <= jumps + 1) answer += choose(jumps + 1, backwards);
    jumps += 1; power *= 2;
  }
  return answer;
}

const waysToReachStair = solve;
class Solution {
  waysToReachStair(k) { return solve(k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, waysToReachStair };
