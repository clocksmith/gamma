'use strict';

// 428. Serialize and Deserialize N-ary Tree.

class Node {
  constructor(val = 0, children = []) { this.val = val; this.children = children; }
}

class Codec {
  serialize(root) {
    if (root === null) return '#';
    const tokens = [], stack = [root];
    while (stack.length > 0) {
      const node = stack.pop(), children = node.children || [];
      tokens.push(`${node.val}:${children.length}`);
      for (let i = children.length - 1; i >= 0; i -= 1) stack.push(children[i]);
    }
    return tokens.join(',');
  }
  deserialize(data) {
    if (data === '#' || data === '') return null;
    const tokens = data.split(',');
    let [value, count] = tokens[0].split(':').map(Number);
    const root = new Node(value, []), stack = [[root, count]];
    for (let i = 1; i < tokens.length; i += 1) {
      while (stack.length > 0 && stack[stack.length - 1][1] === 0) stack.pop();
      [value, count] = tokens[i].split(':').map(Number);
      const child = new Node(value, []), parent = stack[stack.length - 1];
      parent[0].children.push(child); parent[1] -= 1;
      stack.push([child, count]);
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
