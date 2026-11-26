'use strict';

const inputs = require('fs').readFileSync('/dev/stdin', 'utf8').split('\n');

const input = inputs[0].split(' ').map(v => parseInt(v, 10));

let a = 0;
for (let i = 1 ; i <= input[0] ; ++i) {
  a += i
}
a -= input[0];

let b = 0;
for (let i = 1 ; i <= input[1] ; ++i) {
  b = b + i;
}
b -= input[1];

console.log(a + b);
