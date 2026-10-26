'use strict';

// 944. Delete Columns to Make Sorted (Easy).
// Specification: https://leetcode.com/problems/delete-columns-to-make-sorted/description/
// O(rows * columns) time, O(1) space; count columns containing a descending adjacent pair.
function solve(strs) {
  let deletions = 0;
  for (let column = 0; column < strs[0].length; column++) {
    for (let row = 1; row < strs.length; row++) {
      if (strs[row][column] < strs[row - 1][column]) {
        deletions++;
        break;
      }
    }
  }
  return deletions;
}

const minDeletionSize = solve;
class Solution {
  minDeletionSize(strs) { return solve(strs); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minDeletionSize };
