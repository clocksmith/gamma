"use strict";
// Hack2Hire 67ce7ab08f73eb6319edd207 (Custom String Sorting) over an INFERRED spec; qualification unknown.

function solve(customOrder, words) {
  // rank characters: the i-th letter of customOrder becomes code 97 + i, so plain string order is the custom order
  const rank = new Map();
  for (let i = 0; i < customOrder.length; i++) rank.set(customOrder[i], String.fromCharCode(97 + i));
  const keys = words.map((w) => { let k = ""; for (const c of w) k += rank.get(c); return k; });
  const order = words.map((_, i) => i);
  order.sort((a, b) => (keys[a] < keys[b] ? -1 : keys[a] > keys[b] ? 1 : 0));
  return order.map((i) => words[i]);
}

function customSort(customOrder, words) { return solve(customOrder, words); }

module.exports = solve;
module.exports.customSort = customSort;
