"use strict";
// Hack2Hire 67a26ae89056d103b4aafc72 (Get Total Requests) over an INFERRED spec; qualification unknown.

function solve(server, replaced, newId) {
  const count = new Map();
  let total = 0;
  for (const s of server) {
    count.set(s, (count.get(s) || 0) + 1);
    total += s;
  }
  const result = [];
  for (let j = 0; j < replaced.length; j++) {
    const old = replaced[j], nid = newId[j];
    const c = count.get(old) || 0;
    if (c && old !== nid) {
      count.delete(old);
      count.set(nid, (count.get(nid) || 0) + c);
      total += c * (nid - old);
    }
    result.push(total);
  }
  return result;
}

function getTotalRequests(server, replaced, newId) { return solve(server, replaced, newId); }

module.exports = solve;
module.exports.getTotalRequests = getTotalRequests;
