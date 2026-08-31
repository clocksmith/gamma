import { resolve } from "node:path";
import { fileURLToPath } from "node:url";

const publicBase = "";

export const crawlerMeta = [
  '<meta name="robots" content="noindex, nofollow, noarchive, nosnippet, noimageindex">',
  '<meta name="googlebot" content="noindex, nofollow, noarchive, nosnippet, noimageindex">',
  '<meta name="bingbot" content="noindex, nofollow, noarchive, nosnippet, noimageindex">',
  '<meta name="referrer" content="no-referrer">'
].join("\n");

function reviewBanner(profileId) {
  const message = profileId === "internal-review"
    ? "Internal review copy. This local artifact includes development evidence and simulation tools and is not deployable."
    : "Public playtest copy. Deterministic play runs entirely in this browser. The private local bridge is optional for Claude or Codex; internal review material is not included.";
  return `<aside class="published-review-notice" role="note">
  ${message}
</aside>`;
}

const staticReviewStyle = `<style>
.published-review-notice {
  margin: 0;
  padding: .72rem 1rem;
  border-bottom: 1px solid rgba(185, 146, 68, .55);
  background: #fff4cf;
  color: #3d321c;
  font: 600 13px/1.45 ui-monospace, SFMono-Regular, Menlo, monospace;
}
.published-review-notice code { font: inherit; }
</style>`;

export function protectHtml(html) {
  if (!html.includes("<head>")) {
    throw new TypeError("Published HTML must contain a <head> element.");
  }
  return html.replace("<head>", `<head>\n${crawlerMeta}`);
}

export function rewritePrototypeHtml(
  html,
  { kind, profileId = "public-playtest" } = {}
) {
  const profileHtml = profileId === "public-playtest"
    ? html.replace(/\s*<a href="\/lab">[^<]*<\/a>/g, "")
    : html;
  let rewritten = protectHtml(profileHtml)
    .replace("</head>", `${staticReviewStyle}\n</head>`)
    .replace("<body>", `<body>\n${reviewBanner(profileId)}`)
    .replaceAll('href="/web/', `href="${publicBase}/web/`)
    .replaceAll('src="/web/', `src="${publicBase}/web/`)
    .replaceAll('href="/docs/', `href="${publicBase}/docs/`)
    .replaceAll('href="/lab"', `href="${publicBase}/lab.html"`)
    .replaceAll('href="/first-game-guide"', `href="${publicBase}/first-game-guide.html"`)
    .replaceAll('src="/?guide=first-game"', `src="${publicBase}/web/index.html?guide=first-game"`)
    .replaceAll('href="/?guide=first-game"', `href="${publicBase}/web/index.html?guide=first-game"`)
    .replaceAll('"/?guide=first-game"', `"${publicBase}/web/index.html?guide=first-game"`);
  if (kind === "simulation" || kind === "guide") {
    rewritten = rewritten.replace('href="/"', `href="${publicBase}/web/index.html"`);
  }
  return rewritten;
}

