'use strict';

// 2792. Count Nodes That Are Great Enough.
class TreeNode {
  constructor(val = 0, left = null, right = null) {
    this.val = val;
    this.left = left;
    this.right = right;
  }
}

// O(n*k) time, O(n+k) space. Child summaries are released after merging; input nodes stay unchanged.
function solve(root, k) {
  if (root === null) return 0;
  const stack = [[root, false]];
  const smallest = new Map();
  let answer = 0;
  while (stack.length > 0) {
    const [node, ready] = stack.pop();
    if (!ready) {
      stack.push([node, true]);
      if (node.right !== null) stack.push([node.right, false]);
      if (node.left !== null) stack.push([node.left, false]);
      continue;
    }
    const left = smallest.get(node.left) || [];
    const right = smallest.get(node.right) || [];
    smallest.delete(node.left);
    smallest.delete(node.right);
    const merged = [];
    let first = 0;
    let second = 0;
    while (merged.length < k && (first < left.length || second < right.length)) {
      if (second === right.length || (first < left.length && left[first] <= right[second])) {
        merged.push(left[first]);
        first += 1;
      } else {
        merged.push(right[second]);
        second += 1;
      }
    }
    if (merged.length === k && merged[k - 1] < node.val) answer += 1;
    let low = 0;
    let high = merged.length;
    while (low < high) {
      const middle = Math.floor((low + high) / 2);
      if (merged[middle] < node.val) low = middle + 1;
      else high = middle;
    }
    if (low < k) {
      merged.splice(low, 0, node.val);
      if (merged.length > k) merged.pop();
    }
    smallest.set(node, merged);
  }
  return answer;
}

const countGreatEnoughNodes = solve;
class Solution {
  countGreatEnoughNodes(root, k) { return solve(root, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, countGreatEnoughNodes, TreeNode };
