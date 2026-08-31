import { execFile } from "node:child_process";
import {
  cp,
  mkdir,
  readFile,
  rm,
  stat,
  writeFile
} from "node:fs/promises";
import { dirname, resolve } from "node:path";
import { promisify } from "node:util";
import { validateEraSituationLedger } from "./content/era-situation-ledger.mjs";

const execFileAsync = promisify(execFile);
const projectRoot = resolve(import.meta.dirname, "..");
const gammaRoot = resolve(projectRoot, "../..");

function titleFromFilename(name) {
  if (name === "index.html") return "Documentation reader";
  return name
    .replace(/\.html$/, "")
    .split("-")
    .map((word) => word[0].toUpperCase() + word.slice(1))
    .join(" ");
}

function documentMetadata(name) {
  const requiredKit = new Map([
    ["core-rules.html", ["Core Rules", "Complete setup, Eras, Actions, and scoring reference."]],
    ["map-reference.html", ["Map Reference", "The 19-district jurisdiction, adjacency, movement, and location effects."]],
    ["component-reference.html", ["Component Reference", "Every Default Game component, its purpose, and its setup location."]],
    ["card-reference.html", ["Card and Board Reference", "Printable canonical faces for every Default Game card type."]]
  ]);
  if (requiredKit.has(name)) {
    const [title, description] = requiredKit.get(name);
    return {
      group: "Required Default Game Play Kit",
      kind: "Required play-kit document",
      title,
      description
    };
  }
  if (name === "world-and-institutions.html") {
    return {
      group: "Learn the game",
      kind: "Document",
      title: titleFromFilename(name),
      description: "Setting, tone, Era fiction, and ending narratives."
    };
  }
  if (name === "advanced-play.html" || name === "optional-tactics.html") {
    return {
      group: "Optional play",
      kind: "Optional module",
      title: titleFromFilename(name),
      description: "Optional material for players who know the Default Play loop."
    };
  }
  if (name === "component-spec.html" || name === "component-inventory.html") {
    return {
      group: "Component review",
      kind: "Physical specification",
      title: titleFromFilename(name),
      description: name === "component-spec.html"
        ? "What every physical component is and how its state is made visible."
        : "Default Game box contents and Advanced-only exclusions."
    };
  }
  return {
    group: "Development and evidence",
    kind: name === "index.html" ? "Index" : "Document",
    title: titleFromFilename(name),
    description: "Design, testing, and implementation record."
  };
}

async function readJson(relative) {
  return JSON.parse(await readFile(resolve(projectRoot, relative), "utf8"));
}

async function requireFile(relative) {
  const absolute = resolve(projectRoot, relative);
  if (!(await stat(absolute)).isFile()) {
    throw new Error("Missing generated input: " + relative);
  }
  return absolute;
}

async function copyRelative(sourceRoot, outputRoot, relative) {
  const source = resolve(sourceRoot, relative);
  const target = resolve(outputRoot, relative);
  await mkdir(dirname(target), { recursive: true });
  await cp(source, target);
}

async function copyProtectedHtml(source, target, protectHtml) {
  const html = await readFile(source, "utf8");
  await mkdir(dirname(target), { recursive: true });
  await writeFile(target, protectHtml(html) + "\n");
}

