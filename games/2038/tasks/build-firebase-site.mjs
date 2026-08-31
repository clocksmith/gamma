import {
  cp,
  mkdir,
  readFile,
  readdir,
  rm,
  stat,
  writeFile
} from "node:fs/promises";
import { execFile } from "node:child_process";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { promisify } from "node:util";
import { loadEraSituationLedger } from "./content/validate-era-situation-ledger.mjs";

const execFileAsync = promisify(execFile);
const projectRoot = resolve(import.meta.dirname, "..");
const gammaRoot = resolve(projectRoot, "../..");
const defaultProfileId = "public-playtest";
const publicBase = "";

export const crawlerMeta = [
  '<meta name="robots" content="noindex, nofollow, noarchive, nosnippet, noimageindex">',
  '<meta name="googlebot" content="noindex, nofollow, noarchive, nosnippet, noimageindex">',
  '<meta name="bingbot" content="noindex, nofollow, noarchive, nosnippet, noimageindex">',
  '<meta name="referrer" content="no-referrer">'
].join("\n");

function publicationBanner(profileId) {
  return profileId === "internal-review"
    ? `<aside class="published-review-notice" role="note">
  Internal review copy. This artifact is not access-controlled and is not approved for public deployment.
</aside>`
    : `<aside class="published-review-notice" role="note">
  Public playtest copy. Deterministic play runs entirely in this browser.
  The private local bridge is optional for Claude and Codex opponents.
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

export function rewritePrototypeHtml(html, { kind, profileId = defaultProfileId }) {
  let rewritten = protectHtml(html)
    .replace(
      "</head>",
      `${staticReviewStyle}\n</head>`
    )
    .replace("<body>", `<body>\n${publicationBanner(profileId)}`)
    .replace(
      profileId === "public-playtest" ? /\s*<a href="\/lab">[^<]*<\/a>/ : /$^/,
      ""
    )
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
  feedbackUrl,
  profileId = defaultProfileId,
  library = false,
  worldCopy = null
}) {
  const title = library
    ? "Mandate 2038 · Supporting material"
    : profileId === "internal-review"
      ? "Mandate 2038 · Internal review"
      : "Mandate 2038 · Public playtest";
  const introduction = library
    ? "Supporting material, playable interfaces, optional rules, specifications, and project records."
    : worldCopy?.box
      ? `${worldCopy.box.frontStrapline} ${worldCopy.box.shortPitch}`
      : "The four documents required to set up and play Default Game.";
  const routeLink = library
    ? '<p><a href="../">Return to Mandate 2038.</a></p>'
    : "";
  const feedbackLink = feedbackUrl
    ? `<p class="feedback"><a href="${escapeHtml(feedbackUrl)}">Send playtest feedback</a></p>`
    : "";
  const worldPrimer = !library && Array.isArray(worldCopy?.worldPrimer)
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
    .feedback { margin-top:2.5rem; }
    .feedback a { color:var(--accent); }
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
  ${routeLink}
  ${feedbackLink}
  <footer>
    Rules <code>${escapeHtml(identity.rulesVersion)}</code> ·
    Executable <code>${escapeHtml(identity.executableVersion)}</code> ·
    Source <code>${escapeHtml(identity.sourceCommit)}</code>
  </footer>
</main>
</body>
</html>`);
}

async function sourceIdentity() {
  const current = JSON.parse(
    await readFile(resolve(projectRoot, "versions/current.json"), "utf8")
  );
  const { stdout } = await execFileAsync("git", ["rev-parse", "HEAD"], {
    cwd: projectRoot
  });
  const { stdout: dirtyOutput } = await execFileAsync(
    "git",
    ["status", "--porcelain", "--", "games/2038", "web", ".gitignore"],
    { cwd: gammaRoot }
  );
  return {
    rulesVersion: current.rulesCandidate.version,
    executableVersion: current.gameVersion,
    sourceCommit: stdout.trim(),
    sourceDirty: Boolean(dirtyOutput.trim()),
    rulesFingerprint: current.rulesCandidate.rulesFingerprint,
    rulesetFingerprint: current.rulesetFingerprint,
    mechanicsFingerprint: current.mechanicsFingerprint
  };
}

