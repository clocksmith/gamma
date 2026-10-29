"use strict";
// Hack2Hire 6a0b74fac84b6e8a3be18c83 (Find IPv4 Addresses in Nested Files) over an INFERRED spec; qualification unknown.

function isRunChar(c) { return c === "." || (c >= "0" && c <= "9"); }

function valid(run) {
  const parts = run.split(".");
  if (parts.length !== 4) return false;
  for (const part of parts) {
    if (!part.length || part.length > 3 || (part.length > 1 && part[0] === "0") || Number(part) > 255) return false;
  }
  return true;
}

function solve(root) {
  const found = new Set();
  const stack = [root];
  while (stack.length) {
    const node = stack.pop();
    for (const line of node.lines) {
      let i = 0;
      while (i < line.length) {
        if (!isRunChar(line[i])) { i++; continue; }
        let j = i;
        while (j < line.length && isRunChar(line[j])) j++;
        const run = line.slice(i, j);
        if (valid(run)) found.add(run);
        i = j;
      }
    }
    for (const child of node.children) stack.push(child);
  }
  return [...found].sort();
}

function findIpAddresses(root) { return solve(root); }

module.exports = solve;
module.exports.findIpAddresses = findIpAddresses;
