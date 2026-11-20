// Fawn workspace model-driven comparison — a scripted stand-in for the model, for wiring checks.
//
// It reads tool results in either backend's observation format, chooses elements by role, name
// and document order, and drives each application's task end to end through the frozen tools,
// including recovery after a restart. It never calls a model API and proves nothing about one.

import { RESTART_NOTICE } from './agent-loop.js';

const MAX_DECISIONS = 4;
const OUTLINE_ELEMENT = /\[(h[0-9a-z-]+) (\w+) "([^"]*)"(?: = ("(?:[^"\\]|\\.)*"))?\]/g;
const SNAPSHOT_ELEMENT = /- '?(\w+)(?: "([^"]*)")?([^\n]*?)\[ref=(e\d+)\](?: \[[^\]]*\])*(?:: ([^\n]*))?/g;
const ITEM_NAME = /[A-Z][a-z]+ [A-Z]\b/g;
const ORIGIN = /https?:\/\/127\.0\.0\.1:\d+/;
const SHOWED_URL = /the page then showed (\S+)$/m;

const OBSERVE = Object.freeze({ name: 'observe', input: {} });
const navigate = (url) => ({ name: 'navigate', input: { url } });
const click = (element, dependsOn = [], externalEffect = false) => ({
  name: 'click', input: { element: element.ref, depends_on: dependsOn, external_effect: externalEffect },
});
const fill = (element, value) => ({ name: 'fill', input: { element: element.ref, value, depends_on: [] } });
const submit = (element) => ({ name: 'submit', input: { element: element.ref, depends_on: ['body'] } });
const cents = (text) => {
  const match = /\$(\d+)\.(\d{2})/.exec(text);
  return match ? Number(match[1]) * 100 + Number(match[2]) : null;
};

function elements(text) {
  const outline = [...text.matchAll(OUTLINE_ELEMENT)].map((match) => ({
    ref: match[1], role: match[2], name: match[3], value: match[4] === undefined ? null : JSON.parse(match[4]), index: match.index,
  }));
  const snapshot = [...text.matchAll(SNAPSHOT_ELEMENT)].map((match) => ({
    ref: match[4], role: match[1], name: match[2] ?? '', value: match[5]?.trim() ?? '', index: match.index,
  }));
  return [...outline, ...snapshot].sort((a, b) => a.index - b.index);
}

function find(text, role, name, after = '') {
  const start = text.indexOf(after);
  if (start === -1) return null;
  return elements(text).find((element) => element.index >= start && element.role === role && name.test(element.name)) ?? null;
}

/** Each matching element with the text between it and the previous match, as a table row. */
function rows(text, role, name) {
  const matches = elements(text).filter((element) => element.role === role && name.test(element.name));
  return matches.map((element, index) => ({ element, text: text.slice(index ? matches[index - 1].index : 0, element.index) }));
}

function required(value, description) {
  if (!value) throw new Error(`scripted model: ${description} not found`);
  return value;
}

/** After a restart: open the recorded result when the workspace knows it, otherwise ask a person. */
function* recover() {
  const pending = (yield { name: 'pending_effects', input: {} }).text;
  const showed = SHOWED_URL.exec(pending);
  if (showed) {
    yield navigate(showed[1]);
    return true;
  }
  if (/No external effects are outstanding/.test(pending)) return false;
  yield { name: 'request_human_review', input: { reason: `the result of an external effect is unknown: ${pending}` } };
  return null;
}

/** Submit, retrying after a takeover; null when a restart left the outcome to a person. */
function* submitOnce(name, retryFrom) {
  for (let attempt = 1; attempt <= MAX_DECISIONS; attempt += 1) {
    const text = (yield OBSERVE).text;
    const result = yield submit(required(find(text, 'button', name), `${name} button`));
    if (result.text === RESTART_NOTICE) {
      const recovered = yield* recover();
      if (recovered === null) return null;
      if (recovered) return true;
      continue;
    }
    if (!result.isError) return true;
    if (retryFrom) yield* retryFrom();
  }
  throw new Error('scripted model: the submission did not go through');
}

function* finishWithDownload(name) {
  const text = (yield OBSERVE).text;
  const saved = (yield { name: 'download', input: { element: required(find(text, 'link', name), `${name} link`).ref } }).text;
  yield { name: 'finish', input: { summary: 'scripted wiring check', artifact: required(/Saved artifact (\w+)/.exec(saved), 'artifact')[1] } };
}

