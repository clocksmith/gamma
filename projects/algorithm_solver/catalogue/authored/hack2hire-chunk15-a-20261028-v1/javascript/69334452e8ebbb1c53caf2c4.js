"use strict";
// Hack2Hire 69334452e8ebbb1c53caf2c4 (Design Article System) over an INFERRED spec; qualification unknown.

class ArticleSystem {
  constructor() {
    this.names = [null];
    this.score = [0];
    this.order = [];
    this.votes = new Map();
    this.flips = new Map();
  }

  position(score, article) {
    let lo = 0, hi = this.order.length;
    while (lo < hi) {
      const mid = (lo + hi) >> 1, other = this.order[mid], s = this.score[other];
      if (s > score || (s === score && other < article)) lo = mid + 1; else hi = mid;
    }
    return lo;
  }

  addArticle(articleName) {
    this.names.push(articleName);
    this.score.push(0);
    const article = this.names.length - 1;
    this.order.splice(this.position(0, article), 0, article);
    return article;
  }

  vote(article, user, value) {
    const key = user * 16384 + article, old = this.votes.get(key) || 0;
    if (old === value) return;
    this.votes.set(key, value);
    this.order.splice(this.position(this.score[article], article), 1);
    this.score[article] += value - old;
    this.order.splice(this.position(this.score[article], article), 0, article);
    if (old === -value) {
      if (!this.flips.has(user)) this.flips.set(user, {nodes: new Map(), head: null});
      const list = this.flips.get(user);
      let node = list.nodes.get(article);
      if (node) {
        if (list.head === node) return;
        node.prev.next = node.next;
        if (node.next) node.next.prev = node.prev;
      } else {
        node = {article, prev: null, next: null};
        list.nodes.set(article, node);
      }
      node.prev = null;
      node.next = list.head;
      if (list.head) list.head.prev = node;
      list.head = node;
    }
  }

  upvoteArticle(articleId, userId) {
    this.vote(articleId, userId, 1);
  }

  downvoteArticle(articleId, userId) {
    this.vote(articleId, userId, -1);
  }

  getRecentFlips(userId, k) {
    const result = [], list = this.flips.get(userId);
    for (let node = list ? list.head : null; node && result.length < k; node = node.next) result.push(this.names[node.article]);
    return result;
  }

  getTopArticles(k) {
    return this.order.slice(0, k).map((article) => this.names[article]);
  }
}

function solve(operationNames, argumentLists) {
  if (operationNames[0] !== "ArticleSystem" || argumentLists[0].length !== 0) throw new Error("exact initial constructor required");
  const instance = new ArticleSystem(...argumentLists[0]);
  const allowed = new Set(["addArticle", "upvoteArticle", "downvoteArticle", "getRecentFlips", "getTopArticles"]);
  const result = [null];
  for (let i = 1; i < operationNames.length; i++) {
    if (!allowed.has(operationNames[i])) throw new Error("unknown method");
    const value = instance[operationNames[i]](...argumentLists[i]);
    result.push(value === undefined ? null : value);
  }
  return result;
}

module.exports = solve;
module.exports.ArticleSystem = ArticleSystem;
