"use strict";
// Hack2Hire 69f2665342791c82ab992694 (Design Recipe Management System, variant 1 of 4) over an INFERRED spec; qualification unknown.

class RecipeManager {
  constructor() {
    this.recipes = new Map(); // recipe id -> record
    this.byName = new Map(); // lower-cased name -> recipe id
    this.count = 0;
  }

  addRecipe(name, ingredients, steps) {
    const low = name.toLowerCase();
    if (this.byName.has(low)) return "";
    this.count += 1;
    const recipeId = "recipe" + this.count;
    const rec = {n: this.count, name, ingredients: ingredients.slice(), steps: steps.slice()};
    this.recipes.set(recipeId, rec);
    this.byName.set(low, recipeId);
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
    this.byName.delete(rec.name.toLowerCase());
    this.byName.set(low, recipeId);
    rec.name = name; rec.ingredients = ingredients.slice(); rec.steps = steps.slice();
    return true;
  }

  deleteRecipe(recipeId) {
    const rec = this.recipes.get(recipeId);
    if (rec === undefined) return false;
    this.recipes.delete(recipeId);
    this.byName.delete(rec.name.toLowerCase());
    return true;
  }
}

function solve(operationNames, argumentLists) {
  if (operationNames[0] !== "RecipeManager" || argumentLists[0].length !== 0) throw new Error("exact initial constructor required");
  const instance = new RecipeManager(...argumentLists[0]);
  const allowed = new Set(["addRecipe", "getRecipe", "updateRecipe", "deleteRecipe"]);
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
