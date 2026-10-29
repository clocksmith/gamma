"use strict";
// Hack2Hire 6a21945a8b879849ebc11fd4 (Filter Unsafe Messages, variant 1). Spec inferred by claude-opus-5-5 subagent 2026-10-28; qualification unknown.

function solve(messages, unsafeWords) {
  const unsafe = new Set(unsafeWords), out = [];
  for (const [username, text] of messages) {
    if (!text.split(" ").some((token) => token !== "" && unsafe.has(token))) out.push([username, text]);
  }
  return out;
}

function filterUnsafeMessages(messages, unsafeWords) { return solve(messages, unsafeWords); }
module.exports = solve;
module.exports.filterUnsafeMessages = filterUnsafeMessages;
