/**
 * 3966. Count Good Integers in a Range
 * Candidate source; not executed, syntax-checked, tested, or qualified.
 * Specification: https://leetcode.com/problems/count-good-integers-in-a-range/description/
 * Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3900-3999/3966.Count%20Good%20Integers%20in%20a%20Range/README_EN.md
 * Complexity: O(log r * 100) time, O(log r * 10) space.
 * Leading padding zeros do not constrain the first real digit; zero cancels in the range difference. r <= 1e15, counts exactly representable. Inputs preserved; native method pending.
 */

function solve(l, r, k) {
  function count(bound) {
    if (bound < 0) return 0;
    const digits = String(bound).split('').map(Number);
    const memo = new Map();
    function visit(position, previous, tight) {
      if (position === digits.length) return 1;
      const key = (position * 11 + previous) * 2 + Number(tight);
      if (memo.has(key)) return memo.get(key);
      const limit = tight ? digits[position] : 9;
      let total = 0;
      for (let digit = 0; digit <= limit; digit++) {
        let following;
        if (previous === 10 && digit === 0) following = 10;
        else if (previous === 10 || Math.abs(previous - digit) <= k) following = digit;
        else continue;
        total += visit(position + 1, following, tight && digit === limit);
      }
      memo.set(key, total);
      return total;
    }
    return visit(0, 10, true);
  }
  return count(r) - count(l - 1);
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { solve };
}
