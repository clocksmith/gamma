/**
 * 3906. Count Good Integers on a Grid Path
 * Candidate source; not executed, syntax-checked, tested, or qualified.
 * Specification: https://leetcode.com/problems/count-good-integers-on-a-grid-path/description/
 * Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3900-3999/3906.Count%20Good%20Integers%20on%20a%20Grid%20Path/README_EN.md
 * Complexity: O(16*10^2) time, O(16*10) states.
 * 1<=l<=r<=9e15, exactly three D and R. Bound and answer fit JS safe integers; intermediate counts use BigInt.
 */

function solve(l, r, directions) {
  const selected = new Set([0]);
  let position = 0;
  for (const direction of directions) {
    position += direction === 'D' ? 4 : 1;
    selected.add(position);
  }
  function count(bound) {
    if (bound < 0) return 0n;
    const digits = String(bound).padStart(16, '0').split('').map(Number);
    const memo = new Map();
    function visit(index, previous, tight) {
      if (index === 16) return 1n;
      const key = `${index},${previous},${tight}`;
      if (memo.has(key)) return memo.get(key);
      const maximum = tight ? digits[index] : 9;
      const minimum = selected.has(index) ? previous : 0;
      let answer = 0n;
      for (let digit = minimum; digit <= maximum; digit += 1) {
        answer += visit(index + 1, selected.has(index) ? digit : previous, tight && digit === maximum);
      }
      memo.set(key, answer);
      return answer;
    }
    return visit(0, 0, true);
  }
  return Number(count(r) - count(l - 1));
}

function countGoodIntegersOnPath(l, r, directions) {
  return solve(l, r, directions);
}

class Solution {
  countGoodIntegersOnPath(l, r, directions) {
    return solve(l, r, directions);
  }
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { solve, countGoodIntegersOnPath, Solution };
}
