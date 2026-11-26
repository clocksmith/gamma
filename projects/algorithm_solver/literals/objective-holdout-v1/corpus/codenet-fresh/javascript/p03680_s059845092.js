"use strict";

var main = function main(input) {
  var args = input.split('\n');
  var N = parseInt(args[0], 10);
  var a = [];

  for (var i = 1; i <= N; i++) {
    a.push(parseInt(args[i], 10));
  }

  var next = a[0];
  var flag = false;
  var count = 0;

  for (var _i = 0; _i < N; _i++) {
    count++;

    if (next == 2) {
      flag = true;
      break;
    }

    next = a[next - 1];
  }

  if (flag) {
    console.log(count);
  } else {
    console.log(-1);
  }
};

main(require('fs').readFileSync('/dev/stdin', 'utf-8'));