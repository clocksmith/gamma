"use strict";

function Main(input) {
  let x = input.trim().split(' ')[0]*1;
  let y = input.trim().split(' ')[1]*1;
  let ans = "No";
  if(x == y){
  	ans = "Yes";
  }
  console.log(ans);
}
Main(require("fs").readFileSync("/dev/stdin", "utf8"));