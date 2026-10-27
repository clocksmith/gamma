/**
 * 4021. Minimum Operations to Make a Rotated Palindrome I
 * Candidate source; not executed, syntax-checked, tested, or qualified.
 * Specification: https://leetcode.com/problems/minimum-operations-to-make-a-rotated-palindrome-i/description/
 * Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/4000-4099/4021.Minimum%20Operations%20to%20Make%20a%20Rotated%20Palindrome%20I/README_EN.md
 * Complexity: O(n^2) time, O(n) space.
 * Each mirrored pair can be equalized by advancing one endpoint along the shorter alphabet arc. Increment operations commute with rotation; no rotation count >=n is needed.
 */

function solve(s) {
  const letters = Array.from(s, ch => ch.charCodeAt(0) - 97), n = s.length;
  let answer = 13 * Math.floor(n / 2);
  for (let shift = 0; shift < n && shift < answer; shift++) {
    let cost = shift;
    for (let i = 0; i < Math.floor(n / 2); i++) {
      const difference = Math.abs(letters[(shift + i) % n] - letters[(shift + n - 1 - i) % n]);
      cost += Math.min(difference, 26 - difference);
      if (cost >= answer) break;
    }
    answer = Math.min(answer, cost);
  }
  return answer;
}

function minOperations(s) {
  return solve(s);
}

class Solution {
  minOperations(s) {
    return solve(s);
  }
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { solve, minOperations, Solution };
}
