"use strict";

function Node(val, isLeaf, topLeft, topRight, bottomLeft, bottomRight) {
  this.val = Boolean(val);
  this.isLeaf = Boolean(isLeaf);
  this.topLeft = topLeft === undefined ? null : topLeft;
  this.topRight = topRight === undefined ? null : topRight;
  this.bottomLeft = bottomLeft === undefined ? null : bottomLeft;
  this.bottomRight = bottomRight === undefined ? null : bottomRight;
}

function fromQuadList(data) {
  const root = new Node(Boolean(data[0][1]), Boolean(data[0][0]));
  const q = [root];
  let head = 0, i = 1;
  const attrs = ["topLeft", "topRight", "bottomLeft", "bottomRight"];
  while (head < q.length && i < data.length) {
    const curr = q[head++];
    for (let k = 0; k < 4; k++) {
      if (i < data.length) {
        const item = data[i++];
        if (item !== null && item !== undefined) {
          const child = new Node(Boolean(item[1]), Boolean(item[0]));
          curr[attrs[k]] = child;
          q.push(child);
        }
      }
    }
  }
  return root;
}

function toQuadList(root) {
  const out = [];
  const q = [root];
  let head = 0;
  while (head < q.length) {
    const node = q[head++];
    if (!node) out.push(null);
    else {
      out.push([node.isLeaf ? 1 : 0, node.val ? 1 : 0]);
      q.push(node.topLeft, node.topRight, node.bottomLeft, node.bottomRight);
    }
  }
  while (out.length > 0 && out[out.length - 1] === null) out.pop();
  return out;
}

function intersectNodes(q1, q2) {
  if (q1.isLeaf) return q1.val ? new Node(true, true) : q2;
  if (q2.isLeaf) return q2.val ? new Node(true, true) : q1;
  const tl = intersectNodes(q1.topLeft, q2.topLeft);
  const tr = intersectNodes(q1.topRight, q2.topRight);
  const bl = intersectNodes(q1.bottomLeft, q2.bottomLeft);
  const br = intersectNodes(q1.bottomRight, q2.bottomRight);
  if (tl.isLeaf && tr.isLeaf && bl.isLeaf && br.isLeaf && tl.val === tr.val && tr.val === bl.val && bl.val === br.val) {
    return new Node(tl.val, true);
  }
  return new Node(true, false, tl, tr, bl, br);
}

function solve(quadTree1, quadTree2) {
  if (Array.isArray(quadTree1)) {
    const n1 = fromQuadList(quadTree1);
    const n2 = fromQuadList(quadTree2);
    return toQuadList(intersectNodes(n1, n2));
  }
  return intersectNodes(quadTree1, quadTree2);
}

function intersect(quadTree1, quadTree2) {
  return solve(quadTree1, quadTree2);
}

module.exports = solve;
module.exports.solve = solve;
module.exports.intersect = intersect;
module.exports.Node = Node;
