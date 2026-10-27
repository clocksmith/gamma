'use strict';

// 449. Serialize and Deserialize BST.

class TreeNode {
  constructor(val = 0, left = null, right = null) {
    this.val = val;
    this.left = left;
    this.right = right;
  }
}

class Codec {
  serialize(root) {
    const values = [], stack = root ? [root] : [];
    while (stack.length > 0) {
      const node = stack.pop();
      values.push(String(node.val));
      if (node.right) stack.push(node.right);
      if (node.left) stack.push(node.left);
    }
    return values.join(',');
  }
  deserialize(data) {
    if (data === '') return null;
    const values = data.split(',').map(Number), root = new TreeNode(values[0]), stack = [root];
    for (let i = 1; i < values.length; i += 1) {
      const value = values[i], node = new TreeNode(value);
      if (value < stack[stack.length - 1].val) stack[stack.length - 1].left = node;
      else {
        let parent = stack[stack.length - 1];
        while (stack.length > 0 && stack[stack.length - 1].val < value) parent = stack.pop();
        parent.right = node;
      }
      stack.push(node);
    }
    return root;
  }
}

function solve(operations, args) {
  if (operations.length === 0) return [];
  const instance = new Codec(...args[0]);
  const result = [null];
  for (let i = 1; i < operations.length; i += 1) {
    const value = instance[operations[i]](...args[i]);
    result.push(value === undefined ? null : value);
  }
  return result;
}

const Solution = Codec;

if (typeof module !== 'undefined') module.exports = { solve, Codec, Solution };
