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
    if (!node) out.push(null);
    else {
      out.push(node.val);
      q.push(node.left, node.right);
    }
  }
  while (out.length > 0 && out[out.length - 1] === null) out.pop();
  return out;
}

function serialize(root) {
  if (!root) return "";
  const vals = [];
  const stack = [root];
  while (stack.length > 0) {
    const node = stack.pop();
    vals.push(String(node.val));
    if (node.right) stack.push(node.right);
    if (node.left) stack.push(node.left);
  }
  return vals.join(",");
}

function deserialize(data) {
  if (!data) return null;
  const nums = data.split(",").map(Number);
  const root = new TreeNode(nums[0]);
  const stack = [root];
  for (let i = 1; i < nums.length; i++) {
    const val = nums[i];
    const node = new TreeNode(val);
    if (val < stack[stack.length - 1].val) {
      stack[stack.length - 1].left = node;
    } else {
      let parent = null;
      while (stack.length > 0 && stack[stack.length - 1].val < val) {
        parent = stack.pop();
      }
      parent.right = node;
    }
    stack.push(node);
  }
  return root;
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
