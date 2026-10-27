'use strict';

// 558. Logical OR of Two Binary Grids Represented as Quad-Trees. Build an independent compressed result; neither input tree is modified or aliased.

class Node {
  constructor(val = false, isLeaf = false, topLeft = null, topRight = null,
              bottomLeft = null, bottomRight = null) {
    this.val = val;
    this.isLeaf = isLeaf;
    this.topLeft = topLeft;
    this.topRight = topRight;
    this.bottomLeft = bottomLeft;
    this.bottomRight = bottomRight;
  }
}

function solve(quadTree1, quadTree2) {
  function copy(node) {
    if (node.isLeaf) return new Node(Boolean(node.val), true);
    return new Node(false, false, copy(node.topLeft), copy(node.topRight), copy(node.bottomLeft), copy(node.bottomRight));
  }
  function merge(a, b) {
    if (a.isLeaf) return a.val ? new Node(true, true) : copy(b);
    if (b.isLeaf) return b.val ? new Node(true, true) : copy(a);
    const children = [merge(a.topLeft, b.topLeft), merge(a.topRight, b.topRight), merge(a.bottomLeft, b.bottomLeft), merge(a.bottomRight, b.bottomRight)];
    if (children.every(child => child.isLeaf && child.val === children[0].val)) return new Node(children[0].val, true);
    return new Node(false, false, ...children);
  }
  return merge(quadTree1, quadTree2);
}

const intersect = solve;
class Solution {
  intersect(quadTree1, quadTree2) { return solve(quadTree1, quadTree2); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, intersect };
