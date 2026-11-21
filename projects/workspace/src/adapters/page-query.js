// Fawn workspace — page query shared by the narrow browser adapters
//
// One in-page reader produces observations and element probes for every adapter, so element
// identity and content hashes mean the same thing whichever protocol drives Chromium.

import { canonicalJson, sha256Hex } from '../journal.js';

const SNAPSHOT_MODE = 'snapshot';
const ELEMENT_MODE = 'element';
const ELEMENT_TEXT_CHARS = 200;

// Runs inside the page; must stay self-contained.
function queryPage({ mode, selector, maxElements, maxRegions = 16, maxTextChars, elementTextChars, regions = [], regionGroups = [], outline = false, readRoots = null, includeFormState = false, autoControlRegions = false }) {
  // A typed password never leaves the page: observations, evidence and digests see only whether
  // the field is filled. A person enters credentials; agents and journals do not read them.
  const controlValue = (node) => node.tagName === 'INPUT' && node.type === 'password' ? (node.value ? '[hidden]' : '') : String(node.value);
  // Custom widgets declare their ARIA role; without these, a custom dropdown and its options
  // never appear in an observation and cannot be targeted.
  const WIDGET_ROLES = ['button', 'link', 'checkbox', 'radio', 'switch', 'combobox', 'listbox', 'option',
    'menuitem', 'menuitemcheckbox', 'menuitemradio', 'tab', 'textbox', 'searchbox', 'spinbutton', 'slider'];
  const INTERACTIVE = ['a[href]', 'button', 'input', 'select', 'textarea', ...WIDGET_ROLES.map((role) => `[role="${role}"]`)].join(', ');
  // The choice a select, combobox or listbox currently shows: native selects report the selected
  // option; ARIA comboboxes their own value or text; listboxes their one aria-selected option.
  // Null for other elements, and a null label when the page shows no single choice.
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
  const permissionRoots = readRoots === null ? null : readRoots.map(selector => {
    const matches = document.querySelectorAll(selector);
    if (matches.length !== 1) throw Error('A shared region must still match exactly one element');
    return matches[0];
  });
  const permitted = node => permissionRoots === null || permissionRoots.some(root => root === node || root.contains(node));
  // FNV-1a over the full text, so identity covers text beyond the displayed prefix.
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
      // Live rendering hints, not authority or a promise that dispatch will succeed.
      actionability: {
        visible: node.getClientRects().length > 0 && getComputedStyle(node).visibility !== 'hidden'
          && getComputedStyle(node).visibility !== 'collapse',
        inert: Boolean(node.closest('[inert], [aria-hidden="true"]')),
        disabled: node.matches(':disabled') || Boolean(node.closest('[aria-disabled="true"]')),
      },
      attributes,
      text: text.slice(0, elementTextChars),
      textFingerprint: fingerprint(text),
      value: 'value' in node ? controlValue(node) : null,
      href: node.href ?? null,
      formAction,
      ...(node.tagName === 'INPUT' && node.type === 'file' ? { inputType: 'file',
        files: [...node.files].map(file => ({ name: file.name, byteLength: file.size })),
        multiple: node.multiple, disabled: node.matches(':disabled'), accept: node.accept } : {}),
    };
  };
  if (mode === 'element') {
    const nodes = [...document.querySelectorAll(selector)].filter(permitted);
    if (nodes.length !== 1) return { count: nodes.length, element: null, fullText: null, choice: null };
    return { count: 1, element: describe(nodes[0]), fullText: fullText(nodes[0]), choice: choiceOf(nodes[0]) };
  }
  const HTML_NS = 'http://www.w3.org/1999/xhtml';
  const standardsMode = document.compatMode === 'CSS1Compat';
  const idCounts = new Map();
  const idFoldCounts = standardsMode ? null : new Map();
  const nameCounts = new Map();
  const hrefCounts = new Map();
  const selectorTagOf = (el) => (el.namespaceURI === HTML_NS
    ? el.tagName.toLowerCase()
    : (el.localName === el.localName?.toLowerCase() ? el.localName : null));
  for (const el of document.querySelectorAll('[id], [name], [href]')) {
    if (el.id) {
      idCounts.set(el.id, (idCounts.get(el.id) ?? 0) + 1);
      if (idFoldCounts) {
        const folded = el.id.toLowerCase();
        idFoldCounts.set(folded, (idFoldCounts.get(folded) ?? 0) + 1);
      }
    }
    const matchTag = selectorTagOf(el);
    if (!matchTag) continue;
    const name = el.getAttribute('name');
    if (name) {
      const key = `${matchTag}\0${name}`;
      nameCounts.set(key, (nameCounts.get(key) ?? 0) + 1);
    }
    const href = el.getAttribute('href');
    if (href) {
      const key = `${matchTag}\0${href}`;
      hrefCounts.set(key, (hrefCounts.get(key) ?? 0) + 1);
    }
  }
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
  const selectors = new Map();
  const stableSelector = (node) => {
    const cached = selectors.get(node);
    if (cached !== undefined) return cached;
    const tag = node.tagName.toLowerCase();
    const fastTag = selectorTagOf(node) === tag && CSS.escape(tag) === tag;
    let chosen = null;
    if (node.id) {
      const candidate = `#${CSS.escape(node.id)}`;
      const unique = standardsMode
        ? idCounts.get(node.id) === 1
        : (idFoldCounts.get(node.id.toLowerCase()) === 1 || (idCounts.get(node.id) === 1 && isUnique(candidate)));
      if (unique) chosen = candidate;
    }
    if (!chosen) {
      const name = node.getAttribute('name');
      if (name) {
        const candidate = `${tag}[name="${CSS.escape(name)}"]`;
        if (fastTag ? nameCounts.get(`${tag}\0${name}`) === 1 : isUnique(candidate)) chosen = candidate;
      }
    }
    if (!chosen) {
      const href = node.getAttribute('href');
      if (href) {
        const candidate = `${tag}[href="${CSS.escape(href)}"]`;
        if (fastTag ? hrefCounts.get(`${tag}\0${href}`) === 1 : isUnique(candidate)) chosen = candidate;
      }
    }
    chosen ??= pathSelector(node);
    selectors.set(node, chosen);
    return chosen;
  };
  const CONTROLS = 'input, select, textarea';
  const VALUE_TAGS = ['INPUT', 'SELECT', 'TEXTAREA'];
  const SKIPPED_TAGS = ['SCRIPT', 'STYLE', 'TEMPLATE'];
  const ROLES = { a: 'link', button: 'button', select: 'combobox', textarea: 'textbox' };
  const roots = permissionRoots;
  const allowed = permitted;
  const nodes = [...document.querySelectorAll(INTERACTIVE)].filter(allowed);
  // A handle names an element by its stable selector, so it survives unrelated page changes.
  const handleFor = (stable) => `h${fingerprint(stable).split(':')[1]}`;
  const handles = new Map();
  const issued = new Set();
  const handleNodes = outline && (regions.length > 0 || regionGroups.length > 0)
    ? nodes
    : nodes.slice(0, maxElements);
  for (const node of handleNodes) {
    const base = handleFor(stableSelector(node));
    let handle = base;
    for (let suffix = 2; issued.has(handle); suffix += 1) handle = `${base}-${suffix}`;
    issued.add(handle);
    handles.set(node, handle);
  }
  const roleOf = (node) => {
    const tag = node.tagName.toLowerCase();
    if (node.hasAttribute('role')) return node.getAttribute('role');
    if (tag === 'input') return ['checkbox', 'radio', 'submit', 'button'].includes(node.type) ? node.type : 'textbox';
    return node.getAttribute('role') ?? ROLES[tag] ?? tag;
  };
  // A bounded label reader, not a replacement for Chromium's accessibility-name algorithm.
  // Never use a textbox's current value or a select's option list as its label.
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
    const referenced = references.map(id => document.getElementById(id)).filter(value => value && permitted(value));
    const labels = [...(node.labels ?? [])].filter(permitted);
    const text = referenced.map(labelText).join(' ') || node.getAttribute('aria-label')
      || labels.map(labelText).join(' ')
      || (['button', 'link', 'option', 'tab', 'menuitem'].includes(roleOf(node)) ? fullText(node) : '');
    return text.replace(/\s+/g, ' ').trim();
  };
  // Compact outline: collapsed text and interactive elements as [handle role "name" = "value"].
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
        const value = VALUE_TAGS.includes(node.tagName) ? ` = ${JSON.stringify(controlValue(node))}`
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
      values: controls.map((control) => controlValue(control)),
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
    if (matches.length !== 1 || !allowed(matches[0])) return { selector: regionSelector, count: matches.length, html: null, values: null, outline: null };
    return describeRegion(regionSelector, matches[0]);
  };
  // Every element matching a group selector becomes its own region, named by its stable selector.
  const readGroup = (groupSelector) => {
    try {
      return [...document.querySelectorAll(groupSelector)].filter(allowed).map((node) => describeRegion(stableSelector(node), node, groupSelector));
    } catch {
      return [];
    }
  };
  const formsList = includeFormState ? [...document.querySelectorAll('form')] : null;
  const formKeyOf = (node) => {
    if (!formsList) return undefined;
    const form = node.form ?? node.closest('form');
    if (!form) return null;
    if (form.id) return `#${form.id}`;
    const idx = formsList.indexOf(form);
    return idx >= 0 ? `form@${idx}` : null;
  };
  const isDefaultControlValue = (node) => {
    if (!includeFormState) return undefined;
    if (node.tagName === 'SELECT') {
      const options = [...node.options];
      if (!options.length) return true;
      const hasExplicitDefault = options.some((o) => o.defaultSelected);
      return hasExplicitDefault
        ? options.every((o) => o.selected === o.defaultSelected)
        : (node.selectedIndex <= 0 || node.value === '');
    }
    if (node.tagName === 'INPUT' && ['checkbox', 'radio'].includes(node.type)) {
      return Boolean(node.checked) === Boolean(node.defaultChecked);
    }
    if ('value' in node) {
      const current = controlValue(node);
      return current === '' || current === String(node.defaultValue ?? '');
    }
    return true;
  };
  const mappedElements = nodes.slice(0, maxElements).map((node, idx) => ({
    _node: node,
    item: {
      selector: stableSelector(node),
      handle: handles.get(node),
      role: roleOf(node),
      label: labelOf(node),
      inputType: node.tagName === 'INPUT' ? node.type : '',
      ...describe(node),
      ...(includeFormState ? { formKey: formKeyOf(node), isDefaultValue: isDefaultControlValue(node) } : {}),
    },
    idx,
  }));
  const explicitRegions = new Set(regions);
  const autoRegions = [];
  if (autoControlRegions) {
    for (const { _node, item } of mappedElements) {
      if (explicitRegions.size + autoRegions.length >= maxRegions) break;
      if (!item.selector || explicitRegions.has(item.selector)) continue;
      if (document.querySelectorAll(item.selector).length !== 1) continue;
      explicitRegions.add(item.selector);
      autoRegions.push(describeRegion(item.selector, _node));
    }
  }
  return {
    url: location.href,
    title: roots === null ? document.title : '',
    html: document.documentElement.outerHTML,
    text: (roots === null ? (document.body?.innerText ?? '') : roots.map(fullText).join('\n')).slice(0, maxTextChars),
    isTruncated: nodes.length > maxElements,
    elements: mappedElements.map(({ item }) => item),
    regions: [...regions.map(readRegion), ...autoRegions, ...regionGroups.flatMap(readGroup)],
  };
}

