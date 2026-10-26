'use strict';

// 3756. Concatenate Non-Zero Digits and Multiply by Sum II.
// O(n + q) time and O(n) auxiliary space; modular multiplication uses exact split products in JavaScript.
function multiplyMod(left, right) {
  const modulus = 1000000007;
  return (left * (right % 32768) + ((left * Math.floor(right / 32768)) % modulus) * 32768) % modulus;
}

function solve(s, queries) {
  const modulus = 1000000007;
  const prefix = [0];
  const sums = [0];
  const counts = [0];
  const powers = [1];
  for (let index = 0; index < s.length; index += 1) {
    const digit = s.charCodeAt(index) - 48;
    prefix.push(digit === 0 ? prefix[index] : (prefix[index] * 10 + digit) % modulus);
    sums.push(sums[index] + digit);
    counts.push(counts[index] + (digit === 0 ? 0 : 1));
    powers.push(powers[index] * 10 % modulus);
  }
  const answer = [];
  for (const [left, right] of queries) {
    const length = counts[right + 1] - counts[left];
    const value = (prefix[right + 1] - multiplyMod(prefix[left], powers[length]) + modulus) % modulus;
    answer.push(multiplyMod(value, sums[right + 1] - sums[left]));
  }
  return answer;
}

const sumAndMultiply = solve;
class Solution {
  sumAndMultiply(s, queries) { return solve(s, queries); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, sumAndMultiply };
