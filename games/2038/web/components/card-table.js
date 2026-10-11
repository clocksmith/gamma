import { node, text, reconcile, format } from "./dom.js";

export function createCardTable(
  root,
  config,
  factions,
  headlines,
  mandates,
  copy,
  trainingAnchor,
) {
  const dialog = node("dialog", "card-dialog");
  const close = node("button", "", copy.close);
  close.type = "button";
  const title = node("h2"),
    rules = node("p"),
    lore = node("blockquote");
  dialog.append(close, title, rules, lore);
  close.addEventListener("click", () => dialog.close());
  dialog.addEventListener("click", (event) => {
    if (event.target === dialog) dialog.close();
  });
  const sections = [
    ["stacks", copy.stacks],
    ["objectives", copy.objectives],
    ["headlines", copy.headlines],
    ["training", copy.training],
    ["identities", copy.identities],
  ];
  const lists = new Map();
  for (const [key, label] of sections) {
    const section = node("section", `card-section ${key}-section`);
    section.append(node("h3", "", label));
    const list = node("div", "table-cards");
    section.append(list);
    if (key === "training" && trainingAnchor) trainingAnchor.before(section);
    else root.append(section);
    lists.set(key, list);
  }
  root.append(dialog);
  function cards(key, records) {
    reconcile(
      lists.get(key),
      records,
      (record) => record.key || record.id,
      () => {
        const card = node("button", "table-card");
        card.type = "button";
        card.append(node("small"), node("strong"), node("span"));
        card.addEventListener("click", () => {
          const record = card.record;
          text(title, record.name);
          text(rules, record.rulesText || record.text || record.summary);
          text(
            lore,
            [
              record.newswire,
              record.flavorText,
              record.quote,
              record.introduction,
              record.motto,
            ]
              .filter(Boolean)
              .join("\n\n"),
          );
          if (!dialog.open) dialog.showModal();
        });
        return card;
      },
      (card, record) => {
        card.record = record;
        card.classList.toggle("card-back", Boolean(record.back));
        card.classList.toggle("recognized-identity", Boolean(record.agiDeclared));
        card.dataset.orientation = record.agiDeclared ? "180" : "0";
        text(card.children[0], record.kindLabel);
        text(card.children[1], record.name);
        text(card.children[2], (record.caption || copy.readCard) + (record.agiDeclared ? ` · ${config.scoreDisplay.recognizedLabel}` : ""));
        card.setAttribute(
          "aria-label",
          `${record.kindLabel}: ${record.name}. ${record.caption || copy.readDetails}`,
        );
      },
    );
  }
  return {
    update(state) {
      if (!state) return;
      const training = state.trainingDeck;
      const discarded = config.trainingDeck.cards.find(
        (card) => card.id === training.topDiscard,
      );
      cards("stacks", [
        {
          id: "training-draw",
          name: copy.trainingName,
          kindLabel: copy.drawPile,
          caption: format(copy.cardCount, { count: training.drawCount }),
          back: true,
          summary: copy.deckHidden,
        },
        {
          ...discarded,
          id: "training-discard",
          name: discarded?.name || copy.trainingName,
          kindLabel: copy.discardPile,
          caption: format(copy.cardCount, { count: training.discardCount }),
          back: !discarded,
          summary: copy.empty,
        },
        {
          id: "headline-stack",
          name: copy.headlines,
          kindLabel: copy.unrevealed,
          caption: format(copy.cardCount, {
            count: headlines.headlines.length - state.revealedHeadlines.length,
          }),
          back: true,
          summary: copy.deckHidden,
        },
        {
          id: "objective-stack",
          name: copy.objectivesName,
          kindLabel: copy.unrevealed,
          caption: format(copy.cardCount, {
            count: mandates.mandates.length - state.revealedMandates.length,
          }),
          back: true,
          summary: mandates.selection,
        },
      ]);
      cards(
        "objectives",
        state.revealedMandates.map((card) => ({
          ...card,
          kindLabel: format(copy.eraObjective, card),
        })),
      );
      cards(
        "headlines",
        state.revealedHeadlines
          .slice()
          .reverse()
          .map((card) => ({
            ...card,
            kindLabel:
              card.id === state.activeHeadline?.id
                ? copy.currentHeadline
                : format(copy.eraHeadline, { era: card.round }),
          })),
      );
      const run = state.trainingRun;
      lists.get("training").parentElement.hidden = !run;
      if (run) {
        text(
          lists.get("training").previousSibling,
          format(copy.runProgress, {
            faction: state.players[run.seat].factionName,
            amount: run.provisionalCapability,
          }),
        );
      }
      cards(
        "training",
        (run?.revealed || []).map((id, index) => ({
          ...config.trainingDeck.cards.find((card) => card.id === id),
          key: `${index}-${id}`,
          kindLabel: format(copy.drawNumber, { number: index + 1 }),
        })),
      );
      cards(
        "identities",
        factions.factions.map((card) => ({
          ...card,
          kindLabel: copy.institution,
          agiDeclared: Boolean(state.players.find(player => player.factionId === card.id)?.agiDeclared),
          caption: state.players.find((player) => player.factionId === card.id)
            ? format(copy.seat, {
                seat:
                  state.players.find((player) => player.factionId === card.id)
                    .seat + 1,
              })
            : copy.unused,
          rulesText: card.abilities
            .map(
              (ability) =>
                `${ability.displayName || ability.name}: ${ability.text}`,
            )
            .join("\n"),
        })),
      );
    },
  };
}
