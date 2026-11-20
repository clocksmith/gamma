// Trusted, reviewed group meanings. The independent field-ID oracle lives in oracle.json.
const field = (slot, labels, type = 'text') => ({ kind: 'fill', slot,
  locators: labels.map(label => ['textbox', label, 'input', type]) });
export function groupsFor(vendor) {
  const contact = vendor === 'greenhouse'
    ? [field('firstName', ['First Name']), field('lastName', ['Last Name'])]
    : [field('fullName', ['Full name'])];
  contact.push(field('email', ['Email', 'Email address'], vendor === 'lever' ? 'email' : 'text'),
    field('phone', ['Phone']));
  if (vendor === 'lever') contact.push(field('company', ['Current company']));
  return [
    { id: 'contact', steps: [...contact, { kind: 'click', locators: [['button', 'Continue', 'button', '']] }] },
    { id: 'questions', steps: [{ kind: 'select', slot: 'workMode', locators: [['combobox', 'Work arrangement', 'select', '']] },
      { kind: 'click', locators: [['button', 'Review application', 'button', '']] }] },
  ];
}
export const intermediateClicks = [['button', 'Continue', 'button', ''], ['button', 'Review application', 'button', '']];

// Scripted baseline uses stable accessibility labels, not the oracle's field IDs.
export function scriptedDecision(context, vendor) {
  const meanings = groupsFor(vendor).flatMap(group => group.steps).filter(step => step.slot);
  meanings.push(field('city', ['Current city']), field('visa', ['Visa type']),
    { kind: 'select', slot: 'sponsorship', locators: [['combobox', 'Requires sponsorship', 'select', '']] });
  for (const meaning of meanings) {
    const matches = context.observation.elements.filter(el => meaning.locators.some(locator =>
      JSON.stringify(locator) === JSON.stringify([el.role, el.label, el.tag, el.inputType ?? ''])));
    if (matches.length > 1) return { tool: 'ask_human', input: { reason: 'Ambiguous compatible field' } };
    const el = matches[0];
    if (el && el.value !== context.inputs[meaning.slot]) return { tool: 'act', input: {
      kind: meaning.kind, slot: meaning.slot, handle: el.handle } };
  }
  const buttons = context.observation.elements.filter(el => intermediateClicks.some(locator => locator[1] === el.label));
  if (buttons.length === 1) return { tool: 'act', input: { kind: 'click', handle: buttons[0].handle } };
  return { tool: 'finish', input: { summary: 'Review reached without submission' } };
}
