import { hexDistance } from "../../web/src/engine.js";
export function nominalComputeCapacity(state, player) {
  return player.pieces.reduce((sum, org) => {
    const tile = state.board.find((t) => t.instanceId === org.tileId);
    return (
      sum +
      (tile?.yield.resource === "compute"
        ? tile.yield.amount * (org.equipped ? 2 : 1)
        : 0)
    );
  }, 0);
}
export function neighboringRivals(state, player) {
  const own = player.pieces
    .map((o) => state.board.find((t) => t.instanceId === o.tileId))
    .filter(Boolean);
  return state.players.filter(
    (p) =>
      p.seat !== player.seat &&
      p.pieces.some((o) => {
        const tile = state.board.find((t) => t.instanceId === o.tileId);
        return tile && own.some((a) => hexDistance(a, tile) === 1);
      }),
  ).length;
}
export function controlledAreas(state, player) {
  return state.board.filter((a) => {
    const counts = state.players.map((p) => ({
      seat: p.seat,
      n: p.pieces.filter((x) => x.tileId === a.instanceId).length,
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
  "orgs",
  "equipped_orgs",
  "neighbor_rivals",
  "controlled_areas",
  "compute_capacity",
]);
function value(metric, state, player) {
  if (!metrics.has(metric))
    throw new Error(`Unknown objective metric: ${metric}`);
  if (metric === "orgs") return player.pieces.length;
  if (metric === "equipped_orgs")
    return player.pieces.filter((o) => o.equipped).length;
  if (metric === "controlled_areas") return controlledAreas(state, player);
  if (metric === "compute_capacity")
    return nominalComputeCapacity(state, player);
  if (metric === "neighbor_rivals") return neighboringRivals(state, player);
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
