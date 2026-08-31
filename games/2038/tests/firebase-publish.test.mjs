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
    { kind: "game" }
  );
  assert.doesNotMatch(html, /href="\/lab\.html"/);
  assert.match(html, /src="\/web\/app\.js"/);
  assert.match(html, /Public playtest copy/i);
  assert.match(html, /Deterministic play runs entirely in this browser/i);
  assert.match(html, /bridge is optional for Claude and Codex/i);
  assert.doesNotMatch(html, /start-game[^]*disabled = true/i);
  const module = rewritePrototypeModule(
    'import x from "/lab/contracts/x.js"; fetch("/dist/runtime/factions.json");'
  );
  assert.match(module, /\/lab\/contracts\/x\.js/);
  assert.match(module, /\/dist\/runtime\/factions\.json/);
});

test("internal review executable retains the Lab route and carries a deployment warning", () => {
  const html = rewritePrototypeHtml(
    '<html><head></head><body><a href="/lab">Simulation lab</a></body></html>',
    { kind: "game", profileId: "internal-review" }
  );
  assert.match(html, /href="\/lab\.html"/);
  assert.match(html, /Internal review copy/);
  assert.match(html, /not approved for public deployment/);
});

test("review index clusters public game material before development surfaces", () => {
  const html = buildIndexHtml({
    identity: {
      rulesVersion: "rules-test",
      executableVersion: "exec-test",
      sourceCommit: "commit-test"
    },
    feedbackUrl: "https://example.test/feedback",
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
  assert.match(html, /href="https:\/\/example\.test\/feedback"/);
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
  assert.equal(firebase.hosting.public, "dist/firebase/public");
  assert.equal(firebase.hosting.cleanUrls, undefined);
});

test("public playtest publication is an allowlist with release identity and feedback", async () => {
  const outputRoot = await mkdtemp(join(tmpdir(), "mandate-2038-firebase-"));
  try {
    const { manifest } = await buildFirebaseSite({ outputRoot });
    assert.equal(manifest.deploymentProfile, "public-playtest");
    assert.equal(manifest.artifactKind, "firebase-public-playtest-site");
    assert.equal(manifest.deployable, true);
    assert.equal(manifest.runtimeArtifacts.length, 7);
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
    assert.match(rootIndex, /Send playtest feedback/);
    assert.doesNotMatch(rootIndex, /Simulation lab/i);
    assert.doesNotMatch(rootIndex, /Complete content gallery/i);
    assert.ok(
      rootIndex.indexOf('href="web/index.html"') < rootIndex.indexOf('href="docs/core-rules.html"')
    );
    assert.doesNotMatch(rootIndex, /Mandate 2038: Overview/);
    const game = await readFile(resolve(outputRoot, "web/index.html"), "utf8");
    assert.match(game, /Sell the intelligence\. Seize the grid\. Authorize the future\./);
    assert.match(game, /turning cheap intelligence into infrastructure, authority/);
    assert.doesNotMatch(game, /href="\/lab\.html"/);
    assert.ok(
      (await stat(resolve(outputRoot, "lab/rules/local-power-allocation.js"))).isFile(),
      "the published game includes the selected-rules browser module closure"
    );
    await assert.rejects(stat(resolve(outputRoot, "docs/lore-scratchpad.html")), {
      code: "ENOENT"
    });
    for (const forbidden of [
      "lab.html",
      "gallery.html",
      "library/index.html",
      "docs/thematic-content-bible.html",
      "docs/manufacturing-and-publishing-study.html",
      "docs/balance-and-exploitability.html",
      "docs/design-decisions.html",
      "docs/defect-investigation-and-closure.html",
      "docs/optional-tactics.html",
      "dist/runtime/tactics.json",
      "dist/runtime/reserve-specialists.json",
      "dist/runtime/secret-objectives.json",
      "web/simulation-app.js"
    ]) {
      await assert.rejects(stat(resolve(outputRoot, forbidden)), { code: "ENOENT" });
    }
    for (const required of [
      "docs/core-rules.html",
      "docs/map-reference.html",
      "docs/component-reference.html",
      "docs/card-reference.html",
      "docs/world-and-institutions.html",
      "gallery-baseline.html",
      "release-identity.json",
      "robots.txt"
    ]) {
      assert.ok((await stat(resolve(outputRoot, required))).isFile(), `publishes ${required}`);
    }
    const releaseIdentity = JSON.parse(
      await readFile(resolve(outputRoot, "release-identity.json"), "utf8")
    );
    assert.equal(releaseIdentity.deploymentProfile, "public-playtest");
    assert.match(await readFile(resolve(outputRoot, "robots.txt"), "utf8"), /Disallow: \//);
  } finally {
    await rm(outputRoot, { recursive: true, force: true });
  }
});

test("internal review build remains complete but explicitly non-deployable", async () => {
  const outputRoot = await mkdtemp(join(tmpdir(), "mandate-2038-review-"));
  try {
    const { manifest } = await buildFirebaseSite({
      outputRoot,
      profileId: "internal-review"
    });
    assert.equal(manifest.deploymentProfile, "internal-review");
    assert.equal(manifest.artifactKind, "internal-review-site");
    assert.equal(manifest.deployable, false);
    for (const required of [
      "lab.html",
      "gallery.html",
      "gallery-baseline.html",
      "library/index.html",
      "docs/thematic-content-bible.html",
      "docs/manufacturing-and-publishing-study.html",
      "docs/balance-and-exploitability.html",
      "docs/design-decisions.html",
      "docs/defect-investigation-and-closure.html",
      "docs/optional-tactics.html",
      "dist/runtime/tactics.json",
      "dist/runtime/reserve-specialists.json",
      "dist/runtime/secret-objectives.json",
      "web/simulation-app.js"
    ]) {
      assert.ok((await stat(resolve(outputRoot, required))).isFile(), `reviews ${required}`);
    }
    const rootIndex = await readFile(resolve(outputRoot, "index.html"), "utf8");
    assert.match(rootIndex, /Simulation lab/i);
    assert.match(rootIndex, /Complete content gallery/i);
  } finally {
    await rm(outputRoot, { recursive: true, force: true });
  }
});
