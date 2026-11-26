'use strict'

function main(s) {

  const nums = s.split('\n')[1].split(' ').map(n => Number(n));
  const odd_len = nums.filter(n => n % 2 === 1).length;

  const answer = (odd_len % 2 === 0) ? 'YES' : 'NO';
  console.log(answer);
}

main(require("fs").readFileSync("/dev/stdin", "utf8"));
