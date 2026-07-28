import test from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { resolve } from "node:path";
import {
  buildIndexHtml,
  protectHtml,
  rewritePrototypeHtml,
  rewritePrototypeModule
} from "../tools/build-firebase-site.mjs";

const projectRoot = resolve(import.meta.dirname, "..");
const gammaRoot = resolve(projectRoot, "../..");

test("published HTML carries crawler exclusions", () => {
  const protectedHtml = protectHtml("<!doctype html><html><head></head><body></body></html>");
  assert.match(protectedHtml, /name="robots" content="noindex, nofollow/);
  assert.match(protectedHtml, /name="googlebot" content="noindex, nofollow/);
  assert.match(protectedHtml, /name="referrer" content="no-referrer"/);
});

test("published executable surfaces are path-safe and server controls are disabled", () => {
  const html = rewritePrototypeHtml(
    '<html><head></head><body><a href="/lab">Lab</a><script src="/prototype/app.js"></script></body></html>',
    { kind: "game" }
  );
  assert.match(html, /href="\/m3t4-2038\/lab\.html"/);
  assert.match(html, /src="\/m3t4-2038\/prototype\/app\.js"/);
  assert.match(html, /server-run games and simulations are disabled/i);
  const module = rewritePrototypeModule(
    'import x from "/simulation/contracts/x.js"; fetch("/data/factions.json");'
  );
  assert.match(module, /\/m3t4-2038\/simulation\/contracts\/x\.js/);
  assert.match(module, /\/m3t4-2038\/data\/factions\.json/);
});

test("review index enumerates supplied HTML surfaces and exact identity", () => {
  const html = buildIndexHtml({
    identity: {
      rulesVersion: "rules-test",
      executableVersion: "exec-test",
      sourceCommit: "commit-test"
    },
    pages: [
      {
        group: "Rules",
        kind: "Document",
        title: "Core rules",
        href: "docs/core-rules.html",
        description: "Rules."
      },
      {
        group: "Components",
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
});

test("Firebase blocks cooperative crawlers only for the M3T4 review path", async () => {
  const robots = await readFile(resolve(gammaRoot, "web/robots.txt"), "utf8");
  assert.match(robots, /User-agent: \*/);
  assert.match(robots, /Disallow: \/m3t4-2038\//);
  const firebase = JSON.parse(
    await readFile(resolve(gammaRoot, "web/firebase.json"), "utf8")
  );
  const protectedHeaders = firebase.hosting.headers.find(
    (entry) => entry.source === "/m3t4-2038/**"
  );
  assert.ok(protectedHeaders);
  assert.equal(
    protectedHeaders.headers.find((header) => header.key === "X-Robots-Tag").value,
    "noindex, nofollow, noarchive, nosnippet, noimageindex"
  );
});
