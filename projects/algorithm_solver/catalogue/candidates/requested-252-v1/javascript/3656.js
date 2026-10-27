/**
 * 3656. Determine if a Simple Graph Exists
 * Authored candidate: not executed, imported, syntax-checked, tested, or qualified.
 * Signature: solve(degrees).
 * Algorithm: Erdos-Gallai inequalities with descending prefix sums and binary-searched split.
 * Complexity: O(n log n) time; O(n) space.
 * Numeric semantics: Exact integer arithmetic on the published input bounds; JavaScript Number results remain safe integers.
 * Mutation: Does not mutate input arrays, rows, strings, or trees.
 * Interface: Canonical solve(degrees). Native judge method name was not supplied or independently verified.
 * Specification: https://leetcode.com/problems/determine-if-a-simple-graph-exists/description/
 * Consulted public statement/reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3600-3699/3656.Determine%20if%20a%20Simple%20Graph%20Exists/README_EN.md
 * Reference repository attribution: Doocs contributors, CC-BY-SA-4.0.
 * New readable implementations; no third-party source bodies copied verbatim.
 * No protected tests or private reference implementations used.
 */

function solve(degrees) {
  const ordered = degrees.slice().sort((a, b) => b - a);
  const size = ordered.length;
  const prefix = new Float64Array(size + 1);
  for (let index = 0; index < size; index += 1) {
    if (ordered[index] < 0 || ordered[index] >= size) return false;
    prefix[index + 1] = prefix[index] + ordered[index];
  }
  if (prefix[size] % 2 !== 0) return false;
  for (let count = 1; count <= size; count += 1) {
    let left = count;
    let right = size;
    while (left < right) {
      const middle = Math.floor((left + right) / 2);
      if (ordered[middle] >= count) left = middle + 1;
      else right = middle;
    }
    const split = left;
    const available = count * (count - 1) + (split - count) * count + prefix[size] - prefix[split];
    if (prefix[count] > available) return false;
  }
  return true;
}

if (typeof module !== "undefined" && module.exports) {
  module.exports = { solve };
}
