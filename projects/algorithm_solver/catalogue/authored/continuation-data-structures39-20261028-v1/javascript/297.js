"use strict";

function TreeNode(val, left, right) {
  this.val = val === undefined ? 0 : val;
  this.left = left === undefined ? null : left;
  this.right = right === undefined ? null : right;
}

function fromLevelList(arr) {
  if (!arr || arr.length === 0 || arr[0] === null) return null;
  const root = new TreeNode(arr[0]);
  const q = [root];
  let head = 0, i = 1;
  while (head < q.length && i < arr.length) {
    const node = q[head++];
    if (i < arr.length) {
      const v = arr[i++];
      if (v !== null && v !== undefined) {
        node.left = new TreeNode(v);
        q.push(node.left);
      }
    }
    if (i < arr.length) {
      const v = arr[i++];
      if (v !== null && v !== undefined) {
        node.right = new TreeNode(v);
        q.push(node.right);
      }
    }
  }
  return root;
}

function toLevelList(root) {
  if (!root) return [];
  const out = [];
  const q = [root];
  let head = 0;
  while (head < q.length) {
    const node = q[head++];
    if (!node) {
      out.push(null);
    } else {
      out.push(node.val);
      q.push(node.left, node.right);
    }
  }
  while (out.length > 0 && out[out.length - 1] === null) out.pop();
  return out;
}

function serialize(root) {
  if (!root) return "";
  const tokens = [];
  const q = [root];
  let head = 0;
  while (head < q.length) {
    const node = q[head++];
    if (!node) {
      tokens.push("#");
    } else {
      tokens.push(String(node.val));
      q.push(node.left, node.right);
    }
  }
  while (tokens.length > 0 && tokens[tokens.length - 1] === "#") tokens.pop();
  return tokens.join(",");
}

function deserialize(data) {
  if (!data) return null;
  const parts = data.split(",").map((tok) => (tok === "#" ? null : Number(tok)));
  return fromLevelList(parts);
}

class Codec {
  serialize(root) { return serialize(root); }
  deserialize(data) { return deserialize(data); }
}

function solve(root) {
  const codec = new Codec();
  if (Array.isArray(root)) {
    const tree = fromLevelList(root);
    const rebuilt = codec.deserialize(codec.serialize(tree));
    return toLevelList(rebuilt);
  }
  return codec.deserialize(codec.serialize(root));
}

module.exports = solve;
module.exports.solve = solve;
module.exports.Codec = Codec;
module.exports.serialize = serialize;
module.exports.deserialize = deserialize;
module.exports.TreeNode = TreeNode;
