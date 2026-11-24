'use strict'
 
function Main(input) {
	const ipts = input.split('\n');
	const A = Number(ipts[0].split(' ')[0]);
	const B = Number(ipts[0].split(' ')[1]);
	const C = Number(ipts[0].split(' ')[2]);
	const K = Number(ipts[1]);
	let answer = 0;
	
	answer = Math.max(A, B, C) *  Math.pow(2, K) + A + B + C - Math.max(A, B, C);
	
	console.log(answer);
 
}
 
Main(require("fs").readFileSync("/dev/stdin", "utf8"));