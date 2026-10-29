"use strict";

function evalFn(cf, x, y) {
  if (cf && typeof cf.f === "function") return cf.f(x, y);
  if (typeof cf === "function") return cf(x, y);
  const fid = Number(cf);
  if (fid === 1) return x + y;
  if (fid === 2) return x * y;
  if (fid === 3) return x * x + y;
  if (fid === 4) return x + y * y;
  if (fid === 5) return x * x + y * y;
  if (fid === 6) return (x + y) * (x + y);
  if (fid === 7) return x * x * x + y * y * y;
  if (fid === 8) return x * x * y;
  return x * y * y;
}

function solve(customfunction, z) {
  const res = [];
  let x = 1, y = 1000;
  while (x <= 1000 && y >= 1) {
    const val = evalFn(customfunction, x, y);
    if (val === z) {
      res.push([x, y]);
      x++;
      y--;
    } else if (val < z) {
      x++;
    } else {
      y--;
    }
  }
  return res;
}

function findSolution(customfunction, z) {
  return solve(customfunction, z);
}

module.exports = solve;
module.exports.solve = solve;
module.exports.findSolution = findSolution;
