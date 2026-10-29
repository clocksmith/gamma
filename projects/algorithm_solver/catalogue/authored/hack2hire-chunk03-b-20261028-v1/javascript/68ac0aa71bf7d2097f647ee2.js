"use strict";
// Hack2Hire 68ac0aa71bf7d2097f647ee2 (Most Frequent Call Chain) over an INFERRED spec; qualification unknown.

function solve(traces) {
  const child = new Map();
  const parent = [-1], name = [''], count = [0];  // node 0 is the empty chain; node ids follow first-record order
  const stack = [0];
  for (const trace of traces) {
    if (trace.startsWith('->')) {
      const top = stack[stack.length - 1], fn = trace.slice(3), key = top + ' ' + fn;
      let node = child.get(key);
      if (node === undefined) {
        node = parent.length; child.set(key, node);
        parent.push(top); name.push(fn); count.push(0);
      }
      count[node]++;
      stack.push(node);
    } else {
      stack.pop();
    }
  }
  let best = 0;
  for (let node = 1; node < count.length; node++) if (count[node] > count[best]) best = node;
  const chain = [];
  while (best > 0) { chain.push(name[best]); best = parent[best]; }
  return chain.reverse();
}

function mostFrequentCallChain(traces) { return solve(traces); }

module.exports = solve;
module.exports.mostFrequentCallChain = mostFrequentCallChain;
