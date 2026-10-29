"use strict";
// Hack2Hire 68c327671f64f4312b0a3e1e (Minimize Shopping Department Visits) over an INFERRED spec; qualification unknown.

function solve(products, shoppingList) {
  const department = new Map();
  for (const [name, dept] of products) department.set(name, dept);
  const seen = new Set();
  for (const item of shoppingList) if (department.has(item)) seen.add(department.get(item));
  return seen.size;
}

function minDepartmentVisits(products, shoppingList) { return solve(products, shoppingList); }

module.exports = solve;
module.exports.minDepartmentVisits = minDepartmentVisits;
