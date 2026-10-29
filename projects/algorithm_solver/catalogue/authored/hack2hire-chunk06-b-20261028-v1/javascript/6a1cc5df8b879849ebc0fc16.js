"use strict";
// Hack2Hire 6a1cc5df8b879849ebc0fc16 (Group Chat Mention Counter) over an INFERRED spec; qualification unknown.

function solve(members, messages) {
  const index = new Map();
  members.forEach((member, i) => index.set(member, i));
  const counts = new Array(members.length).fill(0);
  let everyone = 0;
  for (const message of messages) {
    const hit = new Set();
    let allFlag = false;
    for (const token of message.split(" ")) {
      if (token[0] !== "@") continue;
      const body = token.slice(1);
      if (body === "all") allFlag = true;
      else for (const user of body.split(",")) if (index.has(user)) hit.add(index.get(user));
    }
    if (allFlag) everyone++;
    else for (const i of hit) counts[i]++;
  }
  return counts.map((count) => count + everyone);
}

function countMentions(members, messages) { return solve(members, messages); }

module.exports = solve;
module.exports.countMentions = countMentions;
