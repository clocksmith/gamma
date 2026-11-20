// Fawn workspace differentiation — parsing helpers for the service's outline view.

const MONEY = /\$(\d+)\.(\d{2})/;
const HANDLE = /\[(h[0-9a-z-]+) (\w+) "([^"]*)"(?: = ("(?:[^"\\]|\\.)*"))?\]/g;

function cents(text) {
  const match = MONEY.exec(text);
  return match ? Number(match[1]) * 100 + Number(match[2]) : null;
}

/** Interactive elements in an outline: [handle role "name" = "value"]. */
function controls(outline) {
  return [...outline.matchAll(HANDLE)].map(([, handle, role, name, value]) => ({
    handle,
    role,
    name,
    value: value === undefined ? null : JSON.parse(value),
  }));
}

export { cents, controls };
