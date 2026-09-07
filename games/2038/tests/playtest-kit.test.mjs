import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { execFile } from "node:child_process";
import { mkdtemp, readFile, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join, resolve } from "node:path";
import { createContentFixture } from "./helpers/content-fixture.mjs";
import { loadKit } from "../lab/runner/codex-controlled-session-runner.js";
import { promisify } from "node:util";
import test from "node:test";

const execFileAsync = promisify(execFile);
const root = new URL("../", import.meta.url);
const projectRoot = root.pathname;

test("playtest receipts carry the frozen rules, executable, and source commit", async () => {
  const outputRoot = await mkdtemp(join(tmpdir(), "mandate-2038-playtest-receipt-"));
  try {
    const current = JSON.parse(
      await readFile(new URL("versions/current.json", root), "utf8")
    );
    const { stdout: commitOutput } = await execFileAsync(
      "git",
      ["rev-parse", "HEAD"],
      { cwd: projectRoot }
    );
    const sourceCommit = commitOutput.trim();
    const kitManifestPath = join(outputRoot, "physical-kit.json");
    const kitFingerprint =
      "sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa";
    await writeFile(
      kitManifestPath,
      `${JSON.stringify({
        schemaVersion: 1,
        artifactKind: "controlled-physical-playtest-kit",
        kitId: `${current.rulesCandidate.version}-${sourceCommit.slice(0, 8)}`,
        kitFingerprint,
        identity: {
          rulesVersion: current.rulesCandidate.version,
          executableVersion: current.gameVersion,
          sourceCommit
        }
      }, null, 2)}\n`
    );
    const { stdout } = await execFileAsync(
      "node",
      [
        "tasks/create-playtest-session.mjs",
        "--players",
        "4",
        "--seed",
        "receipt-provenance-test",
        "--date",
        "2026-07-28",
        "--output-root",
        outputRoot,
        "--kit-manifest",
        kitManifestPath
      ],
      { cwd: projectRoot }
    );
    const directory = stdout.trim();
    const receipt = JSON.parse(
      await readFile(join(directory, "receipt.json"), "utf8")
    );
    const notes = await readFile(join(directory, "notes.md"), "utf8");
    assert.equal(receipt.game.version, current.rulesCandidate.version);
    assert.equal(receipt.game.executableVersion, current.gameVersion);
    assert.equal(receipt.game.sourceCommit, sourceCommit);
    assert.equal(receipt.game.playtestKitFingerprint, kitFingerprint);
    assert.equal(
      receipt.physicalKit.kitId,
      `${current.rulesCandidate.version}-${sourceCommit.slice(0, 8)}`
    );
    assert.equal(receipt.physicalKit.componentRevision, current.rulesCandidate.version);
    assert.equal(receipt.physicalKit.executableRevision, current.gameVersion);
    assert.equal(receipt.physicalKit.sourceCommit, sourceCommit);
    assert.match(receipt.physicalKit.label, new RegExp(sourceCommit.slice(0, 8)));
    assert.match(notes, new RegExp(`Rules ${current.rulesCandidate.version}`));
    assert.match(notes, new RegExp(`Executable reference ${current.gameVersion}`));
    assert.match(notes, new RegExp(`Source commit ${sourceCommit}`));
  } finally {
    await rm(outputRoot, { recursive: true, force: true });
  }
});

test("baseline gallery excludes every deferred physical module", async () => {
  await execFileAsync(
    "node",
    ["tasks/render-gallery.mjs", "--baseline"],
    { cwd: projectRoot }
  );
  const html = await readFile(
    new URL("dist/site/gallery-baseline.html", root),
    "utf8"
  );
  for (const id of ["tactics", "objectives", "specialists"]) {
    assert.ok(!html.includes(`section id="${id}"`));
    assert.ok(!html.includes(`href="#${id}"`));
  }
  for (const id of ["factions", "actions", "headlines", "reference"]) {
    assert.ok(html.includes(`section id="${id}"`));
  }
});

