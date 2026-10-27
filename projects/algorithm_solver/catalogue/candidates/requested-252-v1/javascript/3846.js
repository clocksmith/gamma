/**
 * 3846. Total Distance to Type a String Using One Finger
 * Authored candidate: not executed, imported, syntax-checked, tested, or qualified.
 * Signature: solve(s).
 * Algorithm: Sum Manhattan distances on the specified left-aligned QWERTY grid, starting at a.
 * Complexity: O(n) time; O(26) space.
 * Numeric semantics: Exact integer arithmetic on the published input bounds; JavaScript Number results remain safe integers.
 * Mutation: Does not mutate input arrays, rows, strings, or trees.
 * Interface: Ordered-positional solve; native forwarding name included only when confirmed.
 * Specification: https://leetcode.com/problems/total-distance-to-type-a-string-using-one-finger/description/
 * Consulted public statement/reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3800-3899/3846.Total%20Distance%20to%20Type%20a%20String%20Using%20One%20Finger/README_EN.md
 * Reference repository attribution: Doocs contributors, CC-BY-SA-4.0.
 * New readable implementations; no third-party source bodies copied verbatim.
 * No protected tests or private reference implementations used.
 */

function solve(s) {
  const positions = new Map();
  const rows = ["qwertyuiop", "asdfghjkl", "zxcvbnm"];
  for (let row = 0; row < rows.length; row += 1) {
    for (let column = 0; column < rows[row].length; column += 1) {
      positions.set(rows[row][column], [row, column]);
    }
  }
  let [previousRow, previousColumn] = positions.get("a");
  let distance = 0;
  for (const key of s) {
    const [row, column] = positions.get(key);
    distance += Math.abs(row - previousRow) + Math.abs(column - previousColumn);
    previousRow = row;
    previousColumn = column;
  }
  return distance;
}

function totalDistance(s) {
  return solve(s);
}

class Solution {
  totalDistance(s) {
    return solve(s);
  }
}

if (typeof module !== "undefined" && module.exports) {
  module.exports = { solve, totalDistance, Solution };
}
