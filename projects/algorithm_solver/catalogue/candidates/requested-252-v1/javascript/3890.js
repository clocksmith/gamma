/**
 * 3890. Integers With Multiple Sum of Two Cubes
 * Candidate source; not executed, syntax-checked, tested, or qualified.
 * Specification: https://leetcode.com/problems/integers-with-multiple-sum-of-two-cubes/description/
 * Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3800-3899/3890.Integers%20With%20Multiple%20Sum%20of%20Two%20Cubes/README_EN.md
 * Complexity: O(n^(2/3) + g log g) time; O(n^(2/3)) space.
 * 1 <= n <= 1e9. Counts unordered positive cube pairs; inputs preserved.
 */

function solve(n) {
  const cubes = [];
  for (let value = 1; value * value * value <= n; value += 1) {
    cubes.push(value * value * value);
  }
  const counts = new Map();
  for (let first = 0; first < cubes.length; first += 1) {
    for (let second = first; second < cubes.length; second += 1) {
      const total = cubes[first] + cubes[second];
      if (total > n) break;
      counts.set(total, (counts.get(total) || 0) + 1);
    }
  }
  return [...counts].filter(entry => entry[1] >= 2).map(entry => entry[0]).sort((a, b) => a - b);
}

function findGoodIntegers(n) {
  return solve(n);
}

class Solution {
  findGoodIntegers(n) {
    return solve(n);
  }
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { solve, findGoodIntegers, Solution };
}
