import assert from "node:assert/strict";
import { readFile, readdir, stat, writeFile } from "node:fs/promises";
import { resolve } from "node:path";
import test from "node:test";
import { createContentFixture } from "./helpers/content-fixture.mjs";

test("generated provenance follows moved graph destinations and rejects stale maps or mixed audiences", async () => {
  const fixture = await createContentFixture();
  try {
    const graphPath = resolve(fixture.root, "content/graph.json");
    const graph = JSON.parse(await readFile(graphPath, "utf8"));
    const mapPath = resolve(fixture.root, graph.provenanceTarget);
    let map = await readFile(mapPath, "utf8");
    const headlines = map.split("\n").find(line => line.split(" | ")[1] === "`dist/runtime/headlines.json`");
    for (const source of ["components/headlines.json", "world.md", "content/data/variables.json"]) {
      assert.ok(headlines.includes(source), `headline content traces ${source}`);
    }
    assert.match(map, /not a complete dependency graph/);
    assert.match(map, /dist\/firebase\/public\/web\/index.html/);
    assert.match(map, /observer\/playtest-protocol.md/);
    assert.deepEqual(await readdir(resolve(fixture.root, "dist/docs")), ["core-rules.md", "world-and-institutions.md"]);
    assert.deepEqual((await readdir(resolve(fixture.root, "dist/site/docs"))).sort(), ["core-rules.html", "index.html", "world-and-institutions.html"]);

    const artifact = graph.artifacts.find(item => item.target === "dist/review/docs/component-inventory.md");
    graph.retiredTargets.push(artifact.target);
    artifact.target = "dist/review/docs/inventory-preview.md";
    await writeFile(graphPath, JSON.stringify(graph));
    await fixture.run("tasks/content/compile.mjs");
    await fixture.run("tasks/render-docs.mjs");
    map = await readFile(mapPath, "utf8");
    assert.match(map, /dist\/review\/docs\/inventory-preview.md/);
    assert.doesNotMatch(map, /dist\/review\/docs\/component-inventory.md/);
    await assert.rejects(stat(resolve(fixture.root, "dist/site/review/component-inventory.html")), {code:"ENOENT"});
    assert.ok((await stat(resolve(fixture.root, "dist/site/review/inventory-preview.html"))).isFile());

    await writeFile(mapPath, "An obsolete handwritten map");
    await assert.rejects(fixture.run("tasks/content/compile.mjs", "--check"), /Generated content drift/);
    artifact.audience = "player";
    await writeFile(graphPath, JSON.stringify(graph));
    await assert.rejects(fixture.run("tasks/content/compile.mjs"), /conflicting audience/);
  } finally {
    await fixture.dispose();
  }
});
