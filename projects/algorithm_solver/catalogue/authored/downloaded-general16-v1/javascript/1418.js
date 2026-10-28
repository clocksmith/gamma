'use strict';

// 1418. Display Table of Food Orders in a Restaurant (Medium).
// Specification: https://leetcode.com/problems/display-table-of-food-orders-in-a-restaurant/description/
function solve(orders) {
  const foods = new Set();
  const tables = new Map();
  for (const [customer, table, food] of orders) {
    foods.add(food);
    if (!tables.has(table)) tables.set(table, new Map());
    const counts = tables.get(table);
    counts.set(food, (counts.get(food) || 0) + 1);
  }
  const sortedFoods = [...foods].sort();
  const header = ["Table", ...sortedFoods];
  const rows = [...tables.entries()]
    .sort((a, b) => Number(a[0]) - Number(b[0]))
    .map(([table, counts]) => [table, ...sortedFoods.map((food) => String(counts.get(food) || 0))]);
  return [header, ...rows];
}
const displayTable = solve;
class Solution { displayTable(...args) { return solve(...args); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, displayTable };
