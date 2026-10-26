'use strict';

// 3477. Fruits Into Baskets II (Easy).
// Specification: https://leetcode.com/problems/fruits-into-baskets-ii/description/
// O(n^2) time, O(n) space; choose the leftmost available fit and preserve both arrays.
function solve(fruits, baskets) {
  const used = new Array(baskets.length).fill(false);
  let unplaced = 0;
  for (const quantity of fruits) {
    let placed = false;
    for (let index = 0; index < baskets.length; index++) {
      if (!used[index] && baskets[index] >= quantity) {
        used[index] = true;
        placed = true;
        break;
      }
    }
    if (!placed) unplaced++;
  }
  return unplaced;
}

const numOfUnplacedFruits = solve;
class Solution {
  numOfUnplacedFruits(fruits, baskets) { return solve(fruits, baskets); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, numOfUnplacedFruits };
