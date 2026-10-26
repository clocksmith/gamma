'use strict';

// 1420. Build Array Where You Can Find The Maximum Exactly K Comparisons: maximum-value DP with prefix sums; O(n*m*k) time and O(m*k) space.

function solve(n, m, k) {
  const modulus = 1000000007;
  if (k === 0 || k > n || k > m) return 0;
  let previous = Array.from({ length: k + 1 }, () => Array(m + 1).fill(0));
  for (let maximum = 1; maximum <= m; maximum += 1) previous[1][maximum] = 1;
  for (let length = 2; length <= n; length += 1) {
    const current = Array.from({ length: k + 1 }, () => Array(m + 1).fill(0));
    for (let comparisons = 1; comparisons <= Math.min(k, length); comparisons += 1) {
      let prefix = 0;
      for (let maximum = 1; maximum <= m; maximum += 1) {
        prefix = (prefix + previous[comparisons - 1][maximum - 1]) % modulus;
        current[comparisons][maximum] = (previous[comparisons][maximum] * maximum + prefix) % modulus;
      }
    }
    previous = current;
  }
  let answer = 0;
  for (const count of previous[k]) answer = (answer + count) % modulus;
  return answer;
}

const numOfArrays = solve;
class Solution {
  numOfArrays(n, m, k) { return solve(n, m, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, numOfArrays };
