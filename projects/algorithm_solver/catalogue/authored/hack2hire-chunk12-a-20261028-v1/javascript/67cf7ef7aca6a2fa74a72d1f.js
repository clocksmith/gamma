"use strict";
// Hack2Hire 67cf7ef7aca6a2fa74a72d1f (Load Factor Calculation) over an INFERRED spec; qualification unknown.

function solve(dependencies, entry) {
  const index = new Map(), names = [], out = [], indeg = [];
  const node = (name) => {
    if (!index.has(name)) { index.set(name, names.length); names.push(name); out.push([]); indeg.push(0); }
    return index.get(name);
  };
  node(entry);
  for (const [caller, callee] of dependencies) { const a = node(caller), b = node(callee); out[a].push(b); indeg[b]++; }
  const load = new Array(names.length).fill(0);
  load[index.get(entry)] = 1;
  const queue = [];
  for (let v = 0; v < names.length; v++) if (indeg[v] === 0) queue.push(v);
  for (let head = 0; head < queue.length; head++) {
    const v = queue[head];
    for (const w of out[v]) { load[w] += load[v]; if (--indeg[w] === 0) queue.push(w); }
  }
  return names.slice().sort().map((name) => [name, load[index.get(name)]]);
}

function loadFactors(dependencies, entry) { return solve(dependencies, entry); }

module.exports = solve;
module.exports.loadFactors = loadFactors;