test("physical candidate contains final player copy and retains source provenance separately", async () => {
  const declaration = JSON.parse(await readFile(new URL("versions/current-release.json", root), "utf8"));
  assert.deepEqual(declaration.rulesCandidate.files, ["dist/docs/core-rules.md", "physical/governance-ledger.md"]);
  const graph = JSON.parse(await readFile(new URL("content/graph.json", root), "utf8"));
  for (const source of ["world.md", "physical/", "docs/design-decisions.md", "docs/playtesting-and-evidence.md"]) {
    assert.ok(graph.sourceRoots.includes(source), `${source} retains source provenance`);
  }
});


test("fresh kit freezes one complete rulebook and component faces and the reader consumes both", async () => {
  const fixture = await createContentFixture();
  try {
    const git = (...args) => execFileAsync("git", args, {cwd: fixture.root});
    await git("add", ".");
    await git("-c", "user.name=Kit Fixture", "-c", "user.email=fixture@example.invalid",
      "-c", "core.hooksPath=/dev/null", "-c", "commit.gpgsign=false", "commit", "-m", "Freeze fixture sources");
    await git("remote", "add", "origin", fixture.root);
    await git("update-ref", "refs/remotes/origin/main", "HEAD");
    await fixture.run("tasks/create-physical-kit.mjs", "--local");
    const current = JSON.parse(await readFile(resolve(fixture.root, "versions/current.json"), "utf8"));
    const {stdout} = await git("rev-parse", "HEAD");
    const kitRoot = resolve(fixture.root, "dist/physical-kit", `${current.rulesCandidate.version}-${stdout.trim().slice(0, 8)}`);
    const kit = await loadKit(resolve(kitRoot, "physical-kit-manifest.json"));
    assert.deepEqual(kit.manifest.playerDocuments, ["core-rules.md"]);
    assert.deepEqual(kit.documents.map(document => document.id), ["core-rules", "component-masters"]);
    assert.match(kit.documents[0].contents, /Build the jurisdiction/);
    assert.match(kit.inventory.contents, /Shared Governance Board/);
    assert.doesNotMatch(kit.inventory.contents, /## 4. Core Actions/);
    assert.match(kit.documents[1].contents, /<article/);
    assert.doesNotMatch(kit.documents[1].contents, /<style/);
    for (const path of ["map-reference.md", "component-reference.md", "card-reference.md", "world-and-institutions.md", "world.md"]) {
      assert.equal(kit.manifest.files[path], undefined);
      await assert.rejects(readFile(resolve(kitRoot, path)), {code:"ENOENT"});
    }
    for (const [path, receipt] of Object.entries(kit.manifest.files)) {
      const bytes = await readFile(resolve(kitRoot, path));
      assert.equal(createHash("sha256").update(bytes).digest("hex"), receipt.sha256);
    }
    assert.ok(kit.manifest.files["observer/playtest-protocol.md"]);
    assert.ok(kit.manifest.files["observer/contracts/playtest-receipt.schema.json"]);
    assert.ok(kit.manifest.files["observer/release/executable-manifest.json"]);
    assert.ok(kit.manifest.files["observer/source-data/game-config.json"]);
    assert.equal(kit.manifest.files["playtest-protocol.md"], undefined);
    await writeFile(resolve(kitRoot, "core-rules.md"), "Unbound replacement rules");
    await assert.rejects(loadKit(resolve(kitRoot, "physical-kit-manifest.json")), /hash mismatch/);
    await writeFile(resolve(kitRoot, "core-rules.md"), kit.documents[0].contents);
    // Keep historical four-book kits readable without rewriting their records.
    const legacyManifest = structuredClone(kit.manifest);
    delete legacyManifest.playerDocuments;
    for (const name of ["map-reference.md", "component-reference.md", "card-reference.md"]) {
      const contents = await readFile(resolve(fixture.root, "dist/review/docs", name), "utf8");
      await writeFile(resolve(kitRoot, name), contents);
      legacyManifest.files[name] = {bytes:Buffer.byteLength(contents), sha256:createHash("sha256").update(contents).digest("hex")};
    }
    await writeFile(resolve(kitRoot, "legacy-manifest.json"), JSON.stringify(legacyManifest));
    const legacy = await loadKit(resolve(kitRoot, "legacy-manifest.json"));
    assert.deepEqual(legacy.documents.map(document => document.id), ["core-rules", "map-reference", "component-reference", "card-reference"]);
    assert.equal(legacy.inventory.id, "component-reference");
  } finally {
    await fixture.dispose();
  }
});
