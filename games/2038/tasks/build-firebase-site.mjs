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
import { basename, dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { promisify } from "node:util";

const execFileAsync = promisify(execFile);
const projectRoot = resolve(import.meta.dirname, "..");
const gammaRoot = resolve(projectRoot, "../..");
const defaultOutputRoot = resolve(gammaRoot, "web/m3t4-2038");
const publicBase = "/m3t4-2038";

export const crawlerMeta = [
  '<meta name="robots" content="noindex, nofollow, noarchive, nosnippet, noimageindex">',
  '<meta name="googlebot" content="noindex, nofollow, noarchive, nosnippet, noimageindex">',
  '<meta name="bingbot" content="noindex, nofollow, noarchive, nosnippet, noimageindex">',
  '<meta name="referrer" content="no-referrer">'
].join("\n");

const staticReviewBanner = `<aside class="published-review-notice" role="note">
  Published review copy. Deterministic play runs entirely in this browser.
  The private local bridge is optional for Claude, Codex, and server-backed simulations.
</aside>`;

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

export function rewritePrototypeHtml(html, { kind }) {
  let rewritten = protectHtml(html)
    .replace(
      "</head>",
      `${staticReviewStyle}\n</head>`
    )
    .replace("<body>", `<body>\n${staticReviewBanner}`)
    .replaceAll('href="/web/', `href="${publicBase}/web/`)
    .replaceAll('src="/web/', `src="${publicBase}/web/`)
    .replaceAll('href="/docs/', `href="${publicBase}/docs/`)
    .replaceAll('href="/lab"', `href="${publicBase}/lab.html"`);
  if (kind === "simulation") {
    rewritten = rewritten.replace('href="/"', `href="${publicBase}/web/index.html"`);
  }
  return rewritten;
}

export function rewritePrototypeModule(source) {
  return source
    .replaceAll('fetch("/generated/', `fetch("${publicBase}/generated/`)
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
  return `<li>
  <a href="${escapeHtml(page.href)}">${escapeHtml(page.title)}</a>
  <span>${escapeHtml(page.kind)} · ${escapeHtml(page.description)}</span>
</li>`;
}

export function buildIndexHtml({ identity, pages }) {
  return protectHtml(`<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>M3T4 2038 · All pages</title>
  <style>
    :root { color-scheme: dark; --ink:#eeeae0; --muted:#a9afa7; --line:#3b443b; --accent:#e4b553; }
    * { box-sizing: border-box; }
    body { margin:0; background:#121712; color:var(--ink); font:16px/1.5 ui-monospace,SFMono-Regular,Menlo,monospace; }
    main { width:min(760px,calc(100% - 2rem)); margin:0 auto; padding:3rem 0 5rem; }
    h1 { margin:0 0 .5rem; font:700 clamp(2.4rem,8vw,4.5rem)/1 Georgia,serif; }
    p { margin:.5rem 0 2rem; color:var(--muted); }
    ul { margin:0; padding:0; list-style:none; border-top:1px solid var(--line); }
    li { padding:1rem 0; border-bottom:1px solid var(--line); }
    li a { display:inline-block; color:var(--accent); font:700 1.12rem/1.3 Georgia,serif; }
    li a:hover,li a:focus-visible { color:#fff0bd; }
    li span { display:block; margin-top:.25rem; color:var(--muted); font-size:.8rem; }
    footer { margin-top:2.5rem; color:var(--muted); font-size:.72rem; overflow-wrap:anywhere; }
    footer code { color:var(--ink); }
  </style>
</head>
<body>
<main>
  <h1>M3T4 2038</h1>
  <p>Everything currently available:</p>
  <ul class="page-list">
    ${pages.map(pageListItem).join("\n")}
  </ul>
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
    ["status", "--porcelain", "--", "games/frontier-2038", "web", ".gitignore"],
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

function parseArguments(values) {
  const index = values.indexOf("--output-root");
  if (index === -1) return { outputRoot: defaultOutputRoot };
  if (!values[index + 1]) throw new TypeError("--output-root requires a path.");
  return { outputRoot: resolve(values[index + 1]) };
}

export async function buildFirebaseSite({ outputRoot = defaultOutputRoot } = {}) {
  if (outputRoot === gammaRoot || outputRoot === resolve(gammaRoot, "web")) {
    throw new RangeError("Refusing to replace a repository or Firebase web root.");
  }
  for (const required of [
    "build/docs/index.html",
    "build/gallery.html",
    "build/gallery-baseline.html",
    "web/index.html",
    "web/simulation.html"
  ]) {
    const file = resolve(projectRoot, required);
    if (!(await stat(file)).isFile()) throw new Error(`Missing generated input: ${required}`);
  }

  await rm(outputRoot, { recursive: true, force: true });
  await mkdir(outputRoot, { recursive: true });
  const identity = await sourceIdentity();
  const pages = [];

  const docsSource = resolve(projectRoot, "build/docs");
  const docsTarget = resolve(outputRoot, "docs");
  await mkdir(docsTarget, { recursive: true });
  for (const name of await htmlFiles(docsSource)) {
    await copyProtectedHtml(resolve(docsSource, name), resolve(docsTarget, name));
    const title = name === "index.html"
      ? "Documentation reader"
      : name.replace(/\.html$/, "").split("-").map(
        (word) => word[0].toUpperCase() + word.slice(1)
      ).join(" ");
    pages.push({
      group: "Rules and design record",
      kind: name === "index.html" ? "Index" : "Document",
      title,
      href: `docs/${name}`,
      description: name === "core-rules.html"
        ? "How to play the controlled physical-test rules candidate."
        : name === "world-and-institutions.html"
          ? "Setting, tone, Era fiction, and ending narratives."
          : name === "optional-tactics.html"
            ? "The excluded Tactic module’s complete optional rules."
        : "Generated from the canonical Markdown documentation."
    });
  }

  for (const [sourceName, targetName, title, description] of [
    [
      "gallery.html",
      "gallery.html",
      "Complete content gallery",
      "All baseline and deferred cards with player-facing text and art direction."
    ],
    [
      "gallery-baseline.html",
      "gallery-baseline.html",
      "Baseline component gallery",
      "Only components used by the controlled physical-test candidate."
    ]
  ]) {
    await copyProtectedHtml(
      resolve(projectRoot, "build", sourceName),
      resolve(outputRoot, targetName)
    );
    pages.push({
      group: "Component surfaces",
      kind: "Gallery",
      title,
      href: targetName,
      description
    });
  }

  await cp(resolve(projectRoot, "web"), resolve(outputRoot, "web"), {
    recursive: true
  });
  await rm(resolve(outputRoot, "web/simulation.html"));
  const prototypeIndex = await readFile(
    resolve(projectRoot, "web/index.html"),
    "utf8"
  );
  const simulationIndex = await readFile(
    resolve(projectRoot, "web/simulation.html"),
    "utf8"
  );
  await writeFile(
    resolve(outputRoot, "web/index.html"),
    `${rewritePrototypeHtml(prototypeIndex, { kind: "game" })}\n`
  );
  await writeFile(
    resolve(outputRoot, "lab.html"),
    `${rewritePrototypeHtml(simulationIndex, { kind: "simulation" })}\n`
  );
  for (const moduleName of ["app.js", "simulation-app.js"]) {
    const source = await readFile(resolve(projectRoot, "web", moduleName), "utf8");
    await writeFile(
      resolve(outputRoot, "web", moduleName),
      rewritePrototypeModule(source)
    );
  }
  await cp(resolve(projectRoot, "generated"), resolve(outputRoot, "generated"), {
    recursive: true
  });
  const publishedSimulationModules = [
    "content/simulation-copy.js",
    "contracts/decision-contract.js",
    "contracts/report-migrations.js",
    "environment/core-economy-match.js",
    "environment/rules-variant.js",
    "environment/selected-rules-match.js",
    "personas/player-profile.js",
    "policies/weighted-policy.js",
    "rules/declaration-readiness.js",
    "runtime/create-browser-interactive-game.js",
    "runtime/interactive-game-core.js"
  ];
  for (const relative of publishedSimulationModules) {
    const target = resolve(outputRoot, "lab", relative);
    await mkdir(dirname(target), { recursive: true });
    await cp(resolve(projectRoot, "lab", relative), target);
  }
  pages.unshift(
    {
      group: "Executable review surfaces",
      kind: "Playable interface",
      title: "Play the game",
      href: "web/index.html",
      description: "Play against browser-native deterministic opponents; the local bridge is optional for Claude or Codex."
    },
    {
      group: "Executable review surfaces",
      kind: "Simulation interface",
      title: "Simulation lab",
      href: "lab.html",
      description: "Run local simulations from the deployed browser or load and replay saved reports."
    }
  );

  const indexHtml = buildIndexHtml({ identity, pages });
  await writeFile(resolve(outputRoot, "index.html"), `${indexHtml}\n`);
  const manifest = {
    schemaVersion: 1,
    artifactKind: "firebase-static-review-site",
    publicBase,
    identity,
    crawlerPolicy: {
      accessControlled: false,
      robotsPath: "/robots.txt",
      disallowPath: `${publicBase}/`,
      xRobotsTag: "noindex, nofollow, noarchive, nosnippet, noimageindex",
      limitation: "Crawler directives are voluntary and do not prevent hostile scraping."
    },
    pages
  };
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
    `firebase-site: rendered ${result.manifest.pages.length + 1} HTML surfaces to ${result.outputRoot}\n`
  );
}
