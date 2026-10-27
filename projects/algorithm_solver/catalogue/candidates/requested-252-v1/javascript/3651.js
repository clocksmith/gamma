/**
 * 3651. Minimum Cost Path with Teleportations
 * Candidate source; not executed, syntax-checked, tested, or qualified.
 * Specification: https://leetcode.com/problems/minimum-cost-path-with-teleportations/description/
 * Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3600-3699/3651.Minimum%20Cost%20Path%20with%20Teleportations/README_EN.md
 * Complexity: O(mn log(mn) + k mn) time; O(mn) space.
 * Grid is preserved; start-cell cost is zero; equal-value teleport groups are handled together.
 */

function solve(grid, k) {
  const rows = grid.length, columns = grid[0].length;
  const values = grid.flat();
  const order = Array.from({ length: values.length }, (_, i) => i).sort((a, b) => values[b] - values[a]);
  let costs = Array(values.length).fill(Infinity);
  costs[0] = 0;
  function relax(current) {
    for (let row = 0; row < rows; row += 1) {
      for (let column = 0; column < columns; column += 1) {
        const index = row * columns + column;
        if (row > 0) current[index] = Math.min(current[index], current[index - columns] + values[index]);
        if (column > 0) current[index] = Math.min(current[index], current[index - 1] + values[index]);
      }
    }
  }
  relax(costs);
  let answer = costs[costs.length - 1];
  for (let used = 0; used < k; used += 1) {
    const nextCosts = Array(values.length).fill(Infinity);
    let best = Infinity, start = 0;
    while (start < order.length) {
      let end = start;
      while (end < order.length && values[order[end]] === values[order[start]]) {
        best = Math.min(best, costs[order[end]]); end += 1;
      }
      for (let offset = start; offset < end; offset += 1) nextCosts[order[offset]] = best;
      start = end;
    }
    relax(nextCosts); costs = nextCosts;
    answer = Math.min(answer, costs[costs.length - 1]);
  }
  return answer;
}

function minCost(grid, k) {
  return solve(grid, k);
}

class Solution {
  minCost(grid, k) {
    return solve(grid, k);
  }
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { solve, minCost, Solution };
}
