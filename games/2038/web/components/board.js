import { node, text, reconcile, orgToken, updateOrg, format } from "./dom.js";

export function createBoard(root, note, config, copy) {
  const kits = new Map(config.playerKits.map((kit) => [kit.id, kit]));
  const center = node("article", "era-hex");
  const era = node("strong"),
    cycle = node("span"),
    initiative = node("span");
  era.className = "era-marker";
  initiative.className = "initiative-marker";
  center.append(era, cycle, initiative);
  const tiles = node("div", "board-tiles");
  root.replaceChildren(tiles, center);
  let selected = null;
  let latest = null;
  function describe() {
    const tile = latest?.board.find((item) => item.instanceId === selected);
    if (!tile) return;
    const action = config.actions.find((item) => item.id === tile.actionId);
    const occupants = latest.players.flatMap((player) =>
      player.pieces
        .filter((org) => org.tileId === tile.instanceId)
        .map(
          (org) =>
            `${player.factionName}: Org ${org.id.split("-").at(-1)}${org.equipped ? " (equipped)" : ""}`,
        ),
    );
    text(
      note,
      `${action.name}: ${action.summary} Production: ${tile.production}. ${occupants.join("; ") || copy.noOrgs}`,
    );
  }
  return {
    update(state) {
      if (!state) return;
      latest = state;
      text(era, format(copy.era, { era: state.round }));
      text(cycle, format(copy.cycle, state));
      const first = state.players[state.initiativeSeat];
      text(
        initiative,
        format(copy.first, { symbol: kits.get(first.kitId).symbol }),
      );
      initiative.title = format(copy.initiative, {
        faction: first.factionName,
      });
      reconcile(
        tiles,
        state.board,
        (tile) => tile.instanceId,
        (tile) => {
          const element = node("button", "action-area");
          element.type = "button";
          element.append(
            node("strong"),
            node("small"),
            node("span", "hex-orgs"),
          );
          element.addEventListener("click", () => {
            selected = tile.instanceId;
            for (const sibling of tiles.children)
              sibling.setAttribute("aria-pressed", String(sibling === element));
            describe();
          });
          return element;
        },
        (element, tile) => {
          const action = config.actions.find(
            (item) => item.id === tile.actionId,
          );
          element.style.setProperty("--hex-x", tile.q);
          element.style.setProperty("--hex-y", tile.r + tile.q / 2);
          element.setAttribute(
            "aria-pressed",
            String(selected === tile.instanceId),
          );
          text(element.children[0], action.name);
          text(element.children[1], `${tile.q}, ${tile.r}`);
          const occupants = state.players.flatMap((player) =>
            player.pieces
              .filter((org) => org.tileId === tile.instanceId)
              .map((org) => ({ org, player })),
          );
          const holder = element.children[2];
          holder.classList.toggle("crowded", occupants.length > 6);
          element.setAttribute(
            "aria-label",
            `${action.name}, ${tile.q}, ${tile.r}. ${occupants.length} Orgs. ${action.summary} Production: ${tile.production}`,
          );
          reconcile(
            holder,
            occupants,
            (item) => item.org.id,
            ({ org, player }) =>
              orgToken(org, kits.get(player.kitId), player.factionName),
            (token, { org, player }) => {
              updateOrg(token, org, kits.get(player.kitId), player.factionName);
              const index = occupants.findIndex(
                (item) => item.org.id === org.id,
              );
              token.style.setProperty("--token-column", index % 5);
              token.style.setProperty("--token-row", Math.floor(index / 5));
            },
          );
        },
      );
      describe();
    },
  };
}
