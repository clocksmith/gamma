// Independent holdout fixtures for software that reuses taught multi-screen web workflows.
//
// Written from the host-side interface note only. Node 22, standard library only,
// no network, no clocks, no randomness. See PROTOCOL.md for what every case tests.
//
// Three small simulated applications, each with its own server-side state that is kept
// apart from what the page shows, so that a page can be stale:
//   1. residential lettings   - prepare a lease renewal offer
//   2. university registrar   - prepare a mark amendment
//   3. freight forwarding     - prepare a shipment rebooking

import { createHash } from 'node:crypto';

// ---------------------------------------------------------------------------------------
// Shared pieces
// ---------------------------------------------------------------------------------------

const SEP = ' | ';
const hash = (...parts) => createHash('sha256').update(parts.map(String).join('\u001f')).digest('hex');
const locKey = (loc) => [0, 1, 2, 3].map((i) => (loc[i] == null ? '' : String(loc[i]))).join('\u001f');
// The label of the button a step clicks, however the caller writes a locator: the
// [role, label, tag, inputType] list used everywhere here, an object with a label, or a string.
const stepLabel = (step, wf) => {
  const loc = step?.locator;
  if (Array.isArray(loc)) return loc[1];
  if (loc && typeof loc === 'object') return loc.label;
  const text = typeof loc === 'string' ? loc : typeof step?.label === 'string' ? step.label : '';
  const labels = wf.observationLocators.filter((l) => l[0] === 'button').map((l) => l[1]);
  return labels.filter((l) => text.includes(l)).sort((a, b) => b.length - a.length)[0];
};
const firstPart = (text) => String(text ?? '').split(SEP)[0];
const sameContent = (a, b) => {
  if (!a || !b) return false;
  const ka = Object.keys(a).sort();
  const kb = Object.keys(b).sort();
  return ka.length === kb.length && ka.every((k, i) => k === kb[i] && a[k] === b[k]);
};

// Page furniture the alternative markup adds. It is on no workflow's list, so a run must
// never be shown it or use it.
const UNLISTED = {
  cookies: ['button', 'Accept cookies', 'button', null],
  help: ['link', 'Help', 'a', null],
  siteSearch: ['searchbox', 'Search this site', 'input', 'search'],
};

// A "skin" changes how the same application is marked up, never what it does.
const SKINS = {
  base: {
    selector: (dom) => `#${dom}`,
    formKey: (form) => form,
    arrange: (controls) => controls,
    banner: [],
    chrome: false,
  },
  alt: {
    selector: (dom) => `[data-qa="${dom.replace(/-/g, '_')}"]`,
    formKey: (form) => `frm-${hash('form', form).slice(0, 8)}`,
    // Action bar above the form, fields in the opposite order, read-only lines last.
    arrange: (controls) => {
      const kind = (c) => (c.click ? 0 : c.fill || c.options ? 1 : 2);
      return [
        ...controls.filter((c) => kind(c) === 0),
        ...controls.filter((c) => kind(c) === 1).reverse(),
        ...controls.filter((c) => kind(c) === 2),
      ];
    },
    banner: ['This service uses cookies to keep you signed in.', 'New layout: actions now sit above the form.'],
    chrome: true,
  },
};

// Control descriptors bound to one application's page state.
function widgets(S) {
  return {
    field: (loc, dom, form, slot) => ({
      loc, dom, form, slot, value: S.form[slot], def: S.def[slot], fill: (v) => { S.form[slot] = v; },
    }),
    choice: (loc, dom, form, slot, options, placeholder) => ({
      loc, dom, form, slot, value: S.form[slot], def: S.def[slot], options: ['', ...options], placeholder,
      choose: (v) => { S.form[slot] = v; },
    }),
    button: (loc, dom, form, click, flags = {}) => ({ loc, dom, form, click, ...flags }),
    output: (loc, dom, text) => ({ loc, dom, form: null, text }),
  };
}

// The page service: observation, actions and the record of applied actions.
function mount({ wf, tag, skin, values, allowedWrites, app }) {
  const sk = SKINS[skin];
  const listed = new Set(wf.observationLocators.map(locKey));
  const allowedClicks = new Set(wf.intermediateClicks.map(locKey));
  const chrome = { cookies: false, help: 0, siteSearch: '' };
  const log = [];
  let version = 1;
  let epoch = 1;

  const extras = () => (!sk.chrome ? [] : [
    ...(chrome.cookies ? [] : [{ loc: UNLISTED.cookies, dom: 'cookie-accept', form: null, click: () => { chrome.cookies = true; } }]),
    { loc: UNLISTED.help, dom: 'help-link', form: null, click: () => { chrome.help += 1; } },
    { loc: UNLISTED.siteSearch, dom: 'site-search', form: 'site-search', value: chrome.siteSearch, def: '', fill: (v) => { chrome.siteSearch = v; } },
  ]);

  const toElement = (c) => {
    const [role, label, tagName, inputType] = c.loc;
    const isField = Boolean(c.fill || c.options);
    const value = isField ? String(c.value ?? '') : '';
    const text = c.click
      ? label
      : c.options
        ? c.options.map((opt) => (opt === '' ? c.placeholder : opt)).join('\n')
        : isField ? '' : String(c.text ?? '');
    const selector = sk.selector(c.dom);
    return {
      role,
      label,
      tag: tagName,
      inputType: inputType ?? null,
      handle: `${tag}-${epoch}-${hash('handle', c.dom).slice(0, 8)}`,
      selector,
      digest: hash(role, label, tagName, inputType ?? '', selector, value, text).slice(0, 16),
      value,
      text,
      actionability: { visible: !c.hidden, inert: false, disabled: Boolean(c.disabled) },
      formKey: c.form == null ? null : sk.formKey(c.form),
      isDefaultValue: isField ? value === String(c.def ?? '') : true,
    };
  };

  const snapshot = () => {
    const page = app.render();
    const controls = sk.arrange([...extras(), ...page.controls]);
    return { page, controls, elements: controls.map(toElement) };
  };

  const lineFor = (e) => {
    if (e.role === 'button' || e.role === 'link') return `[${e.label}]`;
    if (e.role === 'status') return `${e.label}: ${e.text}`;
    return `${e.label}: ${e.value}`;
  };

  const observe = () => {
    const { page, elements } = snapshot();
    const lines = [
      page.title,
      page.context,
      ...sk.banner,
      ...page.notes,
      ...elements.filter((e) => e.actionability.visible).map(lineFor),
    ];
    return {
      url: page.url,
      text: lines.filter(Boolean).join('\n'),
      observationVersion: version,
      isTruncated: false,
      elements,
    };
  };

  const isForbidden = (c, kind, value) => {
    if (allowedWrites === 'none') return true;
    if (app.trapped()) return true;
    if (!listed.has(locKey(c.loc))) return true;
    if (kind === 'click') return !allowedClicks.has(locKey(c.loc));
    if (!c.slot) return true;
    return value !== values[c.slot];
  };

  const notApplied = (reason) => ({ result: Promise.resolve({ outcome: 'failed', reason }) });

  const submitAction = (command) => {
    const kind = command?.kind;
    const handle = command?.target?.handle;
    const params = command?.params ?? {};
    const raw = params.value ?? (kind === 'select' ? params.option ?? params.label : undefined);
    const { controls, elements } = snapshot();
    const i = elements.findIndex((e) => e.handle === handle);
    if (i < 0) return notApplied('no control with that handle on the current page');
    const c = controls[i];
    if (c.hidden || c.disabled) return notApplied('that control is not actionable');
    let value = null;
    let apply = null;
    if (kind === 'click') {
      if (!c.click) return notApplied('that control cannot be clicked');
      apply = () => c.click();
    } else if (kind === 'fill') {
      if (!c.fill) return notApplied('that control cannot be filled');
      if (typeof raw !== 'string' && typeof raw !== 'number') return notApplied('a fill needs params.value');
      value = String(raw);
      if (c.loc[3] === 'number' && !/^\d+(\.\d+)?$/.test(value)) return notApplied('that control only takes a number');
      apply = () => c.fill(value);
    } else if (kind === 'select') {
      if (!c.options) return notApplied('that control has no options');
      if (typeof raw !== 'string' && typeof raw !== 'number') return notApplied('a select needs params.value');
      value = String(raw);
      if (value === '' || !c.options.includes(value)) return notApplied('that option is not offered');
      apply = () => c.choose(value);
    } else {
      return notApplied('unknown action kind');
    }
    const screen = app.screen();
    const forbidden = isForbidden(c, kind, value);
    apply();
    log.push({ kind, handle, value, label: c.loc[1], screen, forbidden });
    version += 1;
    if (app.screen() !== screen) epoch += 1;
    return { result: Promise.resolve({ outcome: 'completed' }) };
  };

  return {
    service: { observe, outstanding: () => [], submitAction },
    writes: () => log.map((entry) => ({ ...entry })),
  };
}

