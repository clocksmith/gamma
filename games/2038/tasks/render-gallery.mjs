// Renders a single browsable "component gallery" of all Mandate 2038 game
// content: factions, actions, eras, headlines, mandates, projects, power
// sources, tactics, specialists, secret objectives, and reference cards.
//
// Every card shows its rendered player-facing text from dist/runtime/*.json.
// Output lands in dist/site/ (gitignored) and is served at /gallery by
// tasks/serve.mjs.

import { generateBoard } from "../web/src/engine.js";
import { mkdir, readFile, writeFile } from "node:fs/promises";
import { resolve } from "node:path";

const projectRoot = resolve(import.meta.dirname, "..");
const graph = JSON.parse(
  await readFile(resolve(projectRoot, "content/graph.json"), "utf8"),
);
const consumedInputs = new Set();
const outDir = resolve(projectRoot, "dist/site");
const checkOnly = process.argv.slice(2).includes("--check");
const baselineOnly = process.argv.slice(2).includes("--baseline");

function escapeHtml(text) {
  return String(text ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

async function readData(name) {
  const source = graph.galleryRendering.inputs[name];
  if (!source) throw new Error(`Undeclared gallery content: ${name}`);
  consumedInputs.add(source);
  return JSON.parse(await readFile(resolve(projectRoot, source), "utf8"));
}

// --- card primitives ---------------------------------------------------------

function badges(items) {
  const clean = items.filter(Boolean);
  if (!clean.length) return "";
  return `<div class="badges">${clean.map((b) => `<span class="badge">${escapeHtml(b)}</span>`).join("")}</div>`;
}

function tags(items) {
  if (!items || !items.length) return "";
  return `<div class="tags">${items.map((t) => `<span class="tag">${escapeHtml(t)}</span>`).join("")}</div>`;
}

function textRows(rows) {
  return rows
    .filter((row) => row && row.text)
    .map((row) => {
      const cls = row.kind ? ` class="${row.kind}"` : "";
      const label = row.label
        ? `<span class="field-label">${escapeHtml(row.label)}</span>`
        : "";
      return `<p${cls}>${label}${escapeHtml(row.text)}</p>`;
    })
    .join("");
}

function listRows(label, lines) {
  if (!lines || !lines.length) return "";
  return `<div class="sublist"><span class="field-label">${escapeHtml(label)}</span><ul>${lines
    .map((line) => `<li>${escapeHtml(line)}</li>`)
    .join("")}</ul></div>`;
}

function card({
  accent,
  title,
  subtitle,
  badgeList = [],
  bodyHtml = "",
  tagList,
}) {
  const accentStyle = accent ? ` style="--accent:${escapeHtml(accent)}"` : "";
  return `<article class="card"${accentStyle}>
<div class="card-body">
<h3 class="card-title">${escapeHtml(title)}</h3>
${subtitle ? `<p class="card-sub">${escapeHtml(subtitle)}</p>` : ""}
${badges(badgeList)}
${bodyHtml}
${tags(tagList)}
</div>
</article>`;
}

function section(id, label, count, cardsHtml, blurb) {
  return `<section id="${id}" class="cat">
<header class="cat-head"><h2>${escapeHtml(label)} <span class="count">${count}</span></h2>${blurb ? `<p class="cat-blurb">${escapeHtml(blurb)}</p>` : ""}</header>
<div class="grid">${cardsHtml}</div>
</section>`;
}

const roman = ["", "I", "II", "III", "IV", "V"];
const roundBadge = (n) => (n ? `Era ${roman[n] || n}` : "");
const eraBadge = (n) => (n ? `Era ${roman[n] || n}` : "");
const timingBadge = (t) => (t ? t.replace(/_/g, " ") : "");

// --- category builders -------------------------------------------------------

function buildFactions(data, config) {
  const cards = data.factions.map(f => {
    const stats = Object.entries(f.starts).map(([key,value]) =>
      `<div><dt>${escapeHtml(config.resources[key]?.name || key)}</dt><dd>${value}</dd></div>`).join('');
    const ability = f.abilities.map(a => `<p><strong>${escapeHtml(a.displayName || a.name)}</strong><br>${escapeHtml(a.text)}</p>`).join('');
    const lore = [f.motto, f.introduction, ...f.abilities.map(a => a.flavorText), f.scoringRule?.flavorText].filter(Boolean);
    return `<article class="identity-pair" style="--accent:${escapeHtml(f.brandColor)}">
      <div class="card identity-face identity-front">
        <div class="identity-pointer pointer-top"><span>▲</span>${escapeHtml(config.scoreDisplay.unrecognizedLabel)}</div>
        <div class="card-body"><h3>${escapeHtml(f.name)}</h3><p>${escapeHtml(f.chiefExecutive)}</p><dl class="stats">${stats}</dl>${ability}</div>
        <div class="identity-pointer pointer-bottom"><span>▲</span>${escapeHtml(config.scoreDisplay.recognizedLabel)}</div>
      </div>
      <div class="card identity-face identity-back"><div class="card-body"><h3>${escapeHtml(f.name)}</h3>${lore.map(t=>`<p class="flavor">${escapeHtml(t)}</p>`).join('')}</div></div>
    </article>`;
  }).join('');
  return section('factions', 'Faction identity cards', data.factions.length, cards, config.scoreDisplay.instructions);
}

function buildPlayerMats(config) {
  const mats = config.playerKits.map(kit => `<article class="card player-mat" data-kit="${kit.id}" style="--accent:${kit.color}">
    <h3>${kit.symbol} ${kit.colorName} · ${kit.symbolName}</h3>
    <div class="mat-holdings">${Object.entries(config.resources).map(([key,t]) =>
      `<div class="resource-track" data-resource="${key}"><strong>${escapeHtml(t.name)}</strong><div>${Array.from({length:t.cap+1},(_,n)=>`<span>${n}</span>`).join('')}</div></div>`).join('')}</div>
    <div class="mat-actions">${config.actions.map(a=>`<p><strong>${escapeHtml(a.name)}</strong> ${escapeHtml(a.summary)}</p>`).join('')}</div>
    <p>${escapeHtml(config.turnReference)}</p><p>${escapeHtml(config.scoreDisplay.description)}</p><p>${escapeHtml(config.scoreDisplay.instructions)}</p>
    <div class="final-score-scale" aria-label="Final Mandate">${Array.from({length:config.scoreDisplay.maximum+1},(_,n)=>`<span data-score="${n}">${n}</span>`).join('')}</div>
  </article>`).join('');
  return section('player-mats', 'Player mats', config.playerKits.length, mats, 'Five holding tracks and an identity-card pointer for final Mandate.');
}
function formatTurnContract(tc) {
  if (!tc || typeof tc !== "object") return tc || "";
  const parts = [];
  if (tc.cost) parts.push(`Cost: ${tc.cost}`);
  if (Array.isArray(tc.modes) && tc.modes.length)
    parts.push(`Modes: ${tc.modes.join(", ")}`);
  if (tc.risk) parts.push(`Risk: ${tc.risk}`);
  return parts.join(" · ");
}

function buildActions(config) {
  const cards = config.playerKits
    .flatMap((kit) =>
      config.actions.map((action) =>
        card({
          accent: kit.color,
          title: `${kit.symbol} ${action.name}`,
          subtitle: `${kit.colorName} · ${kit.symbolName} kit`,
          badgeList: [
            "Core Action",
            action.initiativeName ? `Initiative: ${action.initiativeName}` : "",
          ],
          bodyHtml: textRows([
            { text: action.summary },
            {
              label: "Turn contract",
              text: formatTurnContract(action.turnContract),
            },
            { text: action.flavorText, kind: "flavor" },
          ]),
        }).replace(
          '<article class="card"',
          `<article class="card core-action" data-kit="${escapeHtml(kit.id)}"`,
        ),
      ),
    )
    .join("");
  return section(
    "actions",
    "Core Actions",
    config.playerKits.length * config.actions.length,
    cards,
    "Optional review copies only. Play uses the shared Action hexes, not Action cards.",
  );
}

function buildEquipment(config) {
  const tokens = config.playerKits
    .flatMap((kit) =>
      Array.from(
        { length: config.playerSupply.agents },
        (_, i) =>
          `<article class="card agent-token" data-kit="${kit.id}" style="--accent:${kit.color}">${[false, true].map((equipped) => `<div class="chip-face" data-org-face="${equipped ? "equipped" : "normal"}"><h3>${kit.symbol} Org ${i + 1}</h3><p>${kit.colorName} · ${kit.symbolName}</p><strong>${equipped ? "Equipped ×2" : "Normal ×1"}</strong></div>`).join("")}</article>`,
      ),
    )
    .join("");
  return section(
    "equipment",
    "Orgs",
    20,
    tokens,
    "Four two-sided tokens per player. Two start available; two remain in reserve.",
  );
}
function buildAreas(config, reference) {
  const face = (side, title, body) =>
    `<div class="hex-face" data-hex-face="${side}"><div><h3>${escapeHtml(title)}</h3>${body}</div></div>`;
  const hexes = generateBoard(config)
    .map((tile) => {
      const action = config.actions.find((a) => a.id === tile.actionId);
      const coordinates = `<p>(${tile.q}, ${tile.r})</p>`;
      return `<article class="card hex-tile">${face("front", action.name, coordinates + textRows([{ text: action.summary }, { text: tile.production }]))}${face(
        "back",
        tile.name,
        coordinates +
          textRows([
            { text: action.flavorText, kind: "flavor" },
            { text: tile.flavorText, kind: "flavor" },
          ]),
      )}</article>`;
    })
    .join("");
  const eras = reference.eraCards;
  const center = `<article class="card hex-tile era-tile">${face("front", "The Eras", eras.map((e) => `<p><strong>${e.round}. ${escapeHtml(e.name)}</strong> · 1 · 2 · 3</p>`).join("") + `<p>${escapeHtml(eras[0].rulesText)}</p>`)}${face("back", "The Eras", eras.map((e) => `<p><strong>${escapeHtml(e.name)}</strong><br>${escapeHtml(e.strapline)}</p>`).join(""))}</article>`;
  return section(
    "areas",
    "Shared hex board",
    19,
    hexes + center,
    "Front and back of each tile. Eighteen Action hexes in two rings around the Era center. Assemble by coordinates; only shared edges connect.",
  );
}
function buildTraining(config) {
  const cards = config.trainingDeck.cards
    .flatMap((c) =>
      Array.from({ length: c.count }, () =>
        card({
          title: c.name,
          bodyHtml: textRows([
            { text: c.rulesText },
            { text: c.flavorText, kind: "flavor" },
          ]),
        }).replace('class="card"', 'class="card training-card"'),
      ),
    )
    .join("");
  return section(
    "training",
    "Training",
    40,
    cards,
    "Four copies of every design. Shared draw pile; reshuffle discards only when it empties.",
  );
}
function buildRounds(config, reference) {
  const erasByRound = new Map(
    (reference.eraCards || []).map((era) => [era.round, era]),
  );
  const cards = config.rounds
    .map((r) => {
      const era = erasByRound.get(r.number);
      return card({
        title: `${roman[r.number] || r.number}. ${era?.name || r.name}`,
        subtitle: era?.strapline,
        bodyHtml: textRows([
          { text: era.rulesText, kind: "rules" },
          { label: "Unlocks", text: era.unlockText },
        ]),
      });
    })
    .join("");
  return section(
    "rounds",
    "Eras",
    config.rounds.length,
    cards,
    "The four-Era escalation from Progress to Continuity.",
  );
}

function buildHeadlines(data) {
  const cards = data.headlines
    .map((h) =>
      card({
        title: h.name,
        badgeList: [roundBadge(h.round)],
        bodyHtml: `${textRows([
          { text: h.newswire, kind: "flavor" },
          { text: h.text, kind: "rules" },
          { text: h.quote ? `“${h.quote}”` : "", kind: "flavor quote" },
        ])}`,
      }),
    )
    .join("");
  return section(
    "headlines",
    "Headlines",
    data.headlines.length,
    cards,
    `Era packets: ${[1, 2, 3, 4].map((era) => data.headlines.filter((card) => card.round === era).length).join(" / ")}. Reveal three per Era.`,
  );
}

function buildMandates(data) {
  const cards = data.mandates
    .map((m) =>
      card({
        title: m.name,
        badgeList: [eraBadge(m.era), m.direction === "min" ? "fewest" : "most"],
        bodyHtml: textRows([
          { text: m.rulesText, kind: "rules" },
          { text: m.flavorText, kind: "flavor" },
        ]),
        tagList: m.mechanicalTags,
      }),
    )
    .join("");
  return section(
    "mandates",
    "Era Mandates",
    data.mandates.length,
    cards,
    "Reveal one per Era; score all four from the final table.",
  );
}

function buildProjects(data, config) {
  const entries = [...data.projects, ...data.institutionalHistory];
  return section(
    "projects",
    "Retained technology lore",
    entries.length,
    entries
      .map((p) =>
        card({
          title: p.displayName || p.name,
          bodyHtml: textRows([
            { text: p.flavorText, kind: "flavor" },
            { text: p.quote, kind: "flavor" },
            { text: p.publicClaim, kind: "flavor" },
            { text: p.tagline, kind: "flavor" },
          ]),
        }),
      )
      .join(""),
    "All technology lore retained; these references add no pieces or subsystems to the playing kit.",
  );
}
function buildTactics(data) {
  const cards = data.tactics
    .map((t) =>
      card({
        title: t.displayName || t.name,
        subtitle:
          t.displayName && t.displayName !== t.name ? t.name : t.technology,
        badgeList: ["Deferred module"],
        bodyHtml: textRows([
          { text: t.text, kind: "rules" },
          { text: t.flavorText, kind: "flavor" },
        ]),
      }),
    )
    .join("");
  return section(
    "tactics",
    "Tactics (deferred)",
    data.tactics.length,
    cards,
    "Optional development module; excluded from baseline balance.",
  );
}

function buildSpecialists(data) {
  const cards = data.specialists
    .map((s) =>
      card({
        title: s.name,
        subtitle: s.title,
        badgeList: ["Reserve"],
        bodyHtml: textRows([{ text: s.flavorText, kind: "flavor" }]),
      }),
    )
    .join("");
  return section(
    "specialists",
    "Reserve Specialists",
    data.specialists.length,
    cards,
    "Design-reserve identities not promoted to full factions.",
  );
}

function buildObjectives(data) {
  const cards = data.objectives
    .map((o) =>
      card({
        title: o.name,
        badgeList: ["Deferred module"],
        bodyHtml: textRows([
          { text: o.rulesText, kind: "rules" },
          { text: o.flavorText, kind: "flavor" },
        ]),
        tagList: o.mechanicalTags,
      }),
    )
    .join("");
  return section(
    "objectives",
    "Secret Objectives (deferred)",
    data.objectives.length,
    cards,
    "Optional module; not used in baseline scoring.",
  );
}

function buildReferenceCards(data) {
  const eras = (data.eraCards || []).map((c) =>
    card({
      title: c.name,
      subtitle: c.strapline,
      badgeList: [roundBadge(c.round), "Governance Board panel"],
      bodyHtml: textRows([
        { text: c.rulesText, kind: "rules" },
        { label: "Unlocks", text: c.unlockText },
      ]),
    }),
  );
  const refs = (data.playerReferences || []).map((c) =>
    card({
      title: c.name,
      badgeList: ["Player aid"],
      bodyHtml: `${listRows("Front", c.frontText)}${listRows("Back", c.backText)}`,
    }),
  );
  const all = [...eras, ...refs].join("");
  return section(
    "reference",
    "Board Panels and Player Aids",
    eras.length + refs.length,
    all,
    "Four printed Era panels and the four topics repeated on each foldout player aid.",
  );
}

// --- page assembly -----------------------------------------------------------

const STYLE = `
:root { color-scheme: light dark; --accent: #64748b; }
* { box-sizing: border-box; }
body { margin: 0; font: 15px/1.55 -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; color: #1a1a1a; background: #ececea; }
.layout { display: grid; grid-template-columns: 240px minmax(0,1fr); }
nav.sidebar { position: sticky; top: 0; align-self: start; height: 100vh; overflow-y: auto; padding: 1.3rem 1.1rem; background: #171d26; color: #cbd5e1; }
nav.sidebar h1 { font-size: 0.95rem; margin: 0 0 0.2rem; color: #fff; }
nav.sidebar p.tagline { font-size: 0.75rem; color: #94a3b8; margin: 0 0 1rem; }
nav.sidebar a { display: flex; justify-content: space-between; gap: 0.5rem; color: #cbd5e1; text-decoration: none; padding: 0.3rem 0.4rem; border-radius: 6px; font-size: 0.86rem; }
nav.sidebar a:hover { background: #232c39; color: #fff; }
nav.sidebar a .n { color: #64748b; font-variant-numeric: tabular-nums; }
.search { width: 100%; margin: 0 0 0.9rem; padding: 0.5rem 0.65rem; border-radius: 8px; border: 1px solid #334155; background: #0f141b; color: #e2e8f0; font-size: 0.85rem; }
main { padding: 1.8rem clamp(1rem, 3vw, 2.4rem); }
.page-head { margin: 0 0 1.5rem; }
.page-head h1 { margin: 0 0 0.2rem; font-size: 1.6rem; }
.page-head p { margin: 0; color: #475569; max-width: 60ch; }
.cat { margin: 0 0 2.6rem; scroll-margin-top: 1rem; }
.cat-head h2 { margin: 0 0 0.15rem; font-size: 1.15rem; display: flex; align-items: baseline; gap: 0.5rem; }
.cat-head .count { font-size: 0.8rem; color: #fff; background: #64748b; border-radius: 999px; padding: 0.05rem 0.5rem; }
.cat-blurb { margin: 0 0 1rem; color: #64748b; font-size: 0.85rem; }
.grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 1rem; }
.card { display: flex; flex-direction: column; background: #fff; border: 1px solid #d7d7d2; border-top: 3px solid var(--accent); border-radius: 10px; overflow: hidden; }
.card-body { padding: 0.7rem 0.9rem 0.95rem; display: flex; flex-direction: column; gap: 0.5rem; }
.card-title { margin: 0; font-size: 1.02rem; }
.card-sub { margin: -0.25rem 0 0; color: #64748b; font-size: 0.82rem; font-style: italic; }
.card p { margin: 0; }
.rules { font-size: 0.9rem; }
.flavor { color: #64748b; font-style: italic; font-size: 0.85rem; }
.motto { font-weight: 500; }
.mech-name { font-size: 0.72rem; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.05em; margin: 0; }
.field-label { display: block; font-size: 0.65rem; font-weight: 700; letter-spacing: 0.07em; text-transform: uppercase; color: #9aa3ad; margin-bottom: 0.15rem; }
.badges { display: flex; flex-wrap: wrap; gap: 0.3rem; }
.badge { font-size: 0.68rem; font-weight: 600; background: color-mix(in srgb, var(--accent) 16%, #eef0f2); color: color-mix(in srgb, var(--accent) 75%, #334155); border-radius: 5px; padding: 0.1rem 0.42rem; }
.tags { display: flex; flex-wrap: wrap; gap: 0.25rem; }
.tag { font-size: 0.66rem; color: #94a3b8; background: #f1f1ee; border-radius: 4px; padding: 0.05rem 0.35rem; }
.project-chip { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); }
.chip-face { padding: .7rem; }
.chip-face + .chip-face { border-left: 2px dashed var(--accent); }
.chip-face h3 { margin: 0; }
.chip-owner { font-weight: 600; color: var(--accent); }
#areas .grid { grid-template-columns: repeat(auto-fit, minmax(min(100%, 440px), 1fr)); }
.card.hex-tile { background: transparent; border: 0; overflow: visible; gap: 16px; }
.hex-face { width: 100%; aspect-ratio: 1.1547; display: flex; align-items: center; justify-content: center;
  clip-path: polygon(25% 0,75% 0,100% 50%,75% 100%,25% 100%,0 50%);
  background: #fff; color: #111; container-type: inline-size; }
.hex-face > div { width: 52%; font-size: 3.1cqw; line-height: 1.35; }
.hex-face h3 { margin: 0 0 .5em; font-size: 4.2cqw; }
.hex-face p { margin: .5em 0; }
.hex-face .flavor { font-size: inherit; }
@media print {
  nav.sidebar, .page-head, .cat-head { display: none; }
  .layout { display: block; } main { padding: 0; }
  #areas .grid { display: block; }
  .hex-face { width: 127.02mm; height: 110mm; break-inside: avoid; print-color-adjust: exact; }
  .card.hex-tile { break-inside: auto; margin: 0; }
}
@media print {
  #projects .grid { display: block; }
  .project-chip { width: 150mm; height: 85mm; margin-bottom: 5mm; border: 1px solid #333; border-radius: 0; box-sizing: border-box; break-inside: avoid; }
  .chip-face { box-sizing: border-box; overflow-wrap: anywhere; font: 10pt/1.3 sans-serif; padding: 4mm; }
  .chip-face h3 { font-size: 12pt; }
}
.stats { display: flex; flex-wrap: wrap; gap: 0.4rem; margin: 0; }
.stats div { background: #f4f4f2; border-radius: 6px; padding: 0.2rem 0.45rem; text-align: center; min-width: 3.4rem; }
.stats dt { font-size: 0.6rem; text-transform: uppercase; letter-spacing: 0.05em; color: #9aa3ad; margin: 0; }
.stats dd { margin: 0; font-weight: 700; font-size: 0.95rem; }
.abilities { display: flex; flex-direction: column; gap: 0.5rem; }
.ability { border-left: 3px solid color-mix(in srgb, var(--accent) 45%, #d7d7d2); padding-left: 0.6rem; }
.ability-head { display: flex; flex-wrap: wrap; align-items: baseline; gap: 0.4rem; }
.sublist ul { margin: 0.15rem 0 0; padding-left: 1.1rem; font-size: 0.85rem; }
.card.hidden, .cat.hidden { display: none; }
@media (prefers-color-scheme: dark) {
  body { color: #e2e8f0; background: #0d1117; }
  .page-head p, .cat-blurb { color: #94a3b8; }
  .card { background: #161b22; border-color: #2a313c; }
  .card-sub, .flavor { color: #94a3b8; }
  .stats div { background: #1e2530; }
  .tag { background: #1e2530; color: #94a3b8; }
}

#player-mats .grid { grid-template-columns: repeat(auto-fit,minmax(min(100%,680px),1fr)); }
.player-mat { padding: 18px; gap: 9px; }
.player-mat h3 { margin: 0; }
.mat-holdings { display: grid; gap: 6px; }
.resource-track { display: grid; grid-template-columns: 100px 1fr; gap: 8px; }
.resource-track > div { display: flex; gap: 3px; }
.resource-track span { flex: 0 0 6.1%; text-align: center; border: 1px solid #666; }
.mat-actions { display: grid; grid-template-columns: 1fr 1fr; gap: 6px 14px; }
.final-score-scale { display: flex; justify-content: space-between; margin-top: auto; border-bottom: 1px solid; }
.final-score-scale span { flex: 1; text-align: center; font-size: 9px; border-bottom: 6px solid transparent; position: relative; }
.final-score-scale span::after { content: ''; position: absolute; width: 1px; height: 5px; background: currentColor; bottom: -6px; left: 50%; }
.identity-pair { display: grid; gap: 16px; }
.identity-face { position: relative; }
.identity-front { min-height: 350px; padding-block: 24px; }
.identity-pointer { position: absolute; left: 0; width: 100%; text-align: center; font-size: 10px; font-weight: bold; }
.identity-pointer > span { display: block; line-height: 1; }
.pointer-top { top: 0; } .pointer-bottom { bottom: 0; transform: rotate(180deg); }
@media print {
  body { background: white; color: black; }
  #player-mats .grid { display: block; }
  .card.player-mat { width: 210mm; height: 148mm; padding: 5mm; gap: 2mm; font: 10pt/1.25 sans-serif; border-radius: 0; break-inside: avoid; break-after: page; overflow: visible; }
  .resource-track { grid-template-columns: 25mm 1fr; gap: 2mm; }
  .resource-track span { height: 6mm; line-height: 6mm; }
  .mat-holdings { gap: 1mm; }
  .mat-actions { gap: 2mm; }
  .final-score-scale span { font-size: 6.5pt; }
  #factions .grid { display: block; }
  .identity-pair { display: flex; gap: 4mm; break-inside: avoid; margin-bottom: 4mm; }
  .card.identity-face { width: 63mm; height: 88mm; min-height: 0; border-radius: 0; background: white; color: black; }
  .identity-front { padding-block: 7mm; }
  .identity-face .card-body { padding: 3mm; gap: 2mm; font: 8pt/1.25 sans-serif; }
  .identity-face h3 { font-size: 11pt; margin: 0; }
  .identity-face .flavor { font-size: 7.5pt; color: black; }
  .identity-face .stats { display: grid; grid-template-columns: repeat(3,1fr); gap: 1mm; }
  .identity-face .stats div { min-width: 0; padding: 1mm; flex: 1; }
  .identity-face .stats dt { font-size: 6pt; letter-spacing: 0; color: #333; }
  .identity-face .stats dd { font-size: 9pt; }
  .identity-pointer { font-size: 6pt; }
}

@media print {
  #training .grid, #headlines .grid, #mandates .grid { display: flex; flex-wrap: wrap; gap: 4mm; }
  #training .card, #headlines .card, #mandates .card { width: 63mm; height: 88mm; border-radius: 0; break-inside: avoid; background: white; color: black; }
  #training .card-body, #headlines .card-body, #mandates .card-body { padding: 3mm; gap: 2mm; font: 8pt/1.2 sans-serif; }
  #training .card-title, #headlines .card-title, #mandates .card-title { font-size: 10pt; }
  #training p, #headlines p, #mandates p { font-size: 8pt; color: black; }
  #mandates .tags { display: none; }
  #equipment .grid { display: flex; flex-wrap: wrap; gap: 3mm; }
  .card.agent-token { display: flex; flex-direction: row; gap: 2mm; border: 0; overflow: visible; break-inside: avoid; }
  .agent-token .chip-face { width: 24mm; height: 24mm; padding: 3mm 1mm; border: 1px solid var(--accent); border-radius: 50%; text-align: center; font: 7pt/1.4 sans-serif; background: white; color: black; }
  .agent-token .chip-face h3 { font-size: 9pt; }
  .agent-token .chip-face p { display: none; }
}
@media (max-width: 760px) { .layout { grid-template-columns: 1fr; } nav.sidebar { position: static; height: auto; } }`;

const SCRIPT = `const search = document.getElementById('q');
const cards = [...document.querySelectorAll('.card')];
const cats = [...document.querySelectorAll('.cat')];
search.addEventListener('input', () => {
  const q = search.value.trim().toLowerCase();
  for (const c of cards) c.classList.toggle('hidden', q && !c.textContent.toLowerCase().includes(q));
  for (const s of cats) {
    const visible = [...s.querySelectorAll('.card')].some((c) => !c.classList.contains('hidden'));
    s.classList.toggle('hidden', !visible);
  }
});`;

async function build() {
  const [
    factions,
    config,
    headlines,
    mandates,
    escalation,
    tactics,
    specialists,
    objectives,
    reference,
  ] = await Promise.all([
    readData("factions"),
    readData("game-config"),
    readData("headlines"),
    readData("mandates"),
    readData("projects"),
    readData("tactics"),
    readData("reserve-specialists"),
    readData("secret-objectives"),
    readData("reference-cards"),
  ]);

  const allSections = [
    {
      id: "player-mats",
      label: "Player mats",
      html: buildPlayerMats(config),
      n: config.playerKits.length,
    },
    {
      id: "factions",
      label: "Factions",
      html: buildFactions(factions, config),
      n: factions.factions.length,
    },
    {
      id: "equipment",
      label: "Kit-owned equipment",
      html: buildEquipment(config),
      n: config.playerKits.length * config.playerSupply.agents,
    },
    {
      id: "actions",
      label: "Core Actions",
      html: buildActions(config),
      n: config.playerKits.length * config.actions.length,
    },
    {
      id: "rounds",
      label: "Eras",
      html: buildRounds(config, reference),
      n: config.rounds.length,
    },
    { id: "training", label: "Training", html: buildTraining(config), n: 40 },
    {
      id: "headlines",
      label: "Headlines",
      html: buildHeadlines(headlines),
      n: headlines.headlines.length,
    },
    {
      id: "mandates",
      label: "Era Mandates",
      html: buildMandates(mandates),
      n: mandates.mandates.length,
    },
    {
      id: "projects",
      label: "Retained technology lore",
      html: buildProjects(escalation, config),
      n: escalation.projects.length,
    },
    {
      id: "areas",
      label: "Shared action areas",
      html: buildAreas(config, reference),
      n: 19,
    },
    {
      id: "reference",
      label: "Board Panels and Player Aids",
      html: buildReferenceCards(reference),
      n:
        (reference.eraCards || []).length +
        (reference.playerReferences || []).length,
    },
    {
      id: "tactics",
      label: "Tactics",
      html: buildTactics(tactics),
      n: tactics.tactics.length,
    },
    {
      id: "objectives",
      label: "Secret Objectives",
      html: buildObjectives(objectives),
      n: objectives.objectives.length,
    },
    {
      id: "specialists",
      label: "Reserve Specialists",
      html: buildSpecialists(specialists),
      n: specialists.specialists.length,
    },
  ];
  const deferredIds = new Set([
    "tactics",
    "objectives",
    "specialists",
    "actions",
    "rounds",
    "reference",
    "projects",
  ]);
  const sections = baselineOnly
    ? allSections.filter((section) => !deferredIds.has(section.id))
    : allSections;

  const total = sections.reduce((sum, s) => sum + s.n, 0);
  const navLinks = sections
    .map(
      (s) =>
        `<a href="#${s.id}">${escapeHtml(s.label)}<span class="n">${s.n}</span></a>`,
    )
    .join("\n");

  return `<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Mandate 2038 — Content Gallery</title>
<style>${STYLE}</style>
</head>
<body>
<div class="layout">
<nav class="sidebar">
<h1>Mandate 2038</h1>
<p class="tagline">Content gallery · ${total} components</p>
<input id="q" class="search" type="search" placeholder="Filter all cards…" autocomplete="off">
${navLinks}
</nav>
<main>
<div class="page-head">
<h1>Content Gallery</h1>
<p>Every ${baselineOnly ? "baseline " : ""}game component with its rendered player-facing text from <code>dist/runtime/*.json</code>.</p>
</div>
${sections.map((s) => s.html).join("\n")}
</main>
</div>
<script>${SCRIPT}</script>
</body>
</html>
`;
}

const html = await build();
if (consumedInputs.size !== Object.keys(graph.galleryRendering.inputs).length)
  throw new Error("Unused gallery input declaration.");
const outName = graph.galleryRendering.outputs[
  baselineOnly ? "baseline" : "complete"
].target.replace(/^dist\/site\//, "");
const outPath = resolve(outDir, outName);

if (checkOnly) {
  let actual;
  try {
    actual = await readFile(outPath, "utf8");
  } catch {
    process.stderr.write(
      `gallery: dist/site/${outName} missing. Run the matching gallery build.\n`,
    );
    process.exit(1);
  }
  if (actual !== html) {
    process.stderr.write(
      `gallery: dist/site/${outName} is stale. Run the matching gallery build.\n`,
    );
    process.exit(1);
  }
  process.stdout.write(`gallery: verified dist/site/${outName}\n`);
} else {
  await mkdir(outDir, { recursive: true });
  await writeFile(outPath, html);
  process.stdout.write(`gallery: rendered dist/site/${outName}\n`);
}
