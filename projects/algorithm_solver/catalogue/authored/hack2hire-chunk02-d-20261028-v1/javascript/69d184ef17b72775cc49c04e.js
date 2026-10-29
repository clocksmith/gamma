"use strict";
// Hack2Hire 69d184ef17b72775cc49c04e (File System Permissions) over an INFERRED spec; qualification unknown.

function solve(teams, queries) {
  const enter = new Map(), leave = new Map(), grants = new Map();
  let clock = 0;
  const stack = [];
  for (let i = teams.length - 1; i >= 0; i--) stack.push([teams[i], false]);
  while (stack.length) {
    const [node, done] = stack.pop();
    if (done) { leave.set(node.uuid, clock - 1); continue; }
    enter.set(node.uuid, clock++);
    for (const user of node.userIds) {
      if (!grants.has(user)) grants.set(user, []);
      grants.get(user).push(node.uuid);
    }
    stack.push([node, true]);
    for (let i = node.children.length - 1; i >= 0; i--) stack.push([node.children[i], false]);
  }
  const outer = new Map();
  for (const [user, uuids] of grants) {
    const starts = [], ends = [];
    const ordered = uuids.slice().sort((p, q) => enter.get(p) - enter.get(q));
    for (const uuid of ordered) {
      if (ends.length && enter.get(uuid) <= ends[ends.length - 1]) continue;
      starts.push(enter.get(uuid));
      ends.push(leave.get(uuid));
    }
    outer.set(user, [starts, ends]);
  }
  return queries.map(([user, uuid]) => {
    const spans = outer.get(user);
    if (spans === undefined || !enter.has(uuid)) return false;
    const position = enter.get(uuid);
    let lo = 0, hi = spans[0].length;
    while (lo < hi) { const mid = (lo + hi) >> 1; if (spans[0][mid] <= position) lo = mid + 1; else hi = mid; }
    return lo > 0 && spans[1][lo - 1] >= position;
  });
}

function checkAccess(teams, queries) { return solve(teams, queries); }

module.exports = solve;
module.exports.checkAccess = checkAccess;
