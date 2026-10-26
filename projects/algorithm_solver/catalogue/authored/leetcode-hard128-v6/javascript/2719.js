'use strict';

// 2719. Count of Integers.
// Bounded decimal digit-sum dynamic programming, subtracting the lower exclusive prefix; O(L*min(9L,max_sum)*10) time and O(min(9L,max_sum)) space. Inputs are preserved.

function solve(num1, num2, min_sum, max_sum) {
  const modulus = 1000000007;
  function countThrough(bound) {
    if (bound < 0n) return 0;
    const digits = bound.toString(), cap = Math.min(max_sum, 9 * digits.length);
    let loose = Array(cap + 1).fill(0), tightSum = 0;
    for (const character of digits) {
      const digit = Number(character), following = Array(cap + 1).fill(0);
      for (let total = 0; total <= cap; total += 1) {
        if (loose[total] === 0) continue;
        for (let value = 0; value <= 9 && total + value <= cap; value += 1) {
          following[total + value] = (following[total + value] + loose[total]) % modulus;
        }
      }
      for (let value = 0; value < digit && tightSum + value <= cap; value += 1) {
        following[tightSum + value] = (following[tightSum + value] + 1) % modulus;
      }
      tightSum += digit;
      loose = following;
    }
    let answer = min_sum <= tightSum && tightSum <= max_sum ? 1 : 0;
    for (let total = min_sum; total <= cap; total += 1) answer = (answer + loose[total]) % modulus;
    return answer;
  }
  return (countThrough(BigInt(num2)) - countThrough(BigInt(num1) - 1n) + modulus) % modulus;
}

const count = solve;
class Solution {
  count(num1, num2, min_sum, max_sum) { return solve(num1, num2, min_sum, max_sum); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, count };