function elementDigest(element) {
  return sha256Hex(canonicalJson({
    tag: element.tag,
    attributes: element.attributes,
    ...(element.actionability ? { actionability: element.actionability } : {}),
    text: element.text,
    textFingerprint: element.textFingerprint,
    ...(element.formAction ? { formAction: element.formAction } : {}),
  }));
}

/** Structural hints exclude instance IDs, prose, URLs and control values; never authority. */
function structuralLocator(element) {
  return [element.role ?? '', (element.label ?? '').replace(/\s+/g, ' ').trim(),
    element.tag ?? '', element.inputType ?? ''];
}

function structuralOutlineHash(elements) {
  return sha256Hex(canonicalJson(elements.map(structuralLocator)));
}

function snapshotArgs(config, { regions = [], regionGroups = [], outline = false, readRoots = null, includeFormState = false, autoControlRegions = false } = {}) {
  return {
    mode: SNAPSHOT_MODE,
    readRoots,
    maxElements: config.observation.maxElements,
    maxTextChars: config.observation.maxTextChars,
    elementTextChars: ELEMENT_TEXT_CHARS,
    regions,
    regionGroups,
    outline,
    ...(includeFormState ? { includeFormState: true } : {}),
    ...(autoControlRegions ? { autoControlRegions: true, maxRegions: config.observation.maxRegions } : {}),
  };
}

