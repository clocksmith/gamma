'use strict'

function Main(input) {
  const a = Number(input.split(' ')[0]);
  const b = Number(input.split(' ')[1]);

  if(a + b === 15) {
    console.log('+');
  } else if(a * b === 15) {
    console.log('*');
  } else {
    console.log('x');
  }

}

Main(require("fs").readFileSync("/dev/stdin", "utf8").trim());