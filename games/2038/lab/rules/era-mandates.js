export function facilityContractResource(board, facility) {
  return (
    board.find((a) => a.instanceId === facility.tileId)?.contractResource ||
    null
  );
}
export function facilityComputeCapacity(board, facility) {
  const a = board.find((a) => a.instanceId === facility.tileId);
  return a?.yield.resource === "compute"
    ? a.yield.amount * (facility.upgraded ? 2 : 1)
    : 0;
}
export function activeJointVenture(state, contract) {
  return (
    contract.kind === "joint_venture" &&
    contract.left.seat !== contract.right.seat &&
    [contract.left, contract.right].every((end) =>
      state.players
        .find((p) => p.seat === end.seat)
        ?.facilities.some(
          (f) =>
            f.id === end.facilityId &&
            state.board.some((a) => a.instanceId === f.tileId),
        ),
    )
  );
}
export function nominalComputeCapacity(state, player) {
  let total = player.facilities.reduce(
    (sum, f) => sum + facilityComputeCapacity(state.board, f),
    0,
  );
  for (const c of state.contracts || []) {
    if (!activeJointVenture(state, c)) continue;
    const other =
      c.left.seat === player.seat
        ? c.right
        : c.right.seat === player.seat
          ? c.left
          : null;
    if (other) {
      const host = state.players
        .find((p) => p.seat === other.seat)
        .facilities.find((f) => f.id === other.facilityId);
      if (facilityContractResource(state.board, host) === "compute") total++;
    }
  }
  return total;
}
export function controlledAreas(state, player) {
  return state.board.filter((a) => {
    const counts = state.players.map((p) => ({
      seat: p.seat,
      n: [...p.pieces, ...p.facilities].filter((x) => x.tileId === a.instanceId)
        .length,
    }));
    const best = Math.max(...counts.map((x) => x.n));
    const winners = counts.filter((x) => x.n === best);
    return best > 0 && winners.length === 1 && winners[0].seat === player.seat;
  }).length;
}
const metrics = new Set([
  "capability",
  "customers",
  "reputation",
  "runway",
  "compute",
  "facilities",
  "upgraded_facilities",
  "active_ventures",
  "controlled_areas",
  "compute_capacity",
]);
function value(metric, state, player) {
  if (!metrics.has(metric))
    throw new Error(`Unknown objective metric: ${metric}`);
  if (metric === "facilities") return player.facilities.length;
  if (metric === "upgraded_facilities")
    return player.facilities.filter((f) => f.upgraded).length;
  if (metric === "controlled_areas") return controlledAreas(state, player);
  if (metric === "compute_capacity")
    return nominalComputeCapacity(state, player);
  if (metric === "active_ventures")
    return (state.contracts || []).filter(
      (c) =>
        [c.left.seat, c.right.seat].includes(player.seat) &&
        activeJointVenture(state, c),
    ).length;
  return player[metric];
}
export function evaluateEraMandate(card, state, player) {
  if (
    !["min", "max"].includes(card.direction) ||
    !Array.isArray(card.qualification)
  )
    throw new Error("Invalid objective");
  return {
    qualified: card.qualification.every((q) => {
      if (!Number.isFinite(q.minimum)) throw new Error("Invalid qualification");
      return value(q.metric, state, player) >= q.minimum;
    }),
    value: value(card.metric, state, player),
    direction: card.direction,
  };
}
export function finalObjectiveStandings(card, state) {
  const rows = state.players.map((p) => ({
    seat: p.seat,
    ...evaluateEraMandate(card, state, p),
  }));
  const eligible = rows.filter((r) => r.qualified);
  if (!eligible.length) return rows.map((r) => ({ ...r, points: 0 }));
  const best = (card.direction === "min" ? Math.min : Math.max)(
    ...eligible.map((r) => r.value),
  );
  const winners = eligible.filter((r) => r.value === best);
  return rows.map((r) => ({
    ...r,
    points: winners.some((w) => w.seat === r.seat)
      ? winners.length === 1
        ? state.config.scoring.objectiveWinner
        : state.config.scoring.objectiveTie
      : 0,
  }));
}
