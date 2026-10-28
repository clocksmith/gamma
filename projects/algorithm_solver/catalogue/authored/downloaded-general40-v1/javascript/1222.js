'use strict';

// 1222. Queens That Can Attack the King (Medium).
// Specification: https://leetcode.com/problems/queens-that-can-attack-the-king/description/
function solve(queens, king) {
  const queenSet = new Set(queens.map(([r, c]) => `${r},${c}`));
  const result = [];
  const directions = [[1, 0], [-1, 0], [0, 1], [0, -1], [1, 1], [1, -1], [-1, 1], [-1, -1]];
  for (const [dr, dc] of directions) {
    let r = king[0] + dr; let c = king[1] + dc;
    while (r >= 0 && r < 8 && c >= 0 && c < 8) {
      if (queenSet.has(`${r},${c}`)) { result.push([r, c]); break; }
      r += dr; c += dc;
    }
  }
  result.sort((a, b) => a[0] - b[0] || a[1] - b[1]);
  return result;
}
const queensThatCanAttackTheKing = solve;
class Solution { queensThatCanAttackTheKing(queens, king) { return solve(queens, king); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, queensThatCanAttackTheKing };
