"use strict"
const Main = (input) =>{
let xs = input.trim().split(' ').map(v=>parseInt(v,10));
    let a = xs[0];
    let b = xs[1];
    let ans = 1;
  if (b==1){
    console.log(0)
  }else{
    for(let i = 0; (a-1)*i+a < b; i++){
    ans += 1;
    }
    console.log(ans);
    }}
Main(require('fs').readFileSync('/dev/stdin','utf8'));