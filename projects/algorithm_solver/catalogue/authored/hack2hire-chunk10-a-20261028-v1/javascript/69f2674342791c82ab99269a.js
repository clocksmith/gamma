"use strict";
// Hack2Hire 69f2674342791c82ab99269a (Design Recipe Management System, variant 3 of 4) over an INFERRED spec; qualification unknown.

class RecipeManager {
  constructor() {
    this.recipes = new Map(); // recipe id -> record
    this.byName = new Map(); // lower-cased name -> recipe id
    this.count = 0;
    this.byIngredient = new Map(); // lower-cased ingredient -> set of recipe numbers
  }

  addRecipe(name, ingredients, steps) {
    const low = name.toLowerCase();
    if (this.byName.has(low)) return "";
    this.count += 1;
    const recipeId = "recipe" + this.count;
    const rec = {n: this.count, name, ingredients: ingredients.slice(), steps: steps.slice(), sum: 0, votes: 0};
    this.recipes.set(recipeId, rec);
    this.byName.set(low, recipeId);
    this._index(rec, 1);
    return recipeId;
  }

  getRecipe(recipeId) {
    const rec = this.recipes.get(recipeId);
    return rec === undefined ? [] : [rec.name, rec.ingredients.slice(), rec.steps.slice()];
  }

  updateRecipe(recipeId, name, ingredients, steps) {
    const rec = this.recipes.get(recipeId);
    if (rec === undefined) return false;
    const low = name.toLowerCase(), owner = this.byName.get(low);
    if (owner !== undefined && owner !== recipeId) return false;
    this._index(rec, -1);
    this.byName.delete(rec.name.toLowerCase());
    this.byName.set(low, recipeId);
    rec.name = name; rec.ingredients = ingredients.slice(); rec.steps = steps.slice();
    this._index(rec, 1);
    return true;
  }

  deleteRecipe(recipeId) {
    const rec = this.recipes.get(recipeId);
    if (rec === undefined) return false;
    this.recipes.delete(recipeId);
    this.byName.delete(rec.name.toLowerCase());
    this._index(rec, -1);
    return true;
  }

  _index(rec, sign) {
    for (const low of new Set(rec.ingredients.map((g) => g.toLowerCase()))) {
      if (sign > 0) {
        if (!this.byIngredient.has(low)) this.byIngredient.set(low, new Set());
        this.byIngredient.get(low).add(rec.n);
      } else this.byIngredient.get(low).delete(rec.n);
    }
  }

  searchByIngredient(ingredient) {
    const ids = this.byIngredient.get(ingredient.toLowerCase());
    return ids === undefined ? [] : [...ids].sort((a, b) => a - b).map((n) => "recipe" + n);
  }

  rateRecipe(recipeId, rating) {
    const rec = this.recipes.get(recipeId);
    if (rec === undefined) return false;
    rec.sum += rating; rec.votes += 1;
    return true;
  }

  getTopRated(k) {
    // exact: higher average (cross-multiplied), then lower id number
    const better = (a, b) => { const l = a.sum * b.votes, r = b.sum * a.votes; return l > r || (l === r && a.n < b.n); };
    const rated = [...this.recipes.values()].filter((rec) => rec.votes > 0);
    let best;
    if (k < 64 && k < rated.length) {
      best = []; // small selection buffer, best first
      for (const rec of rated) {
        if (best.length === k && !better(rec, best[best.length - 1])) continue;
        let i = best.length;
        while (i > 0 && better(rec, best[i - 1])) i -= 1;
        best.splice(i, 0, rec);
        if (best.length > k) best.pop();
      }
    } else best = rated.sort((a, b) => (better(a, b) ? -1 : better(b, a) ? 1 : 0)).slice(0, k);
    return best.map((rec) => "recipe" + rec.n);
  }
}

function solve(operationNames, argumentLists) {
  if (operationNames[0] !== "RecipeManager" || argumentLists[0].length !== 0) throw new Error("exact initial constructor required");
  const instance = new RecipeManager(...argumentLists[0]);
  const allowed = new Set(["addRecipe", "getRecipe", "updateRecipe", "deleteRecipe", "searchByIngredient", "rateRecipe", "getTopRated"]);
  const result = [null];
  for (let i = 1; i < operationNames.length; i++) {
    if (!allowed.has(operationNames[i])) throw new Error("unknown method");
    const value = instance[operationNames[i]](...argumentLists[i]);
    result.push(value === undefined ? null : value);
  }
  return result;
}

module.exports = solve;
module.exports.RecipeManager = RecipeManager;
