'use strict';

// 2106. Maximum Fruits Harvested After at Most K Steps. Sliding window with the cheaper of the two one-turn routes; O(n) time and O(1) auxiliary space. Inputs are preserved.

function solve(fruits, startPos, k) {
  let left = 0;
  let total = 0;
  let answer = 0;
  for (let right = 0; right < fruits.length; right += 1) {
    const [position, amount] = fruits[right];
    total += amount;
    while (left <= right) {
      const west = Math.max(0, startPos - fruits[left][0]);
      const east = Math.max(0, position - startPos);
      if (west + east + Math.min(west, east) <= k) break;
      total -= fruits[left][1];
      left += 1;
    }
    answer = Math.max(answer, total);
  }
  return answer;
}

const maxTotalFruits = solve;
class Solution {
  maxTotalFruits(fruits, startPos, k) { return solve(fruits, startPos, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maxTotalFruits };
