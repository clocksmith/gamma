"use strict";
// Hack2Hire 6962cbcef731aa3969ef5176 (File System Deletion) over an INFERRED spec; qualification unknown.

function solve(dirs, edges, files, path) {
  const directories = new Set(dirs);
  if (!directories.has(path) && !files.includes(path)) return [];
  const children = new Map();
  for (const [p, c] of edges) { let list = children.get(p); if (!list) children.set(p, list = []); list.push(c); }
  const deleted = [], nodes = [path], next = [0], empty = [];
  while (nodes.length) {
    const top = nodes.length - 1, node = nodes[top];
    const kids = directories.has(node) ? children.get(node) || empty : empty;
    if (next[top] < kids.length) { nodes.push(kids[next[top]++]); next.push(0); }
    else { nodes.pop(); next.pop(); deleted.push(node); }
  }
  return deleted;
}

function deletePath(dirs, edges, files, path) { return solve(dirs, edges, files, path); }

module.exports = solve;
module.exports.deletePath = deletePath;
