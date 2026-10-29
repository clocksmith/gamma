"use strict";
// Original Hack2Hire 6a2091c38b879849ebc118ad variant over an INFERRED specification; qualification unknown.
const compareStamp = (x, y) => x[0].length - y[0].length || (x[0] < y[0] ? -1 : x[0] > y[0] ? 1 : 0);
const byKey = (a, b) => (a < b ? -1 : a > b ? 1 : 0);
function solve(logs) {
  const journeys = new Map();
  for (const [user, stamp, action] of logs) {
    if (!journeys.has(user)) journeys.set(user, []);
    journeys.get(user).push([stamp, action]);
  }
  const root = new Map();
  for (const events of journeys.values()) {
    events.sort(compareStamp);
    let node = root;
    for (const [, action] of events) {
      if (!node.has(action)) node.set(action, [0, new Map()]);
      const child = node.get(action);
      child[0]++;
      node = child[1];
    }
  }
  const lines = [], stack = [];
  const pushChildren = (node, depth) => { for (const a of [...node.keys()].sort(byKey).reverse()) stack.push([a, node.get(a), depth]); };
  pushChildren(root, 0);
  while (stack.length) {
    const [action, [count, children], depth] = stack.pop();
    lines.push("  ".repeat(depth) + action + " (" + count + ")");
    pushChildren(children, depth + 1);
  }
  return lines;
}
function userJourneyTrie(logs) { return solve(logs); }
module.exports = solve;
module.exports.userJourneyTrie = userJourneyTrie;
