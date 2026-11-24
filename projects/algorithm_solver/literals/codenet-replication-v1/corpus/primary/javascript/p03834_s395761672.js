"use strict";

function main(input){
  const args = input.trim().split(',');
  console.log(args.join(" "));
}

main(require('fs').readFileSync('/dev/stdin', 'utf8'));  