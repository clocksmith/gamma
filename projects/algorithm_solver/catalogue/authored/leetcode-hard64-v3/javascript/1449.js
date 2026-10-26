'use strict';

// 1449. Form Largest Integer With Digits That Add up to Target: maximize digit count, then reconstruct in descending digit order; O(9*target) time and O(target) space.

function solve(cost, target) {
  const digits = Array(target + 1).fill(-1);
  digits[0] = 0;
  for (let amount = 1; amount <= target; amount += 1) {
    for (const price of cost) {
      if (amount >= price && digits[amount - price] >= 0) digits[amount] = Math.max(digits[amount], digits[amount - price] + 1);
    }
  }
  if (digits[target] < 0) return '0';
  const answer = [];
  let amount = target;
  for (let digit = 9; digit >= 1; digit -= 1) {
    const price = cost[digit - 1];
    while (amount >= price && digits[amount] === digits[amount - price] + 1) {
      answer.push(String(digit));
      amount -= price;
    }
  }
  return answer.join('');
}

const largestNumber = solve;
class Solution {
  largestNumber(cost, target) { return solve(cost, target); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, largestNumber };
