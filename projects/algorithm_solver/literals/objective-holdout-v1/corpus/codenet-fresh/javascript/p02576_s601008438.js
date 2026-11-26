'use strict'
 
function main(s) {
  s = s.replace(/\r?\n/g,'');
  s = s.split(' ');
  
  let N = Number(s[0]); //need takoyaki
  let X = Number(s[1]); //max takoyaki
  let T = Number(s[2]); //time 
  
  let nT = Math.ceil(N / X);
  let kekka = T * nT;
  
  console.log(kekka);
}
 
main(require("fs").readFileSync("/dev/stdin", "utf8"));
