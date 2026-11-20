// Browser equivalence and scaling check for page-query.js: existing snapshot/handle parity
// against direct querySelectorAll uniqueness checks across standards/quirks mode, duplicate
// id/name/href, CSS special characters, inline SVG, outlines/regionGroups, and 10k-link DOMs.
import assert from 'node:assert/strict';
import { chromium } from 'playwright-core';
import { loadServiceConfig } from '../../src/config.js';
import { playwrightLaunchOptions } from '../../src/browser-launch.js';
import { buildSnapshot, queryPage, snapshotArgs } from '../../src/adapters/page-query.js';

function referenceQueryPage({
  mode,
  selector,
  maxElements,
  maxTextChars,
  elementTextChars,
  regions = [],
  regionGroups = [],
  outline = false,
  readRoots = null,
}) {
  const WIDGET_ROLES = ['button', 'link', 'checkbox', 'radio', 'switch', 'combobox', 'listbox', 'option',
    'menuitem', 'menuitemcheckbox', 'menuitemradio', 'tab', 'textbox', 'searchbox', 'spinbutton', 'slider'];
  const INTERACTIVE = ['a[href]', 'button', 'input', 'select', 'textarea',
    ...WIDGET_ROLES.map((role) => `[role="${role}"]`)].join(', ');
  const choiceOf = (node) => {
    const visibleText = (element) => (element.innerText ?? element.textContent ?? '').trim();
    if (node.tagName === 'SELECT') {
      const option = node.selectedOptions[0];
      return option ? { value: option.value, label: option.label.trim() } : { value: null, label: null };
    }
    const role = node.getAttribute('role');
    if (role === 'combobox') {
      const shown = ['INPUT', 'TEXTAREA'].includes(node.tagName) ? node.value.trim() : visibleText(node);
      return { value: shown, label: shown };
    }
    if (role === 'listbox') {
      const selected = node.querySelectorAll('[role="option"][aria-selected="true"]');
      const label = selected.length === 1 ? visibleText(selected[0]) : null;
      return { value: label, label };
    }
    return null;
  };
  const statesOf = (node) => [
    (node.getAttribute('aria-checked') === 'true' || (node.tagName === 'INPUT' && ['checkbox', 'radio'].includes(node.type) && node.checked)) && 'checked',
    node.getAttribute('aria-selected') === 'true' && 'selected',
    node.getAttribute('aria-expanded') === 'true' && 'expanded',
  ].filter(Boolean);
  const permissionRoots = readRoots === null ? null : readRoots.map((sel) => {
    const matches = document.querySelectorAll(sel);
    if (matches.length !== 1) throw Error('A shared region must still match exactly one element');
    return matches[0];
  });
  const permitted = (node) => permissionRoots === null || permissionRoots.some((root) => root === node || root.contains(node));
  const isUnique = (candidate) => {
    try {
      return document.querySelectorAll(candidate).length === 1;
    } catch {
      return false;
    }
  };
  const pathSelector = (node) => {
    const parts = [];
    for (let current = node; current && current !== document.documentElement; current = current.parentElement) {
      const tag = current.tagName.toLowerCase();
      const siblings = current.parentElement
        ? [...current.parentElement.children].filter((child) => child.tagName === current.tagName)
        : [current];
      parts.unshift(siblings.length > 1 ? `${tag}:nth-of-type(${siblings.indexOf(current) + 1})` : tag);
    }
    return `html > ${parts.join(' > ')}`;
  };
  const stableSelector = (node) => {
    const tag = node.tagName.toLowerCase();
    const candidates = [];
    if (node.id) candidates.push(`#${CSS.escape(node.id)}`);
    const name = node.getAttribute('name');
    if (name) candidates.push(`${tag}[name="${CSS.escape(name)}"]`);
    const href = node.getAttribute('href');
    if (href) candidates.push(`${tag}[href="${CSS.escape(href)}"]`);
    return candidates.find(isUnique) ?? pathSelector(node);
  };
  const fingerprint = (text) => {
    let hash = 0x811c9dc5;
    for (let index = 0; index < text.length; index += 1) {
      hash ^= text.charCodeAt(index);
      hash = Math.imul(hash, 0x01000193) >>> 0;
    }
    return `${text.length}:${hash.toString(16)}`;
  };
  const fullText = (node) => (node.innerText ?? node.textContent ?? '').trim();
  const describe = (node) => {
    const attributes = [...node.attributes]
      .map((attribute) => [attribute.name, attribute.value])
      .sort((a, b) => (a[0] < b[0] ? -1 : 1));
    const formAction = node.form && ['submit', 'image'].includes(node.type)
      ? (node.hasAttribute('formaction') ? node.formAction : node.form.action)
      : null;
    const text = fullText(node);
    return {
      tag: node.tagName.toLowerCase(),
      attributes,
      text: text.slice(0, elementTextChars),
      textFingerprint: fingerprint(text),
      value: 'value' in node ? String(node.value) : null,
      href: node.href ?? null,
      formAction,
      ...(node.tagName === 'INPUT' && node.type === 'file' ? { inputType: 'file',
        files: [...node.files].map((file) => ({ name: file.name, byteLength: file.size })),
        multiple: node.multiple, disabled: node.matches(':disabled'), accept: node.accept } : {}),
    };
  };
  if (mode === 'element') {
    const nodes = [...document.querySelectorAll(selector)].filter(permitted);
    if (nodes.length !== 1) return { count: nodes.length, element: null, fullText: null, choice: null };
    return { count: 1, element: describe(nodes[0]), fullText: fullText(nodes[0]), choice: choiceOf(nodes[0]) };
  }
  const CONTROLS = 'input, select, textarea';
  const VALUE_TAGS = ['INPUT', 'SELECT', 'TEXTAREA'];
  const SKIPPED_TAGS = ['SCRIPT', 'STYLE', 'TEMPLATE'];
  const ROLES = { a: 'link', button: 'button', select: 'combobox', textarea: 'textbox' };
  const nodes = [...document.querySelectorAll(INTERACTIVE)].filter(permitted);
  const handleFor = (stable) => `h${fingerprint(stable).split(':')[1]}`;
  const handles = new Map();
  const issued = new Set();
  for (const node of nodes) {
    let handle = handleFor(stableSelector(node));
    for (let suffix = 2; issued.has(handle); suffix += 1) handle = `${handleFor(stableSelector(node))}-${suffix}`;
    issued.add(handle);
    handles.set(node, handle);
  }
  const roleOf = (node) => {
    const tag = node.tagName.toLowerCase();
    if (node.hasAttribute('role')) return node.getAttribute('role');
    if (tag === 'input') return ['checkbox', 'radio', 'submit', 'button'].includes(node.type) ? node.type : 'textbox';
    return node.getAttribute('role') ?? ROLES[tag] ?? tag;
  };
  const labelOf = (node) => {
    const labelText = (root) => {
      const visit = (current) => {
        if (current.nodeType === Node.TEXT_NODE) return current.textContent;
        if (current.nodeType !== Node.ELEMENT_NODE || (current !== root
          && current.matches('input, select, textarea, [role="combobox"], [role="listbox"], script, style'))) return '';
        return [...current.childNodes].map(visit).join(' ');
      };
      return visit(root);
    };
    const references = (node.getAttribute('aria-labelledby') ?? '').split(/\s+/).filter(Boolean);
    const referenced = references.map((id) => document.getElementById(id)).filter((value) => value && permitted(value));
    const labels = [...(node.labels ?? [])].filter(permitted);
    const text = referenced.map(labelText).join(' ') || node.getAttribute('aria-label')
      || labels.map(labelText).join(' ')
      || (['button', 'link', 'option', 'tab', 'menuitem'].includes(roleOf(node)) ? fullText(node) : '');
    return text.replace(/\s+/g, ' ').trim();
  };
  const renderOutline = (root) => {
    const parts = [];
    const visit = (node) => {
      if (node.nodeType === Node.TEXT_NODE) {
        const text = node.textContent.replace(/\s+/g, ' ').trim();
        if (text) parts.push(text);
        return;
      }
      if (node.nodeType !== Node.ELEMENT_NODE || SKIPPED_TAGS.includes(node.tagName)) return;
      const handle = handles.get(node);
      if (handle) {
        const name = (node.innerText ?? '').trim() || node.getAttribute('aria-label') || node.getAttribute('name') || '';
        const choice = node.tagName === 'SELECT' ? null : choiceOf(node);
        const value = VALUE_TAGS.includes(node.tagName) ? ` = ${JSON.stringify(String(node.value))}`
          : choice ? ` = ${JSON.stringify(choice.label ?? '')}` : '';
        const states = statesOf(node).map((state) => ` ${state}`).join('');
        parts.push(`[${handle} ${roleOf(node)} ${JSON.stringify(name)}${value}${states}]`);
        return;
      }
      node.childNodes.forEach(visit);
    };
    visit(root);
    return parts.join(' | ').slice(0, maxTextChars);
  };
  const describeRegion = (regionSelector, region, group = null) => {
    const controls = [...(region.matches(CONTROLS) ? [region] : []), ...region.querySelectorAll(CONTROLS)];
    return {
      selector: regionSelector,
      group,
      count: 1,
      html: region.outerHTML,
      values: controls.map((control) => String(control.value)),
      outline: outline ? renderOutline(region) : null,
    };
  };
  const readRegion = (regionSelector) => {
    let matches;
    try {
      matches = document.querySelectorAll(regionSelector);
    } catch {
      return { selector: regionSelector, count: 0, html: null, values: null, outline: null };
    }
    if (matches.length !== 1 || !permitted(matches[0])) return { selector: regionSelector, count: matches.length, html: null, values: null, outline: null };
    return describeRegion(regionSelector, matches[0]);
  };
  const readGroup = (groupSelector) => {
    try {
      return [...document.querySelectorAll(groupSelector)].filter(permitted).map((node) => describeRegion(stableSelector(node), node, groupSelector));
    } catch {
      return [];
    }
  };
  return {
    url: location.href,
    title: permissionRoots === null ? document.title : '',
    html: document.documentElement.outerHTML,
    text: (permissionRoots === null ? (document.body?.innerText ?? '') : permissionRoots.map(fullText).join('\n')).slice(0, maxTextChars),
    isTruncated: nodes.length > maxElements,
    elements: nodes.slice(0, maxElements).map((node) => ({ selector: stableSelector(node), handle: handles.get(node),
      role: roleOf(node), label: labelOf(node), inputType: node.tagName === 'INPUT' ? node.type : '', ...describe(node) })),
    regions: [...regions.map(readRegion), ...regionGroups.flatMap(readGroup)],
  };
}

