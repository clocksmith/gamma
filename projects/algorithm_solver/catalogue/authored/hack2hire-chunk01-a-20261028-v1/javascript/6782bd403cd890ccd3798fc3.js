"use strict";
// Hack2Hire 6782bd403cd890ccd3798fc3 (Construct Restaurant Daily Menu) over an INFERRED spec; qualification unknown.
function solve(menu) {
  if (!menu.active) return null;
  const root = {key: menu.key, value: menu.value, active: true, children: []}, stack = [[menu, root]];
  while (stack.length) {
    const [source, copy] = stack.pop();
    for (const child of source.children) {
      if (!child.active) continue;
      const node = {key: child.key, value: child.value, active: true, children: []};
      copy.children.push(node);
      stack.push([child, node]);
    }
  }
  return root;
}
function buildDailyMenu(menu) { return solve(menu); }
module.exports = solve;
module.exports.buildDailyMenu = buildDailyMenu;
