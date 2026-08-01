import assert from "node:assert/strict";
import { execFile } from "node:child_process";
import { mkdtemp, readFile, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { promisify } from "node:util";
import test from "node:test";

const execFileAsync = promisify(execFile);
const root = new URL("../", import.meta.url);
const projectRoot = root.pathname;

test("playtest receipts carry the frozen rules, executable, and source commit", async () => {
  const outputRoot = await mkdtemp(join(tmpdir(), "m3t4-playtest-receipt-"));
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
    new URL("build/gallery-baseline.html", root),
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
