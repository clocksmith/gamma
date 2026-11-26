'use strict';
function main(input) {
  const arr = input.trim();
  let x = '';

  for (let i = 0; i < arr.length; i ++) {
    x += 'x';
  }
  
  console.log(x);
}

main(require("fs").readFileSync("/dev/stdin", "utf8"));