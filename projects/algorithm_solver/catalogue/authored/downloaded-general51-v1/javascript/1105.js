'use strict';

// 1105. Filling Bookcase Shelves (Medium).
// Specification: https://leetcode.com/problems/filling-bookcase-shelves/description/
function solve(books, shelfWidth) {
  const dp = new Array(books.length + 1).fill(Infinity);
  dp[0] = 0;
  for (let i = 1; i <= books.length; i++) {
    let width = 0; let height = 0;
    for (let j = i; j >= 1; j--) {
      width += books[j - 1][0];
      if (width > shelfWidth) break;
      height = Math.max(height, books[j - 1][1]);
      dp[i] = Math.min(dp[i], dp[j - 1] + height);
    }
  }
  return dp[books.length];
}
const minHeightShelves = solve;
class Solution { minHeightShelves(books, shelfWidth) { return solve(books, shelfWidth); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, minHeightShelves };
