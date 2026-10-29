"use strict";

function solve(rand7Stream) {
  if (Array.isArray(rand7Stream)) {
    for (let i = 0; i < rand7Stream.length; i += 2) {
      const idx = (rand7Stream[i] - 1) * 7 + rand7Stream[i + 1];
      if (idx <= 40) return ((idx - 1) % 10) + 1;
    }
    return 1;
  }
  const r7 = typeof globalThis.rand7 === "function" ? globalThis.rand7 : () => 1;
  while (true) {
    const idx = (r7() - 1) * 7 + r7();
    if (idx <= 40) return ((idx - 1) % 10) + 1;
  }
}

function rand10(rand7Stream) {
  return solve(rand7Stream);
}

module.exports = solve;
module.exports.solve = solve;
module.exports.rand10 = rand10;
