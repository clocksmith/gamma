'use strict';
// 297. Serialize and Deserialize Binary Tree.
class TreeNode {
  constructor(val = 0, left = null, right = null) { this.val = val; this.left = left; this.right = right; }
}
class Codec {
  serialize(root) {
    const values = []; const queue = [root];
    for (let head = 0; head < queue.length; head += 1) {
      const node = queue[head];
      if (node === null) values.push('#');
      else { values.push(String(node.val)); queue.push(node.left, node.right); }
    }
    while (values.length && values[values.length - 1] === '#') values.pop();
    return values.join(',');
  }
  deserialize(data) {
    if (!data) return null;
    const values = data.split(',');
    const root = new TreeNode(Number(values[0])); const queue = [root]; let index = 1;
    for (let head = 0; head < queue.length && index < values.length; head += 1) {
      const node = queue[head];
      if (values[index] !== '#') { node.left = new TreeNode(Number(values[index])); queue.push(node.left); }
      index += 1;
      if (index < values.length && values[index] !== '#') { node.right = new TreeNode(Number(values[index])); queue.push(node.right); }
      index += 1;
    }
    return root;
  }
}
function solve(root) { const codec = new Codec(); return codec.deserialize(codec.serialize(root)); }
if (typeof module !== 'undefined') module.exports = { solve, Codec, TreeNode };
