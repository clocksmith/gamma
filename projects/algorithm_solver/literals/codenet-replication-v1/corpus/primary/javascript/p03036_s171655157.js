'use strict'
function Main(input) {
    input = input.split(' ');
    let r = parseInt(input[0], 10);
    let D = parseInt(input[1], 10);
    let n = parseInt(input[2], 10);
  	let x = [n*r - D];
	for(let i = 0; i < 10; i++){
      let ans = x[i]*r - D;
      x.push(ans);
	console.log('%d',x[i]);
    }
}
Main(require("fs").readFileSync("/dev/stdin", "utf8"));