async function copyProtectedHtml(source, target) {
  const html = await readFile(source, "utf8");
  await mkdir(dirname(target), { recursive: true });
  await writeFile(target, `${protectHtml(html)}\n`);
}

async function htmlFiles(directory) {
  return (await readdir(directory))
    .filter((name) => name.endsWith(".html"))
    .sort();
}

async function copyCanonicalRuntimeArtifacts(outputRoot, requestedArtifacts) {
  const graph = JSON.parse(
    await readFile(resolve(projectRoot, "content/graph.json"), "utf8")
  );
  const declaredRuntimeTargets = graph.artifacts
    .map((artifact) => artifact.target)
    .filter((target) => /^dist\/runtime\/[^/]+\.json$/.test(target));
  const runtimeTargets = requestedArtifacts.includes("*")
    ? declaredRuntimeTargets
    : requestedArtifacts;
  if (runtimeTargets.length === 0) {
    throw new Error("Content graph declares no publishable runtime artifacts.");
  }
  for (const relative of runtimeTargets) {
    if (!declaredRuntimeTargets.includes(relative)) {
      throw new Error(`Deployment profile references an undeclared runtime artifact: ${relative}`);
    }
  }
  for (const relative of runtimeTargets) {
    const target = resolve(outputRoot, relative);
    await mkdir(dirname(target), { recursive: true });
    await cp(resolve(projectRoot, relative), target);
  }
  return runtimeTargets;
}

function argumentValue(values, name) {
  const index = values.indexOf(name);
  if (index === -1) return undefined;
  if (!values[index + 1]) throw new TypeError(`${name} requires a value.`);
  return values[index + 1];
}

function parseArguments(values) {
  const outputRoot = argumentValue(values, "--output-root");
  return {
    profileId: argumentValue(values, "--profile") || defaultProfileId,
    ...(outputRoot ? { outputRoot: resolve(outputRoot) } : {})
  };
}

async function copyWebSurface(outputRoot, profile) {
  const sourceRoot = resolve(projectRoot, "web");
  const targetRoot = resolve(outputRoot, "web");
  for (const relative of profile.webFiles) {
    const target = resolve(targetRoot, relative);
    await mkdir(dirname(target), { recursive: true });
    await cp(resolve(sourceRoot, relative), target);
  }
}

