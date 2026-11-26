'use strict';
const main = input => {
  const nums = input[0].split(' ').map(val => parseInt(val));
  let n = nums[0], k = nums[1];
  k=k>n?n:k;
  let h = input[1].split(' ').map(val => parseInt(val));
  h.sort((x, y) => y-x);
  // console.log(h);
  let arr = h.slice(k, h.length);
  if (!arr.length) return console.log(0);
  let ans = arr.reduce((prev, current) => prev + current);
  console.log(ans);
  // console.log(arr);
  
}
main(require("fs").readFileSync("/dev/stdin", "utf8").split('\n'));