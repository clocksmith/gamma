function axialDistance(left, right) {
  const leftS = -left.q - left.r;
  const rightS = -right.q - right.r;
  return Math.max(
    Math.abs(left.q - right.q),
    Math.abs(left.r - right.r),
    Math.abs(leftS - rightS)
  );
}

function repeatedUnits(kind, count, metadata = {}) {
  return Array.from({ length: Math.max(0, count) }, (_, index) => ({
    kind,
    index,
    ...metadata
  }));
}

export function canAllocateLocalPower({
  board,
  player,
  selectedFacilityIds,
  connectedGenerators,
  startingGridPower,
  importedPower,
  supplementalPower,
  exportedPower
}) {
  const selected = selectedFacilityIds.map((facilityId) => {
    const facility = player.facilities.find((candidate) => candidate.id === facilityId);
    if (!facility) throw new RangeError(`Unknown selected Facility: ${facilityId}.`);
    return facility;
  });
  const firstFacilityId = player.facilities[0]?.id || null;
  const units = [
    ...repeatedUnits("starting_grid", startingGridPower),
    ...connectedGenerators.flatMap((generator) => {
      const tile = board.find((candidate) => candidate.instanceId === generator.tileId);
      return repeatedUnits("generator", generator.capacity, { tile });
    }),
    ...repeatedUnits("imported", importedPower),
    ...repeatedUnits("supplemental", supplementalPower)
  ];
  const demands = [
    ...selected.map((facility) => ({ kind: "facility", facility })),
    ...repeatedUnits("export", exportedPower)
  ];
  const eligibleUnitIndexes = demands.map((demand) =>
    units.flatMap((unit, index) => {
      if (demand.kind === "export") {
        return unit.kind === "generator" ? [index] : [];
      }
      if (unit.kind === "starting_grid") {
        return demand.facility.id === firstFacilityId ? [index] : [];
      }
      if (["imported", "supplemental"].includes(unit.kind)) return [index];
      const facilityTile = board.find(
        (candidate) => candidate.instanceId === demand.facility.tileId
      );
      return unit.tile && facilityTile && axialDistance(unit.tile, facilityTile) <= 1
        ? [index]
        : [];
    })
  );
  const demandOrder = demands.map((_, index) => index).sort(
    (left, right) =>
      eligibleUnitIndexes[left].length - eligibleUnitIndexes[right].length
  );
  const used = new Set();
  const assign = (position) => {
    if (position === demandOrder.length) return true;
    for (const unitIndex of eligibleUnitIndexes[demandOrder[position]]) {
      if (used.has(unitIndex)) continue;
      used.add(unitIndex);
      if (assign(position + 1)) return true;
      used.delete(unitIndex);
    }
    return false;
  };
  return assign(0);
}
