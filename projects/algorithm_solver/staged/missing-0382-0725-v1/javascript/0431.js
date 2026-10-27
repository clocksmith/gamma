'use strict';

// 431. Encode N-ary Tree to Binary Tree.

class Node {
  constructor(val = 0, children = []) { this.val = val; this.children = children; }
}


class TreeNode {
  constructor(val = 0, left = null, right = null) {
    this.val = val;
    this.left = left;
    this.right = right;
  }
}

class Codec {
  encode(root) {
    if (root === null) return null;
    const result = new TreeNode(root.val), stack = [[root, result]];
    while (stack.length > 0) {
      const [original, binary] = stack.pop();
      let previous = null;
      for (const child of original.children || []) {
        const copy = new TreeNode(child.val);
        if (previous === null) binary.left = copy;
        else previous.right = copy;
        previous = copy;
        stack.push([child, copy]);
      }
    }
    return result;
  }
  decode(data) {
    if (data === null) return null;
    const result = new Node(data.val, []), stack = [[data, result]];
    while (stack.length > 0) {
      const [binary, original] = stack.pop();
      for (let child = binary.left; child !== null; child = child.right) {
        const copy = new Node(child.val, []);
        original.children.push(copy); stack.push([child, copy]);
      }
    }
    return result;
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
