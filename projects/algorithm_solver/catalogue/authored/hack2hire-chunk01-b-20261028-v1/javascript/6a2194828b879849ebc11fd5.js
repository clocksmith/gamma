"use strict";
// Hack2Hire 6a2194828b879849ebc11fd5 (Filter Unsafe Messages, variant 2). Spec inferred by claude-opus-5-5 subagent 2026-10-28; qualification unknown.

function solve(messages, unsafeWords) {
  const root = { next: new Map(), end: false };
  for (const word of unsafeWords) {
    let node = root;
    for (const ch of word) {
      if (!node.next.has(ch)) node.next.set(ch, { next: new Map(), end: false });
      node = node.next.get(ch);
    }
    node.end = true;
  }
  const unsafe = (text) => {
    for (let start = 0; start < text.length; start++) {
      let node = root;
      for (let i = start; i < text.length; i++) {
        node = node.next.get(text[i]);
        if (node === undefined) break;
        if (node.end) return true;
      }
    }
    return false;
  };
  const out = [];
  for (const [username, text] of messages) if (!unsafe(text)) out.push([username, text]);
  return out;
}

function filterUnsafeMessages(messages, unsafeWords) { return solve(messages, unsafeWords); }
module.exports = solve;
module.exports.filterUnsafeMessages = filterUnsafeMessages;
