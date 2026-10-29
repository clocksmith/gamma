"use strict";
// Hack2Hire 6862f418eb0810914237ab13 (API Path Matching) over an INFERRED spec; qualification unknown.

class APIMatchingSystem {
  constructor() { this.root = {handler: null, children: new Map()}; }

  registerPath(path, handler) {
    let node = this.root;
    if (path !== "/") {
      for (const seg of path.slice(1).split("/")) {
        let child = node.children.get(seg);
        if (child === undefined) { child = {handler: null, children: new Map()}; node.children.set(seg, child); }
        node = child;
      }
    }
    node.handler = handler;
  }

  matchPath(path) {
    let node = this.root;
    let best = node.handler;
    if (path !== "/") {
      for (const seg of path.slice(1).split("/")) {
        node = node.children.get(seg);
        if (node === undefined) break;
        if (node.handler !== null) best = node.handler;
      }
    }
    return best === null ? "" : best;
  }
}

function solve(operationNames, argumentLists) {
  if (operationNames[0] !== "APIMatchingSystem" || argumentLists[0].length !== 0) throw new Error("exact initial constructor required");
  const instance = new APIMatchingSystem(...argumentLists[0]);
  const allowed = new Set(["registerPath", "matchPath"]);
  const result = [null];
  for (let i = 1; i < operationNames.length; i++) {
    if (!allowed.has(operationNames[i])) throw new Error("unknown method");
    const value = instance[operationNames[i]](...argumentLists[i]);
    result.push(value === undefined ? null : value);
  }
  return result;
}

module.exports = solve;
module.exports.APIMatchingSystem = APIMatchingSystem;
