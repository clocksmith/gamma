"use strict";

class Cashier {
  constructor(n, discount, products, prices) {
    this.n = n;
    this.discount = discount;
    this.priceMap = new Map();
    for (let i = 0; i < products.length; i++) {
      this.priceMap.set(products[i], prices[i]);
    }
    this.count = 0;
  }
  getBill(product, amount) {
    this.count++;
    let total = 0;
    for (let i = 0; i < product.length; i++) {
      total += this.priceMap.get(product[i]) * amount[i];
    }
    if (this.count % this.n === 0) {
      return (total * (100 - this.discount)) / 100.0;
    }
    return total;
  }
}

function solve(operation_names, argument_lists) {
  const [n, d, prods, prices] = argument_lists[0];
  const inst = new Cashier(n, d, prods, prices);
  const out = [null];
  for (let i = 1; i < operation_names.length; i++) {
    out.push(inst.getBill(argument_lists[i][0], argument_lists[i][1]));
  }
  return out;
}

module.exports = solve;
module.exports.solve = solve;
module.exports.Cashier = Cashier;
