'use strict';

// 3869. Count Fancy Numbers in a Range.
// O(100 D^2 + 10*2^10) time and O(D + 2^10) space; digit-sum DP plus deduplicated strictly monotone numbers.
function solve(l, r) {
  function good(value) {
    const digits = String(value);
    let increasing = true;
    let decreasing = true;
    for (let index = 1; index < digits.length; index += 1) {
      if (digits[index - 1] >= digits[index]) increasing = false;
      if (digits[index - 1] <= digits[index]) decreasing = false;
    }
    return increasing || decreasing;
  }
  const monotone = new Set();
  for (let mask = 1; mask < (1 << 10); mask += 1) {
    const digits = [];
    for (let digit = 0; digit < 10; digit += 1) if (mask & (1 << digit)) digits.push(String(digit));
    if (digits[0] !== '0') monotone.add(Number(digits.join('')));
    if (digits[digits.length - 1] !== '0') monotone.add(Number(digits.slice().reverse().join('')));
  }
  const extra = [];
  for (const value of monotone) {
    let total = 0;
    for (const char of String(value)) total += Number(char);
    if (!good(total)) extra.push(value);
  }
  function count(bound) {
    if (bound <= 0) return 0;
    const digits = Array.from(String(bound), Number);
    const limit = 9 * digits.length;
    let loose = Array(limit + 1).fill(0);
    let tight = Array(limit + 1).fill(0);
    tight[0] = 1;
    for (let position = 0; position < digits.length; position += 1) {
      const digit = digits[position];
      const nextLoose = Array(limit + 1).fill(0);
      const nextTight = Array(limit + 1).fill(0);
      for (let total = 0; total <= 9 * position; total += 1) {
        if (loose[total] > 0) for (let added = 0; added < 10; added += 1) nextLoose[total + added] += loose[total];
        if (tight[total] > 0) {
          for (let added = 0; added < digit; added += 1) nextLoose[total + added] += tight[total];
          nextTight[total + digit] += tight[total];
        }
      }
      loose = nextLoose;
      tight = nextTight;
    }
    let answer = 0;
    for (let total = 1; total <= limit; total += 1) if (good(total)) answer += loose[total] + tight[total];
    for (const value of extra) if (value <= bound) answer += 1;
    return answer;
  }
  return count(r) - count(l - 1);
}

const countFancy = solve;
class Solution {
  countFancy(l, r) { return solve(l, r); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, countFancy };
