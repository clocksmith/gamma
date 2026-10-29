"use strict";
// Hack2Hire 6a95ede5cddc54478ddf6b5b (Triangle Point Membership) over an INFERRED spec; qualification unknown.

function cross(ox, oy, ax, ay, bx, by) { return (ax - ox) * (by - oy) - (ay - oy) * (bx - ox); }

function solve(x1, y1, x2, y2, x3, y3, xp, yp, xq, yq) {
  if (cross(x1, y1, x2, y2, x3, y3) === 0) return 0;
  const inside = (px, py) => {
    const d1 = cross(x1, y1, x2, y2, px, py), d2 = cross(x2, y2, x3, y3, px, py), d3 = cross(x3, y3, x1, y1, px, py);
    return !((d1 < 0 || d2 < 0 || d3 < 0) && (d1 > 0 || d2 > 0 || d3 > 0));
  };
  const p = inside(xp, yp), q = inside(xq, yq);
  return p && q ? 3 : p ? 1 : q ? 2 : 4;
}

function pointsBelong(x1, y1, x2, y2, x3, y3, xp, yp, xq, yq) { return solve(x1, y1, x2, y2, x3, y3, xp, yp, xq, yq); }

module.exports = solve;
module.exports.pointsBelong = pointsBelong;
