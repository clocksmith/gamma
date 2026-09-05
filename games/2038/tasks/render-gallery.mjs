// Renders a single browsable "component gallery" of all Mandate 2038 game
// content: factions, actions, eras, headlines, mandates, escalations, power
// sources, tactics, specialists, secret objectives, and reference cards.
//
// Every card shows its rendered player-facing text from dist/runtime/*.json.
// Output lands in dist/site/ (gitignored) and is served at /gallery by
// tasks/serve.mjs.

import { mkdir, readFile, writeFile } from "node:fs/promises";
import { resolve } from "node:path";

const projectRoot = resolve(import.meta.dirname, "..");
const dataDir = resolve(projectRoot, "dist/runtime");
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
  return JSON.parse(await readFile(resolve(dataDir, `${name}.json`), "utf8"));
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
      const label = row.label ? `<span class="field-label">${escapeHtml(row.label)}</span>` : "";
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

function card({ accent, title, subtitle, badgeList = [], bodyHtml = "", tagList }) {
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

function buildFactions(data) {
  const cards = data.factions
    .map((f) => {
      const stats = f.starts
        ? `<dl class="stats">${Object.entries(f.starts)
            .map(([k, v]) => `<div><dt>${escapeHtml(k)}</dt><dd>${escapeHtml(v)}</dd></div>`)
            .join("")}</dl>`
        : "";
      const abilities = (f.abilities || [])
        .map(
          (a) => `<div class="ability">
<div class="ability-head"><strong>${escapeHtml(a.displayName || a.name)}</strong>${badges([roundBadge(a.round), timingBadge(a.timing)])}</div>
${a.displayName && a.displayName !== a.name ? `<p class="mech-name">${escapeHtml(a.name)}</p>` : ""}
<p class="rules">${escapeHtml(a.text)}</p>
${a.flavorText ? `<p class="flavor">${escapeHtml(a.flavorText)}</p>` : ""}
</div>`
        )
        .join("");
      const scoringRule = f.scoringRule
        ? `<div class="ability scoring-contract">
<div class="ability-head"><strong>${escapeHtml(f.scoringRule.name)}</strong>${badges(["scoring contract", timingBadge(f.scoringRule.timing)])}</div>
<p class="rules">${escapeHtml(f.scoringRule.text)}</p>
${f.scoringRule.flavorText ? `<p class="flavor">${escapeHtml(f.scoringRule.flavorText)}</p>` : ""}
</div>`
        : "";
      const body = `${f.motto ? `<p class="flavor motto">“${escapeHtml(f.motto)}”</p>` : ""}
${textRows([
        { label: "Promise", text: f.publicPromise },
        { label: "Anxiety", text: f.privateAnxiety, kind: "flavor" },
        { text: f.introduction }
      ])}
${stats}
${scoringRule}
<div class="abilities"><span class="field-label">Abilities</span>${abilities}</div>`;
      return card({
        accent: f.color,
        title: f.name,
        subtitle: f.role,
        badgeList: [f.color ? "faction" : ""],
        bodyHtml: body
      });
    })
    .join("");
  return section("factions", "Factions", data.factions.length, cards, "Asymmetric institutions with starting resources and per-Era abilities.");
}

function formatTurnContract(tc) {
  if (!tc || typeof tc !== "object") return tc || "";
  const parts = [];
  if (tc.cost) parts.push(`Cost: ${tc.cost}`);
  if (Array.isArray(tc.modes) && tc.modes.length) parts.push(`Modes: ${tc.modes.join(", ")}`);
  if (tc.risk) parts.push(`Risk: ${tc.risk}`);
  return parts.join(" · ");
}

function buildActions(config) {
  const cards = config.actions
    .map((a) =>
      card({
        title: a.name,
        subtitle: a.slogan,
        badgeList: ["Core Action", a.initiativeName ? `Initiative: ${a.initiativeName}` : ""],
        bodyHtml: textRows([
          { text: a.summary },
          { label: "Turn contract", text: formatTurnContract(a.turnContract) },
          { text: a.flavorText, kind: "flavor" }
        ])
      })
    )
    .join("");
  return section("actions", "Core Actions", config.actions.length, cards, "The six institutional functions; each player uses three per Era.");
}

function buildRounds(config, reference) {
  const erasByRound = new Map((reference.eraCards || []).map((era) => [era.round, era]));
  const cards = config.rounds
    .map((r) => {
      const era = erasByRound.get(r.number);
      return (
      card({
        title: `${roman[r.number] || r.number}. ${era?.name || r.name}`,
        subtitle: era?.strapline,
        badgeList: [
          `${r.cycles} cycles`,
          `Audit base ${r.auditBaseDraws}`,
          `${r.escalationAvailability} escalation availability`
        ],
        bodyHtml: `${textRows([{ text: era?.loreText, kind: "flavor" }])}
${listRows("New this era", era?.unlockText ? [era.unlockText] : [])}
${listRows("Escalation actions", r.escalations)}`
      })
      );
    })
    .join("");
  return section("rounds", "Eras", config.rounds.length, cards, "The four-Era escalation from Progress to Continuity.");
}

function buildHeadlines(data) {
  const cards = data.headlines
    .map((h) =>
      card({
        title: h.name,
        subtitle: h.strapline,
        badgeList: [
          roundBadge(h.round),
        ],
        bodyHtml: `${textRows([
          { text: h.newswire, kind: "flavor" },
          { text: h.text, kind: "rules" },
          { text: h.quote ? `“${h.quote}”` : "", kind: "flavor quote" }
        ])}`,
        tagList: h.regimeTags
      })
    )
    .join("");
  return section("headlines", "Headlines", data.headlines.length, cards, "Sixteen Headlines, in Era packets of five, four, three, and four. Reveal three per Era.");
}

function buildMandates(data) {
  const cards = data.mandates
    .map((m) =>
      card({
        title: m.name,
        badgeList: [eraBadge(m.era), `min ${m.minimumQualification}`],
        bodyHtml: textRows([
          { text: m.rulesText, kind: "rules" },
          { text: m.flavorText, kind: "flavor" }
        ]),
        tagList: m.mechanicalTags
      })
    )
    .join("");
  return section("mandates", "Era Mandates", data.mandates.length, cards, "Per-Era scoring races; the qualifying leader scores.");
}

function buildEscalations(data) {
  const cards = data.escalations
    .map((w) =>
      card({
        title: w.displayName || w.name,
        subtitle: w.displayName && w.displayName !== w.name ? w.name : "",
        badgeList: [roundBadge(w.unlockedRound), timingBadge(w.timing)],
        bodyHtml: textRows([
          { text: w.text, kind: "rules" },
          { text: w.flavorText, kind: "flavor" }
        ])
      })
    )
    .join("");
  return section("escalations", "Escalations", data.escalations.length, cards, "Once-per-game escalation plays unlocked by era.");
}

function buildPowerSources(config) {
  const cards = config.powerSources
    .map((p) =>
      card({
        title: p.name,
        subtitle: p.tagline,
        badgeList: [
          p.round ? roundBadge(p.round) : "",
          p.id === "clean_infrastructure"
            ? "Renewable tile"
            : p.id === "emergency_infrastructure"
              ? "Grid tile"
              : "Fusion Escalation",
          `${p.runwayCost} Runway`,
          `${p.capacity} Power`
        ],
        bodyHtml: textRows([
          { text: p.rulesText, kind: "rules" },
          { label: "Public claim", text: p.publicClaim },
          { text: [p.scrutinyPerUse ? `Scrutiny/Production: ${p.scrutinyPerUse}` : "", p.trust ? `Trust: ${p.trust}` : ""].filter(Boolean).join(" · ") }
        ])
      })
    )
    .join("");
  return section("power", "Embedded Power Contracts", config.powerSources.length, cards, "Printed on the two Energy tiles and the Fusion Escalation; no separate reference cards.");
}

function buildTactics(data) {
  const cards = data.tactics
    .map((t) =>
      card({
        title: t.displayName || t.name,
        subtitle: t.displayName && t.displayName !== t.name ? t.name : t.technology,
        badgeList: ["Deferred module"],
        bodyHtml: textRows([
          { text: t.text, kind: "rules" },
          { text: t.flavorText, kind: "flavor" }
        ])
      })
    )
    .join("");
  return section("tactics", "Tactics (deferred)", data.tactics.length, cards, "Optional development module; excluded from baseline balance.");
}

function buildSpecialists(data) {
  const cards = data.specialists
    .map((s) =>
      card({
        title: s.name,
        subtitle: s.title,
        badgeList: ["Reserve"],
        bodyHtml: textRows([
          { text: s.flavorText, kind: "flavor" }
        ])
      })
    )
    .join("");
  return section("specialists", "Reserve Specialists", data.specialists.length, cards, "Design-reserve identities not promoted to full factions.");
}

function buildObjectives(data) {
  const cards = data.objectives
    .map((o) =>
      card({
        title: o.name,
        badgeList: ["Deferred module"],
        bodyHtml: textRows([
          { text: o.rulesText, kind: "rules" },
          { text: o.flavorText, kind: "flavor" }
        ]),
        tagList: o.mechanicalTags
      })
    )
    .join("");
  return section("objectives", "Secret Objectives (deferred)", data.objectives.length, cards, "Optional module; not used in baseline scoring.");
}

function buildReferenceCards(data) {
  const eras = (data.eraCards || []).map((c) =>
    card({
      title: c.name,
      subtitle: c.strapline,
      badgeList: [roundBadge(c.round), "Governance Board panel"],
      bodyHtml: textRows([
        { text: c.rulesText, kind: "rules" },
        { label: "Unlocks", text: c.unlockText }
      ])
    })
  );
  const refs = (data.playerReferences || []).map((c) =>
    card({
      title: c.name,
      badgeList: ["Player aid"],
      bodyHtml: `${listRows("Front", c.frontText)}${listRows("Back", c.backText)}`
    })
  );
  const all = [...eras, ...refs].join("");
  return section("reference", "Board Panels and Player Aids", eras.length + refs.length, all, "Four printed Era panels and the four topics repeated on each foldout player aid.");
}

// --- page assembly -----------------------------------------------------------

const STYLE = `:root { color-scheme: light dark; --accent: #64748b; }
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
  const [factions, config, headlines, mandates, escalation, tactics, specialists, objectives, reference] =
    await Promise.all([
      readData("factions"),
      readData("game-config"),
      readData("headlines"),
      readData("mandates"),
      readData("escalations"),
      readData("tactics"),
      readData("reserve-specialists"),
      readData("secret-objectives"),
      readData("reference-cards")
    ]);

  const allSections = [
    { id: "factions", label: "Factions", html: buildFactions(factions), n: factions.factions.length },
    { id: "actions", label: "Core Actions", html: buildActions(config), n: config.actions.length },
    { id: "rounds", label: "Eras", html: buildRounds(config, reference), n: config.rounds.length },
    { id: "headlines", label: "Headlines", html: buildHeadlines(headlines), n: headlines.headlines.length },
    { id: "mandates", label: "Era Mandates", html: buildMandates(mandates), n: mandates.mandates.length },
    { id: "escalations", label: "Escalations", html: buildEscalations(escalation), n: escalation.escalations.length },
    { id: "power", label: "Embedded Power Contracts", html: buildPowerSources(config), n: config.powerSources.length },
    { id: "reference", label: "Board Panels and Player Aids", html: buildReferenceCards(reference), n: (reference.eraCards || []).length + (reference.playerReferences || []).length },
    { id: "tactics", label: "Tactics", html: buildTactics(tactics), n: tactics.tactics.length },
    { id: "objectives", label: "Secret Objectives", html: buildObjectives(objectives), n: objectives.objectives.length },
    { id: "specialists", label: "Reserve Specialists", html: buildSpecialists(specialists), n: specialists.specialists.length }
  ];
  const deferredIds = new Set(["tactics", "objectives", "specialists"]);
  const sections = baselineOnly
    ? allSections.filter((section) => !deferredIds.has(section.id))
    : allSections;

  const total = sections.reduce((sum, s) => sum + s.n, 0);
  const navLinks = sections
    .map((s) => `<a href="#${s.id}">${escapeHtml(s.label)}<span class="n">${s.n}</span></a>`)
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
const outName = baselineOnly ? "gallery-baseline.html" : "gallery.html";
const outPath = resolve(outDir, outName);

if (checkOnly) {
  let actual;
  try {
    actual = await readFile(outPath, "utf8");
  } catch {
    process.stderr.write(`gallery: dist/site/${outName} missing. Run the matching gallery build.\n`);
    process.exit(1);
  }
  if (actual !== html) {
    process.stderr.write(`gallery: dist/site/${outName} is stale. Run the matching gallery build.\n`);
    process.exit(1);
  }
  process.stdout.write(`gallery: verified dist/site/${outName}\n`);
} else {
  await mkdir(outDir, { recursive: true });
  await writeFile(outPath, html);
  process.stdout.write(`gallery: rendered dist/site/${outName}\n`);
}
