"use strict";

function hasShips(sea, tr, bl) {
  if (sea && typeof sea.hasShips === "function") return sea.hasShips(tr, bl);
  const [x2, y2] = tr, [x1, y1] = bl;
  for (let i = 0; i < sea.length; i++) {
    const [sx, sy] = sea[i];
    if (sx >= x1 && sx <= x2 && sy >= y1 && sy <= y2) return true;
  }
  return false;
}

function solve(sea, topRight, bottomLeft) {
  const countRec = (tr, bl) => {
    const [x2, y2] = tr, [x1, y1] = bl;
    if (x1 > x2 || y1 > y2 || !hasShips(sea, tr, bl)) return 0;
    if (x1 === x2 && y1 === y2) return 1;
    const mx = (x1 + x2) >> 1;
    const my = (y1 + y2) >> 1;
    return (
      countRec([mx, my], [x1, y1]) +
      countRec([x2, my], [mx + 1, y1]) +
      countRec([mx, y2], [x1, my + 1]) +
      countRec([x2, y2], [mx + 1, my + 1])
    );
  };
  return countRec(topRight, bottomLeft);
}

function countShips(sea, topRight, bottomLeft) {
  return solve(sea, topRight, bottomLeft);
}

module.exports = solve;
module.exports.solve = solve;
module.exports.countShips = countShips;
