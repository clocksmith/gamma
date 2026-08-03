export const FLAT_TOP_HEX_WIDTH_FACTOR = 0.75;

export function flatTopAxialPosition(tile, {
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
    left: originX + width * FLAT_TOP_HEX_WIDTH_FACTOR * (tile.q + tile.r / 2) - width / 2,
    top: originY + height * tile.r - height / 2
  };
}
