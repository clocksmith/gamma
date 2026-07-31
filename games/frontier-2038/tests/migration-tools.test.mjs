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
    "--scope=proposed",
    "--include-preserved-references"
  ]);
  const spaced = await runJson("migration/audit.mjs", [
    "--scope",
    "proposed",
    "--include-preserved-references"
  ]);

  assert.equal(documented.code, 0);
  assert.equal(spaced.code, 0);
  assert.equal(documented.report.scope, "proposed");
  assert.deepEqual(spaced.report.moves, documented.report.moves);
  assert.ok(documented.report.moves.every((move) => move.auditable));
  assert.ok(documented.report.moves.every((move) => Array.isArray(move.liveReferences)));
  assert.ok(
    documented.report.moves.some((move) => move.preservedReferenceSummary.evidence > 0),
    "historical evidence is counted without becoming an actionable live reference"
  );
  const prototypeMove = documented.report.moves.find((move) => move.from === "prototype/");
  assert.ok(
    prototypeMove.preservedReferences.generated.includes("data/game-config.json"),
    "content-graph projections are preserved generated references, not live migration work"
  );
});

test("migration preflight blocks the current plan with actionable source-root evidence", async () => {
  const result = await runJson("migration/preflight.mjs", ["--scope", "confirmed"]);

  assert.equal(result.code, 1);
  assert.equal(result.report.scope, "confirmed");
  assert.ok(result.report.blockers.some((blocker) => blocker.includes("planning_only")));
  assert.ok(
    result.report.blockers.some((blocker) =>
      blocker.includes("outside content graph sourceRoots")
    )
  );
  assert.ok(
    result.report.contentSourceRequirements.some((item) =>
      item.source === "content/physical/variables.json" &&
      item.plannedPath === "physical/variables.json" &&
      item.allowedAfterMove === false
    )
  );
});
