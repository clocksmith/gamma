"use strict";
// Hack2Hire 690416e84845d25b8e994885 (Find Complete Flight Path) over an INFERRED spec; qualification unknown.

function solve(tickets) {
  const adj = new Map(), balance = new Map();
  for (const [a, b] of tickets) {
    if (!adj.has(a)) adj.set(a, []);
    adj.get(a).push(b);
    balance.set(a, (balance.get(a) || 0) + 1);
    balance.set(b, (balance.get(b) || 0) - 1);
  }
  for (const list of adj.values()) { list.sort(); list.reverse(); } // pop() then yields the smallest destination
  let start = null;
  for (const [airport, d] of balance) if (d === 1) start = airport;
  if (start === null) start = [...adj.keys()].sort()[0];
  const stack = [start], route = [];
  while (stack.length) {
    const nxt = adj.get(stack[stack.length - 1]);
    if (nxt && nxt.length) stack.push(nxt.pop());
    else route.push(stack.pop());
  }
  return route.reverse();
}

function findItinerary(tickets) { return solve(tickets); }

module.exports = solve;
module.exports.findItinerary = findItinerary;
