"use strict";
// Hack2Hire 680984a8cbb5948f87732b46 (Nested Set Equality) over an INFERRED spec; qualification unknown.

function solve(a, b) {
  const ids = new Map();
  const idOf = (key) => {
    let v = ids.get(key);
    if (v === undefined) { v = ids.size; ids.set(key, v); }
    return v;
  };
  const canonical = (root) => {
    const nodes = [root], next = [0], accs = [[]];
    for (;;) {
      const top = nodes.length - 1, node = nodes[top], i = next[top];
      if (i < node.length) {
        next[top] = i + 1;
        const x = node[i];
        if (typeof x === "string") accs[top].push(idOf("a" + x));
        else { nodes.push(x); next.push(0); accs.push([]); }
      } else {
        const distinct = Array.from(new Set(accs[top])).sort((p, q) => p - q);
        const lid = idOf("s" + distinct.join(","));
        nodes.pop(); next.pop(); accs.pop();
        if (!nodes.length) return lid;
        accs[accs.length - 1].push(lid);
      }
    }
  };
  return canonical(a) === canonical(b);
}

function nestedSetEqual(a, b) { return solve(a, b); }

module.exports = solve;
module.exports.nestedSetEqual = nestedSetEqual;
