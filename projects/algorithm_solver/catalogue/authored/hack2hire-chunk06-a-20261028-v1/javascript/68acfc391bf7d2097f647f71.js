"use strict";
// Hack2Hire 68acfc391bf7d2097f647f71 (Find Users with Valid Login Sessions) over an INFERRED spec; qualification unknown.

const cmp = (a, b) => (a < b ? -1 : a > b ? 1 : 0);

function solve(logs, maxTime) {
  const openSince = new Map(), valid = new Set();
  for (const line of logs) {
    const [user, action, stamp] = line.split(' '), t = Number(stamp);
    if (action === 'signin') openSince.set(user, t);
    else if (openSince.has(user)) {
      const start = openSince.get(user);
      openSince.delete(user);
      if (t - start <= maxTime) valid.add(user);
    }
  }
  return Array.from(valid).sort(cmp);
}

function findValidUsers(logs, maxTime) { return solve(logs, maxTime); }

module.exports = solve;
module.exports.findValidUsers = findValidUsers;
