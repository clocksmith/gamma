"use strict";
// Hack2Hire 6945c50a2c048134ada834f9 (Chat Message Range Merge, variant 1) over an INFERRED spec; qualification unknown.
function solve(messages, queries) {
  const position = new Map(messages.map((m, i) => [m[0], i])), last = messages.length - 1;
  const intervals = queries.map(([target, before, after]) => {
    const p = position.get(target);
    return [Math.max(0, p - before), Math.min(last, p + after)];
  }).sort((a, b) => a[0] - b[0] || a[1] - b[1]);
  const merged = [];
  for (const [start, end] of intervals) {
    const top = merged[merged.length - 1];
    if (top && start <= top[1] + 1) { if (end > top[1]) top[1] = end; }
    else merged.push([start, end]);
  }
  return merged.map(([start, end]) => [messages[start][0], messages[end][0]]);
}
function mergeChatRanges(messages, queries) { return solve(messages, queries); }
module.exports = solve;
module.exports.mergeChatRanges = mergeChatRanges;