/** A region digest covers its markup and control values; a missing or ambiguous region has none. */
function regionDigest(region) {
  return region.count === 1 ? sha256Hex(canonicalJson({ html: region.html, values: region.values })) : null;
}

function elementArgs(selector) {
  return { mode: ELEMENT_MODE, selector, elementTextChars: ELEMENT_TEXT_CHARS };
}

/** Convert an in-page snapshot into the service's observation input. */
function buildSnapshot(raw, pageCount) {
  const elements = raw.elements.map((element) => ({ ...element, digest: elementDigest(element) }));
  const controlValues = elements.filter((element) => element.value !== null)
    .map((element) => [element.selector, element.value]);
  return {
    url: raw.url,
    title: raw.title,
    text: raw.text,
    isTruncated: raw.isTruncated,
    elements,
    structuralHash: structuralOutlineHash(elements),
    pageCount,
    contentHash: sha256Hex(canonicalJson({ url: raw.url, html: raw.html, controlValues,
      ...(elements.some(element => element.actionability) ? {
        actionability: elements.map(element => [element.selector, element.actionability ?? null]),
      } : {}) })),
    regionDigests: Object.fromEntries((raw.regions ?? []).map((region) => [region.selector, regionDigest(region)])),
    regionOutlines: Object.fromEntries((raw.regions ?? []).filter((region) => region.outline !== null)
      .map((region) => [region.selector, region.outline])),
    regionGroups: (raw.regions ?? []).filter((region) => region.group !== undefined && region.group !== null)
      .reduce((groups, region) => ({ ...groups, [region.group]: [...(groups[region.group] ?? []), region.selector] }), {}),
  };
}

/**
 * Convert an in-page element probe into the service's probe result. Conditions read the full
 * text: a displayed prefix would make text-excludes report absence that is not established.
 */
function buildProbe(result) {
  if (result.forbidden) throw new Error('Element probe exceeds the selected observation regions');
  if (!result.element) return { count: result.count, digest: null, text: null, value: null, choice: null };
  return {
    count: result.count,
    digest: elementDigest(result.element),
    text: result.fullText,
    value: result.element.value,
    choice: result.choice ?? null,
    ...(result.element.inputType === 'file' ? { tag: result.element.tag, inputType: 'file',
      files: result.element.files, multiple: result.element.multiple, disabled: result.element.disabled,
      accept: result.element.accept } : {}),
  };
}

export { buildProbe, buildSnapshot, elementArgs, queryPage, snapshotArgs, structuralLocator, structuralOutlineHash };
