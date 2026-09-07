import { createContentFixture } from "./helpers/content-fixture.mjs";
import { resolveValue, resolveString } from "../tasks/content/references.mjs";
import { createHash } from "node:crypto";
import assert from "node:assert/strict";
import { readFile, writeFile } from "node:fs/promises";
import test from "node:test";
import { execFile } from "node:child_process";
import { promisify } from "node:util";
import { resolve } from "node:path";
import { verifyRelease } from "../tasks/release-artifacts.mjs";
import { parseWorldCopyFromText, parseScenarioCanon, readWorldDocument, parseComponentLore, worldPassages } from "../tasks/content/world-parser.mjs";
import { buildScenarioIndex } from "../tasks/content/scenario-index.mjs";
import { validateEraSituationLedger } from "../tasks/content/validate-era-situation-ledger.mjs";
import { playerContent, documentSection, documentSections, documentTable } from "../tasks/content/authored.mjs";
const read = path => readFile(new URL(`../${path}`, import.meta.url), "utf8");

test("Markdown owns narrative; mechanics own ending conditions; player projections contain neither editorial notes nor unresolved references", async () => {
  const { text, worldCopy, scenarios } = await readWorldDocument();
  assert.equal(scenarios.length, 51);
  assert.equal(scenarios.filter(s => s.disposition === "lore-only").length, 11);
  assert.equal(scenarios.filter(s => ["deferred", "research-backlog"].includes(s.disposition)).length, 18);
  const index = await buildScenarioIndex();
  assert.deepEqual(index.scenarios.map(({ surfaceBindings, ...s }) => s), [...scenarios].sort((a, b) => a.id.localeCompare(b.id, "en")));
  assert.deepEqual(JSON.parse(await read("dist/runtime/world-copy.json")), playerContent(worldCopy));
  assert.doesNotMatch(text, /```json|content\.worldCopy|scenario-backlog/);
  const player = await read("dist/docs/world-and-institutions.md");
  assert.doesNotMatch(player, /\$\{|<!--|Mechanic status|scenario-canon/);
  for (const ending of worldCopy.endings) assert.ok(player.includes(ending.text));
  const variables = JSON.parse(await read("content/data/variables.json"));
  assert.equal(worldCopy.title, variables.game.title);
  assert.deepEqual(worldCopy.endings.map(e => e.name).sort(), Object.values(variables.terms.endings).sort());
  const changed = parseScenarioCanon(text.replace("* **Public benefit**:", "* **Public benefit**: Authored correction."));
  assert.match(changed[0].publicBenefit, /^Authored correction\./);
});

test("world copy rejects duplicates, omissions, unknown labels, and missing identities", async () => {
  const text = await read("world.md");
  for (const [changed, error] of [
    [text.replace("* **Compute**:", "* **Runway**:"), /Duplicate world copy field/],
    [text.replace(/^\* \*\*Compute\*\*:[^\n]*\n/m, ""), /Missing world copy field: Compute/],
    [text.replace("* **Compute**:", "* **Unknown**:"), /Unknown world copy field/],
    [text.replace("ending:closed_loop", "ending:singularity"), /Duplicate ending ID/],
    [text.replace("<!-- ending:closed_loop scenario:matter-compiler -->", ""), /Malformed World Ending/],
    [text.replace("* **Back copy**:", "* **Front strapline**:"), /Duplicate world copy field/]
  ]) assert.throws(() => parseWorldCopyFromText(changed), error);
  const wrapped = text.replace(/(\* \*\*Runway\*\*:[^\n]*)/, "$1\n  Continued on another line.");
  assert.match(parseWorldCopyFromText(wrapped).tokenCopy[0].microcopy, /Continued on another line\.$/);
  assert.deepEqual(parseWorldCopyFromText(text.replace(/\n/g, "\r\n")), parseWorldCopyFromText(text));
});

test("canon requires explicit unique identities, dispositions, and complete narratives", async () => {
  const text = await read("world.md");
  for (const [changed, error] of [
    [text.replace("* **ID**: agi-refinancing-declaration", "* **ID**: abundance-constituency"), /Duplicate scenario ID/],
    [text.replace("* **Policy**: adopted-revised", "* **Policy**: unknown"), /Unknown scenario policy/],
    [text.replace(/^\* \*\*Policy\*\*:[^\n]*\n/m, ""), /Missing.*Policy/],
    [text.replace("* **Era**: progress", "* **Era**: progress\n* **Era**: capacity"), /Duplicate.*field: Era/],
    [text.replace("* **Era**:", "* **Erra**:"), /Unknown.*field: Erra/],
    [text.replace("<!-- scenario-canon:start -->", "<!-- scenario-canon:start -->\n```json"), /not fenced data/]
  ]) assert.throws(() => parseScenarioCanon(changed), error);
  const first = parseScenarioCanon(text)[0];
  const withoutNarrative = text.replace(first.narrative, "");
  assert.throws(() => parseScenarioCanon(withoutNarrative), /Missing or malformed scenario narrative/);
  assert.deepEqual(parseScenarioCanon(text.replace(/\n/g, "\r\n")), parseScenarioCanon(text));
  assert.equal(documentSection(text, "scenario-canon").match(/^### /gm).length, 51);
});

test("lore-only entries cannot gain mechanics, public deployment, or game bindings", async () => {
  const ledger = await buildScenarioIndex();
  assert.deepEqual(await validateEraSituationLedger(ledger), { eras: 4, scenarios: 51, surfaces: 54 });
  for (const mutate of [
    s => { s.mechanicPreservation.status = "retained"; },
    s => { s.deploymentProfiles.push("public-playtest"); },
    s => { s.surfaceBindings.push({surfaceId: "ending:singularity", copyReference: "world.md#endings/singularity"}); }
  ]) {
    const copy = structuredClone(ledger);
    mutate(copy.scenarios.find(s => s.disposition === "lore-only"));
    await assert.rejects(validateEraSituationLedger(copy), /Lore-only|unauthorized game-surface|enters public-playtest/);
  }
});

test("historical world releases retain their first committed bytes", async () => {
  const originals = {
    "versions/0.19.2/manifest.json": "1ddcc4c5031641fd8c35c03d1e3e389ca9748922cad520714cc3fe77eb6aeb2f",
    "versions/0.19.2/game-bundle.json": "7d145fad46d5220dfac89210dec0fb6426f27bbeeb747448e5fc988904f655cf",
    "versions/0.11.0-rc.4-test/manifest.json": "925aa12914c663d1b71a69f7aeeface1fc6b8e67def60008bcd2564030b2d506",
    "versions/0.11.0-rc.4-test/rules-candidate-bundle.json": "5b5bd45469ce4430fed65de4451c7fc6c9687ff76b5cc3675781fdb9f6d1c4d0"
};
  for (const [path, digest] of Object.entries(originals)) {
    assert.equal(createHash("sha256").update(await read(path)).digest("hex"), digest, path);
  }
});

test("current teaching materials follow the release declaration and supported Audit counts", async () => {
  const readme = await read("README.md");
  const protocol = await read("docs/playtesting-and-evidence.md");
  assert.match(readme, /versions\/current-release\.json/);
  assert.match(protocol.split("\n\n")[1], /versions\/current-release\.json/);
  assert.doesNotMatch(readme, /0\.19\.1|0\.11\.0-rc\.3-test/);
  for (const path of ["rules.md", "dist/docs/core-rules.md"]) {
    const source = await read(path);
    const table = source.match(/^\| Era \| 2 players[^\n]*\n(?:\|[^\n]*\n){5}/m)?.[0];
    assert.ok(table, `${path} includes the Audit table`);
    assert.doesNotMatch(table, /6 players/);
    assert.equal(table.split("\n")[0], "| Era | 2 players | 3 players | 4 players | 5 players |");
    assert.ok(table.includes("| IV | 3 | 4 | 5 | 6 |"));
  }
});


test("shared policy tables reject malformed rows and preserve escaped punctuation", () => {
  const source = "<!-- policies:start -->\n| Key | Meaning |\n| --- | --- |\n| sample | One \\| two |\n<!-- policies:end -->";
  assert.deepEqual(documentTable(source, "policies", ["Key", "Meaning"]), [{Key:"sample",Meaning:"One | two"}]);
  assert.throws(() => documentTable(source.replace("| --- | --- |", "| --- |"), "policies", ["Key", "Meaning"]), /columns/);
  assert.throws(() => documentTable(source.replace("| sample | One \\| two |", "| sample | |"), "policies", ["Key", "Meaning"]), /Incomplete/);
});

test("an edited lore record compiles while stale release publication and freezing are rejected", async () => {
  const {root: fixture, dispose} = await createContentFixture();
  const exec = promisify(execFile);
  try {
    const graph = JSON.parse(await read("content/graph.json"));
    const release = JSON.parse(await read("versions/current-release.json"));
    await verifyRelease(fixture);
    const sealedManifest = await readFile(resolve(fixture, `versions/${release.gameVersion}/manifest.json`), "utf8");
    const path = resolve(fixture, "world.md");
    const original = await readFile(path, "utf8");
    const id = Object.keys(parseComponentLore(original)).find(key => parseComponentLore(original)[key].newswire);
    assert.ok(id);
    const marker = `<!-- lore-${id}:start -->\n\n#### Newswire`;
    assert.ok(original.includes(marker));
    const edited = original.replace(marker, marker + "\n\nAuthoring fixture correction.")
      .replace(`<!-- lore-${id}:end -->`, `#### Author notes\n\nINTERNAL_COMPONENT_SENTINEL \${missing.private.note}\n\n<!-- lore-${id}:end -->`)
      .replace("<!-- world-guide:start -->", "<!-- world-guide:start -->\nINTERNAL_GUIDE_SENTINEL");
    await writeFile(path, edited);
    await exec(process.execPath, ["tasks/content/compile.mjs"], {cwd:fixture});
    await exec(process.execPath, ["tasks/content/compile.mjs", "--check"], {cwd:fixture});
    const runtime = JSON.parse(await readFile(resolve(fixture, "dist/runtime/headlines.json"), "utf8"));
    assert.ok(runtime.headlines.some(f => f.newswire.startsWith("Authoring fixture correction.")));
    const cards = await readFile(resolve(fixture, "dist/docs/card-reference.md"), "utf8");
    assert.ok(cards.includes("Authoring fixture correction."));
    for (const artifact of graph.artifacts.filter(a => ["text", "json"].includes(a.format))) {
      const output = await readFile(resolve(fixture, artifact.target), "utf8");
      assert.doesNotMatch(output, /INTERNAL_COMPONENT_SENTINEL|INTERNAL_GUIDE_SENTINEL|loreRef|missing.private.note/);
    }
    await exec(process.execPath, ["tasks/render-gallery.mjs", "--baseline"], {cwd:fixture});
    await exec(process.execPath, ["tasks/render-docs.mjs"], {cwd:fixture});
    for (const target of ["dist/site/gallery-baseline.html", "dist/site/docs/card-reference.html"]) {
      const output = await readFile(resolve(fixture, target), "utf8");
      assert.ok(output.includes("Authoring fixture correction."));
      assert.doesNotMatch(output, /INTERNAL_COMPONENT_SENTINEL|INTERNAL_GUIDE_SENTINEL/);
    }
    await assert.rejects(verifyRelease(fixture), /Stale generated release artifact/);
    await assert.rejects(exec(process.execPath, ["tasks/build-firebase-site.mjs", "--profile", "public-playtest"], {cwd:fixture}), /Stale generated release artifact/);
    await assert.rejects(exec(process.execPath, ["tasks/create-physical-kit.mjs", "--local"], {cwd:fixture}), /Stale generated release artifact/);
    assert.equal(await readFile(resolve(fixture, `versions/${release.gameVersion}/manifest.json`), "utf8"), sealedManifest);
    graph.artifacts.push({source: "world.md", target: "dist/docs/unselected-lore.md", format: "text"});
    await writeFile(resolve(fixture, "content/graph.json"), JSON.stringify(graph));
    await assert.rejects(exec(process.execPath, ["tasks/content/compile.mjs"], {cwd:fixture}), /author bible cannot be exported/);
  } finally {
    await dispose();
  }
});


test("lore references reject missing entries, ambiguous overrides, unapproved fields and internal excerpt access", async () => {
  const text = await read("world.md");
  const lore = parseComponentLore(text);
  const id = Object.keys(lore).find(id => lore[id].motto);
  const record = { id: "fixture", cost: 3, loreRef: id };
  const variables = JSON.parse(await read("content/data/variables.json"));
  const context = { ...resolveValue(variables, variables), lore, excerpts: {world: worldPassages(text)} };
  const compiled = resolveValue(record, context);
  assert.equal(compiled.cost, 3);
  assert.equal(compiled.loreRef, undefined);
  assert.ok(compiled.motto);
  assert.equal(record.loreRef, id);
  assert.throws(() => resolveValue({loreRef: "missing"}, context), /Unknown lore reference/);
  assert.throws(() => resolveValue({...record, motto: "Override"}, context), /conflicts with component/);
  assert.throws(() => resolveValue({loreRef: {}}, context), /Unknown lore reference/);
  assert.throws(() => resolveString("${excerpts.world.world-guide}", context), /Unknown content reference/);
  assert.throws(() => parseComponentLore(text.replace("#### Motto", "#### Mechanics")), /Unknown player field/);
  assert.throws(() => parseComponentLore(text.replace("#### Motto", "#### Motto\n\nOne\n\n#### Motto")), /Duplicate/);
  assert.throws(() => parseComponentLore(text.replace(`<!-- lore-${id}:end -->`, "")), /exactly one/);
  assert.throws(() => parseWorldCopyFromText(text, {}), /Missing mechanical ending condition/);
});
