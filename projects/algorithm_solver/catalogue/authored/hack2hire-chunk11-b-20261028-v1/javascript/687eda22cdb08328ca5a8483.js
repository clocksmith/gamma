"use strict";
// Hack2Hire 687eda22cdb08328ca5a8483 (IP Routing Lookup) over an INFERRED spec; qualification unknown.

function address(text) {
  const [a, b, c, d] = text.split(".").map(Number);
  return ((a * 256 + b) * 256 + c) * 256 + d; // exact: below 2**32
}

function solve(routes, queries) {
  const tables = new Map(); // prefix length -> Map(masked network -> next hop); later routes overwrite
  for (const [prefix, hop] of routes) {
    const [base, lengthText] = prefix.split("/");
    const length = Number(lengthText);
    if (!tables.has(length)) tables.set(length, new Map());
    tables.get(length).set(Math.floor(address(base) / 2 ** (32 - length)), hop);
  }
  const lengths = [...tables.keys()].sort((p, q) => q - p);
  const out = [];
  for (const query of queries) {
    const ip = address(query);
    let answer = "";
    for (const length of lengths) {
      const hop = tables.get(length).get(Math.floor(ip / 2 ** (32 - length)));
      if (hop !== undefined) { answer = hop; break; }
    }
    out.push(answer);
  }
  return out;
}

function routeLookup(routes, queries) { return solve(routes, queries); }

module.exports = solve;
module.exports.routeLookup = routeLookup;
