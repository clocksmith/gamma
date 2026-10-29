"use strict";
// Hack2Hire 6934db665f306485cc5f08ba (Find Duplicate Files, variant 1). Spec inferred by claude-opus-5-5 subagent 2026-10-28; qualification unknown.

const byCodeUnit = (a, b) => (a < b ? -1 : a > b ? 1 : 0);

function solve(root) {
  const files = [], stack = [[root, ""]];
  while (stack.length) {
    const [node, prefix] = stack.pop();
    for (const f of node.files) files.push([prefix + "/" + f.name, f.content]);
    for (const d of node.directories) stack.push([d, prefix + "/" + d.name]);
  }
  const bySize = new Map();
  for (const entry of files) {
    if (!bySize.has(entry[1].length)) bySize.set(entry[1].length, []);
    bySize.get(entry[1].length).push(entry);
  }
  const groups = [];
  for (const bucket of bySize.values()) {
    if (bucket.length < 2) continue;
    const byContent = new Map();
    for (const [path, content] of bucket) {
      const key = content.join(",");
      if (!byContent.has(key)) byContent.set(key, []);
      byContent.get(key).push(path);
    }
    for (const group of byContent.values()) if (group.length > 1) groups.push(group.sort(byCodeUnit));
  }
  return groups.sort((a, b) => byCodeUnit(a[0], b[0]));
}

function findDuplicateFiles(root) { return solve(root); }
module.exports = solve;
module.exports.findDuplicateFiles = findDuplicateFiles;
