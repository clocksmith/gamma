// Presentation only: components receive public snapshots, never a running match.
export function node(tag, className, text) {
  const element = document.createElement(tag);
  if (className) element.className = className;
  if (text !== undefined) element.textContent = text;
  return element;
}
export function text(element, value) {
  const next = String(value ?? "");
  if (element.textContent !== next) element.textContent = next;
}
export function reconcile(parent, items, key, create, update) {
  const existing = new Map(
    [...parent.children].map((child) => [child.dataset.key, child]),
  );
  items.forEach((item, index) => {
    const id = String(key(item));
    const element = existing.get(id) || create(item);
    element.dataset.key = id;
    update(element, item);
    if (parent.children[index] !== element)
      parent.insertBefore(element, parent.children[index] || null);
    existing.delete(id);
  });
  for (const element of existing.values()) element.remove();
}
export function orgToken(org, kit, label) {
  const token = node("span", "org-token");
  updateOrg(token, org, kit, label);
  return token;
}
export function updateOrg(token, org, kit, label) {
  token.style.setProperty("--kit-color", kit.color);
  token.dataset.org = org.id;
  token.dataset.equipped = String(Boolean(org.equipped));
  token.title = `${label} · Org ${org.id.split("-").at(-1)} · ${org.equipped ? "Equipped: double production" : "Normal production"}`;
  token.setAttribute("aria-label", token.title);
  text(
    token,
    `${kit.symbol}${org.id.split("-").at(-1)}${org.equipped ? "²" : ""}`,
  );
}

export function format(template, values = {}) {
  return template.replace(/\{(\w+)\}/g, (_, key) => String(values[key] ?? ""));
}
