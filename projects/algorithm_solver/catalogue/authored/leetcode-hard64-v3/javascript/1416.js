'use strict';

// 1416. Restore The Array: prefix DP over bounded decimal values; O(n log(k+1)) time and O(n) space.

function solve(s, k) {
  const modulus = 1000000007;
  const ways = Array(s.length + 1).fill(0);
  ways[0] = 1;
  for (let start = 0; start < s.length; start += 1) {
    if (s[start] === '0' || ways[start] === 0) continue;
    let value = 0;
    for (let end = start; end < s.length; end += 1) {
      value = value * 10 + s.charCodeAt(end) - 48;
      if (value > k) break;
      ways[end + 1] = (ways[end + 1] + ways[start]) % modulus;
    }
  }
  return ways[s.length];
}

const numberOfArrays = solve;
class Solution {
  numberOfArrays(s, k) { return solve(s, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, numberOfArrays };