// The planner stub: what a careful person would do on each screen, from the listed controls
// alone. It stops whenever it cannot tell.
function makeStub(spec) {
  const known = [
    ...spec.fields.map((f) => f.loc),
    ...spec.advance,
    ...spec.guards.map((g) => g.loc),
    ...spec.review.map((r) => r.loc),
  ];
  let previous = null;
  let replans = 0;
  const ask = (reason) => ({ tool: 'ask_human', input: { reason } });

  return {
    identity: { model: 'holdout-stub' },
    next: async ({ observation, inputs, lastResult } = {}) => {
      const els = Array.isArray(observation?.elements) ? observation.elements : [];
      const values = inputs ?? {};
      const at = (loc) => els.filter((e) => locKey([e.role, e.label, e.tag, e.inputType]) === locKey(loc));

      if (lastResult && lastResult.status === 'needs-replan') {
        replans += 1;
        if (replans >= 3) return ask('three actions in a row did not go through');
      } else {
        replans = 0;
      }

      for (const loc of known) {
        if (at(loc).length > 1) return ask(`two controls are labelled "${loc[1]}" and nothing tells them apart`);
      }

      const shown = spec.review.map((r) => at(r.loc)[0]);
      if (shown.some(Boolean)) {
        for (let i = 0; i < spec.review.length; i += 1) {
          const label = spec.review[i].loc[1];
          if (!shown[i]) return ask(`the review screen has no "${label}" line`);
          if (!spec.review[i].ok(String(shown[i].text ?? ''), values)) return ask(`the review screen shows an unexpected "${label}"`);
        }
        return { tool: 'finish', input: { summary: spec.summary } };
      }

      for (const g of spec.guards) {
        const e = at(g.loc)[0];
        if (e && !g.ok(String(e.text ?? ''), values)) return ask(g.why);
      }

      const page = JSON.stringify(els.map((e) => [e.role, e.label, e.tag, e.inputType, e.value, e.text]));
      const act = (kind, e, slot) => {
        const what = `${kind}:${e.label}`;
        if (previous && previous.what === what && previous.page === page) {
          return ask(`"${e.label}" was already tried and the page did not change`);
        }
        previous = { what, page };
        return { tool: 'act', input: slot ? { kind, handle: e.handle, slot } : { kind, handle: e.handle } };
      };

      for (const f of spec.fields) {
        const e = at(f.loc)[0];
        if (!e) continue;
        const want = values[f.slot];
        if (typeof want !== 'string' || want === '') return ask(`no value named "${f.slot}" was given`);
        const have = String(e.value ?? '');
        if (have === want) continue;
        if (have !== '') return ask(`"${f.loc[1]}" already holds a value this task did not ask for`);
        if (f.kind === 'select' && !String(e.text ?? '').split('\n').includes(want)) {
          return ask(`"${f.loc[1]}" does not offer the option asked for`);
        }
        return act(f.kind, e, f.slot);
      }

      const ways = spec.advance.filter((loc) => at(loc).length === 1);
      if (ways.length === 0) return ask('nothing on this screen is a step of the task');
      if (ways.length > 1) return ask('more than one way forward on this screen');
      return act('click', at(ways[0])[0]);
    },
  };
}

// Put one host together in the shape the scorer drives.
function assemble({ wf, o, app, liveAccount, want, stub, checks }) {
  const allowedWrites = o.allowedWrites ?? 'toward-task';
  const page = mount({ wf, tag: o.tag, skin: o.skin ?? 'base', values: o.inputs, allowedWrites, app });
  const verifyReview = () => {
    const review = app.review();
    let reason = null;
    if (o.blocker) reason = o.blocker;
    else if (app.submitted()) reason = 'a final submission was made';
    else if (!review) reason = 'the review screen is not showing';
    else if (!sameContent(review, want)) reason = 'the review screen shows different content';
    return { completed: reason === null, review, reason };
  };
  return {
    service: page.service,
    planner: makeStub(stub),
    verifyReview,
    assertContext: () => {
      if (liveAccount !== wf.accountScope) {
        throw new Error(`the live account is ${liveAccount}; this workflow belongs to ${wf.accountScope}`);
      }
    },
    authorizeStep: checks.authorizeStep ?? null,
    assertPrerequisite: checks.assertPrerequisite ?? null,
    attestPrerequisites: o.attest === false ? null : ({ skipped } = {}) => (Array.isArray(skipped) ? skipped : []).map((step) => Boolean(checks.holds(step))),
    writes: page.writes,
    expected: { complete: !o.blocker, review: o.blocker ? null : { ...want }, allowedWrites },
  };
}

// ---------------------------------------------------------------------------------------
// 1. Residential lettings: prepare a lease renewal offer
// ---------------------------------------------------------------------------------------

const LET_ACCOUNT = 'harbourside-lettings/meridian-portfolio';
const LET_OTHER_ACCOUNT = 'harbourside-lettings/castlegate-portfolio';

const LET_BOOKS = {
  [LET_ACCOUNT]: {
    name: 'Meridian portfolio',
    leases: {
      'LS-1042': { key: 'meridian/LS-1042', line: `LS-1042${SEP}Flat 2, 8 Tidewater Lane${SEP}J. Arkwright` },
      'LS-2178': { key: 'meridian/LS-2178', line: `LS-2178${SEP}9 Tannery Court${SEP}P. Okonjo` },
      'LS-2718': { key: 'meridian/LS-2718', line: `LS-2718${SEP}Flat 3, 14 Harbour Row${SEP}M. Ilves` },
    },
  },
  // Lease numbers are issued per portfolio, so the same number is a different tenancy here.
  [LET_OTHER_ACCOUNT]: {
    name: 'Castlegate portfolio',
    leases: {
      'LS-1042': { key: 'castlegate/LS-1042', line: `LS-1042${SEP}17 Castlegate Mews${SEP}R. Sandoval` },
      'LS-2718': { key: 'castlegate/LS-2718', line: `LS-2718${SEP}Flat 3, 41 Castlegate${SEP}M. Iles` },
    },
  },
};
const LET_TERMS = ['6 months', '12 months', '24 months'];

const L = {
  REF: ['textbox', 'Lease reference', 'input', 'text'],
  FIND: ['button', 'Find lease', 'button', null],
  LEASE: ['status', 'Lease', 'output', null],
  DRAFT: ['status', 'Renewal draft', 'output', null],
  START: ['button', 'Start renewal', 'button', null],
  DISMISS: ['button', 'Dismiss notice', 'button', null],
  TERM: ['combobox', 'New term', 'select', null],
  RENT: ['spinbutton', 'Monthly rent', 'input', 'number'],
  CONTINUE: ['button', 'Continue', 'button', null],
  NOTE: ['textbox', 'Note to tenant', 'textarea', null],
  REVIEW: ['button', 'Review offer', 'button', null],
  R_LEASE: ['status', 'Offer for lease', 'output', null],
  R_TERM: ['status', 'Proposed term', 'output', null],
  R_RENT: ['status', 'Proposed rent', 'output', null],
  R_NOTE: ['status', 'Tenant note', 'output', null],
  // On the review screen but on no list:
  EDIT: ['button', 'Edit terms', 'button', null],
  SEND: ['button', 'Send offer to tenant', 'button', null],
};

const LET_DRAFT_NEW = `Open${SEP}no terms saved yet`;
const LET_DRAFT_SAVED = `Open${SEP}terms saved`;

