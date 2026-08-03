import assert from "node:assert/strict";
import test from "node:test";
import { BOARD_RINGS, axialDistance } from "../web/src/engine.js";
import { flatTopAxialPosition } from "../web/src/hex-layout.js";

const width = 144;
const height = 125;
const origin = { originX: 0, originY: 0 };

test("flat-top browser layout makes every rules-adjacent board pair share a honeycomb edge", () => {
  const coordinates = Object.values(BOARD_RINGS).flat();
  const centers = coordinates.map(([q, r]) => {
    const position = flatTopAxialPosition({ q, r }, { width, height, ...origin });
    return { q, r, x: position.left + width / 2, y: position.top + height / 2 };
  });

  for (const [index, tile] of centers.entries()) {
    for (const other of centers.slice(index + 1)) {
      if (axialDistance(tile, other) !== 1) continue;
      const deltaX = Math.abs(tile.x - other.x);
      const deltaY = Math.abs(tile.y - other.y);
      assert.ok(
        (deltaX === width * 0.75 && deltaY === 0) ||
        (deltaX === width * 0.375 && deltaY === height),
        `(${tile.q},${tile.r}) and (${other.q},${other.r}) share an exact flat-top edge`
      );
    }
  }
});

test("flat-top browser layout preserves the sparse public wedges", () => {
  const publicTiles = BOARD_RINGS.outer.map(([q, r]) => ({ q, r }));
  for (const [index, tile] of publicTiles.entries()) {
    for (const other of publicTiles.slice(index + 1)) {
      assert.notEqual(axialDistance(tile, other), 1);
    }
  }
});
