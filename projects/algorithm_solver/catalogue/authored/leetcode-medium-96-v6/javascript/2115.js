'use strict';

// 2115. Find All Possible Recipes from Given Supplies: propagate available ingredients through recipe dependency counts.
// O(r + e + s) expected time and space for recipes, ingredient entries, and supplies; inputs are read-only.
function solve(recipes, ingredients, supplies) {
  const dependents = new Map();
  const remaining = ingredients.map(required => required.length);
  for (let index = 0; index < ingredients.length; index += 1) {
    for (const ingredient of ingredients[index]) {
      if (!dependents.has(ingredient)) dependents.set(ingredient, []);
      dependents.get(ingredient).push(index);
    }
  }
  const available = new Set(supplies);
  const queue = Array.from(available);
  const completed = new Array(recipes.length).fill(false);
  for (let index = 0; index < recipes.length; index += 1) {
    if (remaining[index] === 0) {
      completed[index] = true;
      if (!available.has(recipes[index])) {
        available.add(recipes[index]);
        queue.push(recipes[index]);
      }
    }
  }
  for (let head = 0; head < queue.length; head += 1) {
    for (const index of dependents.get(queue[head]) || []) {
      remaining[index] -= 1;
      if (remaining[index] === 0) {
        completed[index] = true;
        if (!available.has(recipes[index])) {
          available.add(recipes[index]);
          queue.push(recipes[index]);
        }
      }
    }
  }
  return recipes.filter((_, index) => completed[index]);
}

const findAllRecipes = solve;
class Solution {
  findAllRecipes(recipes, ingredients, supplies) { return solve(recipes, ingredients, supplies); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, findAllRecipes };
