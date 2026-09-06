// Render generated dist/docs/ documents, internal docs/, and the physical form
// specification into dist/site/docs/, served at /docs by tasks/serve.mjs.
// content/graph.json declares player sources: rules.md, world.md, component
// records, and reference layouts. This reader adds presentation only.
// No third-party Markdown dependency: the converter below covers exactly the
// Markdown subset these documents use.

import { mkdir, readFile, readdir, rename, rm, writeFile } from "node:fs/promises";
import { randomUUID } from "node:crypto";
import { basename, resolve } from "node:path";
import { stripSectionMarkers } from "./content/authored.mjs";

const projectRoot = resolve(import.meta.dirname, "..");
const docsDir = resolve(projectRoot, "docs");
const generatedDocsDir = resolve(projectRoot, "dist/docs");
const physicalDir = resolve(projectRoot, "physical");
const outDir = resolve(projectRoot, "dist/site/docs");
const checkOnly = process.argv.slice(2).includes("--check");

function escapeHtml(text) {
  return text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
}

function slugify(text) {
  return text
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
}

function renderedDocHref(href) {
  return href.replace(/^(\.\/)?([^/?#]+)\.md([?#].*)?$/, "$1$2.html$3");
}

// Inline: escape, protect code spans, then links, bold, italic.
function renderInline(text) {
  const codeSpans = [];
  let working = text.replace(/`([^`]+)`/g, (_, code) => {
    codeSpans.push(code);
    return `\u0000${codeSpans.length - 1}\u0000`;
  });
  working = escapeHtml(working);
  working = working.replace(
    /\[([^\]]+)\]\(([^)]+)\)/g,
    (_, label, href) =>
      `<a href="${escapeHtml(renderedDocHref(href))}">${label}</a>`
  );
  working = working.replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");
  working = working.replace(/(^|[^A-Za-z0-9])__([^_]+)__($|[^A-Za-z0-9])/g, "$1<strong>$2</strong>$3");
  working = working.replace(/(^|[^*])\*([^*]+)\*/g, "$1<em>$2</em>");
  working = working.replace(/(^|[^A-Za-z0-9])_([^_]+)_($|[^A-Za-z0-9])/g, "$1<em>$2</em>$3");
  working = working.replace(
    /\u0000(\d+)\u0000/g,
    (_, index) => `<code>${escapeHtml(codeSpans[Number(index)])}</code>`
  );
  return working;
}

function renderTable(rows) {
  const cells = (line) =>
    line
      .trim()
      .replace(/^\||\|$/g, "")
      .split("|")
      .map((cell) => cell.trim());
  const header = cells(rows[0]);
  const aligns = cells(rows[1]).map((spec) => {
    const left = spec.startsWith(":");
    const right = spec.endsWith(":");
    if (left && right) return "center";
    if (right) return "right";
    return left ? "left" : "";
  });
  const body = rows.slice(2).map(cells);
  const th = header
    .map((cell, index) => {
      const align = aligns[index] ? ` style="text-align:${aligns[index]}"` : "";
      return `<th${align}>${renderInline(cell)}</th>`;
    })
    .join("");
  const trs = body
    .map((row) => {
      const tds = row
        .map((cell, index) => {
          const align = aligns[index] ? ` style="text-align:${aligns[index]}"` : "";
          return `<td${align}>${renderInline(cell)}</td>`;
        })
        .join("");
      return `<tr>${tds}</tr>`;
    })
    .join("\n");
  return `<table>\n<thead><tr>${th}</tr></thead>\n<tbody>\n${trs}\n</tbody>\n</table>`;
}

// Indentation-driven list builder; supports nested ordered/unordered lists.
function renderList(items) {
  let html = "";
  const stack = []; // { indent, tag }
  for (const item of items) {
    while (stack.length && item.indent < stack[stack.length - 1].indent) {
      html += `</li></${stack.pop().tag}>`;
    }
    if (!stack.length || item.indent > stack[stack.length - 1].indent) {
      stack.push({ indent: item.indent, tag: item.tag });
      html += `<${item.tag}><li>${renderInline(item.text)}`;
    } else {
      html += `</li><li>${renderInline(item.text)}`;
    }
  }
  while (stack.length) html += `</li></${stack.pop().tag}>`;
  return html;
}

function isListLine(line) {
  const match = line.match(/^(\s*)([-*]|\d+\.)\s+(.*)$/);
  if (!match) return null;
  return {
    indent: match[1].length,
    tag: /\d+\./.test(match[2]) ? "ol" : "ul",
    text: match[3]
  };
}

function markdownToHtml(markdown) {
  const lines = markdown.split("\n");
  const blocks = [];
  const headings = [];
  let index = 0;

  while (index < lines.length) {
    const line = lines[index];

    if (line.trim() === "") {
      index += 1;
      continue;
    }

    // Fenced code block.
    if (line.trim().startsWith("```")) {
      const code = [];
      index += 1;
      while (index < lines.length && !lines[index].trim().startsWith("```")) {
        code.push(lines[index]);
        index += 1;
      }
      index += 1;
      blocks.push(`<pre><code>${escapeHtml(code.join("\n"))}</code></pre>`);
      continue;
    }

    // Heading.
    const heading = line.match(/^(#{1,6})\s+(.*)$/);
    if (heading) {
      const level = heading[1].length;
      const text = heading[2].trim();
      const slug = slugify(text);
      headings.push({ level, text, slug });
      blocks.push(`<h${level} id="${slug}">${renderInline(text)}</h${level}>`);
      index += 1;
      continue;
    }

    // Horizontal rule.
    if (/^(-{3,}|\*{3,}|_{3,})$/.test(line.trim())) {
      blocks.push("<hr>");
      index += 1;
      continue;
    }

    // Table (header row followed by a separator row).
    if (line.includes("|") && index + 1 < lines.length && /^\s*\|?[\s:|-]+\|[\s:|-]+$/.test(lines[index + 1])) {
      const rows = [];
      while (index < lines.length && lines[index].includes("|")) {
        rows.push(lines[index]);
        index += 1;
      }
      blocks.push(renderTable(rows));
      continue;
    }

    // Blockquote.
    if (line.trim().startsWith(">")) {
      const quote = [];
      while (index < lines.length && lines[index].trim().startsWith(">")) {
        quote.push(lines[index].replace(/^\s*>\s?/, ""));
        index += 1;
      }
      blocks.push(`<blockquote>${renderInline(quote.join(" "))}</blockquote>`);
      continue;
    }

    // List.
    if (isListLine(line)) {
      const items = [];
      while (index < lines.length && (isListLine(lines[index]) || (lines[index].trim() !== "" && items.length && /^\s+\S/.test(lines[index]) && !isListLine(lines[index])))) {
        const item = isListLine(lines[index]);
        if (item) {
          items.push(item);
        } else {
          // Continuation line wraps into the previous item.
          items[items.length - 1].text += ` ${lines[index].trim()}`;
        }
        index += 1;
      }
      blocks.push(renderList(items));
      continue;
    }

    // Paragraph (gather until blank line or a new block starts).
    const paragraph = [];
    while (
      index < lines.length &&
      lines[index].trim() !== "" &&
      !/^#{1,6}\s/.test(lines[index]) &&
      !lines[index].trim().startsWith("```") &&
      !lines[index].trim().startsWith(">") &&
      !isListLine(lines[index])
    ) {
      paragraph.push(lines[index].trim());
      index += 1;
    }
    blocks.push(`<p>${renderInline(paragraph.join(" "))}</p>`);
  }

  return { body: blocks.join("\n"), headings };
}

const STYLE = `:root {
  color-scheme: light;
  --ink: #000;
  --muted: #4d4d4d;
  --paper: #fff;
  --paper-2: #fff;
  --line: #000;
  --night: #000;
  --signal: #000;
  --power: #c9a227;
  --shadow: rgba(0, 0, 0, 0.16);
}
* { box-sizing: border-box; }
body {
  margin: 0;
  font: 17px/1.72 Georgia, "Times New Roman", serif;
  color: var(--ink);
  background: var(--paper);
}
.layout { display: grid; grid-template-columns: 300px minmax(0, 1fr); min-height: 100vh; }
nav.sidebar {
  position: sticky; top: 0; align-self: start; height: 100vh; overflow-y: auto;
  padding: 1.5rem 1.25rem; background: var(--night); color: #fff; font: 0.9rem/1.45 "Avenir Next", "Gill Sans", sans-serif;
}
nav.sidebar .brand { font-size: 0.8rem; letter-spacing: 0.08em; text-transform: uppercase; color: #fff; margin: 0 0 1rem; font-weight: 700; }
nav.sidebar .kit-summary { margin: 0 0 1rem; color: #c0c0c0; font-size: 0.76rem; line-height: 1.45; letter-spacing: .08em; text-transform: uppercase; }
nav.sidebar .nav-link { display: flex; align-items: baseline; justify-content: space-between; gap: 0.5rem; color: #fff; text-decoration: none; padding: 0.5rem 0.6rem; border-left: 2px solid transparent; }
nav.sidebar .nav-link:hover { background: #242424; color: #fff; }
nav.sidebar .nav-link.current { border-left-color: var(--power); background: #242424; color: #fff; font-weight: 700; }
nav.sidebar .nav-link .rt { font-size: 0.7rem; color: #c0c0c0; white-space: nowrap; }
nav.sidebar .nav-link.current .rt { color: #fff; }
nav.sidebar .toc { margin: 0.15rem 0 0.7rem 0.5rem; border-left: 1px solid #666; padding-left: 0.7rem; }
nav.sidebar .toc a { display: block; font-size: 0.82rem; color: #c0c0c0; padding: 0.12rem 0; text-decoration: none; }
nav.sidebar .toc a:hover { color: #fff; }
nav.sidebar .toc a.lvl-3 { padding-left: 0.75rem; }
nav.sidebar .toc a.lvl-4 { padding-left: 1.5rem; }
main { padding: 2.5rem clamp(1rem, 5vw, 4rem); max-width: 68rem; }
main h1, main h2, main h3, main h4 { font-family: "Avenir Next", "Gill Sans", "Trebuchet MS", sans-serif; }
main h1 { font-size: 2.35rem; line-height: 1.1; margin: 0 0 0.7rem; letter-spacing: -.03em; }
main h2 { margin-top: 2.7rem; padding-bottom: 0.45rem; border-bottom: 2px solid var(--night); font-size: 1.35rem; }
main h3 { margin-top: 1.8rem; }
main h4 { margin-top: 1.3rem; color: var(--muted); }
a { color: var(--ink); text-decoration-thickness: 1px; text-underline-offset: .18em; }
code { background: #f2f2f2; padding: 0.1em 0.35em; border-radius: 0; font-size: 0.86em; }
pre { background: var(--night); color: #fff; padding: 1rem 1.2rem; border-radius: 0; overflow-x: auto; }
pre code { background: none; padding: 0; color: inherit; }
blockquote { margin: 1.2rem 0; padding: 0.6rem 1.1rem; border-left: 4px solid var(--power); background: #f2f2f2; color: var(--ink); border-radius: 0; }
table { border-collapse: collapse; width: 100%; margin: 1.2rem 0; font-size: 0.94rem; }
th, td { border: 1px solid var(--line); padding: 0.5rem 0.7rem; text-align: left; vertical-align: top; }
thead th { background: #000; color: #fff; font-family: "Avenir Next", "Gill Sans", sans-serif; }
tbody tr:nth-child(even) { background: #f2f2f2; }
hr { border: none; border-top: 1px solid var(--line); margin: 2rem 0; }
/* Document index: one title and one list. */
main.document-index { max-width:42rem; margin:0 auto; padding:clamp(1.5rem,6vw,4rem) 1.25rem; font:18px/1.6 system-ui,sans-serif; }
main.document-index h1 { margin:0 0 1.5rem; font:700 clamp(1.8rem,6vw,2.4rem)/1.2 system-ui,sans-serif; letter-spacing:normal; }
.article-list { margin:0; padding:0; list-style:none; }
.article-list a { display:block; width:fit-content; max-width:100%; padding:.5rem 0; overflow-wrap:anywhere; }
.article-list a:hover { text-decoration-thickness:2px; }
.article-list a:focus-visible { outline:2px solid currentColor; outline-offset:4px; }
@media (max-width: 820px) {
  .layout { display: block; }
  nav.sidebar {
    position: static;
    height: auto;
    display: flex;
    align-items: center;
    gap: 0.55rem;
    padding: 0.72rem 1rem;
    overflow-x: auto;
    white-space: nowrap;
  }
  nav.sidebar .brand { margin: 0 0.35rem 0 0; }
  nav.sidebar .nav-link { display: none; }
  nav.sidebar .nav-link.current { display: inline-flex; padding: 0.32rem 0.5rem; }
  nav.sidebar .toc { display: none; }
  main {
    max-width: 42rem;
    padding: 1.5rem 1.15rem 3rem;
    font-size: 1.0625rem;
    line-height: 1.78;
  }
  main h1 { font-size: clamp(1.8rem, 8vw, 2.35rem); }
  main h2 { margin-top: 2.8rem; font-size: 1.45rem; line-height: 1.25; }
  main h3 { margin-top: 2.15rem; font-size: 1.18rem; line-height: 1.3; }
  main h2, main h3, main h4 { scroll-margin-top: 1rem; }
  table {
    display: block;
    width: 100%;
    overflow-x: auto;
    -webkit-overflow-scrolling: touch;
    font-size: 0.86rem;
  }
  th, td { min-width: 7.5rem; }
  pre { margin-inline: -0.15rem; padding: 0.85rem 1rem; font-size: 0.82rem; }
}
@media (max-width: 420px) {
  main { padding-inline: 1rem; font-size: 1rem; }
  nav.sidebar { padding-inline: 0.85rem; }
  nav.sidebar .brand { font-size: 0.7rem; }
  nav.sidebar .nav-link.current .rt { display: none; }
  th, td { min-width: 6.5rem; padding: 0.45rem 0.55rem; }
}`;

// Human-readable, sentence-case navigation title from the file slug, so multiple
// docs whose Markdown H1 is literally "Mandate 2038" get distinct labels.
function humanizeTitle(slug) {
  const title = slug.replaceAll("-", " ");
  return title.charAt(0).toUpperCase() + title.slice(1);
}

function page({ title, docs, current, tocHtml, bodyHtml }) {
  const links = docs
    .map((doc) => {
      const isCurrent = doc.slug === current;
      const toc = isCurrent ? tocHtml : "";
      return `<a class="nav-link ${isCurrent ? "current" : ""}" href="${doc.slug}.html"><span>${escapeHtml(doc.label)}</span></a>${toc}`;
    })
    .join("\n");
  return `<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Mandate 2038: ${escapeHtml(title)}</title>
<style>${STYLE}</style>
</head>
<body>
${current === "index" ? '<main class="document-index">' : `<div class="layout">
<nav class="sidebar">
<a class="nav-link ${current === "index" ? "current" : ""}" href="index.html"><span>Overview</span></a>
${links}
</nav>
<main>`}
<h1 class="site-title">${current === "index" ? "Mandate 2038" : `Mandate 2038: ${escapeHtml(title)}`}</h1>
${bodyHtml}
</main>
${current === "index" ? "" : "</div>"}
</body>
</html>
`;
}

function withoutLeadingH1(body) {
  return body.replace(/^<h1\b[^>]*>[\s\S]*?<\/h1>\n?/, "");
}

function firstHeadingTitle(headings, fallback) {
  const h1 = headings.find((heading) => heading.level === 1);
  return h1 ? h1.text : fallback;
}

const sources = [
  ...(await readdir(docsDir))
    .filter((name) => name.endsWith(".md"))
    .map((file) => ({ file, sourceDir: docsDir })),
  ...(await readdir(generatedDocsDir))
    .filter((name) => name.endsWith(".md"))
    .map((file) => ({ file, sourceDir: generatedDocsDir })),
  ...["component-spec.md"].map((file) => ({
    file,
    sourceDir: physicalDir
  }))
].sort((left, right) => left.file.localeCompare(right.file));

const rendered = [];
for (const { file, sourceDir } of sources) {
  const markdown = stripSectionMarkers(await readFile(resolve(sourceDir, file), "utf8"));
  const { body, headings } = markdownToHtml(markdown);
  const slug = basename(file, ".md");
  rendered.push({
    slug,
    file,
    body,
    headings,
    title: firstHeadingTitle(headings, slug),
    label: humanizeTitle(slug)
  });
}

const playKit = [
  "core-rules",
  "map-reference",
  "component-reference",
  "card-reference"
];
const playKitDocs = playKit
  .map((slug) => rendered.find((doc) => doc.slug === slug))
  .filter(Boolean);
const docList = playKitDocs.map((doc) => ({
  slug: doc.slug,
  label: doc.label
}));

function tocFor(headings) {
  const entries = headings.filter((heading) => heading.level >= 2 && heading.level <= 4);
  if (!entries.length) return "";
  const items = entries
    .map((heading) => `<a class="lvl-${heading.level}" href="#${heading.slug}">${escapeHtml(heading.text)}</a>`)
    .join("\n");
  return `<div class="toc">${items}</div>`;
}

const pages = [];
for (const doc of rendered) {
  pages.push({
    path: resolve(outDir, `${doc.slug}.html`),
    label: `dist/site/docs/${doc.slug}.html`,
    html: page({
      title: doc.label,
      docs: docList,
      current: doc.slug,
      tocHtml: tocFor(doc.headings),
      bodyHtml: withoutLeadingH1(doc.body)
    })
  });
}

const indexDocs = [...playKitDocs, rendered.find((doc) => doc.slug === "world-and-institutions")].filter(Boolean);
const indexBody = `<ul class="article-list">
${indexDocs.map((doc) => `<li><a href="${doc.slug}.html">${escapeHtml(doc.label)}</a></li>`).join("\n")}
</ul>`;

pages.push({
  path: resolve(outDir, "index.html"),
  label: "dist/site/docs/index.html",
  html: page({
    title: "Overview",
    docs: docList,
    current: "index",
    tocHtml: "",
    bodyHtml: indexBody
  })
});

if (checkOnly) {
  const stale = [];
  const expectedNames = new Set(pages.map((item) => basename(item.path)));
  let actualNames = [];
  try {
    actualNames = (await readdir(outDir)).filter((name) => name.endsWith(".html"));
  } catch {
    actualNames = [];
  }
  for (const name of actualNames) {
    if (!expectedNames.has(name)) stale.push(`dist/site/docs/${name} (orphaned)`);
  }
  for (const item of pages) {
    let actual;
    try {
      actual = await readFile(item.path, "utf8");
    } catch {
      stale.push(`${item.label} (missing)`);
      continue;
    }
    if (actual !== item.html) stale.push(item.label);
  }
  if (stale.length) {
    process.stderr.write(
      `docs-html: drift detected:\n${stale.map((path) => `- ${path}`).join("\n")}\nRun npm run docs:html.\n`
    );
    process.exit(1);
  }
  process.stdout.write(`docs-html: verified ${pages.length} rendered pages\n`);
} else {
  await mkdir(outDir, { recursive: true });
  for (const item of pages) {
    const temporary = `${item.path}.${randomUUID()}.tmp`;
    try {
      await writeFile(temporary, item.html, { flag: "wx" });
      await rename(temporary, item.path);
    } finally {
      await rm(temporary, { force: true });
    }
  }
  const expectedNames = new Set(pages.map((item) => basename(item.path)));
  for (const name of (await readdir(outDir)).filter((item) => item.endsWith(".html"))) {
    if (!expectedNames.has(name)) {
      await rm(resolve(outDir, name), { force: true });
    }
  }
  process.stdout.write(`docs-html: rendered ${pages.length} pages to dist/site/docs/\n`);
}
