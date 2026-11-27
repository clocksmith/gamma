// CSS draws point-top hexes. The board's q/r coordinates use the matching
// point-top axial projection: q steps are down-right and r steps are down.
export const POINTY_TOP_HEX_WIDTH_FACTOR = 0.75;

export function pointyTopAxialPosition(tile, {
  width,
  height,
  originX,
  originY
}) {
  if (!Number.isFinite(tile?.q) || !Number.isFinite(tile?.r)) {
    throw new TypeError("A tile with finite axial q and r coordinates is required.");
  }
  for (const [name, value] of Object.entries({ width, height, originX, originY })) {
    if (!Number.isFinite(value)) throw new TypeError(`${name} must be finite.`);
  }
  return {
    left: originX + width * POINTY_TOP_HEX_WIDTH_FACTOR * tile.q - width / 2,
    top: originY + height * (tile.r + tile.q / 2) - height / 2
  };
}
