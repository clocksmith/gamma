"use strict";

function main(input) {
  var N = splitNum(input).slice(0, 4);
  N.sort();
  var res = JSON.stringify(N) === JSON.stringify([1, 4, 7, 9]);
  console.log(res ? 'YES' : 'NO');
}

main(require('fs').readFileSync('/dev/stdin', 'utf8'));

function splitNum(line) {
  return line.split(/\s+/).map(function (n) {
    return parseInt(n);
  });
}
