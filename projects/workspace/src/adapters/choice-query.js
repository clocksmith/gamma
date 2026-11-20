// Fawn workspace — choosing an option in a native select, an ARIA combobox or an ARIA listbox
//
// Both adapters run the same plan and in-page readers, so a choice behaves identically whichever
// protocol drives Chromium. The adapter supplies only how to evaluate, click and set a native value.
// Whether the page kept the choice is the service's check, not this module's.

// Runs inside the page; must stay self-contained.
function prepareChoice({ selector, value }) {
  const nodes = document.querySelectorAll(selector);
  if (nodes.length !== 1) return { error: `selector matched ${nodes.length} elements` };
  const node = nodes[0];
  if (node.tagName === 'SELECT') {
    const matches = [...node.options].filter((option) =>
      option.value === value || option.label.trim() === value || option.text.trim() === value);
    if (matches.length !== 1) return { error: `${matches.length} options match ${JSON.stringify(value)}` };
    if (matches[0].disabled) return { error: `option ${JSON.stringify(value)} is disabled` };
    return { mode: 'native', optionValue: matches[0].value };
  }
  const role = node.getAttribute('role');
  if (role === 'combobox') return { mode: 'combobox', expanded: node.getAttribute('aria-expanded') === 'true' };
  if (role === 'listbox') return { mode: 'listbox', expanded: true };
  return { error: 'element is not a select, combobox or listbox' };
}

// Runs inside the page; must stay self-contained. Finds the one visible, enabled option whose
// accessible name equals the value: inside the listbox itself, inside the elements a combobox
// names through aria-controls or aria-owns, or, when it names none, anywhere in the document.
function locateOption({ selector, value }) {
  const node = document.querySelector(selector);
  if (!node) return { count: 0, visibleOptions: 0 };
  const named = (attribute) => (node.getAttribute(attribute) ?? '').split(/\s+/).filter(Boolean)
    .map((id) => document.getElementById(id)).filter(Boolean);
  const roots = node.getAttribute('role') === 'listbox' ? [node] : [...named('aria-controls'), ...named('aria-owns')];
  const scopes = roots.length > 0 ? roots : [document];
  const visible = (element) => {
    const box = element.getBoundingClientRect();
    return box.width > 0 && box.height > 0 && getComputedStyle(element).visibility !== 'hidden';
  };
  const nameOf = (element) => (element.getAttribute('aria-label') ?? element.innerText ?? element.textContent ?? '').trim();
  const options = [...new Set(scopes.flatMap((scope) => [...scope.querySelectorAll('[role="option"]')]))].filter(visible);
  const matches = options.filter((option) => nameOf(option) === value && option.getAttribute('aria-disabled') !== 'true');
  if (matches.length !== 1) return { count: matches.length, visibleOptions: options.length };
  matches[0].scrollIntoView({ block: 'nearest', inline: 'nearest' });
  const box = matches[0].getBoundingClientRect();
  return { count: 1, x: box.left + box.width / 2, y: box.top + box.height / 2 };
}

/**
 * Choose `value` in the control at `selector`. A native select is set by its matching option's
 * value. A combobox is opened when it is collapsed; then the matching option is clicked once it
 * appears, polling every `pollMs` for up to `timeoutMs`. Throws when no single option matches.
 * @param {{ evaluate: Function, clickSelector: Function, clickPoint: Function, setNative: Function }} ops
 */
async function performChoice(ops, { selector, value, pollMs, timeoutMs }) {
  const plan = await ops.evaluate(prepareChoice, { selector, value });
  if (plan.error) throw new Error(`select ${selector}: ${plan.error}`);
  if (plan.mode === 'native') {
    await ops.setNative(selector, plan.optionValue);
    return { selector, mode: plan.mode, selected: [plan.optionValue] };
  }
  if (!plan.expanded) await ops.clickSelector(selector);
  const deadline = Date.now() + timeoutMs;
  for (;;) {
    const option = await ops.evaluate(locateOption, { selector, value });
    if (option.count === 1) {
      await ops.clickPoint(option.x, option.y);
      return { selector, mode: plan.mode, option: value };
    }
    if (Date.now() >= deadline) {
      throw new Error(`select ${selector}: ${option.count} visible options named ${JSON.stringify(value)} among ${option.visibleOptions}`);
    }
    await new Promise((resolve) => setTimeout(resolve, pollMs));
  }
}

export { locateOption, performChoice, prepareChoice };
