"use strict";
// Hack2Hire 695ec22e9c1c1f40daea759e (Poker Hand Game Checker, level 2) over an INFERRED spec; qualification unknown.

const VALUE = new Map(['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A'].map((r, i) => [r, i + 2]));

function strength(hand) {
  const values = [], suits = new Set();
  for (const card of hand) {
    const [rank, suit] = card.split(' of ');
    values.push(VALUE.get(rank)); suits.add(suit);
  }
  const counts = new Map();
  for (const v of values) counts.set(v, (counts.get(v) || 0) + 1);
  const groups = [...counts.entries()].sort((a, b) => (b[1] - a[1]) || (b[0] - a[0]));
  const shape = groups.map((g) => g[1]).join(','), order = groups.map((g) => g[0]);
  const flush = suits.size === 1;
  let high = 0;
  if (groups.length === 5) {
    if (order[0] - order[4] === 4) high = order[0];
    else if (order.join(',') === '14,5,4,3,2') high = 5;
  }
  let category;
  if (high && flush) category = 8;
  else if (shape === '4,1') category = 7;
  else if (shape === '3,2') category = 6;
  else if (flush) category = 5;
  else if (high) category = 4;
  else if (shape === '3,1,1') category = 3;
  else if (shape === '2,2,1') category = 2;
  else if (shape === '2,1,1,1') category = 1;
  else category = 0;
  return category === 8 || category === 4 ? [category, high] : [category, ...order];
}

function compareKeys(a, b) {
  for (let i = 0; i < Math.min(a.length, b.length); i++) if (a[i] !== b[i]) return a[i] - b[i];
  return a.length - b.length;
}

function solve(hands) {
  const keys = hands.map(strength);
  let best = keys[0];
  for (const k of keys) if (compareKeys(k, best) > 0) best = k;
  const result = [];
  keys.forEach((k, i) => { if (compareKeys(k, best) === 0) result.push(i); });
  return result;
}

function findWinners(hands) { return solve(hands); }

module.exports = solve;
module.exports.findWinners = findWinners;