export function rewritePrototypeModule(source) {
  return source
    .replaceAll('fetch("/dist/runtime/', `fetch("${publicBase}/dist/runtime/`)
    .replaceAll('from "/lab/', `from "${publicBase}/lab/`);
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

function pageListItem(page) {
  const className = page.kind === "Playable interface"
    ? ' class="primary-action"'
    : "";
  return `<li${className}>
  <a href="${escapeHtml(page.href)}">${escapeHtml(page.title)}</a>
  <span>${escapeHtml(page.kind)} · ${escapeHtml(page.description)}</span>
</li>`;
}

const publicGroupOrder = [
  "Start here",
  "Required Default Game Play Kit",
  "Learn the game",
  "Optional play",
  "Development and evidence",
  "Component review"
];

const defaultGamePlayKitOrder = new Map([
  ["Core Rules", 0],
  ["Map Reference", 1],
  ["Component Reference", 2],
  ["Card and Board Reference", 3]
]);

function renderPageGroups(pages) {
  const grouped = new Map(publicGroupOrder.map((group) => [group, []]));
  for (const page of pages) {
    const group = grouped.has(page.group)
      ? page.group
      : "Development and evidence";
    grouped.get(group).push(page);
  }
  return publicGroupOrder
    .filter((group) => grouped.get(group).length)
    .map((group) => {
      const entries = grouped.get(group);
      if (group === "Required Default Game Play Kit") {
        entries.sort((left, right) =>
          defaultGamePlayKitOrder.get(left.title) -
            defaultGamePlayKitOrder.get(right.title)
        );
      }
      return `<section class="page-group"><h2>${escapeHtml(group)}</h2><ul class="page-list">
${entries.map(pageListItem).join("\n")}
</ul></section>`;
    })
    .join("\n");
}

export function buildIndexHtml({
  identity,
  pages,
  profileId = "public-playtest",
  worldCopy = null
}) {
  const internal = profileId === "internal-review";
  const title = internal
    ? "Mandate 2038 · Internal review"
    : "Mandate 2038 · Public playtest";
  const introduction = worldCopy?.box
    ? `${worldCopy.box.frontStrapline} ${worldCopy.box.shortPitch}`
    : internal
      ? "Local review material, evidence, and simulation tools."
      : "The playable public test and its required supporting material.";
  const worldPrimer = Array.isArray(worldCopy?.worldPrimer)
    ? `<section class="world-primer" aria-labelledby="world-primer-title">
  <h2 id="world-primer-title">The world of 2038</h2>
  ${worldCopy.worldPrimer.map((paragraph) =>
    `<p>${escapeHtml(paragraph)}</p>`
  ).join("\n  ")}
</section>`
    : "";
  return protectHtml(`<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <link rel="icon" href="/web/favicon.svg" type="image/svg+xml">
  <title>${title}</title>
  <style>
    :root { color-scheme: dark; --ink:#eeeae0; --muted:#a9afa7; --line:#3b443b; --accent:#e4b553; }
    * { box-sizing: border-box; }
    body { margin:0; background:#121712; color:var(--ink); font:16px/1.5 ui-monospace,SFMono-Regular,Menlo,monospace; }
    main { width:min(760px,calc(100% - 2rem)); margin:0 auto; padding:3rem 0 5rem; }
    h1 { margin:0 0 .5rem; font:700 clamp(2.4rem,8vw,4.5rem)/1 Georgia,serif; }
    h2 { margin:2.5rem 0 .7rem; color:var(--accent); font:700 1rem/1.2 ui-monospace,SFMono-Regular,Menlo,monospace; letter-spacing:.08em; text-transform:uppercase; }
    p { margin:.5rem 0 2rem; color:var(--muted); }
    ul { margin:0; padding:0; list-style:none; border-top:1px solid var(--line); }
    li { padding:1rem 0; border-bottom:1px solid var(--line); }
    li a { display:inline-block; color:var(--accent); font:700 1.12rem/1.3 Georgia,serif; }
    li a:hover,li a:focus-visible { color:#fff0bd; }
    li span { display:block; margin-top:.25rem; color:var(--muted); font-size:.8rem; }
    li.primary-action { margin:.75rem 0; padding:1.2rem; border:1px solid var(--accent); background:rgba(228,181,83,.08); }
    li.primary-action a { font-size:1.5rem; }
    .world-primer { margin-top:3rem; padding-top:.5rem; border-top:1px solid var(--line); }
    .world-primer p { margin:.65rem 0; color:var(--muted); }
    footer { margin-top:2.5rem; color:var(--muted); font-size:.72rem; overflow-wrap:anywhere; }
    footer code { color:var(--ink); }
  </style>
</head>
<body>
<main>
  <h1>Mandate 2038</h1>
  <p>${introduction}</p>
  ${renderPageGroups(pages)}
  ${worldPrimer}
  <footer>
    Rules <code>${escapeHtml(identity.rulesVersion)}</code> ·
    Executable <code>${escapeHtml(identity.executableVersion)}</code> ·
    Source <code>${escapeHtml(identity.sourceCommit)}</code>
  </footer>
</main>
</body>
</html>`);
}

export async function buildFirebaseSite(options = {}) {
  const { buildProfiledFirebaseSite } = await import("./firebase-site-profile.mjs");
  return buildProfiledFirebaseSite(options, {
    buildIndexHtml,
    protectHtml,
    rewritePrototypeHtml,
    rewritePrototypeModule
  });
}

const isCli = process.argv[1] &&
  resolve(process.argv[1]) === fileURLToPath(import.meta.url);
if (isCli) {
  const { parseFirebaseSiteArguments } = await import("./firebase-site-profile.mjs");
  const result = await buildFirebaseSite(
    parseFirebaseSiteArguments(process.argv.slice(2))
  );
  process.stdout.write(
    `firebase-site: rendered ${result.manifest.pages.length + 1} HTML surfaces ` +
      `for ${result.manifest.profileId} to ${result.outputRoot}\n`
  );
}
