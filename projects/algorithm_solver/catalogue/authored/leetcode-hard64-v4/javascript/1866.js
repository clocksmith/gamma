'use strict';

// 1866. Number of Ways to Rearrange Sticks With K Sticks Visible. Insert the shortest stick into a visibility DP; O(n*k) time and O(k) space. Inputs are preserved.

function solve(n, k) {
  const modulus = 1000000007;
  let ways = Array(k + 1).fill(0);
  ways[0] = 1;
  for (let size = 1; size <= n; size += 1) {
    const following = Array(k + 1).fill(0);
    for (let visible = 1; visible <= Math.min(size, k); visible += 1) {
      following[visible] = (ways[visible - 1] + (size - 1) * ways[visible]) % modulus;
    }
    ways = following;
  }
  return ways[k];
}

const rearrangeSticks = solve;
class Solution {
  rearrangeSticks(n, k) { return solve(n, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, rearrangeSticks };
