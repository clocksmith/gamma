const [config, headlines, mandates, eraCards, uiCopy] = await Promise.all([
  fetch("/dist/runtime/game-config.json").then((response) => response.json()),
  fetch("/dist/runtime/headlines.json").then((response) => response.json()),
  fetch("/dist/runtime/mandates.json").then((response) => response.json()),
  fetch("/dist/runtime/reference-cards.json").then((response) => response.json()),
  fetch("/dist/runtime/ui-copy.json").then((response) => response.json())
]);

const copy = uiCopy.firstGameGuide;
const $ = (id) => document.getElementById(id);
const format = (template, values) => template.replace(/\{(\w+)\}/g, (_, key) => values[key] ?? "");
const escapeHtml = (value) => String(value).replace(/[&<>"']/g, (character) => ({
  "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
})[character]);

const lesson = { index: 0, choice: null };
const eraOne = eraCards.eraCards.find((card) => card.round === 1);
const headline = headlines.headlines.find((card) => card.round === 1);
const research = config.actions.find((action) => action.id === "research");
const eraOneMandates = mandates.mandates.filter((mandate) => mandate.era === 1);
const trainingCards = config.trainingDeck.cards.filter((card) => card.kind === "domain").slice(0, 2);

$("guide-eyebrow").textContent = copy.eyebrow;
$("guide-title").textContent = copy.title;
$("guide-dek").textContent = copy.dek;
$("guide-scenario").textContent = copy.scenario;

function card({ eyebrow, title, body, extra = "", compact = false, highlight = false }) {
  return `<article class="guide-card${compact ? " compact" : ""}${highlight ? " highlight" : ""}">
    <p class="eyebrow">${escapeHtml(eyebrow)}</p><h3>${escapeHtml(title)}</h3>
    <p>${escapeHtml(body)}</p>${extra}</article>`;
}

function componentFor(index) {
  if (index === 0) {
    return `<div class="guide-card-grid">${card({
      eyebrow: "Personal score", title: uiCopy.prototype.tracks.mandate,
      body: "Lead this track at the end of Era IV to win the institutional contest."
    })}${card({
      eyebrow: "Shared result", title: "World Ending",
      body: Object.values(config.worldEnding.outcomes).join(" · ")
    })}</div>`;
  }
  if (index === 1) return card({ eyebrow: "Era card", title: eraOne.name, body: eraOne.rulesText, extra: `<p>${escapeHtml(eraOne.unlockText)}</p>`, highlight: true });
  if (index === 2) return card({ eyebrow: headline.strapline, title: headline.name, body: headline.text, extra: `<p>${escapeHtml(headline.newswire)}</p>`, highlight: true });
  if (index === 3) return card({ eyebrow: research.initiativeName, title: research.name, body: research.summary, extra: `<p>${escapeHtml(research.flavorText)}</p>`, highlight: true });
  if (index === 4) return `<div class="guide-card-grid">${trainingCards.map((training) => card({ eyebrow: "Training face", title: training.name, body: training.flavorText, compact: true })).join("")}</div>`;
  if (index === 5) return `<div class="guide-card-grid">${eraOneMandates.map((mandate) => card({ eyebrow: "Era I Mandate", title: mandate.name, body: mandate.rulesText, compact: true })).join("")}</div>`;
  return card({ eyebrow: copy.finish.title, title: eraCards.eraCards.map((card) => card.name).join(" → "), body: copy.finish.body, highlight: true });
}

function renderChoice() {
  const choice = $("guide-choice");
  const result = $("choice-result");
  choice.hidden = lesson.index !== 4;
  result.hidden = lesson.choice === null;
  if (lesson.index !== 4) return;
  choice.innerHTML = `<p>${escapeHtml(copy.choice.prompt)}</p><div>
    <button type="button" data-choice="bank">${escapeHtml(copy.choice.bank)}</button>
    <button type="button" data-choice="press">${escapeHtml(copy.choice.press)}</button></div>`;
  for (const button of choice.querySelectorAll("button")) {
    button.addEventListener("click", () => {
      lesson.choice = button.dataset.choice;
      result.textContent = lesson.choice === "bank" ? copy.choice.bankResult : copy.choice.pressResult;
      result.hidden = false;
    });
  }
}

function render() {
  const final = lesson.index === copy.steps.length;
  const current = final ? copy.finish : copy.steps[lesson.index];
  $("lesson-number").textContent = final ? copy.scenario : format(copy.step, { number: lesson.index + 1, total: copy.steps.length });
  $("lesson-title").textContent = current.title;
  $("lesson-body").textContent = current.body;
  $("canonical-component").innerHTML = componentFor(lesson.index);
  $("guide-back").hidden = lesson.index === 0;
  $("guide-back").textContent = copy.back;
  $("guide-next").textContent = final ? copy.restart : lesson.index === copy.steps.length - 1 ? copy.complete : copy.next;
  $("guide-steps").innerHTML = copy.steps.map((step, index) => `<li><button type="button" class="${index === lesson.index ? "current" : ""}${index < lesson.index ? " done" : ""}" data-step="${index}"><span>${escapeHtml(step.title)}</span>${index + 1}</button></li>`).join("");
  for (const button of $("guide-steps").querySelectorAll("button")) button.addEventListener("click", () => { lesson.index = Number(button.dataset.step); render(); });
  renderChoice();
}

$("guide-back").addEventListener("click", () => { lesson.index -= 1; render(); });
$("guide-next").addEventListener("click", () => { lesson.index = lesson.index === copy.steps.length ? 0 : lesson.index + 1; render(); });
render();
