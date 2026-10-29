"use strict";
// Hack2Hire 6801c3b66cd5d6c88778f20c (Role Privilege System) over an INFERRED spec; qualification unknown.

function solve(roles, parents, allowed, disallowed) {
  const n = roles.length;
  const position = new Map(roles.map((role, i) => [role, i]));
  const children = Array.from({length: n}, () => []);
  const waiting = parents.map((p) => p.length);
  parents.forEach((roleParents, i) => { for (const parent of roleParents) children[position.get(parent)].push(i); });
  const final = new Array(n).fill(null);
  const queue = [];
  for (let i = 0; i < n; i++) if (waiting[i] === 0) queue.push(i);
  for (let head = 0; head < queue.length; head++) {
    const i = queue[head];
    const privileges = new Set(allowed[i]);
    for (const parent of parents[i]) for (const p of final[position.get(parent)]) privileges.add(p);
    for (const p of disallowed[i]) privileges.delete(p);
    final[i] = privileges;
    for (const child of children[i]) if (--waiting[child] === 0) queue.push(child);
  }
  return final.map((s) => [...s].sort());
}

function finalPrivileges(roles, parents, allowed, disallowed) { return solve(roles, parents, allowed, disallowed); }

module.exports = solve;
module.exports.finalPrivileges = finalPrivileges;
