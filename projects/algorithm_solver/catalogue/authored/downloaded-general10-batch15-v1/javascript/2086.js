'use strict';

// 2086. Minimum Number of Buckets Required to Collect Rainwater from Houses (Medium).
// Specification: https://leetcode.com/problems/minimum-number-of-buckets-required-to-collect-rainwater-from-houses/description/
function solve(street) {
  const cells = street.split('');
  const n = cells.length;
  let count = 0;
  for (let i = 0; i < n; i++) {
    if (cells[i] !== 'H') continue;
    if ((i > 0 && cells[i - 1] === 'B') || (i + 1 < n && cells[i + 1] === 'B')) continue;
    if (i + 1 < n && cells[i + 1] === '.') { cells[i + 1] = 'B'; count++; }
    else if (i > 0 && cells[i - 1] === '.') { cells[i - 1] = 'B'; count++; }
    else return -1;
  }
  return count;
}
const minimumBuckets = solve;
class Solution { minimumBuckets(street) { return solve(street); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, minimumBuckets };
