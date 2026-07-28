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
  Published review copy. For live play or simulations, run <code>npm run dev</code>
  locally and pair this page with the private token printed by Node.
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
    .replaceAll('href="/prototype/', `href="${publicBase}/prototype/`)
    .replaceAll('src="/prototype/', `src="${publicBase}/prototype/`)
    .replaceAll('href="/docs/', `href="${publicBase}/docs/`)
    .replaceAll('href="/lab"', `href="${publicBase}/lab.html"`);
  if (kind === "simulation") {
    rewritten = rewritten.replace('href="/"', `href="${publicBase}/prototype/index.html"`);
  }
  return rewritten;
}

export function rewritePrototypeModule(source) {
  return source
    .replaceAll('fetch("/data/', `fetch("${publicBase}/data/`)
    .replaceAll('from "/simulation/', `from "${publicBase}/simulation/`);
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

function pageCard(page) {
  return `<a class="surface" href="${escapeHtml(page.href)}">
  <span class="kind">${escapeHtml(page.kind)}</span>
  <strong>${escapeHtml(page.title)}</strong>
  <span>${escapeHtml(page.description)}</span>
</a>`;
}

export function buildIndexHtml({ identity, pages }) {
  const grouped = Map.groupBy(pages, (page) => page.group);
  const sections = [...grouped].map(([group, groupPages]) => `<section>
  <h2>${escapeHtml(group)}</h2>
  <div class="surfaces">${groupPages.map(pageCard).join("\n")}</div>
</section>`).join("\n");
  return protectHtml(`<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>M3T4 2038 · controlled review index</title>
  <style>
    :root { color-scheme: dark; --paper:#eee3c5; --ink:#e8e4d6; --muted:#a7a99f; --line:#40483f; --accent:#d3a74e; }
    * { box-sizing: border-box; }
    body { margin:0; background:#121712; color:var(--ink); font:16px/1.55 ui-monospace,SFMono-Regular,Menlo,monospace; }
    main { width:min(1120px,calc(100% - 2rem)); margin:0 auto; padding:4rem 0 6rem; }
    .eyebrow,.kind { color:var(--accent); text-transform:uppercase; letter-spacing:.12em; font-size:.72rem; }
    h1 { max-width:12ch; margin:.35rem 0 1rem; font:700 clamp(3rem,9vw,7.5rem)/.86 Georgia,serif; letter-spacing:-.055em; }
    .lede { max-width:72ch; color:#c5c6bc; font-size:1.05rem; }
    .identity { display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:1px; margin:2rem 0 3.5rem; border:1px solid var(--line); background:var(--line); }
    .identity div { min-width:0; padding:1rem; background:#192019; }
    .identity span { display:block; color:var(--muted); font-size:.7rem; text-transform:uppercase; letter-spacing:.08em; }
    .identity code { display:block; overflow-wrap:anywhere; color:var(--paper); }
    section { margin:3rem 0; }
    h2 { padding-bottom:.7rem; border-bottom:1px solid var(--line); font:700 1.3rem Georgia,serif; }
    .surfaces { display:grid; grid-template-columns:repeat(auto-fit,minmax(250px,1fr)); gap:.8rem; }
    .surface { display:flex; min-height:158px; flex-direction:column; gap:.5rem; padding:1rem; border:1px solid var(--line); background:#181e18; color:inherit; text-decoration:none; }
    .surface:hover,.surface:focus-visible { border-color:var(--accent); background:#202820; outline:none; }
    .surface strong { font:700 1.2rem/1.15 Georgia,serif; }
    .surface span:last-child { color:var(--muted); font-size:.84rem; }
    footer { margin-top:4rem; padding-top:1rem; border-top:1px solid var(--line); color:var(--muted); font-size:.75rem; }
    @media(max-width:700px) { main{padding-top:2rem}.identity{grid-template-columns:1fr} }
  </style>
</head>
<body>
<main>
  <p class="eyebrow">Controlled physical-candidate review</p>
  <h1>M3T4 2038</h1>
  <p class="lede">An index of every published HTML review surface generated from the same semantic game graph. This public URL is intentionally excluded from cooperative search, archive, and AI crawler discovery. It is not access-controlled.</p>
  <div class="identity">
    <div><span>Rules</span><code>${escapeHtml(identity.rulesVersion)}</code></div>
    <div><span>Executable</span><code>${escapeHtml(identity.executableVersion)}</code></div>
    <div><span>Source</span><code>${escapeHtml(identity.sourceCommit)}</code></div>
  </div>
  ${sections}
  <footer>Generated review artifact · no final art · execution uses an explicitly paired localhost bridge</footer>
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
    "dist/docs/index.html",
    "dist/gallery.html",
    "dist/gallery-baseline.html",
    "prototype/index.html",
    "prototype/simulation.html"
  ]) {
    const file = resolve(projectRoot, required);
    if (!(await stat(file)).isFile()) throw new Error(`Missing generated input: ${required}`);
  }

  await rm(outputRoot, { recursive: true, force: true });
  await mkdir(outputRoot, { recursive: true });
  const identity = await sourceIdentity();
  const pages = [];

  const docsSource = resolve(projectRoot, "dist/docs");
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
        ? "The complete controlled physical-test rules candidate."
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
      resolve(projectRoot, "dist", sourceName),
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

  await cp(resolve(projectRoot, "prototype"), resolve(outputRoot, "prototype"), {
    recursive: true
  });
  await rm(resolve(outputRoot, "prototype/simulation.html"));
  const prototypeIndex = await readFile(
    resolve(projectRoot, "prototype/index.html"),
    "utf8"
  );
  const simulationIndex = await readFile(
    resolve(projectRoot, "prototype/simulation.html"),
    "utf8"
  );
  await writeFile(
    resolve(outputRoot, "prototype/index.html"),
    `${rewritePrototypeHtml(prototypeIndex, { kind: "game" })}\n`
  );
  await writeFile(
    resolve(outputRoot, "lab.html"),
    `${rewritePrototypeHtml(simulationIndex, { kind: "simulation" })}\n`
  );
  for (const moduleName of ["app.js", "simulation-app.js"]) {
    const source = await readFile(resolve(projectRoot, "prototype", moduleName), "utf8");
    await writeFile(
      resolve(outputRoot, "prototype", moduleName),
      rewritePrototypeModule(source)
    );
  }
  await cp(resolve(projectRoot, "data"), resolve(outputRoot, "data"), {
    recursive: true
  });
  await mkdir(resolve(outputRoot, "simulation/contracts"), { recursive: true });
  await cp(
    resolve(projectRoot, "simulation/contracts/report-migrations.js"),
    resolve(outputRoot, "simulation/contracts/report-migrations.js")
  );
  pages.unshift(
    {
      group: "Executable review surfaces",
      kind: "Playable interface",
      title: "Rules prototype",
      href: "prototype/index.html",
      description: "Play in the deployed browser through an explicitly paired local Node bridge."
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
