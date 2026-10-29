'use strict';
// Source-free JS observer controls with toy classes; never loads numbered sources.
const assert = require('assert'), h = require('./native_harness.cjs');
const transport = {decode: (x) => structuredClone(x), encode: (x) => structuredClone(x), aliases: () => []};
const T = 'hack2hire:69334452e8ebbb1c53caf2c4';
class ArticleSystem {
  constructor() { this.names = []; this.votes = new Map(); }
  addArticle(articleName) { this.names.push(articleName); return this.names.length; }
  upvoteArticle(articleId, userId) { this.votes.set(userId + ':' + articleId, [articleId, 1]); }
  downvoteArticle(articleId, userId) { this.votes.set(userId + ':' + articleId, [articleId, -1]); }
  getRecentFlips(userId, k) { return []; }
  getTopArticles(k) {
    const score = this.names.map(() => 0);
    for (const [a, v] of this.votes.values()) score[a - 1] += v;
    return this.names.map((_, i) => i).sort((x, y) => score[y] - score[x] || x - y).slice(0, k).map((i) => this.names[i]);
  }
}
const args = [['ArticleSystem', 'addArticle', 'addArticle', 'downvoteArticle', 'getTopArticles'], [[], ['x'], ['y'], [1, 5], [2]]];
for (let i = 0; i < 2; i++) {
  const r = h.observe({ArticleSystem}, T, {args}, transport);
  assert.deepStrictEqual(r.result, [null, 1, 2, null, ['y', 'x']]);
  assert.deepStrictEqual(r.native_method_return_types, ['constructed', 'number', 'number', 'undefined', 'object']);
  assert.deepStrictEqual(r.args_before, r.args_after);
}
const s = h.observe({ArticleSystem}, T, {args: [['ArticleSystem', 'addArticle', 'upvoteArticle', 'getTopArticles'], [[], ['z'], [1, 2], [5]]]}, transport);
assert.deepStrictEqual(s.result, [null, 1, null, ['z']]);
assert.throws(() => h.observe({solve: () => []}, T, {args}, transport));
assert.throws(() => h.shape('hack2hire:unknown', args));
console.log('4 source-free JS observer controls passed');
