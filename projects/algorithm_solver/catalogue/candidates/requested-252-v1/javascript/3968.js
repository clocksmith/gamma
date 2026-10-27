/**
 * 3968. Maximum Manhattan Distance After All Moves
 * Candidate source; not executed, syntax-checked, tested, or qualified.
 * Specification: https://leetcode.com/problems/maximum-manhattan-distance-after-all-moves/description/
 * Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3900-3999/3968.Maximum%20Manhattan%20Distance%20After%20All%20Moves/README_EN.md
 * Complexity: O(n) time, O(1) auxiliary space.
 * Maximum final distance, not maximum intermediate distance. Each underscore is independently chosen; input preserved.
 */

function solve(moves) {
  let horizontal = 0, vertical = 0, free = 0;
  for (const move of moves) {
    if (move === 'U') vertical++;
    else if (move === 'D') vertical--;
    else if (move === 'R') horizontal++;
    else if (move === 'L') horizontal--;
    else free++;
  }
  return Math.abs(horizontal) + Math.abs(vertical) + free;
}

function maxDistance(moves) {
  return solve(moves);
}

class Solution {
  maxDistance(moves) {
    return solve(moves);
  }
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { solve, maxDistance, Solution };
}
