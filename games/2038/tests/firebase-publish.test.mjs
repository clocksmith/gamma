import test from "node:test";
import assert from "node:assert/strict";
import { mkdtemp, readFile, rm, stat } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join, resolve } from "node:path";
import {
  buildFirebaseSite,
  buildIndexHtml,
  protectHtml,
  rewritePrototypeHtml,
  rewritePrototypeModule
} from "../tasks/build-firebase-site.mjs";

const projectRoot = resolve(import.meta.dirname, "..");
const gammaRoot = resolve(projectRoot, "../..");

test("published HTML carries crawler exclusions", () => {
  const protectedHtml = protectHtml("<!doctype html><html><head></head><body></body></html>");
  assert.match(protectedHtml, /name="robots" content="noindex, nofollow/);
  assert.match(protectedHtml, /name="googlebot" content="noindex, nofollow/);
  assert.match(protectedHtml, /name="referrer" content="no-referrer"/);
});

test("published executable surfaces are path-safe and make the paired bridge optional", () => {
  const html = rewritePrototypeHtml(
    '<html><head></head><body><a href="/lab">Lab</a><script src="/web/app.js"></script></body></html>',
    { kind: "game", profileId: "public-playtest" }
  );
  assert.doesNotMatch(html, /href="\/lab(?:\.html)?"/);
  assert.match(html, /src="\/web\/app\.js"/);
  assert.match(html, /Deterministic play runs entirely in this browser/i);
  assert.match(html, /bridge is optional for Claude or Codex/i);
  assert.doesNotMatch(html, /start-game[^]*disabled = true/i);
  const internal = rewritePrototypeHtml(
    '<html><head></head><body><a href="/lab">Lab</a></body></html>',
    { kind: "game", profileId: "internal-review" }
  );
  assert.match(internal, /href="\/lab\.html"/);
  assert.match(internal, /not deployable/i);
  const module = rewritePrototypeModule(
    'import x from "/lab/contracts/x.js"; fetch("/dist/runtime/factions.json");'
  );
  assert.match(module, /\/lab\/contracts\/x\.js/);
  assert.match(module, /\/dist\/runtime\/factions\.json/);
});

test("review index clusters public game material before development surfaces", () => {
  const html = buildIndexHtml({
    identity: {
      rulesVersion: "rules-test",
      executableVersion: "exec-test",
      sourceCommit: "commit-test"
    },
    pages: [
      {
        group: "Start here",
        kind: "Playable interface",
        title: "Play the game",
        href: "web/index.html",
        description: "Play."
      },
      {
        group: "Learn the game",
        kind: "Document",
        title: "Core rules",
        href: "docs/core-rules.html",
        description: "Rules."
      },
      {
        group: "Component review",
        kind: "Gallery",
        title: "Cards",
        href: "gallery.html",
        description: "Cards."
      }
    ]
  });
  assert.match(html, /rules-test/);
  assert.match(html, /exec-test/);
  assert.match(html, /commit-test/);
  assert.match(html, /rel="icon" href="\/web\/favicon\.svg"/);
  assert.match(html, /href="docs\/core-rules\.html"/);
  assert.match(html, /href="gallery\.html"/);
  assert.match(html, /class="primary-action"/);
  assert.ok(html.indexOf('href="web/index.html"') < html.indexOf('href="docs/core-rules.html"'));
  assert.match(html, /<h2>Learn the game<\/h2>/);
  assert.match(html, /<h2>Component review<\/h2>/);
  assert.equal((html.match(/<li(?: class="primary-action")?>/g) ?? []).length, 3);
  assert.doesNotMatch(html, /class="surface"/);
  assert.doesNotMatch(html, /Controlled physical-candidate review/);
});

test("Firebase deployment uses the Mandate project's root-hosting contract", async () => {
  const firebase = JSON.parse(
    await readFile(resolve(projectRoot, "firebase.json"), "utf8")
  );
  assert.equal(firebase.hosting.public, "dist/firebase-public");
  assert.equal(firebase.hosting.cleanUrls, undefined);
});

test("public Firebase publication contains only its declared playtest allowlist", async () => {
  const outputRoot = await mkdtemp(join(tmpdir(), "mandate-2038-firebase-"));
  try {
    const { manifest } = await buildFirebaseSite({
      profileId: "public-playtest",
      outputRoot
    });
    assert.equal(manifest.schemaVersion, 2);
    assert.equal(manifest.profileId, "public-playtest");
    assert.equal(manifest.deployable, true);
    assert.equal(manifest.artifactKind, "mandate-2038-public-playtest");
    assert.equal(manifest.runtimeArtifacts.length, 11);
    assert.ok(
      manifest.runtimeArtifacts.every((target) => /^dist\/runtime\/[^/]+\.json$/.test(target))
    );
    await assert.rejects(
      stat(resolve(outputRoot, "dist/runtime/generated/reference-cards.json")),
      { code: "ENOENT" }
    );
    const authority = JSON.parse(
      await readFile(resolve(outputRoot, "dist/runtime/reference-cards.json"), "utf8")
    ).eraCards.find((era) => era.id === "era_narrative");
    assert.match(authority.unlockText, /Public Capability Covenant/);
    assert.doesNotMatch(authority.unlockText, /Open Weights/i);
    const baseline = await readFile(resolve(outputRoot, "gallery-baseline.html"), "utf8");
    assert.match(baseline, /Public Capability Covenant/);
    const rootIndex = await readFile(resolve(outputRoot, "index.html"), "utf8");
    assert.match(rootIndex, /href="web\/index\.html">Play the game<\/a>/);
    assert.match(rootIndex, /class="primary-action"/);
    assert.match(rootIndex, /adaptive cybernetics/);
    assert.match(rootIndex, /living watershed/);
    assert.ok(
      rootIndex.indexOf('href="web/index.html"') < rootIndex.indexOf('href="docs/core-rules.html"')
    );
    assert.doesNotMatch(rootIndex, /Mandate 2038: Overview/);
    assert.doesNotMatch(rootIndex, /Simulation lab/);
    const game = await readFile(resolve(outputRoot, "web/index.html"), "utf8");
    assert.match(game, /Sell the intelligence\. Seize the grid\. Authorize the future\./);
    assert.match(game, /turning cheap intelligence into infrastructure, authority/);
    assert.ok(
      (await stat(resolve(outputRoot, "lab/rules/local-power-allocation.js"))).isFile(),
      "the published game includes the selected-rules browser module closure"
    );
    await assert.rejects(stat(resolve(outputRoot, "docs/lore-scratchpad.html")), {
      code: "ENOENT"
    });
    for (const forbidden of [
      "docs/thematic-content-bible.html",
      "lab.html",
      "gallery.html",
      "web/simulation-app.js",
      "dist/runtime/era-situation-ledger.json",
      "library/index.html"
    ]) {
      await assert.rejects(stat(resolve(outputRoot, forbidden)), { code: "ENOENT" });
    }
    assert.equal(
      await readFile(resolve(outputRoot, "robots.txt"), "utf8"),
      "User-agent: *\nDisallow: /\n"
    );
  } finally {
    await rm(outputRoot, { recursive: true, force: true });
  }
});

test("internal review retains complete evidence but is non-deployable", async () => {
  const outputRoot = await mkdtemp(join(tmpdir(), "mandate-2038-review-"));
  try {
    const { manifest } = await buildFirebaseSite({
      profileId: "internal-review",
      outputRoot
    });
    assert.equal(manifest.profileId, "internal-review");
    assert.equal(manifest.deployable, false);
    assert.equal(manifest.artifactKind, "mandate-2038-internal-review");
    assert.ok(manifest.siteSurfaces.includes("simulation-lab"));
    assert.ok(manifest.siteSurfaces.includes("complete-gallery"));
    for (const required of [
      "lab.html",
      "gallery.html",
      "docs/thematic-content-bible.html",
      "dist/runtime/era-situation-ledger.json",
      "web/simulation-app.js"
    ]) {
      assert.ok((await stat(resolve(outputRoot, required))).isFile(), required);
    }
    const bible = await readFile(
      resolve(outputRoot, "docs/thematic-content-bible.html"),
      "utf8"
    );
    assert.match(bible, /Canonical Era and situation ledger/);
    assert.match(bible, /43 situations/);
    assert.match(bible, /62 game surfaces/);
    const internalRoot = await readFile(resolve(outputRoot, "index.html"), "utf8");
    assert.match(internalRoot, /Simulation lab/);
  } finally {
    await rm(outputRoot, { recursive: true, force: true });
  }
});
