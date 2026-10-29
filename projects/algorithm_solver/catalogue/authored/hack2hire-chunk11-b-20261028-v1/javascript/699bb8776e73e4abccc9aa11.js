"use strict";
// Hack2Hire 699bb8776e73e4abccc9aa11 (Generate Unique Usernames) over an INFERRED spec; qualification unknown.

function solve(names) {
  const issued = new Set();
  const nextSuffix = new Map(); // base -> first suffix not yet tried for it
  const out = [];
  for (const name of names) {
    const words = name.split(" ");
    const base = (words[0][0] + words[words.length - 1]).toLowerCase().slice(0, 8);
    let user = base;
    if (issued.has(base)) {
      let k = nextSuffix.has(base) ? nextSuffix.get(base) : 1;
      for (;;) {
        const digits = String(k);
        user = base.slice(0, 8 - digits.length) + digits;
        if (!issued.has(user)) break;
        k++;
      }
      nextSuffix.set(base, k + 1);
    }
    issued.add(user);
    out.push(user);
  }
  return out;
}

function generateUsernames(names) { return solve(names); }

module.exports = solve;
module.exports.generateUsernames = generateUsernames;
