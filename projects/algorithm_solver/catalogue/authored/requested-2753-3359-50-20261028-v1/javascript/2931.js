"use strict";

function solve(values) {
  const flat = [];
  for (let i = 0; i < values.length; i++) {
    const row = values[i];
    for (let j = 0; j < row.length; j++) flat.push(row[j]);
  }
  flat.sort((a, b) => a - b);
  let total = 0;
  for (let i = 0; i < flat.length; i++) {
    total += (i + 1) * flat[i];
  }
  return total;
}

function maxSpending(values) {
  return solve(values);
}

module.exports = solve;
module.exports.solve = solve;
module.exports.maxSpending = maxSpending;
