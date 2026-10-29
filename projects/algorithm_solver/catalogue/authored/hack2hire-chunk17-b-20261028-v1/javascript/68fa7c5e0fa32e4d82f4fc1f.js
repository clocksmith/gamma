"use strict";
// Hack2Hire 68fa7c5e0fa32e4d82f4fc1f (URL Router Design) over an INFERRED spec; qualification unknown.

function segmentsOf(path) {
  return path === "/" ? [] : path.slice(1).split("/");
}

class Router {
  constructor() {
    // trie node: {children by segment, handler or null}
    this.root = { children: new Map(), handler: null };
  }

  addRoute(pattern, handler) {
    let node = this.root;
    for (const segment of segmentsOf(pattern)) {
      let child = node.children.get(segment);
      if (child === undefined) {
        child = { children: new Map(), handler: null };
        node.children.set(segment, child);
      }
      node = child;
    }
    node.handler = handler;
  }

  callRoute(path) {
    const segments = segmentsOf(path);
    const size = segments.length;
    let bestCount = size + 1;
    let best = "";
    // depth-first, literal child before '*', so the first match at a given wildcard count is the left-to-right most specific
    // parallel stacks of (node, depth, wildcard count)
    const nodes = [this.root];
    const depths = [0];
    const wilds = [0];
    while (nodes.length) {
      const node = nodes.pop();
      const depth = depths.pop();
      const wild = wilds.pop();
      if (wild >= bestCount) continue;
      if (depth === size) {
        if (node.handler !== null) { bestCount = wild; best = node.handler; }
        continue;
      }
      const star = node.children.get("*");
      if (star !== undefined) { nodes.push(star); depths.push(depth + 1); wilds.push(wild + 1); }
      const literal = node.children.get(segments[depth]);
      if (literal !== undefined && segments[depth] !== "*") { nodes.push(literal); depths.push(depth + 1); wilds.push(wild); }
    }
    return best;
  }
}

function solve(operationNames, argumentLists) {
  if (operationNames[0] !== "Router" || argumentLists[0].length !== 0) throw new Error("exact initial constructor required");
  const instance = new Router(...argumentLists[0]);
  const allowed = new Set(["addRoute", "callRoute"]);
  const result = [null];
  for (let i = 1; i < operationNames.length; i++) {
    if (!allowed.has(operationNames[i])) throw new Error("unknown method");
    const value = instance[operationNames[i]](...argumentLists[i]);
    result.push(value === undefined ? null : value);
  }
  return result;
}

module.exports = solve;
module.exports.Router = Router;