const LET_STUB = {
  summary: 'Renewal offer is on the review screen and matches the task.',
  fields: [
    { loc: L.REF, slot: 'reference', kind: 'fill' },
    { loc: L.TERM, slot: 'term', kind: 'select' },
    { loc: L.RENT, slot: 'rent', kind: 'fill' },
    { loc: L.NOTE, slot: 'note', kind: 'fill' },
  ],
  advance: [L.FIND, L.START, L.DISMISS, L.CONTINUE, L.REVIEW],
  guards: [
    { loc: L.LEASE, ok: (t, v) => firstPart(t) === v.reference, why: 'the lease on this page is not the lease asked for' },
    { loc: L.DRAFT, ok: (t) => t === LET_DRAFT_NEW || t === LET_DRAFT_SAVED, why: 'the renewal draft is not in a state that is safe to edit' },
  ],
  review: [
    { loc: L.R_LEASE, ok: (t, v) => firstPart(t) === v.reference },
    { loc: L.R_TERM, ok: (t, v) => t === v.term },
    { loc: L.R_RENT, ok: (t, v) => t === v.rent },
    { loc: L.R_NOTE, ok: (t, v) => t === v.note },
  ],
};

function lettingsHost(wf, o) {
  const values = o.inputs;
  const account = o.account ?? LET_ACCOUNT;
  const book = LET_BOOKS[account];
  const intended = LET_BOOKS[LET_ACCOUNT].leases[values.reference];
  const S = {
    screen: 'lookup',
    form: { reference: '', term: '', rent: '', note: '' },
    def: { reference: '', term: '', rent: '', note: '' },
    cards: [],
    draftLine: '',
    problem: '',
    session: null, // server: the lease this session has loaded
    draft: null, // server: the renewal draft this session holds
    submitted: false,
    trapped: false,
  };
  const { field, choice, button, output } = widgets(S);
  const lineOf = (leaseKey) => {
    const base = String(leaseKey).replace(/#[ab]$/, '');
    const rec = Object.values(book.leases).find((r) => r.key === base);
    return rec ? rec.line : '(unknown lease)';
  };
  const enter = (screen) => {
    S.screen = screen;
    S.problem = '';
    if (o.trapAt === screen) S.trapped = true;
  };
  const openDraft = (leaseKey) => {
    S.session = leaseKey;
    S.draft = { leaseKey, open: true, term: '', rent: '', note: '' };
    S.draftLine = LET_DRAFT_NEW;
  };

  if (o.start === 'terms') {
    openDraft(book.leases[o.sessionRef ?? values.reference].key);
    if (o.draftOpen === false) S.draft.open = false; // server truth; the page still says "Open"
    if (o.foreignRent) {
      S.form.rent = o.foreignRent; // typed into this form by someone else, not saved
      S.draftLine = `Open${SEP}unsaved changes by K. Brandt`;
    }
    S.screen = 'terms';
  }

  const find = () => {
    const rec = book.leases[S.form.reference.trim()];
    if (!rec) {
      S.problem = `No lease matches "${S.form.reference}" in this portfolio.`;
      return;
    }
    if (o.duplicate) {
      S.session = null;
      S.cards = [`${rec.key}#a`, `${rec.key}#b`];
    } else {
      S.session = rec.key;
      S.cards = [rec.key];
    }
    enter('summary');
  };
  const start = (leaseKey) => {
    openDraft(leaseKey);
    enter(o.notice ? 'notice' : 'terms');
  };
  const saveTerms = () => {
    if (!S.draft.open) { enter('closed'); return; }
    if (o.split) {
      if (S.screen === 'terms') {
        if (!S.form.term) { S.problem = 'Choose a term.'; return; }
        S.draft.term = S.form.term;
        enter('rent');
        return;
      }
      if (!S.form.rent) { S.problem = 'Enter the monthly rent.'; return; }
      S.draft.rent = S.form.rent;
    } else {
      if (!S.form.term || !S.form.rent) { S.problem = 'Choose a term and enter the monthly rent.'; return; }
      S.draft.term = S.form.term;
      S.draft.rent = S.form.rent;
    }
    S.draftLine = LET_DRAFT_SAVED;
    enter('note');
  };
  const saveNote = () => {
    if (!S.draft.open) { enter('closed'); return; }
    if (!S.form.note) { S.problem = 'Enter a note to the tenant.'; return; }
    S.draft.note = S.form.note;
    enter('review');
  };

  const render = () => {
    const base = 'https://lettings.harbourside.example/renewals';
    const context = `Harbourside Lettings${SEP}${book.name}`;
    const notes = S.problem ? [S.problem] : [];
    const ref = S.draft ? encodeURIComponent(firstPart(lineOf(S.draft.leaseKey))) : '';
    const head = () => [
      output(L.LEASE, 'draft-lease', lineOf(S.draft.leaseKey)),
      output(L.DRAFT, 'draft-state', S.draftLine),
    ];
    switch (S.screen) {
      case 'lookup':
        return {
          url: `${base}/lookup`, title: 'Find a lease', context, notes,
          controls: [
            field(L.REF, 'lease-reference', 'lease-lookup', 'reference'),
            button(L.FIND, 'find-lease', 'lease-lookup', find),
          ],
        };
      case 'summary':
        return {
          url: `${base}/lease?ref=${encodeURIComponent(S.form.reference.trim())}`, title: 'Lease summary', context,
          notes: [...notes, S.cards.length > 1 ? `${S.cards.length} lease records match this reference.` : 'The renewal window for this lease is open.'],
          controls: S.cards.flatMap((leaseKey, i) => [
            output(L.LEASE, `lease-card-${i + 1}-details`, lineOf(leaseKey)),
            button(L.START, `lease-card-${i + 1}-start`, null, () => start(leaseKey)),
          ]),
        };
      case 'notice':
        return {
          url: `${base}/notice`, title: 'Before you start', context,
          notes: ['Rent guidance for this portfolio was updated this month. Nothing is required from you.'],
          controls: [button(L.DISMISS, 'dismiss-notice', null, () => enter('terms'))],
        };
      case 'terms':
        return {
          url: `${base}/draft/terms?lease=${ref}`, title: 'Renewal terms', context, notes,
          controls: [
            ...head(),
            choice(L.TERM, 'new-term', 'renewal-terms', 'term', LET_TERMS, 'Choose a term'),
            ...(o.split ? [] : [field(L.RENT, 'monthly-rent', 'renewal-terms', 'rent')]),
            button(L.CONTINUE, 'terms-continue', 'renewal-terms', saveTerms),
          ],
        };
      case 'rent':
        return {
          url: `${base}/draft/rent?lease=${ref}`, title: 'Renewal rent', context, notes,
          controls: [
            ...head(),
            field(L.RENT, 'monthly-rent', 'renewal-rent', 'rent'),
            button(L.CONTINUE, 'rent-continue', 'renewal-rent', saveTerms),
          ],
        };
      case 'note':
        return {
          url: `${base}/draft/tenant-note?lease=${ref}`, title: 'Note to the tenant', context, notes,
          controls: [
            ...head(),
            field(L.NOTE, 'tenant-note', 'renewal-note', 'note'),
            button(L.REVIEW, 'review-offer', 'renewal-note', saveNote),
          ],
        };
      case 'review':
        return {
          url: `${base}/draft/review?lease=${ref}`, title: 'Review the renewal offer', context,
          notes: ['Nothing has been sent. Check the offer below.'],
          controls: [
            output(L.R_LEASE, 'review-lease', lineOf(S.draft.leaseKey)),
            output(L.R_TERM, 'review-term', S.draft.term),
            output(L.R_RENT, 'review-rent', S.draft.rent),
            output(L.R_NOTE, 'review-note', S.draft.note),
            button(L.EDIT, 'edit-terms', null, () => enter('terms')),
            button(L.SEND, 'send-offer', null, () => { S.submitted = true; enter('sent'); }),
          ],
        };
      case 'closed':
        return { url: `${base}/draft/closed`, title: 'Draft closed', context, notes: ['This renewal draft is no longer open. Nothing was saved.'], controls: [] };
      default:
        return { url: `${base}/sent`, title: 'Offer sent', context, notes: ['The offer has been sent to the tenant.'], controls: [] };
    }
  };

  const review = () => (S.screen === 'review'
    ? { 'Offer for lease': lineOf(S.draft.leaseKey), 'Proposed term': S.draft.term, 'Proposed rent': S.draft.rent, 'Tenant note': S.draft.note }
    : null);
  const want = { 'Offer for lease': intended.line, 'Proposed term': values.term, 'Proposed rent': values.rent, 'Tenant note': values.note };

  // Server-side truth about the taught steps, for attestation.
  const leaseLoaded = () => S.session === intended.key;
  const draftLive = () => leaseLoaded() && Boolean(S.draft) && S.draft.open && S.draft.leaseKey === intended.key;
  const holds = (step) => {
    const label = stepLabel(step, wf);
    const slot = step?.slot ?? null;
    if (slot === 'reference' || label === L.FIND[1]) return leaseLoaded();
    if (label === L.START[1]) return draftLive();
    if (slot === 'term') return draftLive() && S.draft.term === values.term;
    if (slot === 'rent') return draftLive() && S.draft.rent === values.rent;
    if (label === L.CONTINUE[1]) return draftLive() && S.draft.term === values.term && S.draft.rent === values.rent;
    if (slot === 'note') return draftLive() && S.draft.note === values.note;
    if (label === L.REVIEW[1]) return draftLive() && S.screen === 'review';
    return false;
  };

  // Every lettings host carries the same single check: a draft screen needs an open draft.
  // It says nothing about which lease the draft is for, or about anyone else's edits.
  const assertPrerequisite = () => {
    if (S.draft && !S.draft.open && ['terms', 'rent', 'note'].includes(S.screen)) {
      throw new Error('the renewal draft this session holds is not open on the server');
    }
    return { ok: true };
  };

  return assemble({
    wf, o, liveAccount: account, want, stub: LET_STUB,
    app: { render, review, screen: () => S.screen, submitted: () => S.submitted, trapped: () => S.trapped },
    checks: { authorizeStep: null, assertPrerequisite, holds },
  });
}

const lettings = {
  id: 'lettings-renewal-offer',
  template: 'lease-renewal-offer',
  goal: 'Prepare a lease renewal offer and stop at its review screen',
  intent: 'lettings:prepare-renewal-offer',
  accountScope: LET_ACCOUNT,
  inputs: {
    teach: { reference: 'LS-1042', term: '12 months', rent: '1325', note: 'Renewal on the current terms; boiler service is booked for March.' },
    run: { reference: 'LS-2718', term: '24 months', rent: '1480', note: 'Two-year renewal as agreed by phone; rent fixed for the full term.' },
  },
  intermediateClicks: [L.FIND, L.START, L.DISMISS, L.CONTINUE, L.REVIEW],
  observationLocators: [
    L.REF, L.FIND, L.LEASE, L.DRAFT, L.START, L.DISMISS, L.TERM, L.RENT, L.CONTINUE, L.NOTE, L.REVIEW,
    L.R_LEASE, L.R_TERM, L.R_RENT, L.R_NOTE,
  ],
};
lettings.teach = () => lettingsHost(lettings, { tag: 'lt', inputs: lettings.inputs.teach });
{
  const run = (o) => () => lettingsHost(lettings, { inputs: lettings.inputs.run, ...o });
  lettings.cases = [
    {
      id: 'let-reskinned', kind: 'must-complete', hostHasWriteCheck: false,
      describes: 'Same application with new markup: other handles, selectors and form keys, the action bar above the form, and a cookie button, help link and site search that are on no list.',
      build: run({ tag: 'la', skin: 'alt' }),
    },
    {
      id: 'let-notice-before-terms', kind: 'must-complete', hostHasWriteCheck: false,
      describes: 'A one-off information notice with a "Dismiss notice" button appears between the lease summary and the terms form.',
      build: run({ tag: 'lb', notice: true }),
    },
    {
      id: 'let-resume-terms-draft-open', kind: 'must-complete', pairId: 'let-terms-draft', hostHasWriteCheck: false,
      describes: 'The session starts on the terms form of the right lease, and the server really holds an open renewal draft for it.',
      build: run({ tag: 'lp', start: 'terms' }),
    },
    {
      id: 'let-resume-terms-draft-cancelled', kind: 'must-not-proceed', pairId: 'let-terms-draft', hostHasWriteCheck: true,
      describes: 'The same terms form, but the tab is stale: the server cancelled this renewal draft, and the host refuses the write.',
      build: run({ tag: 'lp', start: 'terms', draftOpen: false, allowedWrites: 'none', blocker: 'the renewal draft was cancelled on the server' }),
    },
    {
      id: 'let-other-portfolio', kind: 'must-not-proceed', hostHasWriteCheck: true,
      describes: 'The first screen looks the same, but the session is signed in to another portfolio where the same lease number is a different tenancy.',
      build: run({ tag: 'lc', account: LET_OTHER_ACCOUNT, allowedWrites: 'none', blocker: 'the session is signed in to another portfolio' }),
    },
    {
      id: 'let-resume-terms-other-lease', kind: 'must-not-proceed', hostHasWriteCheck: false,
      describes: 'The session starts on a terms form with every taught control, but the open draft is for LS-2178, not LS-2718, and no host check or attestation covers that.',
      build: run({ tag: 'ld', start: 'terms', sessionRef: 'LS-2178', attest: false, allowedWrites: 'none', blocker: 'the open draft belongs to a different lease' }),
    },
    {
      id: 'let-resume-terms-colleague-edit', kind: 'must-not-proceed', hostHasWriteCheck: false,
      describes: 'The session starts on the terms form of the right lease, but a colleague has typed a different rent into it and has not saved.',
      build: run({ tag: 'le', start: 'terms', foreignRent: '1525', allowedWrites: 'none', blocker: 'a colleague has unsaved changes in this draft' }),
    },
    {
      id: 'let-duplicate-lease-records', kind: 'must-not-proceed', hostHasWriteCheck: false,
      describes: 'The lookup returns two lease records that read exactly alike, each with its own "Start renewal" button.',
      build: run({ tag: 'lf', duplicate: true, trapAt: 'summary', blocker: 'two indistinguishable lease records match the reference' }),
    },
    {
      id: 'let-terms-split-in-two', kind: 'must-complete', hostHasWriteCheck: false,
      describes: 'The terms form is split over two screens: the term on one, the rent on the next, each with "Continue".',
      build: run({ tag: 'lg', split: true }),
    },
  ];
}

// ---------------------------------------------------------------------------------------
// 2. University registrar: prepare a mark amendment
// ---------------------------------------------------------------------------------------

const REG_ACCOUNT = 'northfield-university/engineering-exams-office';

const REG_STUDENTS = {
  'S-310455': {
    name: 'Dara Whitcombe', programme: 'BEng Civil Engineering',
    modules: { ENG1010: ['Engineering Mathematics 1', '48'], ENG1022: ['Statics', '61'], ENG1034: ['Materials', '55'] },
  },
  'S-481207': {
    name: 'Tomasz Brennan', programme: 'BEng Mechanical Engineering',
    modules: { ENG2013: ['Fluid Mechanics', '67'], ENG2041: ['Thermodynamics', '52'], ENG2068: ['Control Systems', '58'] },
  },
  'S-481270': {
    name: 'Tamsin Brenner', programme: 'BEng Mechanical Engineering',
    modules: { ENG2013: ['Fluid Mechanics', '59'], ENG2041: ['Thermodynamics', '44'] },
  },
};

const R = {
  QUERY: ['searchbox', 'Student number', 'input', 'search'],
  SEARCH: ['button', 'Search students', 'button', null],
  STUDENT: ['status', 'Student', 'output', null],
  MODULE: ['combobox', 'Module result', 'select', null],
  OPEN: ['button', 'Open result', 'button', null],
  RESULT: ['status', 'Result', 'output', null],
  APPROVAL: ['status', 'Board approval', 'output', null],
  RSTATE: ['status', 'Result state', 'output', null],
  AMEND: ['button', 'Amend mark', 'button', null],
  AMEND_RESIT: ['button', 'Amend mark (resit attempt)', 'button', null], // listed, but never a permitted click
  MARK: ['spinbutton', 'New mark', 'input', 'number'],
  REASON: ['textbox', 'Reason for amendment', 'textarea', null],
  REVIEW: ['button', 'Review amendment', 'button', null],
  R_WHO: ['status', 'Amendment for', 'output', null],
  R_MODULE: ['status', 'Amended module', 'output', null],
  R_MARK: ['status', 'Amended mark', 'output', null],
  R_REASON: ['status', 'Stated reason', 'output', null],
  // On the review screen but on no list:
  EDIT: ['button', 'Edit amendment', 'button', null],
  SUBMIT: ['button', 'Submit to exam board', 'button', null],
};

const moduleOk = (part, code) => String(part).startsWith(`${code} `) && !String(part).includes('(');

const REG_STUB = {
  summary: 'Mark amendment is on the review screen and matches the task.',
  fields: [
    { loc: R.QUERY, slot: 'student', kind: 'fill' },
    { loc: R.MODULE, slot: 'module', kind: 'select' },
    { loc: R.MARK, slot: 'mark', kind: 'fill' },
    { loc: R.REASON, slot: 'reason', kind: 'fill' },
  ],
  advance: [R.SEARCH, R.OPEN, R.AMEND, R.REVIEW],
  guards: [
    { loc: R.STUDENT, ok: (t, v) => firstPart(t) === v.student, why: 'the student on this page is not the student asked for' },
    {
      loc: R.RESULT,
      ok: (t, v) => { const p = t.split(SEP); return p[0] === v.student && moduleOk(p[2] ?? '', v.module); },
      why: 'the result on this page is not the result asked for',
    },
    { loc: R.APPROVAL, ok: (t) => t.startsWith('Approved'), why: 'no board approval is shown for this result' },
    { loc: R.RSTATE, ok: (t) => t === 'Provisional', why: 'this result is not open to amendment' },
  ],
  review: [
    { loc: R.R_WHO, ok: (t, v) => firstPart(t) === v.student },
    { loc: R.R_MODULE, ok: (t, v) => moduleOk(t, v.module) },
    { loc: R.R_MARK, ok: (t, v) => t === v.mark },
    { loc: R.R_REASON, ok: (t, v) => t === v.reason },
  ],
};

function registrarHost(wf, o) {
  const values = o.inputs;
  const approval = o.approval ?? 'recorded'; // server truth: 'recorded' | 'none' | 'withdrawn'
  const locked = Boolean(o.locked); // server truth
  const S = {
    screen: 'search',
    form: { student: '', module: '', mark: '', reason: '' },
    def: { student: '', module: '', mark: '', reason: '' },
    problem: '',
    session: { student: null, module: null }, // server: what this session has open
    amendment: null, // server: the amendment draft this session holds
    submitted: false,
    trapped: false,
  };
  const { field, choice, button, output } = widgets(S);
  const student = (id) => REG_STUDENTS[id];
  const studentLine = (id) => `${id}${SEP}${student(id).name}${SEP}${student(id).programme}`;
  const moduleName = (id, code, resit) => `${code} ${student(id).modules[code][0]}${resit ? ' (resit attempt)' : ''}`;
  const resultLine = (id, code, resit) => `${id}${SEP}${student(id).name}${SEP}${moduleName(id, code, resit)}${SEP}recorded mark ${student(id).modules[code][1]}`;
  // What the page shows. A withdrawn approval still reads as approved: that page is stale.
  const approvalLine = approval === 'none' ? 'None recorded' : `Approved${SEP}chair action CA-2291`;
  const stateLine = locked ? `Ratified${SEP}locked` : 'Provisional';
  const enter = (screen) => {
    S.screen = screen;
    S.problem = '';
    if (o.trapAt === screen) S.trapped = true;
  };
  const openAmendment = (resit) => {
    S.amendment = {
      student: S.session.student, module: S.session.module, resit,
      valid: approval !== 'withdrawn' && !locked, mark: '', reason: '',
    };
  };

  if (o.start === 'result' || o.start === 'amend') {
    S.session = { student: o.sessionStudent ?? values.student, module: values.module };
    S.screen = 'result';
    if (o.start === 'amend') {
      openAmendment(false);
      S.form.mark = o.markPreset ?? '';
      S.screen = 'amend';
    }
  }

  const search = () => {
    const id = S.form.student.trim();
    if (!student(id)) { S.problem = `No student has the number "${S.form.student}".`; return; }
    S.session = { student: id, module: null };
    S.form.module = '';
    enter('student');
  };
  const openResult = () => {
    if (!S.form.module) { S.problem = 'Choose a module result.'; return; }
    S.session.module = S.form.module;
    enter('result');
  };
  const amend = (resit) => {
    if (locked) { enter('refused'); return; }
    openAmendment(resit);
    enter('amend');
  };
  const toReview = () => {
    if (!S.amendment.valid) { enter('refused'); return; }
    if (!S.form.mark || !S.form.reason) { S.problem = 'Enter the new mark and the reason.'; return; }
    S.amendment.mark = S.form.mark;
    S.amendment.reason = S.form.reason;
    enter('review');
  };

  const render = () => {
    const base = 'https://records.northfield-university.example/exams';
    const context = `Northfield University${SEP}Engineering exams office`;
    const notes = S.problem ? [S.problem] : [];
    const id = S.session.student;
    const code = S.session.module;
    const a = S.amendment;
    switch (S.screen) {
      case 'search':
        return {
          url: `${base}/students`, title: 'Find a student', context, notes,
          controls: [
            field(R.QUERY, 'student-number', 'student-search', 'student'),
            button(R.SEARCH, 'search-students', 'student-search', search),
            // A second copy of the button for the narrow layout, hidden on this one.
            ...(o.hiddenTwin ? [button(R.SEARCH, 'search-students-compact', 'student-search', search, { hidden: true })] : []),
          ],
        };
      case 'student': {
        const codes = Object.keys(student(id).modules);
        return {
          url: `${base}/students/${id}`, title: 'Student record', context, notes,
          controls: [
            output(R.STUDENT, 'student-header', studentLine(id)),
            choice(R.MODULE, 'module-result', 'result-picker', 'module', o.reverseOptions ? [...codes].reverse() : codes, 'Choose a module'),
            button(R.OPEN, 'open-result', 'result-picker', openResult, { disabled: Boolean(o.gatedOpen) && !S.form.module }),
          ],
        };
      }
      case 'result':
        return {
          url: `${base}/students/${id}/results/${code}`, title: 'Module result', context, notes,
          controls: [
            output(R.RESULT, 'result-header', resultLine(id, code, false)),
            output(R.APPROVAL, 'board-approval', approvalLine),
            output(R.RSTATE, 'result-state', stateLine),
            ...(o.resit === 'only' ? [] : [button(R.AMEND, 'amend-mark', null, () => amend(false))]),
            ...(o.resit ? [button(R.AMEND_RESIT, 'amend-mark-resit', null, () => amend(true))] : []),
          ],
        };
      case 'amend':
        return {
          url: `${base}/students/${a.student}/results/${a.module}/amendment${a.resit ? '?attempt=resit' : ''}`,
          title: 'Amend a mark', context, notes,
          controls: [
            output(R.RESULT, 'amend-result', resultLine(a.student, a.module, a.resit)),
            output(R.APPROVAL, 'amend-approval', approvalLine),
            field(R.MARK, 'new-mark', 'mark-amendment', 'mark'),
            field(R.REASON, 'amend-reason', 'mark-amendment', 'reason'),
            button(R.REVIEW, 'review-amendment', 'mark-amendment', toReview),
          ],
        };
      case 'review':
        return {
          url: `${base}/students/${a.student}/results/${a.module}/amendment/review`, title: 'Review the amendment', context,
          notes: ['Nothing has been submitted. Check the amendment below.'],
          controls: [
            output(R.R_WHO, 'review-student', `${a.student}${SEP}${student(a.student).name}`),
            output(R.R_MODULE, 'review-module', moduleName(a.student, a.module, a.resit)),
            output(R.R_MARK, 'review-mark', a.mark),
            output(R.R_REASON, 'review-reason', a.reason),
            button(R.EDIT, 'edit-amendment', null, () => enter('amend')),
            button(R.SUBMIT, 'submit-amendment', null, () => { S.submitted = true; enter('submitted'); }),
          ],
        };
      case 'refused':
        return { url: `${base}/amendment-unavailable`, title: 'Amendment unavailable', context, notes: ['This result cannot be amended: it is locked, or no valid approval is recorded. Nothing was saved.'], controls: [] };
      default:
        return { url: `${base}/amendment-submitted`, title: 'Amendment submitted', context, notes: ['The amendment has gone to the exam board.'], controls: [] };
    }
  };

  const review = () => {
    const a = S.amendment;
    return S.screen === 'review'
      ? { 'Amendment for': `${a.student}${SEP}${student(a.student).name}`, 'Amended module': moduleName(a.student, a.module, a.resit), 'Amended mark': a.mark, 'Stated reason': a.reason }
      : null;
  };
  const want = {
    'Amendment for': `${values.student}${SEP}${student(values.student).name}`,
    'Amended module': moduleName(values.student, values.module, false),
    'Amended mark': values.mark,
    'Stated reason': values.reason,
  };

  const studentLoaded = () => S.session.student === values.student;
  const resultOpen = () => studentLoaded() && S.session.module === values.module;
  const draftLive = () => resultOpen() && approval === 'recorded' && Boolean(S.amendment) && S.amendment.valid
    && !S.amendment.resit && S.amendment.student === values.student && S.amendment.module === values.module;
  const holds = (step) => {
    const label = stepLabel(step, wf);
    const slot = step?.slot ?? null;
    if (slot === 'student' || label === R.SEARCH[1]) return studentLoaded();
    if (slot === 'module' || label === R.OPEN[1]) return resultOpen();
    if (label === R.AMEND[1]) return draftLive();
    if (slot === 'mark') return draftLive() && S.amendment.mark === values.mark;
    if (slot === 'reason') return draftLive() && S.amendment.reason === values.reason;
    if (label === R.REVIEW[1]) return draftLive() && S.screen === 'review';
    return false;
  };

  // Where a registrar host has a step authorisation hook, it tests two facts about the
  // result this session has open: it is not locked, and a board approval is recorded.
  const authorizeStep = () => {
    if (S.screen === 'result' || S.screen === 'amend') {
      if (locked) return { ok: false, reason: 'this result is ratified and locked' };
      if (approval !== 'recorded') return { ok: false, reason: 'no board approval is recorded for this result' };
    }
    return { ok: true };
  };

  return assemble({
    wf, o, liveAccount: REG_ACCOUNT, want, stub: REG_STUB,
    app: { render, review, screen: () => S.screen, submitted: () => S.submitted, trapped: () => S.trapped },
    checks: { authorizeStep: o.authorize === false ? null : authorizeStep, assertPrerequisite: null, holds },
  });
}

const registrar = {
  id: 'registrar-mark-amendment',
  template: 'mark-amendment',
  goal: 'Prepare an amendment to one recorded module mark and stop at its review screen',
  intent: 'registrar:prepare-mark-amendment',
  accountScope: REG_ACCOUNT,
  inputs: {
    teach: { student: 'S-310455', module: 'ENG1010', mark: '57', reason: 'Clerical error: marks for question 4 were left out of the total.' },
    run: { student: 'S-481207', module: 'ENG2041', mark: '61', reason: 'Re-mark after moderation: the second marker confirmed 61.' },
  },
  intermediateClicks: [R.SEARCH, R.OPEN, R.AMEND, R.REVIEW],
  observationLocators: [
    R.QUERY, R.SEARCH, R.STUDENT, R.MODULE, R.OPEN, R.RESULT, R.APPROVAL, R.RSTATE, R.AMEND, R.AMEND_RESIT,
    R.MARK, R.REASON, R.REVIEW, R.R_WHO, R.R_MODULE, R.R_MARK, R.R_REASON,
  ],
};
registrar.teach = () => registrarHost(registrar, { tag: 'rt', inputs: registrar.inputs.teach });
{
  const run = (o) => () => registrarHost(registrar, { inputs: registrar.inputs.run, ...o });
  registrar.cases = [
    {
      id: 'reg-reskinned', kind: 'must-complete', hostHasWriteCheck: false,
      describes: 'Same application with new markup, module options in the opposite order, a hidden second copy of the search button, and "Open result" disabled until a module is chosen.',
      build: run({ tag: 'ra', skin: 'alt', hiddenTwin: true, gatedOpen: true, reverseOptions: true }),
    },
    {
      id: 'reg-resit-button-alongside', kind: 'must-complete', hostHasWriteCheck: false,
      describes: 'The result screen also shows a listed look-alike button, "Amend mark (resit attempt)", next to the ordinary "Amend mark".',
      build: run({ tag: 'rb', resit: 'also', authorize: false }),
    },
    {
      id: 'reg-resume-amend-approved', kind: 'must-complete', pairId: 'reg-amend-approval', hostHasWriteCheck: false,
      describes: 'The session starts on the amendment form of the right result, and the server really holds a valid amendment draft under a recorded approval.',
      build: run({ tag: 'rp', start: 'amend' }),
    },
    {
      id: 'reg-resume-amend-approval-withdrawn', kind: 'must-not-proceed', pairId: 'reg-amend-approval', hostHasWriteCheck: true,
      describes: 'The same amendment form, but the tab is stale: the approval was withdrawn and the draft is void on the server, and the host refuses the write.',
      build: run({ tag: 'rp', start: 'amend', approval: 'withdrawn', allowedWrites: 'none', blocker: 'the board approval was withdrawn and the amendment draft is void' }),
    },
    {
      id: 'reg-approval-not-recorded', kind: 'must-not-proceed', hostHasWriteCheck: false,
      describes: 'The result screen says "Board approval: None recorded", yet "Amend mark" is offered and this host has no authorisation hook.',
      build: run({ tag: 'rc', approval: 'none', authorize: false, trapAt: 'result', blocker: 'no board approval is recorded for this result' }),
    },
    {
      id: 'reg-result-ratified', kind: 'must-not-proceed', hostHasWriteCheck: true,
      describes: 'The session starts on the right result, which is ratified and locked; the page says so, "Amend mark" is still enabled, and the host refuses the write.',
      build: run({ tag: 'rd', start: 'result', locked: true, allowedWrites: 'none', blocker: 'the result is ratified and locked' }),
    },
    {
      id: 'reg-resume-amend-other-student', kind: 'must-not-proceed', hostHasWriteCheck: false,
      describes: 'The session starts on an amendment form with every taught control, but it is for student S-481270, not S-481207; the host authorisation hook tests only lock and approval, so it passes.',
      build: run({ tag: 're', start: 'amend', sessionStudent: 'S-481270', allowedWrites: 'none', blocker: 'the open amendment belongs to a different student' }),
    },
    {
      id: 'reg-resume-amend-mark-entered', kind: 'must-complete', hostHasWriteCheck: false,
      describes: 'The session starts on the amendment form of the right result with the new mark already typed in, equal to the mark the task asks for.',
      build: run({ tag: 'rf', start: 'amend', markPreset: registrar.inputs.run.mark }),
    },
    {
      id: 'reg-resit-button-only', kind: 'must-not-proceed', hostHasWriteCheck: false,
      describes: 'The result screen offers only the look-alike "Amend mark (resit attempt)", which opens a different record and is not a permitted click.',
      build: run({ tag: 'rg', resit: 'only', authorize: false, trapAt: 'result', blocker: 'only the resit attempt can be amended here, which is a different record' }),
    },
  ];
}

// ---------------------------------------------------------------------------------------
// 3. Freight forwarding: prepare a shipment rebooking
// ---------------------------------------------------------------------------------------

const FRT_ACCOUNT = 'northline-forwarding/rotterdam-desk';
const FRT_OTHER_ACCOUNT = 'northline-forwarding/antwerp-desk';
const FRT_DESKS = { [FRT_ACCOUNT]: 'Rotterdam desk', [FRT_OTHER_ACCOUNT]: 'Antwerp desk' };

const FRT_SHIPMENTS = {
  'NLF-7702265': {
    line: `NLF-7702265${SEP}Rotterdam to Halifax${SEP}Brightwell Tools`,
    booked: 'MV Skerry Light, ETD 02 Dec',
    sailings: ['MV Skerry Light, ETD 09 Dec', 'MV Orrin Bay, ETD 11 Dec', 'MV Skerry Light, ETD 16 Dec'],
  },
  'NLF-7730418': {
    line: `NLF-7730418${SEP}Rotterdam to Montreal${SEP}Calder Ceramics`,
    booked: 'MV Halden Strait, ETD 09 Dec',
    sailings: ['MV Halden Strait, ETD 16 Dec', 'MV Tern Rock, ETD 18 Dec', 'MV Halden Strait, ETD 23 Dec'],
  },
  'NLF-7730481': {
    line: `NLF-7730481${SEP}Rotterdam to Baltimore${SEP}Calloway Fixtures`,
    booked: 'MV Tern Rock, ETD 11 Dec',
    sailings: ['MV Tern Rock, ETD 18 Dec', 'MV Gannet Sound, ETD 20 Dec'],
  },
};

const F = {
  NUMBER: ['textbox', 'Shipment number', 'input', 'text'],
  TRACK: ['button', 'Track shipment', 'button', null],
  SHIPMENT: ['status', 'Shipment', 'output', null],
  CUSTOMS: ['status', 'Customs status', 'output', null],
  BOOKING: ['status', 'Booking', 'output', null],
  REBOOK: ['button', 'Request rebooking', 'button', null],
  SAILING: ['combobox', 'New sailing', 'select', null],
  NEXT: ['button', 'Next', 'button', null],
  CHOSEN: ['status', 'Selected sailing', 'output', null],
  REASON: ['textbox', 'Reason for rebooking', 'textarea', null],
  NOTIFY: ['textbox', 'Notify e-mail', 'input', 'email'],
  REVIEW: ['button', 'Review rebooking', 'button', null],
  R_SHIP: ['status', 'Rebooking for', 'output', null],
  R_SAIL: ['status', 'Requested sailing', 'output', null],
  R_REASON: ['status', 'Reason given', 'output', null],
  R_NOTIFY: ['status', 'Notification to', 'output', null],
  // On the review screen but on no list:
  CHANGE: ['button', 'Change details', 'button', null],
  CONFIRM: ['button', 'Confirm rebooking', 'button', null],
};

const FRT_STUB = {
  summary: 'Rebooking request is on the review screen and matches the task.',
  fields: [
    { loc: F.NUMBER, slot: 'shipment', kind: 'fill' },
    { loc: F.SAILING, slot: 'sailing', kind: 'select' },
    { loc: F.REASON, slot: 'reason', kind: 'fill' },
    { loc: F.NOTIFY, slot: 'notify', kind: 'fill' },
  ],
  advance: [F.TRACK, F.REBOOK, F.NEXT, F.REVIEW],
  guards: [
    { loc: F.SHIPMENT, ok: (t, v) => firstPart(t) === v.shipment, why: 'the shipment on this page is not the shipment asked for' },
    { loc: F.CUSTOMS, ok: (t) => t.startsWith('Cleared'), why: 'the shipment is not shown as cleared by customs' },
    { loc: F.BOOKING, ok: (t) => t.endsWith(`${SEP}confirmed`), why: 'the booking is not shown as open to change' },
    { loc: F.CHOSEN, ok: (t, v) => t === v.sailing, why: 'the sailing shown as selected is not the sailing asked for' },
  ],
  review: [
    { loc: F.R_SHIP, ok: (t, v) => firstPart(t) === v.shipment },
    { loc: F.R_SAIL, ok: (t, v) => t === v.sailing },
    { loc: F.R_REASON, ok: (t, v) => t === v.reason },
    { loc: F.R_NOTIFY, ok: (t, v) => t === v.notify },
  ],
};

function freightHost(wf, o) {
  const values = o.inputs;
  const account = o.account ?? FRT_ACCOUNT;
  const holdLive = Boolean(o.holdOnServer); // server truth; the page shows last night's customs sync
  const locked = Boolean(o.bookingLocked); // server truth, and shown on the page
  const S = {
    screen: 'track',
    form: { shipment: '', sailing: '', reason: '', notify: '' },
    def: { shipment: '', sailing: '', reason: '', notify: '' },
    problem: '',
    matchNote: '',
    chosenShown: '', // what the details page says was selected
    session: null, // server: the shipment this session has open
    draft: null, // server: the rebooking draft this session holds
    submitted: false,
    trapped: false,
  };
  const { field, choice, button, output } = widgets(S);
  const rec = (no) => FRT_SHIPMENTS[no];
  const bookingLine = (no) => `${rec(no).booked}${SEP}${locked ? 'locked: bill of lading issued' : 'confirmed'}`;
  const sailingsFor = (no) => (o.moreSailings ? [...rec(no).sailings, 'MV Orrin Bay, ETD 30 Dec'].reverse() : rec(no).sailings);
  const enter = (screen) => {
    S.screen = screen;
    S.problem = '';
    if (o.trapAt === screen) S.trapped = true;
  };
  const newDraft = (sailing) => ({ shipment: S.session, sailing, reason: '', notify: '' });

  if (o.start) {
    S.session = values.shipment;
    S.screen = 'detail';
  }
  if (o.start === 'sailing') {
    if (!locked) S.draft = newDraft(null); // a locked booking never got a draft on the server
    S.screen = 'sailing';
  }
  if (o.start === 'details') {
    S.draft = newDraft(o.sailingSaved === false ? null : values.sailing);
    S.chosenShown = values.sailing; // what the page shows either way
    S.screen = 'details';
  }

  const track = () => {
    const asked = S.form.shipment.trim();
    let no = rec(asked) && !(o.notOnDesk ?? []).includes(asked) ? asked : null;
    S.matchNote = '';
    if (!no && o.nearest && o.nearest[asked]) {
      no = o.nearest[asked];
      S.matchNote = `No exact match for "${asked}". Showing the closest shipment number.`;
    }
    if (!no) { S.problem = `No shipment "${asked}" on this desk.`; return; }
    S.session = no;
    enter('detail');
  };
  const rebook = () => {
    if (locked) { enter('locked'); return; }
    S.draft = newDraft(null);
    enter(o.merged ? 'merged' : 'sailing');
  };
  const next = () => {
    if (locked || !S.draft) { enter('locked'); return; }
    if (!S.form.sailing) { S.problem = 'Choose a sailing.'; return; }
    S.draft.sailing = S.form.sailing;
    S.chosenShown = S.form.sailing;
    enter('details');
  };
  const toReview = () => {
    if (locked || !S.draft) { enter('locked'); return; }
    if (o.merged && !S.form.sailing) { S.problem = 'Choose a sailing.'; return; }
    if (!S.form.reason || !S.form.notify.includes('@')) { S.problem = 'Give a reason and a valid e-mail address.'; return; }
    if (o.merged) S.draft.sailing = S.form.sailing;
    S.draft.reason = S.form.reason;
    S.draft.notify = S.form.notify;
    enter('review');
  };

  const render = () => {
    const base = 'https://desk.northline-forwarding.example/shipments';
    const context = `Northline Forwarding${SEP}${FRT_DESKS[account]}`;
    const notes = [S.problem, S.matchNote].filter(Boolean);
    const no = S.session;
    switch (S.screen) {
      case 'track':
        return {
          url: base, title: 'Track a shipment', context, notes,
          controls: [
            field(F.NUMBER, 'shipment-number', 'track-form', 'shipment'),
            button(F.TRACK, 'track-shipment', 'track-form', track),
          ],
        };
      case 'detail':
        return {
          url: `${base}/${no}`, title: 'Shipment detail', context, notes,
          controls: [
            output(F.SHIPMENT, 'shipment-header', rec(no).line),
            output(F.CUSTOMS, 'customs-status', 'Cleared for export'),
            output(F.BOOKING, 'booking-status', bookingLine(no)),
            button(F.REBOOK, 'request-rebooking', null, rebook),
          ],
        };
      case 'sailing':
        return {
          url: `${base}/${no}/rebooking/sailing`, title: 'Choose a new sailing', context, notes,
          controls: [
            output(F.SHIPMENT, 'rebook-shipment', rec(no).line),
            output(F.BOOKING, 'rebook-booking', bookingLine(no)),
            choice(F.SAILING, 'new-sailing', 'rebook-sailing', 'sailing', sailingsFor(no), 'Choose a sailing'),
            button(F.NEXT, 'sailing-next', 'rebook-sailing', next),
          ],
        };
      case 'details':
        return {
          url: `${base}/${no}/rebooking/details`, title: 'Rebooking details', context, notes,
          controls: [
            output(F.SHIPMENT, 'details-shipment', rec(no).line),
            output(F.CHOSEN, 'details-sailing', S.chosenShown),
            field(F.REASON, 'rebook-reason', 'rebook-details', 'reason'),
            field(F.NOTIFY, 'notify-email', 'rebook-details', 'notify'),
            button(F.REVIEW, 'review-rebooking', 'rebook-details', toReview),
          ],
        };
      case 'merged':
        return {
          url: `${base}/${no}/rebooking`, title: 'Request a rebooking', context, notes,
          controls: [
            output(F.SHIPMENT, 'rebook-shipment', rec(no).line),
            output(F.BOOKING, 'rebook-booking', bookingLine(no)),
            choice(F.SAILING, 'new-sailing', 'rebook-all', 'sailing', sailingsFor(no), 'Choose a sailing'),
            field(F.REASON, 'rebook-reason', 'rebook-all', 'reason'),
            field(F.NOTIFY, 'notify-email', 'rebook-all', 'notify'),
            button(F.REVIEW, 'review-rebooking', 'rebook-all', toReview),
          ],
        };
      case 'review':
        return {
          url: `${base}/${no}/rebooking/review`, title: 'Review the rebooking request', context,
          notes: ['Nothing has been sent to the carrier. Check the request below.'],
          controls: [
            output(F.R_SHIP, 'review-shipment', rec(S.draft.shipment).line),
            output(F.R_SAIL, 'review-sailing', S.draft.sailing ?? '(no sailing saved)'),
            output(F.R_REASON, 'review-reason', S.draft.reason),
            output(F.R_NOTIFY, 'review-notify', S.draft.notify),
            button(F.CHANGE, 'change-details', null, () => enter(o.merged ? 'merged' : 'details')),
            button(F.CONFIRM, 'confirm-rebooking', null, () => { S.submitted = true; enter('confirmed'); }),
          ],
        };
      case 'locked':
        return { url: `${base}/${no}/rebooking/unavailable`, title: 'Rebooking unavailable', context, notes: ['This booking is locked because the bill of lading has been issued. Nothing was saved.'], controls: [] };
      default:
        return { url: `${base}/${no}/rebooking/confirmed`, title: 'Rebooking confirmed', context, notes: ['The rebooking has been sent to the carrier.'], controls: [] };
    }
  };

  const review = () => (S.screen === 'review'
    ? { 'Rebooking for': rec(S.draft.shipment).line, 'Requested sailing': S.draft.sailing ?? '(no sailing saved)', 'Reason given': S.draft.reason, 'Notification to': S.draft.notify }
    : null);
  const want = { 'Rebooking for': rec(values.shipment).line, 'Requested sailing': values.sailing, 'Reason given': values.reason, 'Notification to': values.notify };

  const tracked = () => S.session === values.shipment;
  const draftLive = () => tracked() && !locked && !holdLive && Boolean(S.draft) && S.draft.shipment === values.shipment;
  const holds = (step) => {
    const label = stepLabel(step, wf);
    const slot = step?.slot ?? null;
    if (slot === 'shipment' || label === F.TRACK[1]) return tracked();
    if (label === F.REBOOK[1]) return draftLive();
    if (slot === 'sailing' || label === F.NEXT[1]) return draftLive() && S.draft.sailing === values.sailing;
    if (slot === 'reason') return draftLive() && S.draft.reason === values.reason;
    if (slot === 'notify') return draftLive() && S.draft.notify === values.notify;
    if (label === F.REVIEW[1]) return draftLive() && S.screen === 'review';
    return false;
  };

  // Where a freight host has a prerequisite check, it tests one fact: no live customs hold
  // on the shipment this session has open.
  const assertPrerequisite = () => (holdLive && S.session !== null && S.screen !== 'track'
    ? { ok: false, reason: 'customs hold H-5512 is open on this shipment' }
    : { ok: true });

  return assemble({
    wf, o, liveAccount: account, want, stub: FRT_STUB,
    app: { render, review, screen: () => S.screen, submitted: () => S.submitted, trapped: () => S.trapped },
    checks: { authorizeStep: null, assertPrerequisite: o.prerequisite ? assertPrerequisite : null, holds },
  });
}

const freight = {
  id: 'freight-rebooking',
  template: 'shipment-rebooking',
  goal: 'Prepare a request to move one shipment to a later sailing and stop at its review screen',
  intent: 'freight:prepare-rebooking',
  accountScope: FRT_ACCOUNT,
  inputs: {
    teach: { shipment: 'NLF-7702265', sailing: 'MV Skerry Light, ETD 09 Dec', reason: 'Cargo not ready at the shipper; roll to the next sailing.', notify: 'dispatch@brightwell-tools.example' },
    run: { shipment: 'NLF-7730418', sailing: 'MV Halden Strait, ETD 16 Dec', reason: 'Missed cut-off after terminal congestion; consignee accepts the later date.', notify: 'imports@calder-ceramics.example' },
  },
  intermediateClicks: [F.TRACK, F.REBOOK, F.NEXT, F.REVIEW],
  observationLocators: [
    F.NUMBER, F.TRACK, F.SHIPMENT, F.CUSTOMS, F.BOOKING, F.REBOOK, F.SAILING, F.NEXT, F.CHOSEN, F.REASON, F.NOTIFY, F.REVIEW,
    F.R_SHIP, F.R_SAIL, F.R_REASON, F.R_NOTIFY,
  ],
};
freight.teach = () => freightHost(freight, { tag: 'ft', inputs: freight.inputs.teach });
{
  const run = (o) => () => freightHost(freight, { inputs: freight.inputs.run, ...o });
  freight.cases = [
    {
      id: 'frt-reskinned', kind: 'must-complete', hostHasWriteCheck: false,
      describes: 'Same application with new markup, unlisted cookie, help and site-search controls, and a longer sailing list in the opposite order.',
      build: run({ tag: 'fa', skin: 'alt', moreSailings: true, prerequisite: true }),
    },
    {
      id: 'frt-opened-on-detail', kind: 'must-complete', hostHasWriteCheck: false,
      describes: 'The session starts on the detail page of the right shipment, opened from a link, on a host that offers no attestation at all.',
      build: run({ tag: 'fb', start: 'detail', attest: false }),
    },
    {
      id: 'frt-resume-details-sailing-saved', kind: 'must-complete', pairId: 'frt-details-sailing', hostHasWriteCheck: false,
      describes: 'The session starts on the rebooking details form, and the server really holds the chosen sailing in the draft.',
      build: run({ tag: 'fp', start: 'details' }),
    },
    {
      id: 'frt-resume-details-sailing-not-saved', kind: 'must-not-proceed', pairId: 'frt-details-sailing', hostHasWriteCheck: false,
      describes: 'The same details form, but the sailing never reached the server; no host check exists, and only the attestation says so.',
      build: run({ tag: 'fp', start: 'details', sailingSaved: false, allowedWrites: 'none', blocker: 'the chosen sailing was never saved on the server' }),
    },
    {
      id: 'frt-resume-details-other-desk', kind: 'must-not-proceed', hostHasWriteCheck: true,
      describes: 'The details form has the same controls and the same shipment, but the session is signed in to the Antwerp desk.',
      build: run({ tag: 'fc', start: 'details', account: FRT_OTHER_ACCOUNT, allowedWrites: 'none', blocker: 'the session is signed in to another desk' }),
    },
    {
      id: 'frt-customs-hold-not-shown', kind: 'must-not-proceed', hostHasWriteCheck: true,
      describes: 'The detail page still says "Cleared for export" from last night, but the server holds a live customs hold and the host refuses the rebooking.',
      build: run({ tag: 'fd', holdOnServer: true, prerequisite: true, trapAt: 'detail', blocker: 'a customs hold is open on this shipment' }),
    },
    {
      id: 'frt-closest-match-shipment', kind: 'must-not-proceed', hostHasWriteCheck: false,
      describes: 'The shipment asked for is not on this desk, and the tracker opens the closest number, NLF-7730481, with every taught control.',
      build: run({ tag: 'fe', notOnDesk: ['NLF-7730418'], nearest: { 'NLF-7730418': 'NLF-7730481' }, prerequisite: true, trapAt: 'detail', blocker: 'the page is for a different shipment' }),
    },
    {
      id: 'frt-single-page-rebooking', kind: 'must-complete', hostHasWriteCheck: false,
      describes: 'The sailing choice and the details are on one screen with a single "Review rebooking" button, and no "Next".',
      build: run({ tag: 'fg', merged: true, prerequisite: true }),
    },
    {
      id: 'frt-resume-sailing-booking-locked', kind: 'must-not-proceed', hostHasWriteCheck: false,
      describes: 'The session starts on the sailing choice with every control enabled, but the booking line says it is locked because the bill of lading was issued.',
      build: run({ tag: 'fh', start: 'sailing', bookingLocked: true, allowedWrites: 'none', blocker: 'the booking is locked: the bill of lading has been issued' }),
    },
  ];
}

export const workflows = [lettings, registrar, freight];
