"use strict";
// Hack2Hire 68a615443a368733bb104245 (N-ary Tree Leaf Node Removal) over an INFERRED spec; qualification unknown.

function solve(root) {
  if (root.length === 0) return [];
  const values = [root[0]], parent = [-1];
  let head = 0, i = 2;
  while (i < root.length) {
    const p = head++;
    while (i < root.length && root[i] !== null) { values.push(root[i]); parent.push(p); i++; }
    i++;
  }
  const height = new Array(values.length).fill(0);
  for (let v = values.length - 1; v > 0; v--) if (height[v] + 1 > height[parent[v]]) height[parent[v]] = height[v] + 1;
  const days = [];
  for (let d = 0; d <= height[0]; d++) days.push([]);
  for (let v = 0; v < values.length; v++) days[height[v]].push(values[v]);
  for (const day of days) day.sort((a, b) => a - b);
  return days;
}

function removeLeavesByDay(root) { return solve(root); }

module.exports = solve;
module.exports.removeLeavesByDay = removeLeavesByDay;
