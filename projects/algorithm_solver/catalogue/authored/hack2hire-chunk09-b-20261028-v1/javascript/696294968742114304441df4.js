"use strict";
// Hack2Hire 696294968742114304441df4 (Company Role Assignment) over an INFERRED spec; qualification unknown.

function solve(existingAssociations, newAssociations) {
  // '|' cannot occur in ids or roles, so it separates key parts unambiguously.
  const triples = new Set(), roles = new Set();
  for (const [company, contact, role] of existingAssociations) {
    triples.add(company + '|' + contact + '|' + role);
    roles.add(company + '|' + role);
  }
  const out = [];
  for (const [company, contact, role] of newAssociations) {
    const triple = company + '|' + contact + '|' + role, pair = company + '|' + role;
    if (triples.has(triple)) out.push('ALREADY_EXISTS');
    else if (roles.has(pair)) out.push('ROLE_TAKEN');
    else { out.push('VALID'); triples.add(triple); roles.add(pair); }
  }
  return out;
}

function validateAssociations(existingAssociations, newAssociations) { return solve(existingAssociations, newAssociations); }

module.exports = solve;
module.exports.validateAssociations = validateAssociations;