const config = loadServiceConfig(undefined, {
  browserChannel: process.env.FAWN_WORKSPACE_TEST_BROWSER_CHANNEL ?? 'chrome',
  headless: true,
});
const browser = await chromium.launch({
  ...playwrightLaunchOptions(config.browser),
  headless: true,
});

try {
  const page = await browser.newPage();
  const bodyMarkup = `
    <main id="scope">
      <a id="unique:id.[0]#\\"\\\\" href="/dup">Unique escaped ID</a>
      <a id="CaseId" href="/case-a">Case A</a>
      <a id="caseid" href="/case-b">Case B</a>
      <a id="dup-id" name="dup-name" href="/dup">Dup 1</a>
      <a id="dup-id" name="dup-name" href="/dup">Dup 2</a>
      <input name="unique\\"name[1]" value="alpha" />
      <input name="shared-name" value="one" />
      <input name="shared-name" value="two" />
      <a href="/svg-collide">HTML colliding anchor</a>
      <svg viewBox="0 0 10 10">
        <a href="/svg-collide"><text>SVG colliding anchor</text></a>
        <a href="/svg-only"><text>SVG unique anchor</text></a>
        <foreignObject name="camel-only" role="button">Camel tag</foreignObject>
      </svg>
      <section class="card" id="card-1"><button>First card action</button></section>
      <section class="card"><button>Second card action</button><a href="/tail-link">Tail link</a></section>
    </main>
  `;

  for (const doctype of ['<!DOCTYPE html>', '']) {
    await page.setContent(`${doctype}<html><head><title>Parity</title></head><body>${bodyMarkup}</body></html>`);
    for (const opts of [
      { outline: false, regions: [], regionGroups: [], readRoots: null, maxElements: 5 },
      { outline: false, regions: ['#scope'], regionGroups: ['.card'], readRoots: null, maxElements: 50 },
      { outline: true, regions: ['#scope'], regionGroups: ['.card'], readRoots: ['#scope'], maxElements: 4 },
    ]) {
      const args = { ...snapshotArgs(config, opts), maxElements: opts.maxElements };
      const actualRaw = await page.evaluate(queryPage, args);
      // Actionability is intentionally new and independently exercised by
      // workflow-actionability.test.js. Preserve exact parity for every old field,
      // including legacy digests, handles, permission scopes and truncation.
      for (const element of actualRaw.elements) delete element.actionability;
      const actual = buildSnapshot(actualRaw, 1);
      const expected = buildSnapshot(await page.evaluate(referenceQueryPage, args), 1);
      assert.deepEqual(actual, expected);
    }
  }

  const anchors = Array.from({ length: 10000 }, (_, i) => (
    i % 3 === 0
      ? `<a href="#sec-${i}">Section ${i}</a>`
      : `<a href="#shared-${i % 17}">Repeated ${i}</a>`
  )).join('');
  await page.setContent(`<!DOCTYPE html><html><body><main id="big">${anchors}</main></body></html>`);
  const started = performance.now();
  const large = buildSnapshot(await page.evaluate(queryPage, snapshotArgs(config)), 1);
  const elapsedMs = performance.now() - started;
  assert.equal(large.isTruncated, true);
  assert.equal(large.elements.length, config.observation.maxElements);
  assert.ok(elapsedMs < 1500, `Expected linear 10k-anchor snapshot < 1500ms, got ${elapsedMs.toFixed(1)}ms`);
  console.log(`ok: page-query legacy-field parity and 10k-anchor linear scaling (${elapsedMs.toFixed(1)}ms)`);
} finally {
  await browser.close();
}
