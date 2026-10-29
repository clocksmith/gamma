"use strict";
// Hack2Hire 68c4484970268e95f5f43d5e (Minimum Vertices to Traverse Directed Graph) over an INFERRED spec; qualification unknown.

function solve(n, edges) {
  const adj = [];
  for (let i = 0; i < n; i++) adj.push([]);
  for (const [u, v] of edges) adj[u].push(v);
  const index = new Array(n).fill(-1);
  const low = new Array(n).fill(0);
  const pointer = new Array(n).fill(0);
  const onStack = new Array(n).fill(false);
  const comp = new Array(n).fill(-1);
  const stack = [];
  let counter = 0, components = 0;
  for (let s = 0; s < n; s++) {
    if (index[s] !== -1) continue;
    index[s] = low[s] = counter++;
    stack.push(s);
    onStack[s] = true;
    const work = [s];
    while (work.length > 0) {
      const v = work[work.length - 1];
      if (pointer[v] < adj[v].length) {
        const w = adj[v][pointer[v]++];
        if (index[w] === -1) {
          index[w] = low[w] = counter++;
          stack.push(w);
          onStack[w] = true;
          work.push(w);
        } else if (onStack[w] && index[w] < low[v]) low[v] = index[w];
        continue;
      }
      work.pop();
      if (work.length > 0 && low[v] < low[work[work.length - 1]]) low[work[work.length - 1]] = low[v];
      if (low[v] === index[v]) {
        for (;;) {
          const w = stack.pop();
          onStack[w] = false;
          comp[w] = components;
          if (w === v) break;
        }
        components++;
      }
    }
  }
  const entered = new Array(components).fill(false);
  for (const [u, v] of edges) if (comp[u] !== comp[v]) entered[comp[v]] = true;
  let answer = 0;
  for (const e of entered) if (!e) answer++;
  return answer;
}

function minActivatedServers(n, edges) { return solve(n, edges); }

module.exports = solve;
module.exports.minActivatedServers = minActivatedServers;
