'use strict';

// 3867. Sum of GCD of Formed Pairs.
// O(n log n + n log M) time and O(n) space; construct prefix-maximum GCDs before pairing extremes.
function solve(nums) {
  function gcd(left, right) {
    while (right !== 0) [left, right] = [right, left % right];
    return left;
  }
  let maximum = 0;
  const values = [];
  for (const value of nums) {
    maximum = Math.max(maximum, value);
    values.push(gcd(value, maximum));
  }
  values.sort((left, right) => left - right);
  let answer = 0;
  for (let index = 0; index < Math.floor(values.length / 2); index += 1) answer += gcd(values[index], values[values.length - 1 - index]);
  return answer;
}

const gcdSum = solve;
class Solution {
  gcdSum(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, gcdSum };
