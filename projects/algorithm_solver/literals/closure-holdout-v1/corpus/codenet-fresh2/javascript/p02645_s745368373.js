"use strict";

const main = (arg) => {
  const input = arg.trim().split("\n")[0];
  console.log(input.substr(0, 3));
}
main(require('fs').readFileSync('/dev/stdin', 'utf8'));  
