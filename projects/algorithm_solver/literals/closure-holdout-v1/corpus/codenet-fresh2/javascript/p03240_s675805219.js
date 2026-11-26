"use strict";

// read lines from stdin
const input = require("fs")
  .readFileSync("/dev/stdin", "utf8")
  .split("\n");

const N = parseInt(input[0], 10);
const points = [];
const outOfBounds = [];

for (let i = 1; i <= N; i++) {
  const line = input[i].split(" ").map((val) => parseInt(val, 10));
  if (line[2] > 0) {
    points.push({ x: line[0], y: line[1], h: line[2] });
  } else {
    outOfBounds.push({ x: line[0], y: line[1], h: line[2] });
  }
}

points.push(...outOfBounds);

for (let x = 0; x <= 100; x++) {
  for (let y = 0; y <= 100; y++) {
    let found = true;
    let estimate = {
      x,
      y,
      h: 0,
    }
    for (let i = 0; i < points.length; i++) {
      const point = points[i];

      if (estimate.h <= 0) {
        estimate.h = estimateTopHeight(point, estimate);
        continue;
      }

      if (!isValidHeight(point, estimate)) {
        found = false;
        break;
      }
    }

    if (found) {
      console.log(`${estimate.x} ${estimate.y} ${estimate.h}`);
      return;
    }
  }
}

function estimateTopHeight(current, top) {
  return current.h + Math.abs(top.x - current.x) + Math.abs(top.y - current.y);
}

function isValidHeight(current, top) {
  return Math.max(top.h - Math.abs(top.x - current.x) - Math.abs(top.y - current.y), 0) === current.h;
}
