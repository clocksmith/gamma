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
  assert.match(html, /href="\/lab\.html"/);
  assert.match(html, /src="\/web\/app\.js"/);
  assert.match(html, /Deterministic play runs entirely in this browser/i);
  assert.match(html, /bridge is optional for Claude, Codex/i);
  assert.doesNotMatch(html, /start-game[^]*disabled = true/i);
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
  assert.match(html, /href="docs\/core-rules\.html"/);
  assert.match(html, /href="gallery\.html"/);
  assert.match(html, /<h2>Learn the game<\/h2>/);
  assert.match(html, /<h2>Component review<\/h2>/);
  assert.equal((html.match(/<li>/g) ?? []).length, 2);
  assert.doesNotMatch(html, /class="surface"/);
  assert.doesNotMatch(html, /Controlled physical-candidate review/);
});

test("Firebase deployment uses the Mandate project's root-hosting contract", async () => {
  const firebase = JSON.parse(
    await readFile(resolve(projectRoot, "firebase.json"), "utf8")
  );
  assert.equal(firebase.hosting.public, "dist/firebase");
  assert.equal(firebase.hosting.cleanUrls, undefined);
});

test("Firebase publication copies only graph-owned runtime artifacts", async () => {
  const outputRoot = await mkdtemp(join(tmpdir(), "mandate-2038-firebase-"));
  try {
    const { manifest } = await buildFirebaseSite({ outputRoot });
    assert.ok(manifest.runtimeArtifacts.length > 0);
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
    const game = await readFile(resolve(outputRoot, "web/index.html"), "utf8");
    assert.match(game, /Sell the intelligence\. Seize the grid\. Authorize the future\./);
    assert.match(game, /turning cheap intelligence into infrastructure, authority/);
    await assert.rejects(stat(resolve(outputRoot, "docs/lore-scratchpad.html")), {
      code: "ENOENT"
    });
    const bible = await readFile(
      resolve(outputRoot, "docs/thematic-content-bible.html"),
      "utf8"
    );
    assert.match(bible, /sole editorial authority/);
    assert.match(bible, /Whole-game lore atlas/);
  } finally {
    await rm(outputRoot, { recursive: true, force: true });
  }
});
