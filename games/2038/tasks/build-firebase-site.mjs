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
import { verifyRelease } from "./release-artifacts.mjs";
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
  return `<li><a href="${escapeHtml(page.href)}">${escapeHtml(page.title)}</a></li>`;
}

export function buildIndexHtml({
  pages,
  sources = [],
  feedbackUrl,
  profileId = defaultProfileId,
  library = false
}) {
  const title = library
    ? "Mandate 2038 · Supporting material"
    : profileId === "internal-review"
      ? "Mandate 2038 · Internal review"
      : "Mandate 2038";
  const links = [...pages];
  if (library) links.push({ href: "../", title: "Return to Mandate 2038" });
  if (feedbackUrl) links.push({ href: feedbackUrl, title: "Send playtest feedback" });
  return protectHtml(`<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <link rel="icon" href="/web/favicon.svg" type="image/svg+xml">
  <title>${title}</title>
  <style>
    :root { color-scheme: light; }
    * { box-sizing: border-box; }
    body { margin:0; background:#fff url("/web/hex-background.svg") repeat; color:#111; font:18px/1.6 system-ui,sans-serif; }
    main { max-width:42rem; margin:0 auto; padding:clamp(1.5rem,6vw,4rem) 1.25rem; }
    h1 { margin:0 0 1.5rem; font-size:clamp(1.8rem,6vw,2.4rem); line-height:1.2; }
    h2 { margin:2.5rem 0 .75rem; font-size:1.15rem; }
    .sources a { font-size:.9rem; color:#444; }
    ul { margin:0; padding:0; list-style:none; }
    li { margin:0; }
    a { display:block; width:fit-content; max-width:100%; padding:.5rem 0; color:inherit; text-underline-offset:.2em; overflow-wrap:anywhere; }
    a:hover { text-decoration-thickness:2px; }
    a:focus-visible { outline:2px solid currentColor; outline-offset:4px; }
  </style>
</head>
<body>
<main>
  <h1>Mandate 2038</h1>
  <ul>
${links.map(pageListItem).join("\n")}
  </ul>
${sources.length ? `<section class="sources" aria-labelledby="sources-title"><h2 id="sources-title">Sources</h2><ul>${sources.map(pageListItem).join("\n")}</ul></section>` : ""}
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
  const graph = JSON.parse(await readFile(resolve(projectRoot, "content/graph.json"), "utf8"));
  const ledger = await loadEraSituationLedger();
  const profile = ledger.deploymentProfiles[profileId];
  if (!profile) throw new TypeError(`Unknown deployment profile: ${profileId}`);
  if (profile.deployable) await verifyRelease(projectRoot);
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

  const includeAllDocuments = profile.documents.includes("*");
  for (const group of graph.documentRendering) {
    if (group.audience !== "player" && !includeAllDocuments) continue;
    const prefix = group.target.replace(/^dist\/site\//, "");
    const sourceRoot = resolve(projectRoot, group.target);
    for (const name of await htmlFiles(sourceRoot)) {
      if (!includeAllDocuments && !profile.documents.includes(name)) continue;
      await copyProtectedHtml(resolve(sourceRoot, name), resolve(outputRoot, prefix, name));
      pages.push({group:group.audience === "player" ? "Required Play Kit" : "Development and evidence",
        kind:name === "index.html" ? "Index" : "Document",
        title:name.replace(/\.html$/, "").split("-").map(word => word[0].toUpperCase()+word.slice(1)).join(" "),
        href:`${prefix}/${name}`, description:""});
    }
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
  for (const id of profile.interfaces) {
    const item = graph.interfaceArtifacts[id];
    if (!item) throw new Error(`Undeclared interface: ${id}`);
    const html = await readFile(resolve(projectRoot, item.source), "utf8");
    await mkdir(dirname(resolve(outputRoot, item.target)), {recursive:true});
    await writeFile(resolve(outputRoot, item.target), `${rewritePrototypeHtml(html, {kind:item.kind, profileId})}\n`);
  }
  const rewrittenModules = profile.webFiles.filter((relative) => relative.endsWith(".js"));
  for (const moduleName of rewrittenModules) {
    const source = await readFile(resolve(projectRoot, "web", moduleName), "utf8");
    await writeFile(
      resolve(outputRoot, "web", moduleName),
      rewritePrototypeModule(source)
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
  const interfacePages = profile.interfaces.map(id => ({
    group:"Start here", kind:"Interface", title:graph.interfaceArtifacts[id].title,
    href:graph.interfaceArtifacts[id].target, description:""
  }));
  pages.unshift(...interfacePages);

  const sources = [];
  for (const entry of profile.sourceFiles || []) {
    // Public source access is limited to mechanical data and interface/rule copy.
    // The author bible, internal notes and experimental sources are never copied.
    if (!/^(rules\.md|ui\.json|content\/data\/variables\.json|components\/(game|factions|headlines|mandates|projects|reference-cards)\.json)$/.test(entry.source)) {
      throw new Error(`Source is not approved for public distribution: ${entry.source}`);
    }
    const href = `sources/${entry.source}`;
    const target = resolve(outputRoot, href);
    await mkdir(dirname(target), { recursive: true });
    await cp(resolve(projectRoot, entry.source), target);
    sources.push({ title: entry.title, href });
  }

  const rootHtml = buildIndexHtml({
    pages,
    sources,
    feedbackUrl: profile.feedbackUrl,
    profileId
  });
  await writeFile(resolve(outputRoot, "index.html"), `${rootHtml}\n`);
  if (profileId === "internal-review") {
    const libraryPages = pages
      .filter((page) => page.group !== "Required Play Kit")
      .map((page) => ({ ...page, href: `../${page.href}` }));
    const libraryHtml = buildIndexHtml({
      pages: libraryPages,
      feedbackUrl: profile.feedbackUrl,
      profileId,
      library: true
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
