'use strict';

// 3261. Count Substrings That Satisfy K-Constraint II: first-invalid boundaries and prefix sums of valid suffix counts.
// O(n + q) time and O(n + q) space. Inputs are preserved.
function solve(s, k, queries) {
  const n = s.length;
  const firstInvalid = new Int32Array(n).fill(n);
  const prefix = new Float64Array(n + 1);
  const counts = [0, 0];
  let left = 0;
  for (let right = 0; right < n; right += 1) {
    counts[s.charCodeAt(right) - 48] += 1;
    while (counts[0] > k && counts[1] > k) {
      firstInvalid[left] = right;
      counts[s.charCodeAt(left) - 48] -= 1;
      left += 1;
    }
    prefix[right + 1] = prefix[right] + right - left + 1;
  }
  const answer = [];
  for (const [start, end] of queries) {
    const split = Math.min(end + 1, firstInvalid[start]);
    const width = split - start;
    answer.push(width * (width + 1) / 2 + prefix[end + 1] - prefix[split]);
  }
  return answer;
}

const countKConstraintSubstrings = solve;
class Solution {
  countKConstraintSubstrings(s, k, queries) { return solve(s, k, queries); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, countKConstraintSubstrings };
