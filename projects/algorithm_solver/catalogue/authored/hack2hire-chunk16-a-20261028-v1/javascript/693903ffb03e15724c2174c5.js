"use strict";
// Hack2Hire 693903ffb03e15724c2174c5 (Level Order Task Scheduling) over an INFERRED spec; qualification unknown.

function solve(tasks, dependencies) {
  const indegree = new Map(), successors = new Map();
  for (const t of tasks) { indegree.set(t, 0); successors.set(t, []); }
  for (const [from, to] of dependencies) {
    successors.get(from).push(to);
    indegree.set(to, indegree.get(to) + 1);
  }
  const byName = (x, y) => (x < y ? -1 : x > y ? 1 : 0);
  let frontier = tasks.filter((t) => indegree.get(t) === 0).sort(byName);
  const levels = [];
  let emitted = 0;
  while (frontier.length) {
    levels.push(frontier);
    emitted += frontier.length;
    const following = [];
    for (const t of frontier) {
      for (const s of successors.get(t)) {
        const d = indegree.get(s) - 1;
        indegree.set(s, d);
        if (d === 0) following.push(s);
      }
    }
    following.sort(byName);
    frontier = following;
  }
  return emitted === tasks.length ? levels : [];
}

function scheduleByLevels(tasks, dependencies) { return solve(tasks, dependencies); }

module.exports = solve;
module.exports.scheduleByLevels = scheduleByLevels;