const PLANS = Object.freeze({
  * procurement(origin, prompt) {
    const budget = cents(prompt);
    const pageCount = Number(/to page (\d+)/.exec(prompt)[1]);
    for (let decision = 1; decision <= MAX_DECISIONS; decision += 1) {
      let best = null;
      for (let page = 1; page <= pageCount; page += 1) {
        yield navigate(`${origin}/catalog?page=${page}`);
        for (const row of rows((yield OBSERVE).text, 'button', /add to cart/i)) {
          const name = row.text.match(ITEM_NAME)?.at(-1);
          const price = cents(row.text);
          const inStock = /\d+ in stock/.test(row.text);
          if (name && inStock && price <= budget && (!best || price < best.price)) best = { name, price, page };
        }
      }
      yield navigate(`${origin}/catalog?page=${required(best, 'an item within budget').page}`);
      const text = (yield OBSERVE).text;
      if ((yield click(required(find(text, 'button', /add to cart/i, best.name), 'add button'), ['body'], true)).isError) continue;
      break;
    }
    yield navigate(`${origin}/checkout`);
    const form = (yield OBSERVE).text;
    const address = required(find(form, 'textbox', /address/i), 'address field');
    if (!address.value) yield fill(address, /Ship it to "([^"]+)"/.exec(prompt)[1]);
    const reference = find(form, 'textbox', /reference/i);
    if (reference) yield fill(reference, /enter "([^"]+)"/.exec(prompt)[1]);
    if ((yield* submitOnce(/place order/i)) === null) return;
    yield* finishWithDownload(/download invoice/i);
  },
  * helpdesk(origin, prompt) {
    const product = /for the (\w+) product/.exec(prompt)[1];
    for (let decision = 1; decision <= MAX_DECISIONS; decision += 1) {
      yield navigate(`${origin}/queue`);
      const queue = rows((yield OBSERVE).text, 'button', /^claim$/i).map((row) => ({
        ...row,
        id: row.text.match(/#(\d+)/g)?.at(-1)?.slice(1),
        age: Number(/opened (\d+) min ago/.exec(row.text)?.[1] ?? 0),
      })).filter((row) => row.id && row.text.includes(product) && /unclaimed/.test(row.text));
      const oldest = required(queue.sort((a, b) => b.age - a.age)[0], 'an open ticket');
      if ((yield click(oldest.element, ['body'], true)).isError) continue;
      yield navigate(`${origin}/tickets/${oldest.id}`);
      break;
    }
    const ticket = (yield OBSERVE).text;
    const draft = required(find(ticket, 'textbox', /body|reply/i), 'reply field');
    if (!draft.value) yield fill(draft, /send this text: "([^"]+)"/.exec(prompt)[1]);
    const reference = find(ticket, 'textbox', /reference/i);
    if (reference) yield fill(reference, /enter "([^"]+)"/.exec(prompt)[1]);
    if ((yield* submitOnce(/send reply/i)) === null) return;
    yield* finishWithDownload(/download transcript/i);
  },
  * 'clinic-booking'(origin, prompt) {
    const [, type, start, end, patient] = /with a (.+?) between (\S+) and (\S+) for patient "([^"]+)"/.exec(prompt);
    yield navigate(`${origin}/`);
    yield click(required(find((yield OBSERVE).text, 'link', /appointments/i), 'appointments link'));
    const slots = rows((yield OBSERVE).text, 'link', /^book$/i).map((row) => ({
      ...row, when: `${/\d{4}-\d{2}-\d{2}/.exec(row.text)?.[0]} ${/\d{2}:\d{2}/.exec(row.text)?.[0]}`,
    })).filter((row) => row.text.includes(type) && row.when.slice(0, 10) >= start && row.when.slice(0, 10) <= end);
    yield click(required(slots.sort((a, b) => a.when.localeCompare(b.when))[0], 'a slot in the window').element);
    yield fill(required(find((yield OBSERVE).text, 'textbox', /patient/i), 'patient field'), patient);
    if ((yield* submitOnce(/confirm booking/i)) === null) return;
    yield* finishWithDownload(/download confirmation/i);
  },
  * 'expense-filing'(origin, prompt) {
    const [, merchant, date, category] = /from "([^"]+)" dated (\S+) .* under category "([^"]+)"/.exec(prompt);
    yield navigate(`${origin}/`);
    yield click(required(find((yield OBSERVE).text, 'link', /receipts/i), 'receipts link'));
    const receipt = rows((yield OBSERVE).text, 'link', /^open$/i).find((row) => row.text.includes(merchant) && row.text.includes(date));
    yield click(required(receipt, 'the receipt').element);
    const form = (yield OBSERVE).text;
    yield fill(required(find(form, 'combobox', /./, 'Category'), 'category select'), category);
    yield fill(required(find(form, 'textbox', /amount/i), 'amount field'), (cents(form) / 100).toFixed(2));
    if ((yield* submitOnce(/file expense/i)) === null) return;
    yield* finishWithDownload(/download report/i);
  },
});

const APP_OF_PROMPT = Object.freeze([
  [/^In the store at /, 'procurement'],
  [/^In the support desk at /, 'helpdesk'],
  [/^In the clinic portal at /, 'clinic-booking'],
  [/^In the expense system at /, 'expense-filing'],
]);

/** The client interface of anthropic-client.js, answered by one plan per task prompt. */
function createScriptedClient() {
  const running = new Map();
  return {
    async turn({ messages }) {
      const prompt = messages[0].content;
      let plan = running.get(prompt);
      let step;
      if (!plan) {
        const app = APP_OF_PROMPT.find(([pattern]) => pattern.test(prompt))[1];
        plan = PLANS[app](ORIGIN.exec(prompt)[0], prompt);
        running.set(prompt, plan);
        step = plan.next();
      } else {
        const result = messages.at(-1).content.find((block) => block.type === 'tool_result');
        step = plan.next({ text: result.content, isError: Boolean(result.is_error) });
      }
      const call = step.done ? { name: 'finish', input: { summary: 'scripted plan ended' } } : step.value;
      return {
        content: [{ type: 'tool_use', id: `scripted-${messages.length}`, ...call }],
        usage: { input_tokens: Buffer.byteLength(JSON.stringify(messages)), output_tokens: 0 },
      };
    },
    countTokens: async (text) => Math.ceil(Buffer.byteLength(text) / 4),
  };
}

export { createScriptedClient };