async function sourceIdentity() {
  const current = await readJson("versions/current.json");
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

async function publicationContract(profileId) {
  const [ledger, graph, firebase] = await Promise.all([
    readJson("content/data/era-situation-ledger.json"),
    readJson("content/graph.json"),
    readJson("firebase.json")
  ]);
  await validateEraSituationLedger({
    root: projectRoot,
    ledger,
    graph,
    firebase
  });
  const profile = ledger.deploymentProfiles[profileId];
  if (!profile) throw new Error("Unknown publication profile: " + profileId);
  return { profile };
}

function assertSafeOutputRoot(outputRoot) {
  const forbidden = new Set([
    projectRoot,
    gammaRoot,
    resolve(gammaRoot, "web"),
    resolve(projectRoot, "web"),
    resolve(projectRoot, "content"),
    resolve(projectRoot, "docs")
  ]);
  if (forbidden.has(outputRoot)) {
    throw new RangeError("Refusing to replace a repository source directory.");
  }
}

export function parseFirebaseSiteArguments(values) {
  const parsed = { profileId: "public-playtest" };
  for (let index = 0; index < values.length; index += 1) {
    const value = values[index];
    if (value === "--profile") {
      if (!values[index + 1]) throw new TypeError("--profile requires an id.");
      parsed.profileId = values[index + 1];
      index += 1;
      continue;
    }
    if (value === "--output-root") {
      if (!values[index + 1]) throw new TypeError("--output-root requires a path.");
      parsed.outputRoot = resolve(values[index + 1]);
      index += 1;
      continue;
    }
    throw new TypeError("Unknown argument: " + value);
  }
  return parsed;
}

export async function buildProfiledFirebaseSite({
  profileId = "public-playtest",
  outputRoot
} = {}, renderers = {}) {
  const {
    buildIndexHtml,
    protectHtml,
    rewritePrototypeHtml,
    rewritePrototypeModule
  } = renderers;
  if ([buildIndexHtml, protectHtml, rewritePrototypeHtml, rewritePrototypeModule]
    .some((renderer) => typeof renderer !== "function")) {
    throw new TypeError("Firebase site builder requires its HTML renderers.");
  }
  const { profile } = await publicationContract(profileId);
  const resolvedOutputRoot = outputRoot
    ? resolve(outputRoot)
    : resolve(projectRoot, profile.outputRoot);
  assertSafeOutputRoot(resolvedOutputRoot);

  const generatedInputs = new Set();
  if (profile.siteSurfaces.includes("game")) generatedInputs.add("dist/site/index.html");
  if (profile.siteSurfaces.includes("first-game-guide")) {
    generatedInputs.add("dist/site/first-game-guide.html");
  }
  if (profile.siteSurfaces.includes("simulation-lab")) {
    generatedInputs.add("dist/site/simulation.html");
  }
  if (profile.siteSurfaces.includes("baseline-gallery")) {
    generatedInputs.add("dist/site/gallery-baseline.html");
  }
  if (profile.siteSurfaces.includes("complete-gallery")) {
    generatedInputs.add("dist/site/gallery.html");
  }
  for (const relative of generatedInputs) await requireFile(relative);

  await rm(resolvedOutputRoot, { recursive: true, force: true });
  await mkdir(resolvedOutputRoot, { recursive: true });
  const identity = await sourceIdentity();
  const pages = [];

  for (const name of profile.documentFiles) {
    const source = await requireFile("dist/site/docs/" + name);
    const target = resolve(resolvedOutputRoot, "docs", name);
    await copyProtectedHtml(source, target, protectHtml);
    const metadata = documentMetadata(name);
    pages.push({ ...metadata, href: "docs/" + name });
    if (metadata.group === "Required Default Game Play Kit") {
      await copyProtectedHtml(source, resolve(resolvedOutputRoot, name), protectHtml);
    }
  }

  if (profile.siteSurfaces.includes("baseline-gallery")) {
    await copyProtectedHtml(
      resolve(projectRoot, "dist/site/gallery-baseline.html"),
      resolve(resolvedOutputRoot, "gallery-baseline.html"),
      protectHtml
    );
    pages.push({
      group: "Component review",
      kind: "Gallery",
      title: "Baseline component gallery",
      href: "gallery-baseline.html",
      description: "Only components used by the controlled physical-test candidate."
    });
  }
  if (profile.siteSurfaces.includes("complete-gallery")) {
    await copyProtectedHtml(
      resolve(projectRoot, "dist/site/gallery.html"),
      resolve(resolvedOutputRoot, "gallery.html"),
      protectHtml
    );
    pages.push({
      group: "Component review",
      kind: "Gallery",
      title: "Complete content gallery",
      href: "gallery.html",
      description: "All baseline and deferred cards with player-facing text and art direction."
    });
  }

  for (const relative of profile.webFiles) {
    await copyRelative(resolve(projectRoot, "web"), resolve(resolvedOutputRoot, "web"), relative);
  }
  for (const moduleName of ["app.js", "first-game-guide.js", "simulation-app.js"]) {
    if (!profile.webFiles.includes(moduleName)) continue;
    const moduleSource = await readFile(resolve(projectRoot, "web", moduleName), "utf8");
    await writeFile(
      resolve(resolvedOutputRoot, "web", moduleName),
      rewritePrototypeModule(moduleSource)
    );
  }

  if (profile.siteSurfaces.includes("game")) {
    const prototype = await readFile(resolve(projectRoot, "dist/site/index.html"), "utf8");
    await mkdir(resolve(resolvedOutputRoot, "web"), { recursive: true });
    await writeFile(
      resolve(resolvedOutputRoot, "web/index.html"),
      rewritePrototypeHtml(prototype, { kind: "game", profileId }) + "\n"
    );
    pages.unshift({
      group: "Start here",
      kind: "Playable interface",
      title: "Play the game",
      href: "web/index.html",
      description: "Play against browser-native deterministic opponents; the local bridge is optional for Claude or Codex."
    });
  }
  if (profile.siteSurfaces.includes("first-game-guide")) {
    const guide = await readFile(
      resolve(projectRoot, "dist/site/first-game-guide.html"),
      "utf8"
    );
    await writeFile(
      resolve(resolvedOutputRoot, "first-game-guide.html"),
      rewritePrototypeHtml(guide, { kind: "guide", profileId }) + "\n"
    );
    pages.splice(1, 0, {
      group: "Start here",
      kind: "Teaching interface",
      title: "First Game Guide",
      href: "first-game-guide.html",
      description: "A fixed first-Era Default Play lesson using the canonical game components."
    });
  }
  if (profile.siteSurfaces.includes("simulation-lab")) {
    const simulation = await readFile(resolve(projectRoot, "dist/site/simulation.html"), "utf8");
    await writeFile(
      resolve(resolvedOutputRoot, "lab.html"),
      rewritePrototypeHtml(simulation, { kind: "simulation", profileId }) + "\n"
    );
    pages.push({
      group: "Development and evidence",
      kind: "Simulation interface",
      title: "Simulation lab",
      href: "lab.html",
      description: "Run local simulations or load and replay saved reports."
    });
  }

  for (const relative of profile.runtimeArtifacts) {
    await copyRelative(projectRoot, resolvedOutputRoot, relative);
  }
  for (const relative of profile.labModules) {
    await copyRelative(
      resolve(projectRoot, "lab"),
      resolve(resolvedOutputRoot, "lab"),
      relative
    );
  }

  const worldCopy = await readJson("dist/runtime/world-copy.json");
  const rootHtml = buildIndexHtml({ identity, pages, profileId, worldCopy });
  await writeFile(resolve(resolvedOutputRoot, "index.html"), rootHtml + "\n");
  await writeFile(
    resolve(resolvedOutputRoot, "robots.txt"),
    "User-agent: *\nDisallow: /\n"
  );

  const manifest = {
    schemaVersion: 2,
    artifactKind: profile.artifactKind,
    profileId,
    deployable: profile.deployable,
    publicBase: "",
    identity,
    crawlerPolicy: {
      accessControlled: false,
      robotsPath: "/robots.txt",
      disallowPath: "/",
      xRobotsTag: "noindex, nofollow, noarchive, nosnippet, noimageindex",
      limitation: "Crawler directives are voluntary and do not prevent hostile scraping."
    },
    pages,
    documentFiles: [...profile.documentFiles],
    siteSurfaces: [...profile.siteSurfaces],
    runtimeArtifacts: [...profile.runtimeArtifacts],
    webFiles: [...profile.webFiles],
    labModules: [...profile.labModules]
  };
  await writeFile(
    resolve(resolvedOutputRoot, "site-manifest.json"),
    JSON.stringify(manifest, null, 2) + "\n"
  );
  return { outputRoot: resolvedOutputRoot, manifest };
}
