/**
 * 3860. Unique Email Groups
 * Authored candidate: not executed, imported, syntax-checked, tested, or qualified.
 * Signature: solve(emails).
 * Algorithm: Normalize local and domain components exactly as declared, then count unique pairs.
 * Complexity: O(total email characters) time and space.
 * Numeric semantics: Exact integer arithmetic on the published input bounds; JavaScript Number results remain safe integers.
 * Mutation: Does not mutate input arrays, rows, strings, or trees.
 * Interface: Canonical solve(emails); native judge method name not independently bound.
 * Specification: https://leetcode.com/problems/unique-email-groups/description/
 * Consulted public statement/reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3800-3899/3860.Unique%20Email%20Groups/README_EN.md
 * Reference repository attribution: Doocs contributors, CC-BY-SA-4.0.
 * New readable implementations; no third-party source bodies copied verbatim.
 * No protected tests or private reference implementations used.
 */

function solve(emails) {
  const groups = new Set();
  for (const email of emails) {
    const separator = email.indexOf("@");
    let local = email.slice(0, separator);
    const plus = local.indexOf("+");
    if (plus !== -1) local = local.slice(0, plus);
    local = local.replace(/\./g, "").toLowerCase();
    groups.add(local + "@" + email.slice(separator + 1).toLowerCase());
  }
  return groups.size;
}

if (typeof module !== "undefined" && module.exports) {
  module.exports = { solve };
}
