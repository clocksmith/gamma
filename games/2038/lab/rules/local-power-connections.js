// Power is a property of current infrastructure positions, not an allocation.
export function connectedFacilityIds(board, player) {
  const distance = (a, b) => Math.max(Math.abs(a.q - b.q), Math.abs(a.r - b.r),
    Math.abs((-a.q - a.r) - (-b.q - b.r)));
  const firstId = player.facilities[0]?.id;
  return new Set(player.facilities.filter((facility) => {
    if (facility.id === firstId) return true;
    const district = board.find((tile) => tile.instanceId === facility.tileId);
    return district && player.generators.some((generator) => {
      const source = board.find((tile) => tile.instanceId === generator.tileId);
      return source && distance(source, district) <= 1;
    });
  }).map((facility) => facility.id));
}
