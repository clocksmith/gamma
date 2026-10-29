"use strict";
// Hack2Hire 69a35cd56e73e4abccc9bfb7 (Apply Binary Array Operations) over an INFERRED spec; qualification unknown.

function solve(arr, ops) {
  const a = arr.slice(), zeros = [];
  const push = (x) => {
    zeros.push(x);
    let i = zeros.length - 1;
    while (i > 0) { const p = (i - 1) >> 1; if (zeros[p] <= zeros[i]) break; [zeros[i], zeros[p]] = [zeros[p], zeros[i]]; i = p; }
  };
  const pop = () => {
    const top = zeros[0], last = zeros.pop();
    if (zeros.length) {
      zeros[0] = last;
      let i = 0;
      for (;;) {
        const l = 2 * i + 1, r = l + 1; let m = i;
        if (l < zeros.length && zeros[l] < zeros[m]) m = l;
        if (r < zeros.length && zeros[r] < zeros[m]) m = r;
        if (m === i) break;
        [zeros[i], zeros[m]] = [zeros[m], zeros[i]]; i = m;
      }
    }
    return top;
  };
  for (let i = 0; i < a.length; i++) if (a[i] === 0) zeros.push(i);  // increasing order is already a heap
  for (const op of ops) {
    if (op === "1") {
      while (zeros.length && a[zeros[0]] === 1) pop();
      if (zeros.length) a[pop()] = 1;
    } else {
      const i = Number(op.slice(2));
      if (a[i] === 1) { a[i] = 0; push(i); }
    }
  }
  return a;
}

function applyOperations(arr, ops) { return solve(arr, ops); }

module.exports = solve;
module.exports.applyOperations = applyOperations;
