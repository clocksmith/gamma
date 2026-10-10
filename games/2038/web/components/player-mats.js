import { node, text, reconcile, orgToken, updateOrg, format } from "./dom.js";

export function createPlayerMats(root, config, factions, copy) {
  const kits = new Map(config.playerKits.map((kit) => [kit.id, kit]));
  function create(player) {
    const mat = node("article", "public-player player-mat");
    mat.append(
      node("p", "eyebrow"),
      node("h3"),
      node("p", "institution-ability"),
    );
    const tracks = node("div", "holding-tracks");
    for (const [key, resource] of Object.entries(config.resources)) {
      const track = node("div", "holding-track");
      track.dataset.resource = key;
      const label = node("span", "track-label");
      const cells = node("div", "track-cells");
      for (let value = resource.min; value <= resource.cap; value++)
        cells.append(node("span", "track-cell", value));
      track.append(label, cells);
      tracks.append(track);
    }
    const supply = node("div", "org-supply");
    supply.append(
      node("span", "supply-label", copy.readyToPlace),
      node("div", "available-orgs"),
      node("span", "supply-label", copy.reserve),
      node("div", "reserve-orgs"),
    );
    mat.append(tracks, supply, node("p", "mat-score"));
    return mat;
  }
  return {
    update(state) {
      if (!state) return;
      reconcile(
        root,
        state.players,
        (player) => player.seat,
        create,
        (mat, player) => {
          const kit = kits.get(player.kitId);
          const faction = factions.factions.find(
            (item) => item.id === player.factionId,
          );
          mat.style.setProperty("--kit-color", kit.color);
          mat.classList.toggle("human", player.seat === 0);
          text(
            mat.children[0],
            format(copy.kitSeat, {
              symbol: kit.symbol,
              color: kit.colorName,
              seat: player.seat + 1,
              you: player.seat === 0 ? ` · ${copy.you}` : "",
            }),
          );
          text(mat.children[1], player.factionName);
          text(
            mat.children[2],
            faction.abilities
              .map(
                (ability) =>
                  `${ability.displayName || ability.name}: ${ability.text}`,
              )
              .join(" "),
          );
          mat.children[2].title = faction.motto;
          for (const track of mat.querySelectorAll(".holding-track")) {
            const key = track.dataset.resource,
              resource = config.resources[key];
            text(
              track.firstChild,
              format(copy.holding, { name: resource.name, value: player[key] }),
            );
            track.setAttribute(
              "aria-label",
              format(copy.holdingRange, {
                name: resource.name,
                value: player[key],
                cap: resource.cap,
              }),
            );
            for (const cell of track.lastChild.children) {
              cell.classList.toggle(
                "holding-cube",
                Number(cell.textContent) === player[key],
              );
              cell.setAttribute(
                "aria-current",
                String(Number(cell.textContent) === player[key]),
              );
            }
          }
          const available = player.pieces.filter((org) => org.tileId === null);
          const reserve = Array.from(
            { length: player.agentsInSupply },
            (_, index) => ({
              id: `s${player.seat}-agent-${player.pieces.length + index + 1}`,
              equipped: false,
            }),
          );
          for (const [selector, orgs] of [
            [".available-orgs", available],
            [".reserve-orgs", reserve],
          ]) {
            reconcile(
              mat.querySelector(selector),
              orgs,
              (org) => org.id,
              (org) => orgToken(org, kit, player.factionName),
              (token, org) => updateOrg(token, org, kit, player.factionName),
            );
          }
          text(
            mat.lastChild,
            format(copy.score, {
              orgs: player.pieces.filter((org) => org.tileId !== null).length,
              agi: player.agiDeclared ? copy.recognized : copy.notRecognized,
              score: player.mandate,
              suffix: state.complete ? copy.final : copy.ifScoredNow,
            }),
          );
        },
      );
    },
  };
}
