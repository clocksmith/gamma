'use strict';

// 3395. Subsequences with a Unique Middle Mode I.
// Separate middle frequencies at least three from frequency two with three distinct other values; O(n*U) time and O(U) space. Inputs are preserved.

function solve(nums) {
  const modulus = 1000000007, left = new Map(), right = new Map();
  for (const value of nums) right.set(value, (right.get(value) || 0) + 1);
  const values = [...right.keys()];
  function choose(count, amount) { return amount === 0 ? 1 : amount === 1 ? count : count * (count - 1) / 2; }
  let leftPairs = 0, rightPairs = 0, answer = 0;
  for (const count of right.values()) rightPairs += choose(count, 2);
  for (let index = 0; index < nums.length; index += 1) {
    const middle = nums[index];
    rightPairs -= right.get(middle) - 1;
    right.set(middle, right.get(middle) - 1);
    const a = left.get(middle) || 0, b = right.get(middle);
    const otherLeft = index - a, otherRight = nums.length - index - 1 - b;
    let ways = 0;
    for (let first = 0; first <= 2; first += 1) {
      for (let second = 0; second <= 2; second += 1) {
        if (first + second >= 2) ways += choose(a, first) * choose(otherLeft, 2 - first) * choose(b, second) * choose(otherRight, 2 - second);
      }
    }
    const duplicateLeft = leftPairs - choose(a, 2), duplicateRight = rightPairs - choose(b, 2);
    for (const value of values) {
      if (value === middle) continue;
      const lCount = left.get(value) || 0, rCount = right.get(value) || 0;
      ways += a * lCount * (choose(otherRight - rCount, 2) - duplicateRight + choose(rCount, 2));
      ways += b * rCount * (choose(otherLeft - lCount, 2) - duplicateLeft + choose(lCount, 2));
    }
    answer = (answer + ways) % modulus;
    leftPairs += a; left.set(middle, a + 1);
  }
  return answer;
}

const subsequencesWithMiddleMode = solve;
class Solution {
  subsequencesWithMiddleMode(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, subsequencesWithMiddleMode };
