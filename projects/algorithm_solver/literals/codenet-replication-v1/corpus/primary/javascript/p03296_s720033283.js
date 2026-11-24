'use strict'

function Main(input) {
  const N = Number(input.split('\n')[0]);
  let line = input.split('\n')[1].split(' ');
  let count = 0;

  for(let i=1; i<N; i++) {
    if(line[i] === line[i-1]) {
      line[i] = 'x';
      count++;
    } else if(line[i] === line[i+1]) {
      line[i+1] = 'x'
      count++;
    }
  }

  console.log(count);

}

Main(require("fs").readFileSync("/dev/stdin", "utf8").trim());