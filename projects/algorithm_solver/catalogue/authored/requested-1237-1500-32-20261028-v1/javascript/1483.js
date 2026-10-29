"use strict";

class TreeAncestor {
  constructor(n, parent) {
    const maxLog = 16;
    const up = [Int32Array.from(parent)];
    for (let j = 1; j < maxLog; j++) {
      const prev = up[j - 1];
      const nxt = new Int32Array(n);
      for (let i = 0; i < n; i++) {
        const p = prev[i];
        nxt[i] = p === -1 ? -1 : prev[p];
      }
      up.push(nxt);
    }
    this.up = up;
  }
  getKthAncestor(node, k) {
    let curr = node, bit = 0;
    while (k > 0 && curr !== -1) {
      if (k & 1) curr = this.up[bit][curr];
      k >>= 1;
      bit++;
    }
    return curr;
  }
}

function solve(operation_names, argument_lists) {
  const [n, parent] = argument_lists[0];
  const inst = new TreeAncestor(n, parent);
  const out = [null];
  for (let i = 1; i < operation_names.length; i++) {
    out.push(inst.getKthAncestor(argument_lists[i][0], argument_lists[i][1]));
  }
  return out;
}

module.exports = solve;
module.exports.solve = solve;
module.exports.TreeAncestor = TreeAncestor;
