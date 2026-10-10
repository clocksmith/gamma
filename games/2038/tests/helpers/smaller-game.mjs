import { readFile } from "node:fs/promises";
import { SelectedRulesMatch } from "../../lab/environment/selected-rules-match.js";
export const json = async (name) =>
  JSON.parse(
    await readFile(
      new URL(`../../dist/runtime/${name}.json`, import.meta.url),
      "utf8",
    ),
  );
export const config = await json("game-config");
export const factions = await json("factions");
export const headlines = await json("headlines");
export const mandates = await json("mandates");
export const projects = await json("projects");
export const profiles = (await json("player-strategies")).profiles;
export function fixture(options = {}) {
  const factionId = options.factionId || factions.factions[0].id;
  const roster = [
    factions.factions.find((f) => f.id === factionId),
    ...factions.factions.filter((f) => f.id !== factionId),
  ];
  return new SelectedRulesMatch({
    config,
    factions: roster,
    profiles,
    headlines,
    mandates,
    projects,
    seed: "smaller-contract",
    ...options,
  });
}
export function policy(select) {
  return {
    async decide(packet) {
      const picked = select?.(packet) || packet.legalDecisions[0];
      return {
        decision: {
          decisionId: picked.decisionId,
          rationale: "Deterministic contract fixture.",
        },
        receipt: { provider: "fixture", requestId: packet.requestId },
      };
    },
  };
}
export const policies = (m, select) => m.players.map(() => policy(select));
export function host(m, seat, area = "build", equipped = false) {
  const p = m.players[seat];
  const org = p.pieces.find(a => !a.tileId);
  if (!org) throw new Error("Fixture needs an unassigned Org");
  Object.assign(org, { tileId: area, equipped });
  return org;
}
export function action(m, seat, id, predicate = () => true) {
  const d = m.legalResolutions(seat, id).find(predicate);
  if (!d) throw new Error(`No legal fixture choice: ${id}`);
  return d;
}
