/* Original candidate for LeetCode 2773. Contract: https://leetcode.com/problems/height-of-special-binary-tree/
Definition additionally checked against public doocs/leetcode documentation (CC-BY-SA-4.0); original implementation.
Development tests only; not admitted or independently qualified.
solve accepts native special binary-tree nodes (val,left,right), detects circular leaf links by reciprocal identity; JSON compact BFS array input explicitly describes the underlying tree before leaf links.
Complexity: O(n) time and space */
"use strict";

function build(values) {
  if (!values.length || values[0] === null) return [];
  const nodes = [[values[0], -1, -1]];
  let position = 1;
  for (let index = 0; index < nodes.length && position < values.length; index++) {
    for (let side = 1; side <= 2; side++) {
      if (position < values.length && values[position] !== null) {
        nodes[index][side] = nodes.length;
        nodes.push([values[position], -1, -1]);
      }
      position++;
    }
  }
  return nodes;
}

function solve(root) {
  if (!Array.isArray(root)) {
    const stack = [[root, 0]];
    let answer = 0;
    while (stack.length) {
      const [node, depth] = stack.pop();
      answer = Math.max(answer, depth);
      // Reciprocal edges identify the circular leaf list, not tree children.
      if ((node.left && node.left.right === node) ||
          (node.right && node.right.left === node)) continue;
      if (node.left) stack.push([node.left, depth + 1]);
      if (node.right) stack.push([node.right, depth + 1]);
    }
    return answer;
  }
  const nodes = build(root);
  const depths = Array(nodes.length).fill(0);
  let answer = 0;
  for (let index = 0; index < nodes.length; index++) {
    for (const child of nodes[index].slice(1)) {
      if (child < 0) continue;
      depths[child] = depths[index] + 1;
      answer = Math.max(answer, depths[child]);
    }
  }
  return answer;
}

module.exports = solve;
