"use strict";
// Hack2Hire 6a32d45b65569fa70cc7eb97 (Shift Units Protection) over an INFERRED spec; qualification unknown.

function solve(population, unit) {
  const n = unit.length;
  let total = 0, i = 0;
  while (i < n) {
    if (unit[i] !== "1") { i++; continue; }
    let j = i, runSum = 0, runMin = Infinity;
    while (j < n && unit[j] === "1") { runSum += population[j]; runMin = Math.min(runMin, population[j]); j++; }
    total += i > 0 ? runSum + population[i - 1] - Math.min(runMin, population[i - 1]) : runSum;
    i = j;
  }
  return total;
}

function maxProtectedPopulation(population, unit) { return solve(population, unit); }

module.exports = solve;
module.exports.maxProtectedPopulation = maxProtectedPopulation;