export async function buildFirebaseSite({ outputRoot, profileId = defaultProfileId } = {}) {
  const ledger = await loadEraSituationLedger();
  const profile = ledger.deploymentProfiles[profileId];
  if (!profile) throw new TypeError(`Unknown deployment profile: ${profileId}`);
  outputRoot = outputRoot || resolve(projectRoot, profile.outputRoot);
  if (outputRoot === gammaRoot || outputRoot === resolve(gammaRoot, "web")) {
    throw new RangeError("Refusing to replace a repository or Firebase web root.");
  }
  for (const required of [
    "dist/site/docs/index.html",
    "dist/site/gallery.html",
    "dist/site/gallery-baseline.html",
    "dist/site/index.html",
    "dist/site/first-game-guide.html",
    "dist/site/simulation.html"
  ]) {
    const file = resolve(projectRoot, required);
    if (!(await stat(file)).isFile()) throw new Error(`Missing generated input: ${required}`);
  }

  await rm(outputRoot, { recursive: true, force: true });
  await mkdir(outputRoot, { recursive: true });
  const identity = await sourceIdentity();
  const pages = [];

  const docsSource = resolve(projectRoot, "dist/site/docs");
  const docsTarget = resolve(outputRoot, "docs");
  const includeAllDocuments = profile.documents.includes("*");
  const defaultGamePlayKit = new Set([
    "core-rules.html",
    "map-reference.html",
    "component-reference.html",
    "card-reference.html"
  ]);
  await mkdir(docsTarget, { recursive: true });
  for (const name of await htmlFiles(docsSource)) {
    if (!includeAllDocuments && !profile.documents.includes(name)) continue;
    await copyProtectedHtml(resolve(docsSource, name), resolve(docsTarget, name));
    const title = name === "index.html"
      ? "Documentation reader"
      : name.replace(/\.html$/, "").split("-").map(
        (word) => word[0].toUpperCase() + word.slice(1)
      ).join(" ");
    pages.push({
      group: defaultGamePlayKit.has(name)
        ? "Required Default Game Play Kit"
        : name === "world-and-institutions.html"
        ? "Learn the game"
        : name === "optional-tactics.html"
          ? "Optional play"
          : name === "component-spec.html" || name === "component-inventory.html"
            ? "Component review"
          : "Development and evidence",
      kind: defaultGamePlayKit.has(name)
        ? "Required play-kit document"
        : name === "index.html"
        ? "Index"
        : name === "component-spec.html" || name === "component-inventory.html"
          ? "Physical specification"
          : "Document",
      title,
      href: `docs/${name}`,
      description: name === "core-rules.html"
        ? "Complete setup, Eras, Actions, and scoring reference."
        : name === "map-reference.html"
          ? "The 19-district jurisdiction, adjacency, movement, and location effects."
          : name === "component-reference.html"
            ? "Every Default Game component, its purpose, and its setup location."
            : name === "card-reference.html"
              ? "Printable canonical faces for every Default Game card type."
        : name === "world-and-institutions.html"
          ? "Setting, tone, Era fiction, and ending narratives."
        : name === "optional-tactics.html"
            ? "An optional module for players who know the Default Play loop."
            : name === "component-spec.html"
              ? "What every physical component is and how its state is made visible."
              : name === "component-inventory.html"
                ? "Default Game box contents and Advanced-only exclusions."
        : "Design, testing, and implementation record."
    });
  }

  for (const [galleryId, sourceName, targetName, title, description] of [
    [
      "complete",
      "gallery.html",
      "gallery.html",
      "Complete content gallery",
      "All baseline and deferred cards with player-facing text and art direction."
    ],
    [
      "baseline",
      "gallery-baseline.html",
      "gallery-baseline.html",
      "Baseline component gallery",
      "Only components used by the controlled physical-test candidate."
    ]
  ]) {
    if (!profile.galleries.includes(galleryId)) continue;
    await copyProtectedHtml(
      resolve(projectRoot, "dist/site", sourceName),
      resolve(outputRoot, targetName)
    );
    pages.push({
      group: "Component review",
      kind: "Gallery",
      title,
      href: targetName,
      description
    });
  }

  await copyWebSurface(outputRoot, profile);
  const prototypeIndex = await readFile(
    resolve(projectRoot, "dist/site/index.html"),
    "utf8"
  );
  const firstGameGuide = await readFile(
    resolve(projectRoot, "dist/site/first-game-guide.html"),
    "utf8"
  );
  await writeFile(
    resolve(outputRoot, "web/index.html"),
    `${rewritePrototypeHtml(prototypeIndex, { kind: "game", profileId })}\n`
  );
  await writeFile(
    resolve(outputRoot, "first-game-guide.html"),
    `${rewritePrototypeHtml(firstGameGuide, { kind: "guide", profileId })}\n`
  );
  const rewrittenModules = profile.webFiles.filter((relative) => relative.endsWith(".js"));
  for (const moduleName of rewrittenModules) {
    const source = await readFile(resolve(projectRoot, "web", moduleName), "utf8");
    await writeFile(
      resolve(outputRoot, "web", moduleName),
      rewritePrototypeModule(source)
    );
  }
  if (profile.interfaces.includes("simulation-lab")) {
    const simulationIndex = await readFile(
      resolve(projectRoot, "dist/site/simulation.html"),
      "utf8"
    );
    await writeFile(
      resolve(outputRoot, "lab.html"),
      `${rewritePrototypeHtml(simulationIndex, { kind: "simulation", profileId })}\n`
    );
  }
  const runtimeArtifacts = await copyCanonicalRuntimeArtifacts(
    outputRoot,
    profile.runtimeArtifacts
  );
  for (const relative of profile.labModules) {
    const target = resolve(outputRoot, "lab", relative);
    await mkdir(dirname(target), { recursive: true });
    await cp(resolve(projectRoot, "lab", relative), target);
  }
  const interfacePages = [];
  if (profile.interfaces.includes("playable-game")) {
    interfacePages.push({
      group: "Start here",
      kind: "Playable interface",
      title: "Play the game",
      href: "web/index.html",
      description: "Play against browser-native deterministic opponents; the local bridge is optional for Claude or Codex."
    });
  }
  if (profile.interfaces.includes("first-game-guide")) {
    interfacePages.push({
      group: "Start here",
      kind: "Teaching interface",
      title: "First Game Guide",
      href: "first-game-guide.html",
      description: "A fixed first-Era Default Play lesson using the canonical game components."
    });
  }
  if (profile.interfaces.includes("simulation-lab")) {
    interfacePages.push({
      group: "Development and evidence",
      kind: "Simulation interface",
      title: "Simulation lab",
      href: "lab.html",
      description: "Run local simulations from the deployed browser or load and replay saved reports."
    });
  }
  pages.unshift(...interfacePages);

  const publishedWorldCopy = JSON.parse(
    await readFile(resolve(projectRoot, "dist/runtime/world-copy.json"), "utf8")
  );
  const rootHtml = buildIndexHtml({
    identity,
    pages,
    feedbackUrl: profile.feedbackUrl,
    profileId,
    worldCopy: publishedWorldCopy
  });
  await writeFile(resolve(outputRoot, "index.html"), `${rootHtml}\n`);
  if (profileId === "internal-review") {
    const libraryPages = pages
      .filter((page) => page.group !== "Required Default Game Play Kit")
      .map((page) => ({ ...page, href: `../${page.href}` }));
    const libraryHtml = buildIndexHtml({
      identity,
      pages: libraryPages,
      feedbackUrl: profile.feedbackUrl,
      profileId,
      library: true,
      worldCopy: publishedWorldCopy
    });
    await mkdir(resolve(outputRoot, "library"), { recursive: true });
    await writeFile(resolve(outputRoot, "library/index.html"), `${libraryHtml}\n`);
  }
  const manifest = {
    schemaVersion: 2,
    artifactKind: profileId === "public-playtest"
      ? "firebase-public-playtest-site"
      : "internal-review-site",
    deploymentProfile: profileId,
    deployable: profile.deployable,
    publicBase,
    identity,
    feedbackUrl: profile.feedbackUrl,
    crawlerPolicy: {
      accessControlled: profile.accessControlled,
      robotsPath: "/robots.txt",
      disallowPath: `${publicBase}/`,
      xRobotsTag: "noindex, nofollow, noarchive, nosnippet, noimageindex",
      limitation: "Crawler directives are voluntary and do not prevent hostile scraping."
    },
    pages,
    runtimeArtifacts,
    webFiles: [...profile.webFiles],
    labModules: [...profile.labModules]
  };
  await writeFile(
    resolve(outputRoot, "release-identity.json"),
    `${JSON.stringify({ schemaVersion: 1, deploymentProfile: profileId, ...identity }, null, 2)}\n`
  );
  await writeFile(resolve(outputRoot, "robots.txt"), "User-agent: *\nDisallow: /\n");
  await writeFile(
    resolve(outputRoot, "site-manifest.json"),
    `${JSON.stringify(manifest, null, 2)}\n`
  );
  return { outputRoot, manifest };
}

const isCli = process.argv[1] &&
  resolve(process.argv[1]) === fileURLToPath(import.meta.url);
if (isCli) {
  const result = await buildFirebaseSite(parseArguments(process.argv.slice(2)));
  process.stdout.write(
    `firebase-site: rendered ${result.manifest.deploymentProfile} with ${result.manifest.pages.length + 1} HTML surfaces to ${result.outputRoot}\n`
  );
}
