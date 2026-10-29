"use strict";
// Hack2Hire 6779c17edcf91f8e3c1c310f (Monsters Battle, level 1) over an INFERRED spec; qualification unknown.

const LEVEL = 1;

function solve(monsters, root) {
  const kids = new Map(), hostile = new Map(), cost = new Map();
  for (const row of monsters) {
    const label = row[0], bad = label.endsWith("*");
    const name = bad ? label.slice(0, -1) : label;
    kids.set(name, row[row.length - 1]);
    hostile.set(name, bad);
    cost.set(name, LEVEL === 2 ? row[1] : 0);
  }
  const order = [], stack = [root];
  while (stack.length) {
    const u = stack.pop();
    order.push(u);
    for (const c of kids.get(u)) stack.push(c);
  }
  const below = new Map();
  for (let i = order.length - 1; i >= 0; i--) {
    const u = order[i];
    let s = 0;
    for (const c of kids.get(u)) s += below.get(c) + (hostile.get(c) ? 1 : 0);
    below.set(u, s);
  }
  if (LEVEL === 1) {
    const total = below.get(root) + (hostile.get(root) ? 1 : 0);
    return order.filter((u) => !hostile.get(u) && below.get(u) === total).sort();
  }
  if (hostile.get(root)) return -1;
  const need = new Map();
  for (let i = order.length - 1; i >= 0; i--) {
    const u = order[i];
    if (below.get(u) === 0) { need.set(u, 0); continue; }
    let split = 0;
    for (const c of kids.get(u)) {
      if (hostile.get(c) || need.get(c) === null) { split = null; break; }
      split += need.get(c);
    }
    const own = hostile.get(u) ? null : cost.get(u);
    let value = null;
    for (const x of [own, split]) if (x !== null && (value === null || x < value)) value = x;
    need.set(u, value);
  }
  return need.get(root) === null ? -1 : need.get(root);
}

function canDefeatAll(monsters, root) { return solve(monsters, root); }

module.exports = solve;
module.exports.canDefeatAll = canDefeatAll;
