"use strict";
// Hack2Hire 68e8736a80f69c7a01706891 (Print Folder Path Given Node ID) over an INFERRED spec; qualification unknown.

function solve(idList, children, nameList, targetId) {
  const name = new Map();
  for (let i = 0; i < idList.length; i++) name.set(idList[i], nameList[i]);
  if (!name.has(targetId)) return "";
  const parent = new Map();
  for (let i = 0; i < idList.length; i++) for (const k of children[i]) parent.set(k, idList[i]);
  const path = [];
  let node = targetId;
  for (;;) {
    path.push(name.get(node));
    if (!parent.has(node)) break;
    node = parent.get(node);
  }
  path.reverse();
  return path.join("/");
}

function getFolderPath(idList, children, nameList, targetId) { return solve(idList, children, nameList, targetId); }

module.exports = solve;
module.exports.getFolderPath = getFolderPath;
