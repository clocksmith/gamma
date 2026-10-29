"use strict";
// Hack2Hire 6ad143c77cb0eaedae659281 (Format a Task Hierarchy, level 3) over an INFERRED spec; qualification unknown.

const LEVEL = 3;

function solve(records) {
  const arity = new Map([["task", 4], ["subtask", 5]]);
  if (LEVEL === 4) arity.set("complete", 3);
  const parentOf = new Map(), nameOf = new Map(), order = [], marked = new Set();
  for (const record of records) {
    const fields = record.split(",");
    if (fields.length < 2 || arity.get(fields[1]) !== fields.length) continue;
    if (fields[1] === "complete") { if (fields[2]) marked.add(fields[2]); continue; }
    let parent, taskId, name;
    if (fields[1] === "task") { parent = null; taskId = fields[2]; name = fields[3]; }
    else { parent = fields[2]; taskId = fields[3]; name = fields[4]; }
    if (!taskId || !name || parent === "" || nameOf.has(taskId)) continue;
    parentOf.set(taskId, parent); nameOf.set(taskId, name); order.push(taskId);
  }
  const children = new Map(), roots = [];
  for (const taskId of order) {
    const parent = parentOf.get(taskId);
    if (parent === null) roots.push(taskId);
    else { if (!children.has(parent)) children.set(parent, []); children.get(parent).push(taskId); }
  }
  const visit = [], stack = [];
  for (let i = roots.length - 1; i >= 0; i--) stack.push([roots[i], 0, String(i + 1)]);
  while (stack.length) {
    const item = stack.pop();
    visit.push(item);
    const kids = children.get(item[0]) || [];
    for (let j = kids.length - 1; j >= 0; j--) stack.push([kids[j], item[1] + 1, item[2] + "." + (j + 1)]);
  }
  const done = new Map();
  if (LEVEL === 4) {
    for (let i = visit.length - 1; i >= 0; i--) {
      const taskId = visit[i][0], kids = children.get(taskId) || [];
      done.set(taskId, marked.has(taskId) || (kids.length > 0 && kids.every((k) => done.get(k))));
    }
  }
  const lines = [];
  for (const [taskId, depth, number] of visit) {
    let label = nameOf.get(taskId);
    if (LEVEL === 4) label = (done.get(taskId) ? "[x] " : "[ ] ") + label;
    if (LEVEL >= 3) label = number + " " + label;
    lines.push("  ".repeat(depth) + label);
  }
  return lines;
}

function formatTasks(records) { return solve(records); }

module.exports = solve;
module.exports.formatTasks = formatTasks;
