"use strict";
const Main = (input) =>{
	let xs = input.trim().split('\n');
    let xs1 = xs[0].split(" ").map(v=>parseInt(v,10));
    let N = xs1[0];
    let K = xs1[1];
    let Q = xs1[2];
    //console.log(N,K,Q);
    let win = input.split('\n').slice(1, Q + 1);
    let result = new Array(N).fill(K-Q);
   // console.log(win,result);
    for(let i =0; i < Q; i++){
      result[win[i]-1]++
    }
   for(let j =0; j < N; j++){
    if(result[j] > 0){
      console.log("Yes");  
    }else{
      console.log("No");
    }
   }
}
Main(require('fs').readFileSync('/dev/stdin','utf8'));