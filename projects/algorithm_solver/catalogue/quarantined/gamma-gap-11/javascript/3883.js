'use strict';

// 3883. Count Non Decreasing Arrays With Given Digit Sums.
// O(5001*n) time and O(5001) space; prefix-sum DP enforces nondecreasing values and exact decimal digit sums.
function solve(digitSum) {
  const modulus = 1000000007;
  const limit = 5000;
  const sums = new Int32Array(limit + 1);
  for (let value = 1; value <= limit; value += 1) sums[value] = sums[Math.floor(value / 10)] + value % 10;
  if (digitSum.some(wanted => wanted > 31)) return 0;
  let previous = new Float64Array(limit + 1);
  previous[0] = 1;
  for (const wanted of digitSum) {
    const current = new Float64Array(limit + 1);
    let prefix = 0;
    for (let value = 0; value <= limit; value += 1) {
      prefix = (prefix + previous[value]) % modulus;
      if (sums[value] === wanted) current[value] = prefix;
    }
    previous = current;
  }
  let answer = 0;
  for (const count of previous) answer = (answer + count) % modulus;
  return answer;
}

const countArrays = solve;
class Solution {
  countArrays(digitSum) { return solve(digitSum); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, countArrays };
