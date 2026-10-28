'use strict';

// 1196. How Many Apples Can You Put into the Basket (Easy).
// Specification: https://leetcode.com/problems/how-many-apples-can-you-put-into-the-basket/description/
function solve(weight) {
  const sorted = weight.slice().sort((a, b) => a - b);
  let total = 0; let count = 0;
  for (const value of sorted) { if (total + value > 5000) break; total += value; count++; }
  return count;
}
const maxNumberOfApples = solve;
class Solution { maxNumberOfApples(weight) { return solve(weight); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, maxNumberOfApples };
