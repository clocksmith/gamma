import assert from "node:assert/strict";
// Run after build:all. Set PLAYWRIGHT_MODULE to an installed Playwright module if
// it is not resolvable from this checkout. No browser/provider installation here.
const { chromium } = await import(
  process.env.PLAYWRIGHT_MODULE || "playwright"
);
import { resolve } from "node:path";
import { tmpdir } from "node:os";
const root = resolve(import.meta.dirname, "..");
const output = tmpdir();
import { spawn } from "node:child_process";
import { once } from "node:events";
const server = spawn(process.execPath, ["tasks/serve.mjs"], {
  cwd: root,
  env: { ...process.env, FRONTIER_PORT: "8138" },
  stdio: "ignore",
});
let browser;
try {
  browser = await chromium.launch({ channel: "chrome", headless: true });
  for (const viewport of [
    { width: 1440, height: 1000 },
    { width: 390, height: 844 },
  ]) {
    const page = await browser.newPage({ viewport });
    page.setDefaultTimeout(10000);
    const errors = [];
    page.on("pageerror", (e) => errors.push(e.message));
    for (let i = 0; i < 30; i++) {
      try {
        await page.goto("http://127.0.0.1:8138/");
        break;
      } catch (e) {
        if (i === 29) throw e;
        await new Promise((r) => setTimeout(r, 100));
      }
    }
    await page.waitForFunction(
      () => document.querySelector("#faction")?.options.length === 6,
    );
    await page.waitForFunction(
      () => document.querySelectorAll(".player-mat").length === 4,
    );
    for (const count of [2, 3, 5, 4]) {
      await page.selectOption("#player-count", String(count));
      await page.waitForFunction(
        (n) => document.querySelectorAll(".player-mat").length === n,
        count,
      );
      assert.equal(await page.locator(".holding-cube").count(), count * 5);
      assert.equal(
        await page.locator(".available-orgs .org-token").count(),
        count * 2,
      );
      assert.equal(
        await page.locator(".reserve-orgs .org-token").count(),
        count * 2,
      );
    }
    assert.equal(
      await page.locator(".identities-section .table-card").count(),
      6,
    );
    const geometry = await page.evaluate(() => {
      window.testHex = document.querySelector(".action-area");
      const hex = window.testHex.getBoundingClientRect();
      return hex.width / hex.height;
    });
    assert.ok(
      Math.abs(geometry - 2 / Math.sqrt(3)) < 0.002,
      `regular hex at ${viewport.width}px: ${geometry}`,
    );
    await page.selectOption("#kit", "kit-blue");
    await page.waitForFunction(() =>
      document
        .querySelector(".player-mat .eyebrow")
        .textContent.includes("Blue"),
    );
    await page.selectOption("#faction", "foundry");
    await page.waitForFunction(
      () =>
        document.querySelector(
          '.player-mat [data-resource="compute"] .holding-cube',
        ).textContent === "4",
    );
    await page.selectOption("#faction", "coalition_lab");
    await page.waitForFunction(
      () =>
        document.querySelector(
          '.player-mat [data-resource="compute"] .holding-cube',
        ).textContent === "2",
    );
    await page.locator(".identities-section .table-card").first().click();
    assert.equal(await page.locator(".card-dialog[open]").count(), 1);
    await page.keyboard.press("Escape");
    assert.equal(await page.evaluate(() => {
      const decision = document.querySelector('.decision-console').getBoundingClientRect();
      const mats = document.querySelector('.institution-panel').getBoundingClientRect();
      return decision.bottom <= mats.top;
    }), true, 'decisions must not cover player mats');
    await page.screenshot({
      path: `${output}/mandate-components-setup-${viewport.width}.png`,
      fullPage: true,
    });
    await page.click("#start-game");
    await page.waitForFunction(
      () => document.querySelectorAll(".action-area").length === 18,
    );
    await page
      .locator(".action-area")
      .filter({ hasText: "Research" })
      .first()
      .click();
    assert.match(await page.locator(".board-note").innerText(), /Compute/);
    const result = await page.evaluate(async () => {
      const steps = [];
      let selection = 0;
      let trainingChecks = 0;
      const delay = () => new Promise((r) => setTimeout(r, 35));
      for (let i = 0; i < 600; i++) {
        for (
          let n = 0;
          n < 200 &&
          !["waiting", "complete", "failed"].includes(
            document.querySelector("#phase").textContent.trim(),
          );
          n++
        )
          await delay();
        const phase = document.querySelector("#phase").textContent.trim();
        if (phase === "failed")
          throw new Error(document.querySelector("#game-status").textContent);
        if (phase === "complete")
          return {
            steps,
            trainingChecks,
            summary: document.querySelector("#decision-context").textContent,
            overflow: document.documentElement.scrollWidth > innerWidth,
          };
        const buttons = [
          ...document.querySelectorAll("#decisions button"),
        ].filter((b) => !b.disabled);
        if (!buttons.length) throw new Error("No decision controls");
        const actions = buttons.filter((b) =>
          b.textContent.includes("Select "),
        );
        const names = [
          "Build",
          "Research",
          "Organize",
          "Fund",
          "Deploy",
          "Influence",
        ];
        const select = actions.length
          ? actions.find((b) =>
              b.textContent.includes(
                `Select ${names[selection++ % names.length]}`,
              ),
            ) || actions[0]
          : null;
        const target =
          select ||
          buttons.find((b) =>
            /Continue without|Pass$|Confirm assignment|Bank/.test(
              b.textContent,
            ),
          ) ||
          buttons[0];
        if (target.textContent.includes("Bank")) {
          const draws = document.querySelectorAll(
            ".training-section .table-card",
          );
          if (
            !draws.length ||
            document.querySelector(".training-section").hidden
          )
            throw new Error("Training draw not rendered");
          trainingChecks++;
        }
        if (document.querySelectorAll(".holding-cube").length !== 20)
          throw new Error("Missing holding cube");
        if (document.querySelectorAll(".org-token").length !== 16)
          throw new Error("Org conservation failed");
        steps.push({
          title: document.querySelector("#decision-title").textContent,
          choice: target.textContent.trim(),
        });
        target.click();
        await delay();
      }
      throw new Error("Unbounded decision loop");
    });
    assert.equal(result.overflow, false);
    assert.ok(result.trainingChecks > 0);
    assert.equal(
      await page.evaluate(
        () => window.testHex === document.querySelector(".action-area"),
      ),
      true,
    );
    assert.equal(
      await page.locator(".objectives-section .table-card").count(),
      4,
    );
    assert.equal(
      await page.locator(".headlines-section .table-card").count(),
      12,
    );
    assert.equal(await page.locator(".holding-cube").count(), 20);
    assert.equal(await page.locator(".org-token").count(), 16);
    assert.equal(await page.locator(".era-marker").innerText(), "Era 4");
    assert.deepEqual(errors, []);
    await page.screenshot({
      path: `${output}/mandate-components-complete-${viewport.width}.png`,
      fullPage: true,
    });
    console.log(
      JSON.stringify({
        viewport,
        decisions: result.steps.length,
        stages: [...new Set(result.steps.map((s) => s.title))],
        summary: result.summary,
        errors,
      }),
    );
    await page.close();
  }
  const page = await browser.newPage({
    viewport: { width: 1440, height: 1000 },
  });
  await page.goto("http://127.0.0.1:8138/dist/site/gallery-baseline.html");
  assert.equal(await page.locator(".training-card").count(), 40);
  assert.equal(await page.locator(".hex-tile").count(), 19);
  assert.equal(await page.locator('[data-org-face="equipped"]').count(), 20);
  await page
    .locator("#areas")
    .screenshot({ path: resolve(output, "mandate-components-print.png") });
  console.log("Printable inventory: 40 Training, 19 hexes, 20 two-sided Orgs.");
  await page.goto("http://127.0.0.1:8138/");
  await page.waitForFunction(
    () => document.querySelectorAll(".player-mat").length === 4,
  );
  const crowded = await page.evaluate(async () => {
    const { createBoard } = await import("/web/components/board.js");
    const { createPlayerMats } = await import("/web/components/player-mats.js");
    const { createBrowserInteractiveGame } = await import(
      "/lab/runtime/create-browser-interactive-game.js"
    );
    const config = await (await fetch("/dist/runtime/game-config.json")).json();
    const factions = await (await fetch("/dist/runtime/factions.json")).json();
    const copy = (await (await fetch("/dist/runtime/ui-copy.json")).json())
      .prototype.table;
    const runtime = await createBrowserInteractiveGame(
      { playerCount: 5 },
      () => {},
    );
    const state = runtime.match.snapshot();
    for (const player of state.players) {
      player.pieces = Array.from({ length: 4 }, (_, i) => ({
        id: `s${player.seat}-agent-${i + 1}`,
        tileId: state.board[0].instanceId,
        equipped: i % 2 === 0,
      }));
      player.agentsInSupply = 0;
    }
    const root = document.createElement("div");
    root.className = "board";
    root.style.width = "500px";
    const note = document.createElement("p");
    const mats = document.createElement("div");
    document.body.replaceChildren(root, note, mats);
    const board = createBoard(root, note, config, copy);
    const view = createPlayerMats(mats, config, factions, copy);
    board.update(state);
    view.update(state);
    const hex = root.querySelector("button");
    hex.focus();
    hex.click();
    const token = root.querySelector(".org-token"),
      rect = token.getBoundingClientRect(),
      hexRect = hex.getBoundingClientRect();
    const count = root.querySelectorAll(".org-token").length;
    state.players[0].pieces[0].tileId = state.board[1].instanceId;
    state.players[0].pieces[0].equipped = false;
    state.players[0].runway = 12;
    board.update(state);
    view.update(state);
    return {
      count,
      ratio: rect.width / hexRect.height,
      focused: document.activeElement === hex,
      first: hex.querySelectorAll(".org-token").length,
      second: root.querySelectorAll("button")[1].querySelectorAll(".org-token")
        .length,
      cubes: mats.querySelectorAll(".holding-cube").length,
      runway: mats.querySelector('[data-resource="runway"] .holding-cube')
        .textContent,
    };
  });
  assert.equal(crowded.count, 20);
  assert.ok(Math.abs(crowded.ratio - 24 / 110) < 0.002);
  assert.equal(crowded.focused, true);
  assert.equal(crowded.first, 19);
  assert.equal(crowded.second, 1);
  assert.equal(crowded.cubes, 25);
  assert.equal(crowded.runway, "12");
  console.log(JSON.stringify({ crowded }));
} finally {
  await browser?.close();
  const exited = once(server, "exit");
  server.kill();
  await exited;
}
