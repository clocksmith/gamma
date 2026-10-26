/**
 * 3631. Sort Threats by Severity and Exploitability
 * 
 * Authored candidate. Not executed, syntax-checked, tested, or qualified.
 * Interface: native array candidate.
 * Signature: solve(threats).
 * O(n log n) time and O(n) auxiliary/output space.
 * Corrects the earlier database misclassification. This is the native array task, exposed as solve(threats), sortThreats(threats), and Solution.sortThreats(threats). Input and inner rows are preserved; score reaches 3,000,000,000, so no signed 32-bit coercion is used.
 * Specification: https://leetcode.com/problems/sort-threats-by-severity-and-exploitability/description/
 * Consulted reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3600-3699/3631.Sort%20Threats%20by%20Severity%20and%20Exploitability/README_EN.md
 */

function solve(threats) {
  if (!Array.isArray(threats) || threats.length < 1 || threats.length > 100000) {
    throw new TypeError('Expected 1 through 100000 threat rows.');
  }
  const ids = new Set();
  const result = threats.map(row => {
    if (!Array.isArray(row) || row.length !== 3 || !row.every(Number.isSafeInteger) ||
        row[0] < 1 || row[0] > 1000000 || row[1] < 1 || row[1] > 1000000000 ||
        row[2] < 1 || row[2] > 1000000000 || ids.has(row[0])) {
      throw new RangeError('Invalid threat row or duplicate threat ID.');
    }
    ids.add(row[0]);
    return row.slice();
  });
  return result.sort((a, b) => (2 * b[1] + b[2]) - (2 * a[1] + a[2]) || a[0] - b[0]);
}

function sortThreats(threats) {
  return solve(threats);
}

class Solution {
  sortThreats(threats) {
    return solve(threats);
  }
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { solve, sortThreats, Solution };
}
