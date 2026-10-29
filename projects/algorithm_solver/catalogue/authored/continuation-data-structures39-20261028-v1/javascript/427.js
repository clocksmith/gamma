"use strict";

function Node(val, isLeaf, topLeft, topRight, bottomLeft, bottomRight) {
  this.val = Boolean(val);
  this.isLeaf = Boolean(isLeaf);
  this.topLeft = topLeft === undefined ? null : topLeft;
  this.topRight = topRight === undefined ? null : topRight;
  this.bottomLeft = bottomLeft === undefined ? null : bottomLeft;
  this.bottomRight = bottomRight === undefined ? null : bottomRight;
}

function serializeQuad(root) {
  const out = [];
  const q = [root];
  let head = 0;
  while (head < q.length) {
    const node = q[head++];
    if (!node) {
      out.push(null);
    } else {
      out.push([node.isLeaf ? 1 : 0, node.val ? 1 : 0]);
      q.push(node.topLeft, node.topRight, node.bottomLeft, node.bottomRight);
    }
  }
  while (out.length > 0 && out[out.length - 1] === null) out.pop();
  return out;
}

function buildQuad(pref, r0, c0, size) {
  const r1 = r0 + size;
  const c1 = c0 + size;
  const total = pref[r1][c1] - pref[r0][c1] - pref[r1][c0] + pref[r0][c0];
  if (total === 0) return new Node(false, true, null, null, null, null);
  if (total === size * size) return new Node(true, true, null, null, null, null);
  const half = size >> 1;
  return new Node(
    true,
    false,
    buildQuad(pref, r0, c0, half),
    buildQuad(pref, r0, c0 + half, half),
    buildQuad(pref, r0 + half, c0, half),
    buildQuad(pref, r0 + half, c0 + half, half)
  );
}

function solve(grid) {
  const n = grid.length;
  const pref = Array.from({ length: n + 1 }, () => new Array(n + 1).fill(0));
  for (let r = 0; r < n; r++) {
    let rowSum = 0;
    for (let c = 0; c < n; c++) {
      rowSum += grid[r][c];
      pref[r + 1][c + 1] = pref[r][c + 1] + rowSum;
    }
  }
  const root = buildQuad(pref, 0, 0, n);
  return serializeQuad(root);
}

function construct(grid) {
  return solve(grid);
}

module.exports = solve;
module.exports.solve = solve;
module.exports.construct = construct;
module.exports.Node = Node;
