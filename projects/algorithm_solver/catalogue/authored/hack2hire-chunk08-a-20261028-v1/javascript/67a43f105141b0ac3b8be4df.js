"use strict";
// Hack2Hire 67a43f105141b0ac3b8be4df (Recipes From Ingredients) over an INFERRED spec; qualification unknown.

function solve(recipes, ingredients) {
  const supply = new Int32Array(26);
  for (let i = 0; i < ingredients.length; i++) supply[ingredients.charCodeAt(i) - 97]++;
  let count = 0;
  const need = new Int32Array(26);
  for (const recipe of recipes) {
    need.fill(0);
    let ok = true;
    for (let i = 0; i < recipe.length; i++) {
      const c = recipe.charCodeAt(i) - 97;
      if (++need[c] > supply[c]) { ok = false; break; }
    }
    if (ok) count++;
  }
  return count;
}

function countRecipes(recipes, ingredients) { return solve(recipes, ingredients); }

module.exports = solve;
module.exports.countRecipes = countRecipes;
