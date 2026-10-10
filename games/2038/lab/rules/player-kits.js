/** Equipment identity is presentation only; seat owns pieces and no RNG is used. */
export function resolvePlayerKits(config, playerCount, assignments) {
  const kits = config.playerKits;
  if (!Array.isArray(kits) || kits.length !== 5 || new Set(kits.map(kit => kit.id)).size !== 5) {
    throw new TypeError("Expected five distinct canonical player kits.");
  }
  if (!Number.isInteger(playerCount) || playerCount < 1 || playerCount > kits.length) {
    throw new RangeError("Player kit assignments require one to five seats.");
  }
  const ids = assignments === undefined ? kits.slice(0, playerCount).map(kit => kit.id) : assignments;
  if (!Array.isArray(ids) || ids.length !== playerCount || new Set(ids).size !== playerCount) {
    throw new TypeError(`kitAssignments must contain ${playerCount} distinct kit IDs.`);
  }
  return ids.map(id => {
    const kit = kits.find(candidate => candidate.id === id);
    if (!kit) throw new TypeError(`Unknown player kit: ${id}.`);
    return { ...kit };
  });
}
