/**
 * 3879. Maximum Distinct Path Sum in a Binary Tree
 * Authored candidate: not executed, imported, syntax-checked, tested, or qualified.
 * Signature: solve(root).
 * Algorithm: Convert to undirected adjacency, then iterative backtracking from each possible endpoint with a path-local distinct-value set.
 * Complexity: O(n^2) time; O(n) auxiliary space.
 * Numeric semantics: Exact integer arithmetic on the published input bounds; JavaScript Number results remain safe integers.
 * Mutation: Does not mutate input arrays, rows, strings, or trees.
 * Interface: solve(root), maxSum, and Solution.maxSum; normal TreeNode objects.
 * Specification: https://leetcode.com/problems/maximum-distinct-path-sum-in-a-binary-tree/description/
 * Consulted public statement/reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3800-3899/3879.Maximum%20Distinct%20Path%20Sum%20in%20a%20Binary%20Tree/README_EN.md
 * Reference repository attribution: Doocs contributors, CC-BY-SA-4.0.
 * New readable implementations; no third-party source bodies copied verbatim.
 * No protected tests or private reference implementations used.
 * Contract note: Paths may turn through any ancestor and need not include the root. Negative totals are not pruned; all-negative trees return a nonempty path maximum.
 */

function solve(root) {
  if (root == null) throw new TypeError("The specified tree is nonempty.");
  const nodes = [root];
  const adjacency = [[]];
  const values = [];
  for (let index = 0; index < nodes.length; index += 1) {
    const node = nodes[index];
    values.push(node.val);
    for (const child of [node.left, node.right]) {
      if (child != null) {
        const childIndex = nodes.length;
        nodes.push(child);
        adjacency.push([index]);
        adjacency[index].push(childIndex);
      }
    }
  }
  let answer = -Infinity;
  for (let start = 0; start < nodes.length; start += 1) {
    const usedValues = new Set();
    const stack = [[start, -1, 0, false]];
    while (stack.length > 0) {
      const [node, parent, previousTotal, leaving] = stack.pop();
      const value = values[node];
      if (leaving) {
        usedValues.delete(value);
        continue;
      }
      if (usedValues.has(value)) continue;
      usedValues.add(value);
      const total = previousTotal + value;
      answer = Math.max(answer, total);
      stack.push([node, parent, total, true]);
      for (const neighbor of adjacency[node]) {
        if (neighbor !== parent) stack.push([neighbor, node, total, false]);
      }
    }
  }
  return answer;
}

function maxSum(root) {
  return solve(root);
}

class Solution {
  maxSum(root) {
    return solve(root);
  }
}

if (typeof module !== "undefined" && module.exports) {
  module.exports = { solve, maxSum, Solution };
}
