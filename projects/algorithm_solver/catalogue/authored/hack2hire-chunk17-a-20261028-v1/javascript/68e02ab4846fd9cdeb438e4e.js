"use strict";
// Hack2Hire 68e02ab4846fd9cdeb438e4e (URL Query Parameter Parsing) over an INFERRED spec; qualification unknown.

function solve(url) {
  const mark = url.indexOf("?");
  const values = new Map();
  if (mark >= 0) {
    for (const piece of url.slice(mark + 1).split("&")) {
      if (!piece) continue;
      const eq = piece.indexOf("=");
      const key = eq < 0 ? piece : piece.slice(0, eq);
      const value = eq < 0 ? "" : piece.slice(eq + 1);
      if (!key) continue;
      const current = values.get(key);
      if (current === undefined) values.set(key, value);
      else if (Array.isArray(current)) current.push(value);
      else values.set(key, [current, value]);
    }
  }
  return Object.fromEntries(values);
}

function parseQuery(url) { return solve(url); }

module.exports = solve;
module.exports.parseQuery = parseQuery;
