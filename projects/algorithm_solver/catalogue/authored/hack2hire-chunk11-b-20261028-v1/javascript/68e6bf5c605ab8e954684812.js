"use strict";
// Hack2Hire 68e6bf5c605ab8e954684812 (Friendship and Balance Tracker) over an INFERRED spec; qualification unknown.

function pairKey(a, b) { return a < b ? a + "/" + b : b + "/" + a; }

function solve(requests) {
  const balance = new Map();   // user -> balance
  const pending = new Map();   // sequence number of a friend request -> [from, to]
  const friends = new Set();   // ordered user pairs
  const out = [];
  for (const [seq, request] of requests) {
    const parts = request.split("/");
    const kind = parts[1];
    if (kind === "REGISTER") {
      if (balance.has(parts[2])) out.push("ERROR");
      else { balance.set(parts[2], Number(parts[3])); out.push("OK"); }
    } else if (kind === "FRIEND_REQUEST") {
      const a = parts[2], b = parts[3];
      if (!balance.has(a) || !balance.has(b) || a === b || friends.has(pairKey(a, b))) out.push("ERROR");
      else { pending.set(seq, [a, b]); out.push("OK"); }
    } else if (kind === "ACCEPT_FRIEND_REQUEST") {
      const requestPair = pending.get(parts[2]);
      if (requestPair === undefined) out.push("ERROR");
      else { pending.delete(parts[2]); friends.add(pairKey(requestPair[0], requestPair[1])); out.push("OK"); }
    } else if (kind === "TRANSFER") {
      const a = parts[2], b = parts[3], amount = Number(parts[4]);
      if (balance.has(a) && balance.has(b) && a !== b && friends.has(pairKey(a, b)) && balance.get(a) >= amount) {
        balance.set(a, balance.get(a) - amount);
        balance.set(b, balance.get(b) + amount);
        out.push("OK");
      } else out.push("ERROR");
    } else {
      out.push(balance.has(parts[2]) ? String(balance.get(parts[2])) : "ERROR");
    }
  }
  return out;
}

function processRequests(requests) { return solve(requests); }

module.exports = solve;
module.exports.processRequests = processRequests;
