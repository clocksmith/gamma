import assert from "node:assert/strict";
import { execFile } from "node:child_process";
import test from "node:test";
import { promisify } from "node:util";

const execFileAsync = promisify(execFile);
const root = new URL("../", import.meta.url);

async function runJson(script, args) {
  try {
    const { stdout } = await execFileAsync(process.execPath, [script, ...args], { cwd: root });
    return { code: 0, report: JSON.parse(stdout) };
  } catch (error) {
    return {
      code: error.code,
      report: JSON.parse(error.stdout)
    };
  }
}

test("migration audit accepts both documented and spaced scope syntax", async () => {
  const documented = await runJson("migration/audit.mjs", [
    "--scope=all",
    "--include-preserved-references"
  ]);
  const spaced = await runJson("migration/audit.mjs", [
    "--scope",
    "all",
    "--include-preserved-references"
  ]);

  assert.equal(documented.code, 0);
  assert.equal(spaced.code, 0);
  assert.equal(documented.report.scope, "all");
  assert.equal(spaced.report.scope, documented.report.scope);
  assert.deepEqual(
    spaced.report.moves.map((move) => move.from),
    documented.report.moves.map((move) => move.from)
  );
  assert.ok(documented.report.moves.every((move) => move.auditable));
  assert.ok(documented.report.moves.every((move) => Array.isArray(move.liveReferences)));
  assert.ok(
    documented.report.moves.some((move) => move.preservedReferenceSummary.evidence > 0),
    "historical evidence is counted without becoming an actionable live reference"
  );
  assert.ok(
    documented.report.moves.every((move) => move.liveReferences.length === 0),
    "no live source retains a migrated path"
  );
});

test("migration preflight records an applied map as non-runnable", async () => {
  const result = await runJson("migration/preflight.mjs", ["--scope", "confirmed"]);

  assert.equal(result.code, 1);
  assert.equal(result.report.scope, "confirmed");
  assert.equal(result.report.ready, false);
  assert.equal(result.report.mapStatus, "applied");
  assert.ok(result.report.blockers.some((blocker) => blocker.includes('Map status is "applied"')));
  assert.ok(result.report.moves.some((move) =>
    move.from === "data/game-version.json" && move.to === "release/game-version.json" && move.executable
  ));
  assert.deepEqual(result.report.contentSourceRoots, ["content/", "physical/", "web/"]);
});
