'use strict';

// 1653. Minimum Deletions to Make String Balanced: delete the current a or every preceding b.
// O(n) time and O(1) auxiliary space; inputs are read-only.
function solve(s) {
  let deletions = 0;
  let bCount = 0;
  for (const character of s) {
    if (character === 'b') bCount += 1;
    else deletions = Math.min(deletions + 1, bCount);
  }
  return deletions;
}

const minimumDeletions = solve;
class Solution {
  minimumDeletions(s) { return solve(s); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minimumDeletions };
