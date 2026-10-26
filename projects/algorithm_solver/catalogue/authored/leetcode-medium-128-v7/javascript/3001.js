'use strict';

// 3001. Minimum Moves to Capture The Queen: check unobstructed rook and bishop attacks before using the two-move bound.
// O(1) time and O(1) auxiliary space; inputs are read-only.
function solve(a, b, c, d, e, f) {
  if (a === e && !(c === a && Math.min(b, f) < d && d < Math.max(b, f))) return 1;
  if (b === f && !(d === b && Math.min(a, e) < c && c < Math.max(a, e))) return 1;
  if (Math.abs(c - e) === Math.abs(d - f)) {
    const blocked = Math.abs(a - c) === Math.abs(b - d)
      && Math.min(c, e) < a && a < Math.max(c, e)
      && Math.min(d, f) < b && b < Math.max(d, f);
    if (!blocked) return 1;
  }
  return 2;
}

const minMovesToCaptureTheQueen = solve;
class Solution {
  minMovesToCaptureTheQueen(a, b, c, d, e, f) { return solve(a, b, c, d, e, f); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minMovesToCaptureTheQueen };
