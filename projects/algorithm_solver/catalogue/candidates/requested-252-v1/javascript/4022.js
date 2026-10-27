/**
 * 4022. K-th Digit in Infinite String
 * Candidate source; not executed, syntax-checked, tested, or qualified.
 * Specification: https://leetcode.com/problems/k-th-digit-in-infinite-string/description/
 * Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/4000-4099/4022.K-th%20Digit%20in%20Infinite%20String/README_EN.md
 * Complexity: O(log k) arithmetic steps, O(log k) output-conversion space.
 * Block 0 omits zero; odd ten-number blocks reverse their integer order, not the digits inside an integer.
 */

function solve(k) {
  let offset = BigInt(k);
  if (offset <= 9n) return Number(offset);
  offset -= 10n;
  let digits = 2n, firstBlock = 1n;
  while (offset >= 90n * firstBlock * digits) { offset -= 90n * firstBlock * digits; firstBlock *= 10n; digits++; }
  const block = firstBlock + offset / (10n * digits), inside = offset % (10n * digits);
  const numberIndex = inside / digits, digitIndex = Number(inside % digits);
  const value = 10n * block + (block % 2n === 0n ? numberIndex : 9n - numberIndex);
  return Number(value.toString()[digitIndex]);
}

function kthDigit(k) {
  return solve(k);
}

class Solution {
  kthDigit(k) {
    return solve(k);
  }
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { solve, kthDigit, Solution };
}
