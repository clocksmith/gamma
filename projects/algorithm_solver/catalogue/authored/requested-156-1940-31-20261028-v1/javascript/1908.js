"use strict";

function solve(piles) {
  let xorSum = 0;
  for (let i = 0; i < piles.length; i++) xorSum ^= piles[i];
  return xorSum !== 0;
}

function nimGame(piles) {
  return solve(piles);
}

module.exports = solve;
module.exports.solve = solve;
module.exports.nimGame = nimGame;
