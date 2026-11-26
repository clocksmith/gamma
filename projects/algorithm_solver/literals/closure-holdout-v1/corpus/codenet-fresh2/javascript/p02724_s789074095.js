"use strict";

const fs = require("fs");

const lines = fs.readFileSync("/dev/stdin", "utf-8").split("\n");
lines.pop();

let amount = Number(lines[0]);
let result = 0;

result += Math.floor(amount / 500) * 1000;
amount %= 500;

result += Math.floor(amount / 5) * 5;

console.log(result);
